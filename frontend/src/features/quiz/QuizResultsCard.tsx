import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { LearningSession, QuizAttemptView, QuizResult } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  GitGraph,
  RotateCcw,
  Sparkles,
  TrendingUp,
  XCircle,
} from "lucide-react";

export function QuizResultsCard({
  result,
  conceptId,
  conceptName,
}: {
  result: QuizResult;
  conceptId: string;
  conceptName: string;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showReview, setShowReview] = useState(false);

  const startRemedialOrNext = useMutation({
    mutationFn: ({ conceptId, mode }: { conceptId: string; mode: string }) =>
      apiFetch<LearningSession>("/learning-sessions", {
        method: "POST",
        body: JSON.stringify({ mode, concept_id: conceptId }),
      }),
    onSuccess: (session) => {
      void queryClient.invalidateQueries({ queryKey: qk.dashboard });
      void queryClient.invalidateQueries({ queryKey: qk.mastery });
      void queryClient.invalidateQueries({ queryKey: qk.path });
      navigate(`/app/learn/${session.id}`);
    },
  });

  const retestQuiz = useMutation({
    mutationFn: (targetConceptId: string) =>
      apiFetch<QuizAttemptView>("/quiz-attempts", {
        method: "POST",
        body: JSON.stringify({ concept_id: targetConceptId }),
      }),
    onSuccess: (attempt) => {
      navigate(`/app/quiz/${attempt.id}`);
    },
  });

  const percentage = Math.round((result.correct / result.total) * 100);
  const isPassing = percentage >= 60;
  const isRemedialDiagnosis = result.next.mode === "remedial" && Boolean(result.next.concept_id);

  return (
    <div className="space-y-6">
      {/* Hero Score Banner */}
      <Card className="p-6 sm:p-8 text-center space-y-4">
        <div className="inline-flex items-center justify-center p-3 rounded-full bg-surface border border-line">
          {isPassing ? (
            <CheckCircle2 className="h-10 w-10 text-emerald-500" />
          ) : (
            <AlertTriangle className="h-10 w-10 text-copper" />
          )}
        </div>

        <div>
          <Badge tone={isPassing ? "helix" : "copper"} className="uppercase text-xs tracking-wider">
            {isPassing ? "Checkpoint Passed" : "Knowledge Gap Diagnosed"}
          </Badge>
          <h2 className="font-display text-3xl font-bold text-ink sm:text-4xl mt-2">
            You Scored {result.correct} / {result.total} ({percentage}%)
          </h2>
          <p className="mt-1 text-xs text-muted max-w-md mx-auto">
            Checkpoint on <span className="font-semibold text-ink">{conceptName}</span> completed.
            Comprehension telemetry has been recalculated across your genome.
          </p>
        </div>

        {/* Animated Mastery Delta Badges */}
        <div className="mx-auto max-w-xl rounded-control border border-line bg-canvas p-4 text-xs">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted block mb-3">
            Real-Time Mastery Delta
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {result.deltas.map((delta) => {
              const diff = delta.after - delta.before;
              return (
                <div
                  key={delta.concept_id}
                  className="flex items-center justify-between rounded-control border border-line bg-surface p-3"
                >
                  <div className="text-left">
                    <span className="font-semibold block text-ink">{delta.name}</span>
                    <span className="text-[10px] text-muted">
                      {delta.before}% → {delta.after}%
                    </span>
                  </div>
                  <div
                    className={`flex items-center gap-1 font-mono text-xs font-bold ${
                      diff >= 0 ? "text-emerald-500" : "text-copper"
                    }`}
                  >
                    <TrendingUp className={`h-3.5 w-3.5 ${diff < 0 ? "rotate-180" : ""}`} />
                    <span>
                      {diff >= 0 ? "+" : ""}
                      {diff}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* WEAK-PREREQUISITE DIAGNOSIS & ACTION (Core Loop Story) */}
      <Card
        className={`p-6 border-2 shadow-lg ${
          isRemedialDiagnosis
            ? "border-copper/60 bg-copper/5"
            : "border-helix/60 bg-helix/5"
        }`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge tone={isRemedialDiagnosis ? "copper" : "helix"}>
                {isRemedialDiagnosis ? "Causal Diagnosis Detected" : "Adaptive Recommendation"}
              </Badge>
              <span className="text-xs font-mono text-muted">Graph-Informed Loop</span>
            </div>
            <h3 className="font-display text-xl font-bold text-ink">
              {result.next.because}
            </h3>
            <p className="text-xs text-muted leading-relaxed">
              {isRemedialDiagnosis
                ? "Our prerequisite analysis discovered that your comprehension breakdown in Gradient Boosting is rooted in a weak upstream concept. Studying this remedial lesson will stabilize your foundation."
                : "Your mastery on this node is verified. You can continue advancing to the next apex concept on your adaptive path."}
            </p>
          </div>

          <div className="flex flex-col gap-2 shrink-0">
            {result.next.concept_id && (
              <Button
                variant="primary"
                onClick={() =>
                  startRemedialOrNext.mutate({
                    conceptId: result.next.concept_id!,
                    mode: result.next.mode,
                  })
                }
                disabled={startRemedialOrNext.isPending}
                className="text-xs font-semibold py-2.5 px-4 shadow-md"
              >
                <Sparkles className="h-3.5 w-3.5 mr-1" />
                {isRemedialDiagnosis
                  ? `Remedial Lesson: ${result.next.concept_name ?? "Prerequisite"}`
                  : `Next: ${result.next.concept_name ?? "Continue Path"}`}
                <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            )}

            <Button
              variant="secondary"
              onClick={() => retestQuiz.mutate(conceptId)}
              disabled={retestQuiz.isPending}
              className="text-xs"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" />
              Retake Checkpoint Quiz
            </Button>
          </div>
        </div>
      </Card>

      {/* Per-Question Answer Review Accordion */}
      <Card className="p-5">
        <button
          type="button"
          onClick={() => setShowReview(!showReview)}
          className="flex w-full items-center justify-between text-left text-sm font-semibold text-ink"
        >
          <span className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-helix" />
            Detailed Question Explanations ({result.per_question.length} Questions)
          </span>
          {showReview ? (
            <ChevronUp className="h-4 w-4 text-muted" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted" />
          )}
        </button>

        {showReview && (
          <div className="mt-4 space-y-4 border-t border-line pt-4">
            {result.per_question.map((q, idx) => (
              <div
                key={q.question_id}
                className={`rounded-control border p-4 text-xs space-y-2 ${
                  q.is_correct
                    ? "border-emerald-500/30 bg-emerald-500/5"
                    : "border-copper/30 bg-copper/5"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-ink">Question {idx + 1}</span>
                  <Badge tone={q.is_correct ? "neutral" : "copper"}>
                    {q.is_correct ? (
                      <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-500 inline" />
                    ) : (
                      <XCircle className="h-3 w-3 mr-1 text-copper inline" />
                    )}
                    {q.is_correct ? "Correct" : "Incorrect"}
                  </Badge>
                </div>

                <div className="space-y-1">
                  <div className="text-muted">
                    <span className="font-medium text-ink">Selected Choice:</span>{" "}
                    Choice {q.selected_index + 1}
                  </div>
                  {!q.is_correct && (
                    <div className="text-emerald-600 dark:text-emerald-400 font-medium">
                      Correct Answer: Choice {q.correct_index + 1}
                    </div>
                  )}
                </div>

                <div className="rounded-control bg-canvas p-3 border border-line text-ink leading-relaxed">
                  <span className="font-semibold block text-[11px] text-muted uppercase mb-1">
                    Pedagogical Explanation:
                  </span>
                  {q.explanation}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-2">
        <Link to="/app">
          <Button variant="secondary" className="text-xs">
            Return to Dashboard
          </Button>
        </Link>
        <Link to="/app/genome">
          <Button variant="ghost" className="text-xs text-muted hover:text-ink">
            <GitGraph className="h-3.5 w-3.5 mr-1" />
            Inspect Updated Graph
          </Button>
        </Link>
      </div>
    </div>
  );
}
