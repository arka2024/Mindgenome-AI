import { Dialog } from "@/shared/ui/Dialog";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { CheckCircle2, Clock, Percent, ShieldAlert } from "lucide-react";

export function FormulaBreakdownModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="The 40 / 20 / 20 / 20 Mastery Formula"
    >
      <div className="space-y-4 text-xs sm:text-sm">
        <div className="flex items-center gap-2">
          <Badge tone="helix">Explainable Telemetry</Badge>
          <span className="font-mono text-xs text-muted">Auditable Comprehension</span>
        </div>

        <p className="text-muted leading-relaxed">
          MindGenome computes concept mastery deterministically. We avoid black-box scores; every point on your genome corresponds to verifiable cognitive evidence.
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-control border border-line bg-canvas p-3.5 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <Percent className="h-4 w-4 text-helix" /> 40% Quiz Accuracy
              </span>
              <Badge tone="neutral">Base Weight</Badge>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Raw proportion of checkpoint questions answered correctly across all attempts on this concept.
            </p>
          </div>

          <div className="rounded-control border border-line bg-canvas p-3.5 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-developing" /> 20% Recent Score
              </span>
              <Badge tone="neutral">Recency</Badge>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Exponentially weighted average favoring your last 3 attempts, capturing recent learning gains.
            </p>
          </div>

          <div className="rounded-control border border-line bg-canvas p-3.5 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <ShieldAlert className="h-4 w-4 text-copper" /> 20% Difficulty-Adjusted
              </span>
              <Badge tone="neutral">Calibration</Badge>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Weights hard questions higher (1.5x) and easy questions lower (0.75x) to prevent grade inflation.
            </p>
          </div>

          <div className="rounded-control border border-line bg-canvas p-3.5 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-mastered" /> 20% Retention Decay
              </span>
              <Badge tone="neutral">Ebbinghaus</Badge>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Memory stability modeled via half-life decay. Successful revisions slow down the decay rate.
            </p>
          </div>
        </div>

        <div className="rounded-control border border-line bg-surface p-3 text-xs text-muted">
          <span className="font-semibold text-ink block mb-0.5">Evidence Minimum Gate:</span>
          A concept requires at least 3 distinct question evaluations before exiting the{" "}
          <span className="font-mono text-ink">Insufficient Evidence</span> band.
        </div>

        <div className="mt-6 flex justify-end border-t border-line pt-4">
          <Button variant="primary" onClick={() => onOpenChange(false)} className="text-xs">
            Understood
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
