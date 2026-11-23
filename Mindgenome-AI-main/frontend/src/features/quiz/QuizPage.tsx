import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { QuizAttemptView, QuizResult } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { QuizResultsCard } from "./QuizResultsCard";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import {
  ArrowLeft,
  Lightbulb,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";

export function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [showHint, setShowHint] = useState<boolean>(false);
  const [immediateFeedback, setImmediateFeedback] = useState<boolean>(true);
  const [result, setResult] = useState<QuizResult | null>(null);

  const { data: attempt, isLoading, isError } = useQuery({
    queryKey: qk.quiz(id ?? ""),
    queryFn: () => apiFetch<QuizAttemptView>(`/quiz-attempts/${id}`),
    enabled: Boolean(id),
  });

  const submitMutation = useMutation({
    mutationFn: () => {
      if (!attempt) throw new Error("No attempt");
      const payload = {
        answers: attempt.questions.map((q) => ({
          question_id: q.id,
          selected_index: answers[q.id] ?? -1,
        })),
      };
      return apiFetch<QuizResult>(`/quiz-attempts/${id}/submit`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (res) => {
      setResult(res);
      void queryClient.invalidateQueries({ queryKey: qk.dashboard });
      void queryClient.invalidateQueries({ queryKey: qk.mastery });
      void queryClient.invalidateQueries({ queryKey: qk.path });
      void queryClient.invalidateQueries({ queryKey: qk.graph });
    },
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6 py-8">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !attempt) {
    return (
      <EmptyState
        title="Quiz Checkpoint Not Found"
        body="This quiz attempt could not be loaded or has expired."
        action="Back to Genome Dashboard"
        onAction={() => navigate("/app")}
      />
    );
  }

  // If already submitted and results ready, render the full results & diagnosis view!
  if (result) {
    return (
      <div className="mx-auto max-w-3xl py-6">
        <QuizResultsCard
          result={result}
          conceptId={attempt.concept_id}
          conceptName={attempt.concept_name}
        />
      </div>
    );
  }

  const questions = attempt.questions;
  const currentQ = questions[currentIdx] ?? questions[0];
  const isLastQuestion = currentIdx === questions.length - 1;
  const selectedChoice = answers[currentQ.id];
  const isAnswered = typeof selectedChoice === "number";

  const handleSelectChoice = (idx: number) => {
    setAnswers((prev) => ({ ...prev, [currentQ.id]: idx }));
  };

  const handleNext = () => {
    setShowHint(false);
    if (!isLastQuestion) {
      setCurrentIdx((prev) => prev + 1);
    } else {
      submitMutation.mutate();
    }
  };

  const handlePrev = () => {
    setShowHint(false);
    if (currentIdx > 0) {
      setCurrentIdx((prev) => prev - 1);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-line pb-4">
        <div className="flex items-center gap-2">
          <Link to="/app">
            <Button variant="ghost" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <Badge tone="helix">Concept Checkpoint</Badge>
              <span className="text-xs font-mono text-muted">ID: {attempt.id.slice(0, 8)}</span>
            </div>
            <h1 className="font-display text-2xl font-bold text-ink sm:text-3xl mt-1">
              {attempt.concept_name}
            </h1>
          </div>
        </div>

        {/* Feedback Mode Switcher */}
        <button
          type="button"
          onClick={() => setImmediateFeedback(!immediateFeedback)}
          className="flex items-center gap-2 rounded-control border border-line bg-surface px-3 py-1.5 text-xs text-muted hover:text-ink transition-colors"
        >
          {immediateFeedback ? (
            <ToggleRight className="h-4 w-4 text-helix" />
          ) : (
            <ToggleLeft className="h-4 w-4 text-muted" />
          )}
          <span>{immediateFeedback ? "Immediate Feedback Mode" : "End-of-Quiz Review Mode"}</span>
        </button>
      </div>

      {/* Progress Bar & Stepper dots */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted">
          <span className="font-semibold text-ink">
            Question {currentIdx + 1} of {questions.length}
          </span>
          <span className="font-mono">
            {Object.keys(answers).length} / {questions.length} Answered
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-line">
          <div
            className="h-full bg-helix transition-all duration-300 ease-out"
            style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Main Question Card */}
      <Card className="p-6 sm:p-8 space-y-6 shadow-md">
        {/* Question Metadata */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
          <div className="flex items-center gap-2">
            <Badge
              tone={
                currentQ.difficulty === "easy"
                  ? "neutral"
                  : currentQ.difficulty === "medium"
                    ? "helix"
                    : "copper"
              }
              className="capitalize text-[11px]"
            >
              {currentQ.difficulty} Difficulty
            </Badge>
            <div className="flex flex-wrap gap-1">
              {currentQ.concept_tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-control bg-canvas border border-line px-2 py-0.5 text-[10px] text-muted font-mono"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <Button
            variant="ghost"
            className="text-xs text-muted hover:text-ink p-1 h-auto"
            onClick={() => setShowHint(!showHint)}
          >
            <Lightbulb className="h-3.5 w-3.5 mr-1 text-copper" />
            {showHint ? "Hide Hint" : "Need a Hint?"}
          </Button>
        </div>

        {/* Hint Callout */}
        {showHint && (
          <div className="rounded-control border border-copper/40 bg-copper/5 p-3 text-xs text-ink flex items-start gap-2">
            <Lightbulb className="h-4 w-4 text-copper shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block text-copper">Pedagogical Hint:</span>
              <p className="mt-0.5 text-muted">{currentQ.hint}</p>
            </div>
          </div>
        )}

        {/* Question Stem */}
        <div>
          <h2 className="font-display text-lg sm:text-xl font-bold text-ink leading-relaxed">
            {currentQ.stem}
          </h2>
        </div>

        {/* Multiple Choice Options List */}
        <div className="space-y-3" role="radiogroup" aria-label="Question choices">
          {currentQ.choices.map((choice, idx) => {
            const isSelected = selectedChoice === idx;
            const letter = String.fromCharCode(65 + idx);

            return (
              <button
                key={idx}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => handleSelectChoice(idx)}
                className={`flex w-full items-center gap-3.5 rounded-control border p-4 text-left transition-all text-sm ${
                  isSelected
                    ? "border-helix bg-helix/10 text-helix font-medium ring-1 ring-helix shadow-sm"
                    : "border-line bg-canvas text-ink hover:border-ink/40 hover:bg-surface"
                }`}
              >
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold border transition-colors ${
                    isSelected
                      ? "border-helix bg-helix text-canvas"
                      : "border-line bg-surface text-muted"
                  }`}
                >
                  {letter}
                </span>
                <span className="flex-1 leading-relaxed">{choice}</span>
              </button>
            );
          })}
        </div>
      </Card>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="secondary"
          onClick={handlePrev}
          disabled={currentIdx === 0}
          className="text-xs"
        >
          <ArrowLeft className="h-3.5 w-3.5 mr-1" />
          Previous
        </Button>

        <Button
          variant="primary"
          onClick={handleNext}
          disabled={!isAnswered || submitMutation.isPending}
          className="text-xs font-semibold px-6 py-2.5"
        >
          {submitMutation.isPending
            ? "Evaluating..."
            : isLastQuestion
              ? "Submit Checkpoint Quiz ✓"
              : "Next Question →"}
        </Button>
      </div>
    </div>
  );
}
