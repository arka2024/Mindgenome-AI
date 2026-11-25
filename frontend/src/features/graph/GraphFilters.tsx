import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import type { GraphFilterState } from "./types";
import { RotateCcw, Search } from "lucide-react";

export function GraphFilters({
  filters,
  onChange,
  onReset,
}: {
  filters: GraphFilterState;
  onChange: (next: Partial<GraphFilterState>) => void;
  onReset: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-card border border-line bg-surface p-3 text-xs shadow-sm">
      {/* Search Filter */}
      <div className="relative min-w-[200px] flex-1">
        <Input
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
          placeholder="Filter concepts (e.g. Boosting, Trees)..."
          className="pl-8 text-xs py-1.5"
          aria-label="Filter concepts"
        />
        <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted pointer-events-none" />
      </div>

      {/* Mastery Band Filter */}
      <div className="flex items-center gap-1.5">
        <span className="text-muted font-semibold">Band:</span>
        <select
          value={filters.band}
          onChange={(e) => onChange({ band: e.target.value as GraphFilterState["band"] })}
          className="rounded-control border border-line bg-canvas px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-helix"
          aria-label="Filter by mastery band"
        >
          <option value="all">All Bands</option>
          <option value="beginner">Beginner (0–30)</option>
          <option value="developing">Developing (31–60)</option>
          <option value="proficient">Proficient (61–80)</option>
          <option value="mastered">Mastered (81–100)</option>
        </select>
      </div>

      {/* Edge Kind Filter */}
      <div className="flex items-center gap-1.5">
        <span className="text-muted font-semibold">Edge:</span>
        <select
          value={filters.edgeKind}
          onChange={(e) => onChange({ edgeKind: e.target.value as GraphFilterState["edgeKind"] })}
          className="rounded-control border border-line bg-canvas px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-helix"
          aria-label="Filter by edge relationship"
        >
          <option value="all">All Relationships</option>
          <option value="PREREQUISITE_OF">PREREQUISITE_OF</option>
          <option value="USES">USES</option>
          <option value="PART_OF">PART_OF</option>
          <option value="RELATED_TO">RELATED_TO</option>
        </select>
      </div>

      {/* Reset Button */}
      <Button variant="ghost" className="text-xs px-2.5 py-1.5 text-muted hover:text-ink" onClick={onReset}>
        <RotateCcw className="h-3 w-3 mr-1" />
        Reset
      </Button>
    </div>
  );
}
