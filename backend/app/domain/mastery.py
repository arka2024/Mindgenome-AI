from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DIFFICULTY_WEIGHTS = {
    "easy": 0.70,
    "medium": 1.00,
    "hard": 1.30,
}

HALF_LIFE_DAYS = 14.0
LAMBDA_RECENCY = math.log(2) / HALF_LIFE_DAYS


@dataclass
class AnswerRecord:
    is_correct: bool
    difficulty: str
    answered_at: datetime
    answer_id: str | None = None


@dataclass
class MasteryResult:
    mastery: float
    band: str
    evidence_n: int
    quiz_accuracy: float
    recent_performance: float
    difficulty_adjusted: float
    retention: float
    component_trace: dict[str, Any] = field(default_factory=dict)


def compute_mastery(
    answers: list[AnswerRecord],
    revision_successes: int = 0,
    now: datetime | None = None,
) -> MasteryResult:
    """
    Compute mastery according to docs/MASTERY.md:
    M = 0.40 * Acc + 0.20 * Rec + 0.20 * DAP + 0.20 * Ret
    """
    now = now or datetime.now(timezone.utc)
    n = len(answers)

    if n == 0:
        return MasteryResult(
            mastery=0.0,
            band="insufficient_evidence",
            evidence_n=0,
            quiz_accuracy=0.0,
            recent_performance=0.0,
            difficulty_adjusted=0.0,
            retention=0.0,
            component_trace={
                "n": 0,
                "correct": 0,
                "acc": 0.0,
                "rec": 0.0,
                "dap": 0.0,
                "ret": 0.0,
                "m": 0.0,
                "revision_successes": revision_successes,
            },
        )

    # 1. Quiz Accuracy (weight 0.40)
    correct_count = sum(1 for a in answers if a.is_correct)
    acc = 100.0 * (correct_count / n)

    # 2. Recent Performance (weight 0.20)
    sum_w = 0.0
    sum_w_y = 0.0
    for a in answers:
        # Age in days
        dt_ans = a.answered_at if a.answered_at.tzinfo else a.answered_at.replace(tzinfo=timezone.utc)
        delta_days = max(0.0, (now - dt_ans).total_seconds() / 86400.0)
        w_i = math.exp(-LAMBDA_RECENCY * delta_days)
        sum_w += w_i
        if a.is_correct:
            sum_w_y += w_i

    rec = 100.0 * (sum_w_y / sum_w) if sum_w > 0 else acc

    # 3. Difficulty-Adjusted Performance (weight 0.20)
    sum_d = 0.0
    sum_d_y = 0.0
    for a in answers:
        d_val = DIFFICULTY_WEIGHTS.get(a.difficulty.lower(), 1.00)
        sum_d += d_val
        if a.is_correct:
            sum_d_y += d_val

    dap = 100.0 * (sum_d_y / sum_d) if sum_d > 0 else acc

    # 4. Retention / Revision (weight 0.20)
    # S = min(60, 7 * (1 + 0.5 * r))
    stability_days = min(60.0, 7.0 * (1.0 + 0.5 * revision_successes))

    # Delta* = days since last correct answer
    correct_answers = [a for a in answers if a.is_correct]
    if correct_answers:
        latest_correct = max(
            a.answered_at if a.answered_at.tzinfo else a.answered_at.replace(tzinfo=timezone.utc)
            for a in correct_answers
        )
        delta_star = max(0.0, (now - latest_correct).total_seconds() / 86400.0)
        ret = 100.0 * math.exp(-delta_star / stability_days)
    else:
        delta_star = 0.0
        ret = 0.0

    # Combined composite score M
    m = round(0.40 * acc + 0.20 * rec + 0.20 * dap + 0.20 * ret, 2)

    # Evidence rule and band mapping
    if n < 3:
        band = "insufficient_evidence"
    else:
        rounded_m = round(m)
        if rounded_m <= 30:
            band = "beginner"
        elif rounded_m <= 60:
            band = "developing"
        elif rounded_m <= 80:
            band = "proficient"
        else:
            band = "mastered"

    trace = {
        "n": n,
        "correct": correct_count,
        "acc": round(acc, 2),
        "rec": round(rec, 2),
        "dap": round(dap, 2),
        "ret": round(ret, 2),
        "m": m,
        "half_life_days": HALF_LIFE_DAYS,
        "stability_days": stability_days,
        "revision_successes": revision_successes,
        "answer_ids": [a.answer_id for a in answers if a.answer_id],
    }

    return MasteryResult(
        mastery=m,
        band=band,
        evidence_n=n,
        quiz_accuracy=round(acc, 2),
        recent_performance=round(rec, 2),
        difficulty_adjusted=round(dap, 2),
        retention=round(ret, 2),
        component_trace=trace,
    )
