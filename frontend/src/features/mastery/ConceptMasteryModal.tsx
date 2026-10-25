import { useNavigate, Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { LearningSession, MasteryScore, QuizAttemptView } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Dialog } from "@/shared/ui/Dialog";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import type { MasteryBand } from "@/shared/lib/mastery";
import {
  Brain,
  Calendar,
  CheckCircle2,
  Clock,
  GitGraph,
  Percent,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";

export function ConceptMasteryModal({
  conceptId,
  open,
  onOpenChange,
}: {
  conceptId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();

  const { data: detail, isLoading } = useQuery({
    queryKey: qk.masteryOne(conceptId ?? ""),
    queryFn: () =>
      apiFetch<MasteryScore & { history?: Array<{ date: string; mastery: number }> }>(
        `/mastery/${conceptId}`,
      ),
    enabled: Boolean(conceptId) && open,
  });

  const startLearning = useMutation({
    mutationFn: (cid: string) =>
      apiFetch<LearningSession>("/learning-sessions", {
        method: "POST",
        body: JSON.stringify({ mode: "learn", concept_id: cid }),
      }),
    onSuccess: (session) => {
      onOpenChange(false);
      navigate(`/app/learn/${session.id}`);
    },
  });

  const startQuiz = useMutation({
    mutationFn: (cid: string) =>
      apiFetch<QuizAttemptView>("/quiz-attempts", {
        method: "POST",
        body: JSON.stringify({ concept_id: cid }),
      }),
    onSuccess: (attempt) => {
      onOpenChange(false);
      navigate(`/app/quiz/${attempt.id}`);
    },
  });

  if (!conceptId) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={detail?.name ?? "Concept Telemetry"}
    >
      {isLoading || !detail ? (
        <div className="py-12 text-center text-xs text-muted">Loading telemetry...</div>
      ) : (
        <div className="space-y-6 text-sm">
          <div className="flex items-center justify-between border-b border-line pb-3">
            <div className="flex items-center gap-2">
              <Badge tone="helix">Concept Telemetry</Badge>
              <span className="font-mono text-xs text-muted">ID: {conceptId.slice(0, 10)}</span>
            </div>
            <MasteryChip band={detail.band as MasteryBand} score={detail.mastery} />
          </div>

          {/* Historical Progress Trend Curve */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5 text-helix" />
                Mastery Trajectory
              </span>
              <span className="text-xs font-mono text-muted">3-Point Audit</span>
            </div>

            {detail.history && (
              <div className="grid grid-cols-3 gap-2 text-center">
                {detail.history.map((pt, i) => (
                  <div
                    key={i}
                    className="rounded-control border border-line bg-canvas p-3"
                  >
                    <span className="text-[10px] font-mono text-muted block">{pt.date}</span>
                    <span className="font-display text-xl font-bold text-ink">{pt.mastery}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Component Formula Breakdown */}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-muted block mb-3">
              40 / 20 / 20 / 20 Sub-Component Audit
            </span>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-control border border-line bg-canvas p-3 space-y-1">
                <span className="text-muted flex items-center gap-1 text-[11px]">
                  <Percent className="h-3 w-3 text-helix" /> 40% Accuracy
                </span>
                <span className="font-mono text-lg font-bold text-ink">
                  {Math.round(detail.quiz_accuracy)}%
                </span>
              </div>

              <div className="rounded-control border border-line bg-canvas p-3 space-y-1">
                <span className="text-muted flex items-center gap-1 text-[11px]">
                  <Clock className="h-3 w-3 text-developing" /> 20% Recent
                </span>
                <span className="font-mono text-lg font-bold text-ink">
                  {Math.round(detail.recent_performance)}%
                </span>
              </div>

              <div className="rounded-control border border-line bg-canvas p-3 space-y-1">
                <span className="text-muted flex items-center gap-1 text-[11px]">
                  <ShieldAlert className="h-3 w-3 text-copper" /> 20% Difficulty
                </span>
                <span className="font-mono text-lg font-bold text-ink">
                  {Math.round(detail.difficulty_adjusted)}%
                </span>
              </div>

              <div className="rounded-control border border-line bg-canvas p-3 space-y-1">
                <span className="text-muted flex items-center gap-1 text-[11px]">
                  <CheckCircle2 className="h-3 w-3 text-mastered" /> 20% Retention
                </span>
                <span className="font-mono text-lg font-bold text-ink">
                  {Math.round(detail.retention)}%
                </span>
              </div>
            </div>
          </div>

          {/* Evidence Count */}
          <div className="flex items-center justify-between rounded-control border border-line bg-surface p-3 text-xs">
            <span className="text-muted flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-muted" />
              Validated Checkpoint Evaluations
            </span>
            <span className="font-mono font-bold text-ink">{detail.evidence_n} Questions</span>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-2 border-t border-line pt-4">
            <Link to={`/app/genome?focus=${conceptId}`} onClick={() => onOpenChange(false)}>
              <Button variant="ghost" className="text-xs">
                <GitGraph className="h-3.5 w-3.5 mr-1" /> Inspect in Graph
              </Button>
            </Link>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                className="text-xs"
                onClick={() => startLearning.mutate(conceptId)}
                disabled={startLearning.isPending}
              >
                <Sparkles className="h-3.5 w-3.5 mr-1 text-helix" /> Study Lesson
              </Button>
              <Button
                variant="primary"
                className="text-xs"
                onClick={() => startQuiz.mutate(conceptId)}
                disabled={startQuiz.isPending}
              >
                <Brain className="h-3.5 w-3.5 mr-1" /> Take Checkpoint Quiz
              </Button>
            </div>
          </div>
        </div>
      )}
    </Dialog>
  );
}
