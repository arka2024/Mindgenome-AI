import { bandLabel, bandRange, type MasteryBand } from "@/shared/lib/mastery";
import { Helix, Leaf, Sprout, Stem, CircleHelp } from "./bandIcons";
import { cn } from "@/shared/lib/cn";

const ICONS: Record<MasteryBand, typeof Sprout> = {
  beginner: Sprout,
  developing: Stem,
  proficient: Leaf,
  mastered: Helix,
  insufficient_evidence: CircleHelp,
};

export function MasteryChip({
  band,
  score,
}: {
  band: MasteryBand;
  score?: number;
}) {
  const Icon = ICONS[band];
  const color: Record<MasteryBand, string> = {
    beginner: "text-beginner border-beginner/40",
    developing: "text-developing border-developing/40",
    proficient: "text-proficient border-proficient/40",
    mastered: "text-mastered border-mastered/40",
    insufficient_evidence: "text-muted border-line",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border bg-surface px-2 py-0.5 text-xs font-semibold",
        color[band],
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      <span>{bandLabel(band)}</span>
      {typeof score === "number" ? <span className="font-mono">{Math.round(score)}</span> : null}
      <span className="sr-only">{bandRange(band)}</span>
    </span>
  );
}
