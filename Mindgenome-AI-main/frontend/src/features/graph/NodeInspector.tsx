import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { LearningSession } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import type { GraphEdgeData, GraphNodeData } from "./types";
import {
  BookOpen,
  Brain,
  GitBranch,
  Sparkles,
  X,
} from "lucide-react";

export function NodeInspector({
  node,
  allNodes,
  edges,
  onClose,
  onSelectNode,
  onHighlightLineage,
  isLineageHighlighted,
}: {
  node: GraphNodeData;
  allNodes: GraphNodeData[];
  edges: GraphEdgeData[];
  onClose: () => void;
  onSelectNode: (nodeId: string) => void;
  onHighlightLineage: (nodeId: string) => void;
  isLineageHighlighted: boolean;
}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const startLearning = useMutation({
    mutationFn: (conceptId: string) =>
      apiFetch<LearningSession>("/learning-sessions", {
        method: "POST",
        idempotent: true,
        body: JSON.stringify({ mode: "learn", concept_id: conceptId }),
      }),
    onSuccess: (session) => {
      void queryClient.invalidateQueries({ queryKey: qk.dashboard });
      navigate(`/app/learn/${session.id}`);
    },
  });

  const startQuiz = useMutation({
    mutationFn: (conceptId: string) =>
      apiFetch<{ attempt_id: string }>("/quizzes", {
        method: "POST",
        idempotent: true,
        body: JSON.stringify({ concept_id: conceptId }),
      }),
    onSuccess: (res) => {
      navigate(`/app/quiz/${res.attempt_id}`);
    },
  });

  // Find upstream prerequisites: edges where this node is the target and kind is PREREQUISITE_OF
  // (Meaning: source is PREREQUISITE_OF target)
  const prerequisites = edges
    .filter((e) => e.target === node.id && (e.kind === "PREREQUISITE_OF" || e.kind === "USES"))
    .map((e) => allNodes.find((n) => n.id === e.source))
    .filter((n): n is GraphNodeData => Boolean(n));

  // Find downstream dependents: edges where this node is the source of PREREQUISITE_OF
  const dependents = edges
    .filter((e) => e.source === node.id && (e.kind === "PREREQUISITE_OF" || e.kind === "USES"))
    .map((e) => allNodes.find((n) => n.id === e.target))
    .filter((n): n is GraphNodeData => Boolean(n));

  return (
    <aside
      className="flex h-full w-full flex-col justify-between overflow-y-auto border-l border-line bg-surface p-5 shadow-card"
      aria-label="Node Inspector"
    >
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge tone={node.kind === "concept" ? "helix" : "neutral"} className="capitalize">
                {node.kind}
              </Badge>
              <span className="font-mono text-[10px] text-muted">ID: {node.id.slice(0, 10)}</span>
            </div>
            <h3 className="mt-2 font-display text-2xl font-bold text-ink">{node.label}</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-control p-1.5 text-muted hover:bg-canvas hover:text-ink"
            aria-label="Close inspector"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Mastery Status (for Concepts) */}
        {node.kind === "concept" && node.band && (
          <div className="flex items-center justify-between rounded-control border border-line bg-canvas p-3">
            <span className="text-xs font-semibold text-muted">Learner Mastery</span>
            <MasteryChip band={node.band} score={node.mastery ?? undefined} />
          </div>
        )}

        {/* Definition */}
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted">
            Semantic Definition
          </span>
          <p className="mt-1.5 text-xs text-ink/90 leading-relaxed bg-canvas p-3 rounded-control border border-line">
            {node.definition ?? `${node.label} domain concept extracted from your material.`}
          </p>
        </div>

        {/* Prerequisite Lineage Action */}
        {node.kind === "concept" && (
          <div>
            <Button
              variant={isLineageHighlighted ? "secondary" : "ghost"}
              className={`w-full text-xs justify-center border ${
                isLineageHighlighted ? "border-copper text-copper bg-copper/5" : "border-line"
              }`}
              onClick={() => onHighlightLineage(node.id)}
            >
              <GitBranch className="h-3.5 w-3.5 mr-1" />
              {isLineageHighlighted ? "Clear Lineage Highlight" : "Trace Prerequisite Chain"}
            </Button>
          </div>
        )}

        {/* Upstream Prerequisites */}
        <div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-copper">
              Prerequisites ({prerequisites.length})
            </span>
            <span className="text-[10px] text-muted font-mono">Needed first</span>
          </div>

          {prerequisites.length === 0 ? (
            <p className="mt-1.5 text-xs text-muted">No prerequisites required. Foundational concept.</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {prerequisites.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between rounded-control border border-line bg-canvas px-3 py-2 text-xs transition hover:border-helix"
                >
                  <button
                    onClick={() => onSelectNode(p.id)}
                    className="font-semibold text-ink hover:text-helix text-left truncate flex-1"
                  >
                    {p.label}
                  </button>
                  {p.band && <MasteryChip band={p.band} score={p.mastery ?? undefined} />}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Downstream Dependents */}
        <div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-helix">
              Unlocks Dependents ({dependents.length})
            </span>
            <span className="text-[10px] text-muted font-mono">Enables next</span>
          </div>

          {dependents.length === 0 ? (
            <p className="mt-1.5 text-xs text-muted">Apex concept in current corpus.</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {dependents.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between rounded-control border border-line bg-canvas px-3 py-2 text-xs transition hover:border-helix"
                >
                  <button
                    onClick={() => onSelectNode(d.id)}
                    className="font-semibold text-ink hover:text-helix text-left truncate flex-1"
                  >
                    {d.label}
                  </button>
                  {d.band && <MasteryChip band={d.band} score={d.mastery ?? undefined} />}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Grounding Citation */}
        <div className="border-t border-line pt-3 text-[11px] text-muted flex items-center justify-between">
          <span className="flex items-center gap-1">
            <BookOpen className="h-3 w-3 text-helix" />
            <span>Document: Notes Excerpt</span>
          </span>
          <span className="font-mono text-helix">Cited § Chap. 10</span>
        </div>
      </div>

      {/* Action Footer */}
      {node.kind === "concept" && (
        <div className="mt-6 space-y-2 border-t border-line pt-4">
          <Button
            variant="primary"
            className="w-full text-xs font-semibold py-2.5"
            onClick={() => startLearning.mutate(node.id)}
            disabled={startLearning.isPending}
          >
            <Sparkles className="h-3.5 w-3.5 mr-1" />
            {startLearning.isPending ? "Starting..." : `Learn ${node.label}`}
          </Button>
          <Button
            variant="secondary"
            className="w-full text-xs font-semibold py-2"
            onClick={() => startQuiz.mutate(node.id)}
            disabled={startQuiz.isPending}
          >
            <Brain className="h-3.5 w-3.5 mr-1 text-copper" />
            {startQuiz.isPending ? "Generating..." : "Checkpoint Quiz"}
          </Button>
        </div>
      )}
    </aside>
  );
}
