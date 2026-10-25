# Mastery engine (domain, pure functions)

Numeric mastery lives **only** in PostgreSQL (`mastery_scores`, `mastery_history`).
Neo4j may store `STRUGGLES_WITH` as a derived flag after a score is committed.
The domain package must not import FastAPI, SQLAlchemy, Neo4j, or LangChain.

## Inputs

Each concept \(c\) for user \(u\) is scored from `attempt_answers` joined to
`question_concepts` where `question_concepts.concept_id = c`.

For answer \(i\):

| Symbol | Meaning |
| --- | --- |
| \(y_i \in \{0,1\}\) | Correctness |
| \(t_i\) | Answer timestamp (UTC) |
| \(\Delta_i\) | Age in days at scoring time: \((t_{now} - t_i) / 86400\) |
| \(d_i\) | Difficulty weight from question.difficulty |
| \(n\) | Count of scored answers for \((u,c)\) |

Difficulty weights (fixed v1):

| `difficulty` | \(d_i\) |
| --- | --- |
| `easy` | 0.70 |
| `medium` | 1.00 |
| `hard` | 1.30 |

## Components (each in \([0, 100]\))

### 1. QuizAccuracy — weight 0.40

\[
Acc = 100 \times \frac{\sum y_i}{n}
\]

Unweighted lifetime accuracy. Transparent and stable.

### 2. RecentPerformance — weight 0.20

Exponential recency. Half-life \(T_{1/2} = 14\) days:

\[
\lambda = \frac{\ln 2}{14},\quad w_i = e^{-\lambda \Delta_i}
\]

\[
Rec = 100 \times \frac{\sum w_i y_i}{\sum w_i}
\]

If \(n=0\), Rec is undefined (see evidence rule).

### 3. DifficultyAdjustedPerformance — weight 0.20

\[
DAP = 100 \times \frac{\sum y_i d_i}{\sum d_i}
\]

Getting hard items right moves this up faster than easy items; missing hard
items hurts less than missing easy items *relative to weight mass*, which is
intentional: easy misses are stronger evidence of a gap.

### 4. Retention / revision — weight 0.20

Stability grows with successful on-time reviews (from `revision_schedule`
and correct answers after a review was due):

\[
S = \min\left(60,\ 7 \times (1 + 0.5 \times r)\right)
\]

where \(r\) is the count of successful revision events for \((u,c)\).

Let \(\Delta^*\) be days since the last **correct** answer. If none exist, \(Ret=0\).

\[
Ret = 100 \times e^{-\Delta^* / S}
\]

A due-and-completed correct review resets \(\Delta^*\) and increments \(r\).
A missed due date does not increment \(r\) and leaves \(\Delta^*\) growing
(forgetting continues).

## Combined score

\[
M = 0.40\,Acc + 0.20\,Rec + 0.20\,DAP + 0.20\,Ret
\]

Store \(M\) as `numeric(5,2)`. Display as integer. Persist the four components
and a `component_trace` JSON so every score is reconstructable:

```json
{
  "n": 5,
  "correct": 2,
  "acc": 40.0,
  "rec": 38.12,
  "dap": 36.0,
  "ret": 22.31,
  "m": 35.29,
  "half_life_days": 14,
  "stability_days": 7.0,
  "revision_successes": 0,
  "answer_ids": ["..."]
}
```

Recompute from answer ids in tests; never “adjust M by hand” in services.

## Evidence rule

| \(n\) | Band stored | Adaptive use |
| --- | --- | --- |
| 0 | `insufficient_evidence` | Concept is *unseen*; path planner may introduce it |
| 1–2 | `insufficient_evidence` | **Do not** set `STRUGGLES_WITH`, **do not** start remedial loop, **do not** call the concept “weak” in UI copy |
| ≥ 3 | Map \(M\) to a band below | Adaptive engine may act |

## Bands (\(n \ge 3\))

| Band | Inclusive range of rounded \(M\) |
| --- | --- |
| `beginner` | 0–30 |
| `developing` | 31–60 |
| `proficient` | 61–80 |
| `mastered` | 81–100 |

`STRUGGLES_WITH` is written to Neo4j iff band is `beginner` and \(n \ge 3\).
It is removed when the band leaves `beginner`.

## Worked example (Sprint 6 acceptance)

Gradient Boosting: 2/5 correct, all `medium`, all within 24 hours, no prior
revisions, \(n=5\) so evidence is sufficient.

- \(Acc = 40\)
- \(Rec \approx 40\) (all recent)
- \(DAP = 40\) (uniform medium)
- \(Ret = 100 \times e^{-0/7} = 100\) if last answer was correct, **or** if last
  answer was wrong use last *correct* answer age. If 2 correct and the latest
  of those was today, \(Ret \approx 100\).

Then \(M \approx 0.4\cdot40 + 0.2\cdot40 + 0.2\cdot40 + 0.2\cdot100 = 52\) →
`developing` — **not** automatically “weak”.

The blueprint story “2/5 on Gradient Boosting → weak Ensemble Learning” is a
**graph** conclusion: Ensemble Learning is a high-confidence prerequisite of
Gradient Boosting **and** Ensemble Learning itself has \(n\ge 3\) and
`beginner` (or insufficient practice on the prerequisite). Sprint 6 tests must
encode that distinction: a mediocre leaf does not mark a strong parent weak;
we walk to the weakest **ancestor** that meets the evidence rule.

If Ensemble Learning is 1/4 on hard items with \(n=4\) and \(M \le 30\), that
node is the remedial target; Gradient Boosting is paused until the ancestor
retest is \(n\ge 3\) and band ≥ `developing`.

## Decay job

A daily Celery beat task recomputes \(Ret\) (and thus \(M\)) for scores whose
`computed_at` is older than 24h and \(n \ge 1\). Writes `mastery_history` with
`reason = retention_decay`.
