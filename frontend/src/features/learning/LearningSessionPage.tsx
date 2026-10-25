import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { LearningSession, QuizAttemptView } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  GitGraph,
  Lightbulb,
  MessageSquare,
  Sparkles,
} from "lucide-react";

export function LearningSessionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeIdx, setActiveIdx] = useState<number>(0);

  const { data: session, isLoading, isError } = useQuery({
    queryKey: qk.session(id ?? ""),
    queryFn: () => apiFetch<LearningSession>(`/learning-sessions/${id}`),
    enabled: Boolean(id),
  });

  const progressMutation = useMutation({
    mutationFn: ({ index, understoodId }: { index?: number; understoodId?: string }) =>
      apiFetch<LearningSession>(`/learning-sessions/${id}/progress`, {
        method: "POST",
        body: JSON.stringify({ index, understood_id: understoodId }),
      }),
    onSuccess: (updated) => {
      void queryClient.setQueryData(qk.session(id ?? ""), updated);
    },
  });

  const launchQuizMutation = useMutation({
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
      <div className="mx-auto max-w-4xl space-y-6 py-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !session) {
    return (
      <EmptyState
        title="Learning Session Not Found"
        body="We couldn't retrieve this learning section. It may have expired or been completed."
        action="Return to Dashboard"
        onAction={() => navigate("/app")}
      />
    );
  }

  const sections = session.sections;
  const currentSection = sections[activeIdx] ?? sections[0];
  const isLastSection = activeIdx === sections.length - 1;
  const isFirstSection = activeIdx === 0;
  const isRemedial = session.mode === "remedial";

  const handleToggleUnderstood = () => {
    progressMutation.mutate({
      index: activeIdx,
      understoodId: currentSection.id,
    });
  };

  const handleNextSection = () => {
    if (!isLastSection) {
      const nextIdx = activeIdx + 1;
      setActiveIdx(nextIdx);
      progressMutation.mutate({ index: nextIdx });
    }
  };

  const handlePrevSection = () => {
    if (!isFirstSection) {
      const prevIdx = activeIdx - 1;
      setActiveIdx(prevIdx);
      progressMutation.mutate({ index: prevIdx });
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-12">
      {/* Top Breadcrumb & Status */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-line pb-4">
        <div className="flex items-center gap-2">
          <Link to="/app">
            <Button variant="ghost" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <Badge tone={isRemedial ? "copper" : "helix"} className="capitalize">
                {isRemedial ? "Remedial Lesson" : "Learning Session"}
              </Badge>
              <span className="text-xs font-mono text-muted">ID: {session.id.slice(0, 8)}</span>
            </div>
            <h1 className="font-display text-2xl font-bold text-ink sm:text-3xl mt-1">
              {session.concept_name}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link to={`/app/genome?focus=${session.concept_id}`}>
            <Button variant="secondary" className="text-xs">
              <GitGraph className="h-3.5 w-3.5 mr-1" />
              Inspect in Graph
            </Button>
          </Link>
        </div>
      </div>

      {/* Causal Rationale Banner */}
      <div
        className={`rounded-card border p-4 text-xs ${
          isRemedial
            ? "border-copper/40 bg-copper/5 text-ink"
            : "border-helix/40 bg-helix/5 text-ink"
        }`}
      >
        <div className="flex items-start gap-2.5">
          <Lightbulb
            className={`h-4 w-4 shrink-0 mt-0.5 ${isRemedial ? "text-copper" : "text-helix"}`}
          />
          <div>
            <span className="font-semibold block">Adaptive Lesson Objective:</span>
            <p className="mt-0.5 leading-relaxed text-muted">{session.because}</p>
          </div>
        </div>
      </div>

      {/* Progress & Section Navigation Stepper */}
      <Card className="p-4">
        <div className="flex items-center justify-between text-xs text-muted mb-3">
          <span className="font-semibold uppercase tracking-wider text-ink">
            Section {activeIdx + 1} of {sections.length}
          </span>
          <span className="font-mono">
            {sections.filter((s) => s.understood).length}/{sections.length} Understood
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {sections.map((sec, idx) => {
            const isActive = idx === activeIdx;
            return (
              <button
                key={sec.id}
                onClick={() => {
                  setActiveIdx(idx);
                  progressMutation.mutate({ index: idx });
                }}
                className={`flex items-center justify-between rounded-control border p-3 text-left transition-all text-xs ${
                  isActive
                    ? "border-helix bg-helix/10 text-helix font-semibold ring-1 ring-helix"
                    : sec.understood
                      ? "border-emerald-500/40 bg-emerald-500/5 text-ink"
                      : "border-line bg-canvas text-muted hover:border-ink/30"
                }`}
              >
                <div className="truncate mr-2">
                  <span className="block text-[10px] uppercase font-mono opacity-75">
                    Step {idx + 1}
                  </span>
                  <span className="truncate block">{sec.title}</span>
                </div>
                {sec.understood ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                ) : (
                  <span className="h-2 w-2 rounded-full bg-line shrink-0" />
                )}
              </button>
            );
          })}
        </div>
      </Card>

      {/* Main Section Content Card */}
      <Card className="p-6 sm:p-8 space-y-6">
        <div className="border-b border-line pb-4">
          <span className="text-xs font-mono uppercase text-muted">
            Section {activeIdx + 1} • Conceptual Breakdown
          </span>
          <h2 className="font-display text-2xl font-bold text-ink mt-1">
            {currentSection.title}
          </h2>
        </div>

        {/* Section Body Text */}
        <div className="prose prose-sm dark:prose-invert max-w-none text-ink leading-relaxed space-y-4 text-base">
          <p className="leading-relaxed">{currentSection.body}</p>
        </div>

        {/* Highlighted Conceptual Insight Box */}
        <div className="rounded-control border border-line bg-canvas p-4 text-xs leading-relaxed text-ink/90 flex items-start gap-3">
          <BookOpen className="h-4 w-4 text-helix shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-ink">Key Mental Model:</span>
            In MindGenome, we treat concepts not as isolated flashcards, but as active nodes in your
            neural comprehension tree. Take time to connect this section with its prerequisite
            foundations before verifying with the checkpoint quiz.
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6">
          <Button
            variant={currentSection.understood ? "primary" : "secondary"}
            onClick={handleToggleUnderstood}
            className="text-xs"
          >
            <CheckCircle2 className="h-4 w-4 mr-1.5" />
            {currentSection.understood ? "Understood ✓" : "Mark as Understood"}
          </Button>

          <Link
            to={`/app/tutor?prompt=${encodeURIComponent(
              `Can you explain '${currentSection.title}' in the context of ${session.concept_name}?`,
            )}`}
          >
            <Button variant="ghost" className="text-xs text-muted hover:text-ink">
              <MessageSquare className="h-3.5 w-3.5 mr-1" />
              Ask AI Tutor about this section
            </Button>
          </Link>
        </div>
      </Card>

      {/* Stepper Navigation Footer & Quiz Checkpoint Trigger */}
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="secondary"
          onClick={handlePrevSection}
          disabled={isFirstSection}
          className="text-xs"
        >
          <ArrowLeft className="h-3.5 w-3.5 mr-1" />
          Previous Section
        </Button>

        {isLastSection ? (
          <Button
            variant="primary"
            onClick={() => launchQuizMutation.mutate(session.concept_id)}
            disabled={launchQuizMutation.isPending}
            className="text-xs font-semibold px-6 py-2.5 shadow-md"
          >
            <Sparkles className="h-4 w-4 mr-1.5" />
            {launchQuizMutation.isPending ? "Generating Quiz..." : "Take Checkpoint Quiz →"}
          </Button>
        ) : (
          <Button variant="primary" onClick={handleNextSection} className="text-xs">
            Next Section
            <ArrowRight className="h-3.5 w-3.5 ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}
