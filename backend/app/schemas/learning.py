from __future__ import annotations

import uuid
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class MasteryScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    name: str | None = None
    mastery: float
    band: str
    evidence_n: int
    quiz_accuracy: float
    recent_performance: float
    difficulty_adjusted: float
    retention: float
    component_trace: dict[str, Any] = Field(default_factory=dict)


class MasteryHistoryPoint(BaseModel):
    date: str
    mastery: float


class SingleMasteryHistoryResponse(MasteryScoreResponse):
    history: list[MasteryHistoryPoint] = Field(default_factory=list)


class QuizQuestionView(BaseModel):
    id: str
    stem: str
    choices: list[str]
    difficulty: str
    hint: str = ""
    concept_tags: list[str] = Field(default_factory=list)


class QuizAttemptResponse(BaseModel):
    id: str
    attempt_id: str | None = None
    concept_id: str
    concept_name: str
    feedback_mode: Literal["immediate", "end"] = "immediate"
    questions: list[QuizQuestionView] = Field(default_factory=list)


class AnswerSubmission(BaseModel):
    question_id: str
    selected_index: int


class QuizSubmitRequest(BaseModel):
    answers: list[AnswerSubmission]


class PerQuestionResult(BaseModel):
    question_id: str
    selected_index: int
    correct_index: int
    explanation: str
    is_correct: bool


class ConceptDelta(BaseModel):
    concept_id: str
    name: str
    before: float
    after: float


class NextAction(BaseModel):
    mode: Literal["learn", "remedial", "revision", "retest"]
    concept_id: str | None
    concept_name: str | None = None
    because: str


class QuizResultResponse(BaseModel):
    attempt_id: str
    correct: int
    total: int
    per_question: list[PerQuestionResult]
    mastery: MasteryScoreResponse
    deltas: list[ConceptDelta]
    next: NextAction


class LessonSection(BaseModel):
    id: str
    title: str
    body: str
    understood: bool = False


class LearningSessionResponse(BaseModel):
    id: str
    mode: str
    status: str
    concept_id: str
    concept_name: str
    because: str
    current_index: int
    sections: list[LessonSection] = Field(default_factory=list)
    current_section: str


class StartSessionRequest(BaseModel):
    mode: str = "learn"
    concept_id: uuid.UUID | None = None


class SessionProgressRequest(BaseModel):
    index: int | None = None
    understood_id: str | None = None


class LearningPathItemResponse(BaseModel):
    concept_id: str
    name: str
    because: str
    kind: Literal["learn", "remedial", "retest", "revision", "next"]
    band: str | None = None


class LearningPathResponse(BaseModel):
    items: list[LearningPathItemResponse]


class RecommendedConcept(BaseModel):
    concept_id: str
    name: str
    because: str


class RevisionListItem(BaseModel):
    concept_id: str
    name: str
    due: str


class GrowthHistoryItem(BaseModel):
    date: str
    mastery: float


class ActivityLogItem(BaseModel):
    id: str
    at: str
    text: str


class DashboardResponse(BaseModel):
    overall_mastery: float
    band_counts: dict[str, int]
    weak_concepts: list[MasteryScoreResponse]
    recommended: RecommendedConcept
    growth: list[GrowthHistoryItem]
    due_revisions: int
    revision_list: list[RevisionListItem]
    activity: list[ActivityLogItem]
    active_jobs: list[dict[str, Any]] = Field(default_factory=list)
