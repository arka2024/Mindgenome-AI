import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { LearningPath, LearningSession, QuizAttemptView } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  GitGraph,
  Lock,
  RotateCcw,
  Sparkles,
} from "lucide-react";

export function LearningPathPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.path,
    queryFn: () => apiFetch<LearningPath>("/learning-path"),
  });

  const startSession = useMutation({
    mutationFn: ({ conceptId, mode }: { conceptId: string; mode: string }) =>
      apiFetch<LearningSession>("/learning-sessions", {
        method: "POST",
        body: JSON.stringify({ mode, concept_id: conceptId }),
      }),
    onSuccess: (session) => {
      void queryClient.invalidateQueries({ queryKey: qk.dashboard });
      navigate(`/app/learn/${session.id}`);
    },
  });

  const startQuiz = useMutation({
    mutationFn: (conceptId: string) =>
      apiFetch<QuizAttemptView>("/quiz-attempts", {
        method: "POST",
        body: JSON.stringify({ concept_id: conceptId }),
      }),
    onSuccess: (attempt) => {
      navigate(`/app/quiz/${attempt.id}`);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <div className="space-y-4">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        title="Adaptive Path Unavailable"
        body="Could not compute your causal learning path. Please retry."
        action="Retry Calculation"
        onAction={() => void refetch()}
      />
    );
  }

  const items = data.items;

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-3xl font-bold sm:text-4xl">Adaptive Learning Path</h1>
            <Badge tone="copper">
              <Sparkles className="h-3 w-3 mr-1 inline" />
              Graph Optimized
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted">
            Ordered sequence of concepts tailored to close weak prerequisite gaps and ascend the
            curriculum tree efficiently.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/genome">
            <Button variant="secondary" className="text-xs">
              <GitGraph className="h-3.5 w-3.5 mr-1" />
              View on Graph Canvas
            </Button>
          </Link>
        </div>
      </div>

      {/* Path Roadmap Container */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:bottom-6 before:left-3 sm:before:left-4 before:top-6 before:w-0.5 before:bg-line">
        {items.map((step, idx) => {
          const isRemedial = step.kind === "remedial";
          const isRetest = step.kind === "retest";
          const isRevision = step.kind === "revision";
          const isNext = step.kind === "next";

          return (
            <div key={step.concept_id} className="relative group">
              {/* Timeline Connector Node Icon */}
              <div
                className={`absolute -left-6 sm:-left-8 top-5 flex h-6 w-6 sm:h-8 sm:w-8 -translate-x-1/2 items-center justify-center rounded-full border-2 bg-surface shadow-sm ${
                  isRemedial
                    ? "border-copper text-copper"
                    : isRetest
                      ? "border-indigo-500 text-indigo-500"
                      : isRevision
                        ? "border-emerald-500 text-emerald-500"
                        : "border-helix text-helix"
                }`}
              >
                {isRemedial ? (
                  <AlertTriangle className="h-3.5 w-3.5" />
                ) : isRetest ? (
                  <RotateCcw className="h-3.5 w-3.5" />
                ) : isRevision ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : isNext ? (
                  <Lock className="h-3.5 w-3.5" />
                ) : (
                  <BookOpen className="h-3.5 w-3.5" />
                )}
              </div>

              {/* Step Card */}
              <Card
                className={`p-5 sm:p-6 transition-all border ${
                  isRemedial
                    ? "border-copper/60 bg-copper/5 shadow-md"
                    : isRetest
                      ? "border-indigo-500/50 bg-indigo-500/5"
                      : "border-line bg-surface hover:border-helix/40"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-[10px] text-muted uppercase">
                        Step {idx + 1}
                      </span>
                      <Badge
                        tone={
                          isRemedial
                            ? "copper"
                            : isRetest
                              ? "helix"
                              : isRevision
                                ? "neutral"
                                : "helix"
                        }
                        className="text-[10px] uppercase font-semibold"
                      >
                        {step.kind} Focus
                      </Badge>
                      {step.band && <MasteryChip band={step.band} />}
                    </div>

                    <h3 className="font-display text-xl font-bold text-ink">
                      {step.name}
                    </h3>

                    {/* Causal Explanation Box */}
                    <p className="text-xs text-muted leading-relaxed max-w-xl">
                      <span className="font-semibold text-ink">Why this step: </span>
                      {step.because}
                    </p>
                  </div>

                  {/* Action CTA */}
                  <div className="flex items-center gap-2 shrink-0">
                    {isRetest ? (
                      <Button
                        variant="primary"
                        className="text-xs font-semibold px-4"
                        onClick={() => startQuiz.mutate(step.concept_id)}
                        disabled={startQuiz.isPending}
                      >
                        <RotateCcw className="h-3.5 w-3.5 mr-1" />
                        Retest Quiz
                      </Button>
                    ) : (
                      <Button
                        variant={isRemedial ? "primary" : "secondary"}
                        className="text-xs font-semibold px-4"
                        onClick={() =>
                          startSession.mutate({
                            conceptId: step.concept_id,
                            mode: isRemedial ? "remedial" : "learn",
                          })
                        }
                        disabled={startSession.isPending}
                      >
                        <Sparkles className="h-3.5 w-3.5 mr-1" />
                        {isRemedial ? "Start Remedial Lesson" : "Study Concept"}
                        <ArrowRight className="h-3.5 w-3.5 ml-1" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            </div>
          );
        })}
      </div>

      {/* Spaced Repetition Due Sidebar Info */}
      <Card className="p-6 bg-canvas border border-line">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="h-4 w-4 text-helix" />
          <h3 className="font-display text-lg font-bold">Retention Memory Architecture</h3>
        </div>
        <p className="text-xs text-muted leading-relaxed">
          MindGenome monitors exponential forgetting curves using the half-life formulation. Concepts
          fall into light revision after 14 days of inactivity. When you complete remedial lessons and
          retest, your entire prerequisite chain receives confidence reinforcement.
        </p>
      </Card>
    </div>
  );
}
