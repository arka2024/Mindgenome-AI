import { useState } from "react";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import type { GraphEdgeData, GraphNodeData } from "./types";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";

export function AccessibleGraphTree({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
}: {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
  selectedNodeId: string | null;
  onSelectNode: (id: string) => void;
}) {
  const [collapsedChapters, setCollapsedChapters] = useState<Record<string, boolean>>({});

  const toggleChapter = (chapId: string) => {
    setCollapsedChapters((prev) => ({ ...prev, [chapId]: !prev[chapId] }));
  };

  const chapters = nodes.filter((n) => n.kind === "chapter");
  const concepts = nodes.filter((n) => n.kind === "concept");

  return (
    <div className="space-y-4" role="region" aria-label="Hierarchical Concept Tree">
      <div className="rounded-control border border-line bg-surface p-3 text-xs text-muted flex items-center justify-between">
        <span>Keyboard-accessible list view of the knowledge genome.</span>
        <span className="font-mono text-[10px]">{concepts.length} Concepts Indexed</span>
      </div>

      <div className="space-y-3">
        {chapters.map((chap) => {
          const isCollapsed = Boolean(collapsedChapters[chap.id]);
          // Find concepts belonging to this chapter or connected via PART_OF
          const chapterConcepts = concepts.filter((c) => {
            const hasEdge = edges.some(
              (e) =>
                (e.source === chap.id && e.target === c.id) ||
                (e.target === chap.id && e.source === c.id) ||
                c.parent === chap.id,
            );
            return hasEdge;
          });

          const displayConcepts = chapterConcepts.length > 0 ? chapterConcepts : concepts.slice(0, 5);

          return (
            <div key={chap.id} className="rounded-card border border-line bg-surface overflow-hidden">
              <button
                type="button"
                className="flex w-full items-center justify-between bg-canvas px-4 py-3 text-left font-semibold text-sm hover:bg-surface transition"
                onClick={() => toggleChapter(chap.id)}
                aria-expanded={!isCollapsed}
              >
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-helix" />
                  <span>{chap.label}</span>
                  <Badge tone="neutral">{displayConcepts.length} Concepts</Badge>
                </div>
                {isCollapsed ? <ChevronRight className="h-4 w-4 text-muted" /> : <ChevronDown className="h-4 w-4 text-muted" />}
              </button>

              {!isCollapsed && (
                <ul className="divide-y divide-line p-2 space-y-1">
                  {displayConcepts.map((concept) => {
                    const isSelected = selectedNodeId === concept.id;
                    const prereqs = edges
                      .filter((e) => e.target === concept.id && e.kind === "PREREQUISITE_OF")
                      .map((e) => nodes.find((n) => n.id === e.source))
                      .filter((n): n is GraphNodeData => Boolean(n));

                    return (
                      <li
                        key={concept.id}
                        className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 rounded-control transition ${
                          isSelected ? "bg-helix/10 border border-helix/40" : "hover:bg-canvas"
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-ink">{concept.label}</span>
                            {concept.band && <MasteryChip band={concept.band} score={concept.mastery ?? undefined} />}
                          </div>

                          {prereqs.length > 0 && (
                            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
                              <span className="font-semibold text-copper">Requires:</span>
                              {prereqs.map((pr) => (
                                <button
                                  key={pr.id}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onSelectNode(pr.id);
                                  }}
                                  className="rounded bg-canvas px-1.5 py-0.5 border border-line hover:border-copper hover:text-copper transition"
                                >
                                  {pr.label}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-2 self-end sm:self-center">
                          <Button
                            variant={isSelected ? "primary" : "secondary"}
                            className="text-xs"
                            onClick={() => onSelectNode(concept.id)}
                          >
                            Inspect Concept
                          </Button>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
