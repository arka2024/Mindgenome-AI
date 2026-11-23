import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { MasteryScore } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { FormulaBreakdownModal } from "./FormulaBreakdownModal";
import { ConceptMasteryModal } from "./ConceptMasteryModal";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import type { MasteryBand } from "@/shared/lib/mastery";
import { Calculator, Search } from "lucide-react";

export function MasteryPage() {
  const [selectedBand, setSelectedBand] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [formulaModalOpen, setFormulaModalOpen] = useState<boolean>(false);
  const [inspectConceptId, setInspectConceptId] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.mastery,
    queryFn: () => apiFetch<{ items: MasteryScore[] }>("/mastery"),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        title="Mastery Telemetry Unavailable"
        body="Could not load your knowledge mastery breakdown. Please retry."
        action="Retry Connection"
        onAction={() => void refetch()}
      />
    );
  }

  const items = data.items;
  const filtered = items.filter((item) => {
    const matchesBand = selectedBand === "all" || item.band === selectedBand;
    const matchesSearch =
      !searchQuery.trim() ||
      (item.name ?? item.concept_id).toLowerCase().includes(searchQuery.toLowerCase());
    return matchesBand && matchesSearch;
  });

  const avgMastery = Math.round(
    items.reduce((acc, curr) => acc + curr.mastery, 0) / (items.length || 1),
  );

  const bandCounts: Record<string, number> = {
    all: items.length,
    beginner: items.filter((i) => i.band === "beginner").length,
    developing: items.filter((i) => i.band === "developing").length,
    proficient: items.filter((i) => i.band === "proficient").length,
    mastered: items.filter((i) => i.band === "mastered").length,
    insufficient_evidence: items.filter((i) => i.band === "insufficient_evidence").length,
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-3xl font-bold sm:text-4xl">Concept Mastery Telemetry</h1>
            <Badge tone="helix">40/20/20/20 Audited</Badge>
          </div>
          <p className="mt-1 text-xs text-muted max-w-2xl">
            Deterministic comprehension scores across all {items.length} nodes in your knowledge genome,
            weighted by accuracy, recency, difficulty, and retention decay.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            className="text-xs"
            onClick={() => setFormulaModalOpen(true)}
          >
            <Calculator className="h-3.5 w-3.5 mr-1 text-helix" />
            Explain 40/20/20/20 Formula
          </Button>
          <Link to="/app/path">
            <Button variant="primary" className="text-xs">
              Adaptive Path →
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Hero Card */}
      <Card className="p-6">
        <div className="grid gap-6 md:grid-cols-4 items-center">
          <div className="border-b border-line pb-4 md:border-b-0 md:border-r md:pb-0 md:pr-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted block">
              Mean Genome Score
            </span>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="font-display text-4xl font-bold text-ink">{avgMastery}</span>
              <span className="text-xs font-mono text-muted">/ 100</span>
            </div>
            <p className="mt-1 text-[11px] text-muted">Across {items.length} extracted concepts</p>
          </div>

          <div className="md:col-span-3">
            <span className="text-xs font-semibold text-ink block mb-2.5">
              Filter by Mastery Band
            </span>
            <div className="flex flex-wrap gap-2 text-xs">
              <button
                type="button"
                onClick={() => setSelectedBand("all")}
                className={`rounded-control border px-3 py-1.5 font-medium transition-colors ${
                  selectedBand === "all"
                    ? "border-helix bg-helix/10 text-helix"
                    : "border-line bg-canvas text-muted hover:text-ink"
                }`}
              >
                All Concepts ({bandCounts.all})
              </button>
              <button
                type="button"
                onClick={() => setSelectedBand("beginner")}
                className={`rounded-control border px-3 py-1.5 font-medium transition-colors ${
                  selectedBand === "beginner"
                    ? "border-beginner bg-beginner/10 text-beginner"
                    : "border-line bg-canvas text-muted hover:text-ink"
                }`}
              >
                Beginner ({bandCounts.beginner})
              </button>
              <button
                type="button"
                onClick={() => setSelectedBand("developing")}
                className={`rounded-control border px-3 py-1.5 font-medium transition-colors ${
                  selectedBand === "developing"
                    ? "border-developing bg-developing/10 text-developing"
                    : "border-line bg-canvas text-muted hover:text-ink"
                }`}
              >
                Developing ({bandCounts.developing})
              </button>
              <button
                type="button"
                onClick={() => setSelectedBand("proficient")}
                className={`rounded-control border px-3 py-1.5 font-medium transition-colors ${
                  selectedBand === "proficient"
                    ? "border-proficient bg-proficient/10 text-proficient"
                    : "border-line bg-canvas text-muted hover:text-ink"
                }`}
              >
                Proficient ({bandCounts.proficient})
              </button>
              <button
                type="button"
                onClick={() => setSelectedBand("mastered")}
                className={`rounded-control border px-3 py-1.5 font-medium transition-colors ${
                  selectedBand === "mastered"
                    ? "border-mastered bg-mastered/10 text-mastered"
                    : "border-line bg-canvas text-muted hover:text-ink"
                }`}
              >
                Mastered ({bandCounts.mastered})
              </button>
              <button
                type="button"
                onClick={() => setSelectedBand("insufficient_evidence")}
                className={`rounded-control border px-3 py-1.5 font-medium transition-colors ${
                  selectedBand === "insufficient_evidence"
                    ? "border-line bg-surface text-ink font-semibold"
                    : "border-line bg-canvas text-muted hover:text-ink"
                }`}
              >
                Insufficient Evidence ({bandCounts.insufficient_evidence})
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter concepts by name (e.g. Gradient Boosting, Tree)..."
          className="w-full rounded-control border border-line bg-canvas py-2 pl-10 pr-4 text-xs text-ink placeholder:text-muted focus:border-helix focus:outline-none focus:ring-1 focus:ring-helix"
        />
      </div>

      {/* Concept Mastery Table */}
      <Card className="overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-line bg-surface font-semibold text-muted">
              <tr>
                <th className="py-3 px-4">Concept Name</th>
                <th className="py-3 px-4">Mastery Band</th>
                <th className="py-3 px-4">Accuracy (40%)</th>
                <th className="py-3 px-4">Recent (20%)</th>
                <th className="py-3 px-4">Retention (20%)</th>
                <th className="py-3 px-4">Difficulty (20%)</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-muted">
                    No concepts match your filter criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((item) => (
                  <tr
                    key={item.concept_id}
                    onClick={() => setInspectConceptId(item.concept_id)}
                    className="cursor-pointer transition-colors hover:bg-helix/5"
                  >
                    <td className="py-3 px-4">
                      <span className="font-semibold text-ink block">{item.name}</span>
                      <span className="font-mono text-[10px] text-muted">
                        ID: {item.concept_id.slice(0, 10)}…
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <MasteryChip band={item.band as MasteryBand} score={item.mastery} />
                    </td>
                    <td className="py-3 px-4 font-mono">{Math.round(item.quiz_accuracy)}%</td>
                    <td className="py-3 px-4 font-mono">{Math.round(item.recent_performance)}%</td>
                    <td className="py-3 px-4 font-mono">{Math.round(item.retention)}%</td>
                    <td className="py-3 px-4 font-mono">{Math.round(item.difficulty_adjusted)}%</td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        className="h-7 text-[11px] px-2 text-muted hover:text-ink"
                        onClick={(e) => {
                          e.stopPropagation();
                          setInspectConceptId(item.concept_id);
                        }}
                      >
                        Inspect Telemetry →
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Concept Detail Modal */}
      <ConceptMasteryModal
        conceptId={inspectConceptId}
        open={Boolean(inspectConceptId)}
        onOpenChange={(open) => !open && setInspectConceptId(null)}
      />

      {/* Formula Explainability Modal */}
      <FormulaBreakdownModal
        open={formulaModalOpen}
        onOpenChange={setFormulaModalOpen}
      />
    </div>
  );
}
