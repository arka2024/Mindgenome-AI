from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.gemini import gemini_adapter
from app.adapters.neo4j import neo4j_adapter
from app.core.exceptions import NotFoundException, ValidationProblemException
from app.core.logging import logger
from app.domain.mastery import AnswerRecord, compute_mastery
from app.domain.path import determine_next_step
from app.models.enums import LLMPurpose, QuestionDifficulty
from app.models.learning import Concept, Question, QuizAttempt
from app.models.user import User
from app.repositories.learning_repo import LearningRepository
from app.schemas.learning import (
    ConceptDelta,
    MasteryScoreResponse,
    NextAction,
    PerQuestionResult,
    QuizAttemptResponse,
    QuizQuestionView,
    QuizResultResponse,
    QuizSubmitRequest,
)


class QuizService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LearningRepository(session)

    async def get_or_create_quiz(
        self,
        user: User,
        concept_id: uuid.UUID,
        session_id: uuid.UUID | None = None,
    ) -> QuizAttemptResponse:
        # Verify concept exists
        concept = await self.session.get(Concept, concept_id)
        if not concept or concept.user_id != user.id:
            raise NotFoundException(detail="Concept not found.")

        # Find or create questions for this concept
        questions = await self.repo.get_questions_for_concept(concept_id, user.id, limit=5)
        if not questions:
            # Generate questions via Gemini
            system_prompt = (
                "You are an assessment engine for MindGenome AI. Generate 5 multiple-choice questions "
                "testing understanding of the concept. For each question provide: stem, choices (4 options), "
                "correct_index (0-3), difficulty (easy, medium, hard), hint."
            )
            user_prompt = f"Concept: {concept.canonical_name}\nDefinition: {concept.definition or ''}"

            q_data, _ = await gemini_adapter.generate_structured_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                purpose=LLMPurpose.QUESTION_GENERATE,
                user_id=str(user.id),
            )

            # Seed questions if Gemini returned mock
            raw_qs = q_data.get("questions") or [
                {
                    "stem": f"What is the primary objective of {concept.canonical_name}?",
                    "choices": [
                        "Iterative error reduction via gradient descent",
                        "Random feature subset selection",
                        "Static clustering",
                        "Unsupervised dimensionality reduction",
                    ],
                    "correct_index": 0,
                    "difficulty": "medium",
                    "hint": "Think about residual minimization.",
                },
                {
                    "stem": f"Which component is a fundamental building block of {concept.canonical_name}?",
                    "choices": [
                        "Decision tree weak learners",
                        "Neural recurrent gates",
                        "Markov chains",
                        "Support vector hyperplanes",
                    ],
                    "correct_index": 0,
                    "difficulty": "easy",
                    "hint": "Recall the weak learner representation.",
                },
                {
                    "stem": f"How does {concept.canonical_name} address overfitting?",
                    "choices": [
                        "Shrinkage rate (learning rate) and tree depth limits",
                        "Increasing tree depth indefinitely",
                        "Ignoring residuals",
                        "Using all training data without regularization",
                    ],
                    "correct_index": 0,
                    "difficulty": "hard",
                    "hint": "Consider hyperparameter tuning.",
                },
            ]

            for item in raw_qs:
                fp = hashlib.sha256(f"{concept.id}:{item['stem']}".encode()).hexdigest()
                q = await self.repo.create_question(
                    user_id=user.id,
                    stem=item["stem"],
                    choices=item["choices"],
                    correct_index=item["correct_index"],
                    difficulty=QuestionDifficulty(item.get("difficulty", "medium")),
                    concept_id=concept.id,
                    fingerprint=fp,
                )
                questions.append(q)

        # Create attempt
        attempt = await self.repo.create_quiz_attempt(
            user_id=user.id,
            concept_id=concept.id,
            session_id=session_id,
        )

        # Do NOT expose correct_index before submission!
        question_views = [
            QuizQuestionView(
                id=str(q.id),
                stem=q.stem,
                choices=q.choices,
                difficulty=q.difficulty.value,
                hint="Think carefully about the foundational theory.",
                concept_tags=[concept.canonical_name],
            )
            for q in questions
        ]

        return QuizAttemptResponse(
            id=str(attempt.id),
            attempt_id=str(attempt.id),
            concept_id=str(concept.id),
            concept_name=concept.canonical_name,
            feedback_mode="immediate",
            questions=question_views,
        )

    async def get_quiz_attempt_view(self, user: User, attempt_id: uuid.UUID) -> QuizAttemptResponse:
        attempt = await self.repo.get_quiz_attempt(attempt_id, user.id)
        if not attempt:
            raise NotFoundException(detail="Quiz attempt not found.")

        concept = attempt.target_concept
        questions = await self.repo.get_questions_for_concept(attempt.target_concept_id, user.id, limit=5)

        question_views = [
            QuizQuestionView(
                id=str(q.id),
                stem=q.stem,
                choices=q.choices,
                difficulty=q.difficulty.value,
                hint="Recall key concepts from your notes.",
                concept_tags=[concept.canonical_name] if concept else [],
            )
            for q in questions
        ]

        return QuizAttemptResponse(
            id=str(attempt.id),
            attempt_id=str(attempt.id),
            concept_id=str(concept.id) if concept else "",
            concept_name=concept.canonical_name if concept else "",
            feedback_mode="immediate",
            questions=question_views,
        )

    async def submit_quiz(
        self,
        user: User,
        attempt_id: uuid.UUID,
        req: QuizSubmitRequest,
    ) -> QuizResultResponse:
        attempt = await self.repo.get_quiz_attempt(attempt_id, user.id)
        if not attempt:
            raise NotFoundException(detail="Quiz attempt not found.")

        concept_id = attempt.target_concept_id
        if not concept_id:
            raise ValidationProblemException(detail="Quiz attempt has no associated concept.")

        concept = await self.session.get(Concept, concept_id)
        concept_name = concept.canonical_name if concept else "Concept"

        # Record before mastery
        prior_score = await self.repo.get_concept_mastery(user.id, concept_id)
        before_mastery = float(prior_score.mastery) if prior_score else 0.0

        # Grade submitted answers
        submitted_dict = {a.question_id: a.selected_index for a in req.answers}
        questions = await self.repo.get_questions_for_concept(concept_id, user.id, limit=10)
        q_map = {str(q.id): q for q in questions}

        per_question_results: list[PerQuestionResult] = []
        graded_answers_to_record: list[dict[str, Any]] = []
        correct_count = 0

        for q_id_str, selected_idx in submitted_dict.items():
            q_obj = q_map.get(q_id_str)
            if not q_obj:
                continue
            is_correct = selected_idx == q_obj.correct_index
            if is_correct:
                correct_count += 1

            per_question_results.append(
                PerQuestionResult(
                    question_id=q_id_str,
                    selected_index=selected_idx,
                    correct_index=q_obj.correct_index,
                    explanation=(
                        f"Correct answer: '{q_obj.choices[q_obj.correct_index]}'. "
                        f"Target concept: {concept_name}."
                    ),
                    is_correct=is_correct,
                )
            )

            graded_answers_to_record.append({
                "question_id": q_obj.id,
                "selected_index": selected_idx,
                "is_correct": is_correct,
                "time_ms": 1200,
            })

        # Persist answers in database
        await self.repo.record_attempt_answers(attempt, graded_answers_to_record)

        # Load answer history and recompute mastery using pure domain mastery engine
        history_rows = await self.repo.get_concept_answers_history(user.id, concept_id, limit=50)
        answer_records = [
            AnswerRecord(
                is_correct=ans.is_correct,
                difficulty=q.difficulty.value,
                answered_at=ans.answered_at,
                answer_id=str(ans.id),
            )
            for ans, q in history_rows
        ]

        m_result = compute_mastery(answer_records)
        updated_score_obj = await self.repo.save_mastery_result(user.id, concept_id, m_result)

        # Sync Neo4j STRUGGLES_WITH flag
        if m_result.band == "beginner" and m_result.evidence_n >= 3:
            cypher_struggle = """
            MATCH (u:User {user_id: $user_id}), (c:Concept {user_id: $user_id, concept_id: $concept_id})
            MERGE (u)-[s:STRUGGLES_WITH {user_id: $user_id}]->(c)
            ON CREATE SET s.since = datetime(), s.evidence_n = $n
            ON MATCH SET s.evidence_n = $n
            """
            await neo4j_adapter.run_query(cypher_struggle, {
                "user_id": str(user.id),
                "concept_id": str(concept_id),
                "n": m_result.evidence_n,
            })
        else:
            cypher_clean = """
            MATCH (u:User {user_id: $user_id})-[s:STRUGGLES_WITH]->(c:Concept {user_id: $user_id, concept_id: $concept_id})
            DELETE s
            """
            await neo4j_adapter.run_query(cypher_clean, {
                "user_id": str(user.id),
                "concept_id": str(concept_id),
            })

        # Calculate deltas
        deltas = [
            ConceptDelta(
                concept_id=str(concept_id),
                name=concept_name,
                before=before_mastery,
                after=float(updated_score_obj.mastery),
            )
        ]

        # Determine next recommendation via domain path planner
        next_rec = determine_next_step(
            target_concept_id=str(concept_id),
            target_concept_name=concept_name,
            target_score=float(updated_score_obj.mastery),
            ancestor_concepts=[],
            descendant_concepts=[],
        )

        mastery_dto = MasteryScoreResponse(
            concept_id=str(concept_id),
            name=concept_name,
            mastery=float(updated_score_obj.mastery),
            band=updated_score_obj.band.value,
            evidence_n=updated_score_obj.evidence_n,
            quiz_accuracy=float(updated_score_obj.quiz_accuracy),
            recent_performance=float(updated_score_obj.recent_performance),
            difficulty_adjusted=float(updated_score_obj.difficulty_adjusted),
            retention=float(updated_score_obj.retention),
            component_trace=updated_score_obj.component_trace,
        )

        return QuizResultResponse(
            attempt_id=str(attempt.id),
            correct=correct_count,
            total=len(per_question_results),
            per_question=per_question_results,
            mastery=mastery_dto,
            deltas=deltas,
            next=NextAction(
                mode=next_rec.mode,
                concept_id=next_rec.concept_id,
                concept_name=next_rec.concept_name,
                because=next_rec.because,
            ),
        )
