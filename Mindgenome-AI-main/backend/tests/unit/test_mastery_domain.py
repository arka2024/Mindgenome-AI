from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
from app.domain.mastery import AnswerRecord, compute_mastery
from app.domain.path import determine_next_step, plan_learning_path


def test_compute_mastery_empty():
    res = compute_mastery([])
    assert res.mastery == 0.0
    assert res.band == "insufficient_evidence"
    assert res.evidence_n == 0
    assert res.quiz_accuracy == 0.0


def test_compute_mastery_insufficient_evidence_when_n_less_than_3():
    now = datetime.now(timezone.utc)
    answers = [
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=now),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=now),
    ]
    res = compute_mastery(answers, now=now)
    assert res.evidence_n == 2
    assert res.band == "insufficient_evidence"
    assert res.quiz_accuracy == 100.0


def test_compute_mastery_four_components_all_correct():
    now = datetime.now(timezone.utc)
    answers = [
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=now),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=now),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=now),
    ]
    res = compute_mastery(answers, revision_successes=2, now=now)
    assert res.evidence_n == 3
    assert res.quiz_accuracy == 100.0
    assert res.recent_performance == 100.0
    assert res.difficulty_adjusted == 100.0
    assert res.retention == 100.0
    assert res.mastery == 100.0
    assert res.band == "mastered"


def test_compute_mastery_all_incorrect():
    now = datetime.now(timezone.utc)
    answers = [
        AnswerRecord(is_correct=False, difficulty="hard", answered_at=now),
        AnswerRecord(is_correct=False, difficulty="hard", answered_at=now),
        AnswerRecord(is_correct=False, difficulty="hard", answered_at=now),
    ]
    res = compute_mastery(answers, now=now)
    assert res.evidence_n == 3
    assert res.quiz_accuracy == 0.0
    assert res.recent_performance == 0.0
    assert res.difficulty_adjusted == 0.0
    assert res.retention == 0.0
    assert res.mastery == 0.0
    assert res.band == "beginner"


def test_compute_mastery_band_thresholds():
    now = datetime.now(timezone.utc)

    # 1. Beginner (<= 30)
    # 1 correct out of 4, all answered long ago
    old_time = now - timedelta(days=60)
    answers_low = [
        AnswerRecord(is_correct=True, difficulty="easy", answered_at=old_time),
        AnswerRecord(is_correct=False, difficulty="hard", answered_at=old_time),
        AnswerRecord(is_correct=False, difficulty="hard", answered_at=old_time),
        AnswerRecord(is_correct=False, difficulty="hard", answered_at=old_time),
    ]
    res_low = compute_mastery(answers_low, now=now)
    assert res_low.mastery <= 30
    assert res_low.band == "beginner"

    # 2. Developing (31 to 60)
    answers_med = [
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=now - timedelta(days=5)),
        AnswerRecord(is_correct=False, difficulty="medium", answered_at=now - timedelta(days=5)),
        AnswerRecord(is_correct=True, difficulty="easy", answered_at=now - timedelta(days=5)),
    ]
    res_med = compute_mastery(answers_med, now=now)
    assert 30 < res_med.mastery <= 80
    assert res_med.band in ("developing", "proficient")


def test_retention_decay_over_time():
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    thirty_days_ago = now - timedelta(days=30)

    ans_recent = [
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=one_day_ago),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=one_day_ago),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=one_day_ago),
    ]
    ans_old = [
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=thirty_days_ago),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=thirty_days_ago),
        AnswerRecord(is_correct=True, difficulty="medium", answered_at=thirty_days_ago),
    ]

    res_recent = compute_mastery(ans_recent, revision_successes=0, now=now)
    res_old = compute_mastery(ans_old, revision_successes=0, now=now)

    assert res_recent.retention > res_old.retention
    assert res_recent.mastery > res_old.mastery


def test_determine_next_step_weak_ancestor():
    rec = determine_next_step(
        target_concept_id="c2",
        target_concept_name="Backpropagation",
        target_score=45.0,
        ancestor_concepts=[
            {"id": "c1", "name": "Calculus Chain Rule", "mastery": 35.0, "band": "beginner", "n": 4}
        ],
        descendant_concepts=[],
    )
    assert rec.mode == "remedial"
    assert rec.concept_id == "c1"
    assert "Calculus Chain Rule" in rec.because


def test_determine_next_step_proficient_advancement():
    rec = determine_next_step(
        target_concept_id="c1",
        target_concept_name="Calculus Chain Rule",
        target_score=85.0,
        ancestor_concepts=[],
        descendant_concepts=[
            {"id": "c2", "name": "Backpropagation", "mastery": 10.0, "band": "beginner", "n": 0}
        ],
    )
    assert rec.mode == "learn"
    assert rec.concept_id == "c2"
    assert "Backpropagation" in rec.because


def test_quiz_below_75_stays_locked():
    rec = determine_next_step(
        target_concept_id="c1",
        target_concept_name="Photosynthesis",
        target_score=33.0,
        ancestor_concepts=[],
        descendant_concepts=[{"id": "c2", "name": "Calvin Cycle", "mastery": 0.0}],
        quiz_accuracy=66.0,
    )
    assert rec.mode == "retest"
    assert rec.concept_id == "c1"
    assert "75%" in rec.because


def test_quiz_at_75_unlocks_next_course():
    rec = determine_next_step(
        target_concept_id="c1",
        target_concept_name="Photosynthesis",
        target_score=75.0,
        ancestor_concepts=[],
        descendant_concepts=[{"id": "c2", "name": "Calvin Cycle", "mastery": 0.0}],
        quiz_accuracy=75.0,
    )
    assert rec.mode == "learn"
    assert rec.concept_id == "c2"
    assert "unlocked" in rec.because


def test_plan_learning_path_priority():
    concepts = [
        {"id": "1", "name": "Linear Algebra", "mastery": 95.0, "band": "mastered", "n": 5},
        {"id": "2", "name": "Gradient Descent", "mastery": 25.0, "band": "beginner", "n": 3},
        {"id": "3", "name": "Neural Networks", "mastery": 65.0, "band": "developing", "n": 4},
    ]
    path = plan_learning_path(concepts)
    assert len(path) == 3
    # Remedial should be first (Gradient Descent)
    assert path[0].kind == "remedial"
    assert path[0].name == "Gradient Descent"
    # Revision should be last (Linear Algebra)
    assert path[-1].kind == "revision"
    assert path[-1].name == "Linear Algebra"
