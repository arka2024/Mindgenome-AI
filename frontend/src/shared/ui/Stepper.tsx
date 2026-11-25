import { cn } from "@/shared/lib/cn";
import { Check } from "lucide-react";

const STEPS = [
  "queued",
  "parsing",
  "chunking",
  "embedding",
  "extracting",
  "graph_built",
  "ready",
] as const;

const LABELS: Record<(typeof STEPS)[number], string> = {
  queued: "Queued",
  parsing: "Parsing",
  chunking: "Chunking",
  embedding: "Embedding",
  extracting: "Extracting concepts",
  graph_built: "Building graph",
  ready: "Ready",
};

export function Stepper({ status }: { status: string }) {
  const current = STEPS.indexOf(status as (typeof STEPS)[number]);
  const failed = status === "failed";
  return (
    <ol className="grid gap-2 sm:grid-cols-7" aria-label="Ingestion progress">
      {STEPS.map((step, i) => {
        const done = !failed && current >= i;
        const active = current === i;
        return (
          <li
            key={step}
            className={cn(
              "rounded-control border px-2 py-2 text-xs",
              done ? "border-helix bg-helix/10" : "border-line",
              failed && "border-danger/40",
            )}
          >
            <span className="flex items-center gap-1 font-semibold">
              {done && !active ? <Check className="h-3 w-3" aria-hidden /> : `${i + 1}.`}
              {LABELS[step]}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
