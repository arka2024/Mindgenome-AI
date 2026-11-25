import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import { useSession } from "@/features/auth/session";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { ThemeToggle } from "@/app/shell/ThemeToggle";
import {
  Brain,
  CheckCircle2,
  Download,
  RotateCcw,
  ToggleLeft,
  ToggleRight,
  User,
} from "lucide-react";

export function SettingsPage() {
  const user = useSession((s) => s.user);
  const queryClient = useQueryClient();

  const [feedbackMode, setFeedbackMode] = useState<"immediate" | "end">("immediate");
  const [hintsEnabled, setHintsEnabled] = useState<boolean>(true);
  const [dailyGoal, setDailyGoal] = useState<number>(10);
  const [resetSuccess, setResetSuccess] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);

  const handleResetStore = async () => {
    setIsResetting(true);
    try {
      await apiFetch("/store/reset", { method: "POST" });
      await queryClient.invalidateQueries();
      setResetSuccess(true);
      setTimeout(() => setResetSuccess(false), 3000);
    } catch {
      /* ignore */
    } finally {
      setIsResetting(false);
    }
  };

  const handleExportTelemetry = async () => {
    try {
      const res = await apiFetch<unknown>("/dashboard");
      const blob = new Blob([JSON.stringify(res, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mindgenome-telemetry-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-12">
      {/* Header */}
      <div className="border-b border-line pb-4">
        <div className="flex items-center gap-2">
          <h1 className="font-display text-3xl font-bold sm:text-4xl">Learner Preferences & System</h1>
          <Badge tone="neutral">Local Sandbox</Badge>
        </div>
        <p className="mt-1 text-xs text-muted">
          Configure your cognitive checkpoint modes, daily goals, and reset demo states.
        </p>
      </div>

      <div className="grid gap-6">
        {/* Account Profile Card */}
        <Card className="p-6">
          <div className="flex items-center gap-3 border-b border-line pb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-helix/10 text-helix border border-helix/30">
              <User className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-display text-lg font-bold text-ink">
                {user?.display_name ?? "Asha Learner"}
              </h2>
              <span className="text-xs text-muted font-mono">{user?.email ?? "learner@mindgenome.ai"}</span>
            </div>
            <Badge tone="helix" className="ml-auto uppercase text-[10px]">
              {user?.roles?.join(", ") ?? "User"}
            </Badge>
          </div>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-muted block text-[10px] uppercase font-semibold">User ID</span>
              <span className="font-mono text-ink text-[11px]">{user?.id ?? "local-user-id"}</span>
            </div>
            <div>
              <span className="text-muted block text-[10px] uppercase font-semibold">Active Session</span>
              <span className="text-ink">JWT Authenticated (Local MSW Datastore)</span>
            </div>
          </div>
        </Card>

        {/* Pedagogical Quiz Settings */}
        <Card className="p-6 space-y-6">
          <div className="border-b border-line pb-3">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-helix" />
              <h2 className="font-display text-lg font-bold">Checkpoint Quiz Configurations</h2>
            </div>
            <p className="text-xs text-muted mt-0.5">
              Customize how pedagogical feedback is delivered during checkpoints.
            </p>
          </div>

          <div className="space-y-4">
            {/* Feedback Mode */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-ink block">Feedback Timing</span>
                <span className="text-[11px] text-muted">
                  {feedbackMode === "immediate"
                    ? "Display explanations and correctness immediately after each question."
                    : "Show complete diagnostic review only after all questions are completed."}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setFeedbackMode(feedbackMode === "immediate" ? "end" : "immediate")}
                className="flex items-center gap-1.5 text-xs font-medium text-helix"
              >
                {feedbackMode === "immediate" ? (
                  <ToggleRight className="h-6 w-6 text-helix" />
                ) : (
                  <ToggleLeft className="h-6 w-6 text-muted" />
                )}
                <span className="capitalize">{feedbackMode} Feedback</span>
              </button>
            </div>

            {/* Hints Toggle */}
            <div className="flex items-center justify-between border-t border-line pt-4">
              <div>
                <span className="text-xs font-semibold text-ink block">Allow Hints During Checkpoint</span>
                <span className="text-[11px] text-muted">
                  Reveal conceptual hint accordions without incurring score penalties.
                </span>
              </div>
              <button
                type="button"
                onClick={() => setHintsEnabled(!hintsEnabled)}
                className="flex items-center gap-1.5 text-xs font-medium text-helix"
              >
                {hintsEnabled ? (
                  <ToggleRight className="h-6 w-6 text-helix" />
                ) : (
                  <ToggleLeft className="h-6 w-6 text-muted" />
                )}
                <span>{hintsEnabled ? "Enabled" : "Disabled"}</span>
              </button>
            </div>

            {/* Daily Questions Goal */}
            <div className="flex items-center justify-between border-t border-line pt-4">
              <div>
                <span className="text-xs font-semibold text-ink block">Daily Mastery Evaluation Goal</span>
                <span className="text-[11px] text-muted">
                  Target number of validated questions per day to maintain active retention.
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {[5, 10, 20].map((goal) => (
                  <button
                    key={goal}
                    type="button"
                    onClick={() => setDailyGoal(goal)}
                    className={`rounded-control border px-3 py-1 text-xs font-semibold transition-colors ${
                      dailyGoal === goal
                        ? "border-helix bg-helix/10 text-helix"
                        : "border-line bg-canvas text-muted hover:text-ink"
                    }`}
                  >
                    {goal} Qs
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Appearance Settings */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-ink block">Color Theme</span>
              <span className="text-[11px] text-muted">
                Toggle between light and dark high-contrast design token themes.
              </span>
            </div>
            <ThemeToggle />
          </div>
        </Card>

        {/* Demo State Control & Telemetry Export */}
        <Card className="p-6 border-copper/30 bg-copper/5 space-y-4">
          <div className="border-b border-line pb-3">
            <span className="text-xs font-semibold text-copper uppercase tracking-wider block">
              Demo Environment Controls
            </span>
            <p className="text-xs text-muted mt-0.5">
              Reset the local MSW store to re-run the 2/5 → diagnosis → remedial → 4/5 story anytime.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <span className="text-xs font-semibold text-ink block">Reset Knowledge Genome</span>
              <span className="text-[11px] text-muted">
                Restores initial scores (Gradient Boosting at 42%, Ensemble Learning at 28%).
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                onClick={handleResetStore}
                disabled={isResetting}
                className="text-xs"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1" />
                {isResetting ? "Resetting..." : "Reset Demo Story"}
              </Button>
              <Button
                variant="primary"
                onClick={handleExportTelemetry}
                className="text-xs"
              >
                <Download className="h-3.5 w-3.5 mr-1" />
                Export Telemetry (JSON)
              </Button>
            </div>
          </div>

          {resetSuccess && (
            <div className="rounded-control bg-emerald-500/10 border border-emerald-500/30 p-2.5 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>Knowledge Genome state reset successfully! Ready for demo cycle.</span>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
