import { lazy, Suspense } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { Dashboard, LearningSession } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { MasteryChip } from "@/shared/ui/MasteryBand";
import { useSession } from "@/features/auth/session";
import type { MasteryBand } from "@/shared/lib/mastery";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  GitGraph,
  Layers,
  MessageSquare,
  Sparkles,
  TrendingUp,
  Upload,
} from "lucide-react";

const GrowthChart = lazy(() => import("./GrowthChart"));

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useSession((s) => s.user);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: qk.dashboard,
    queryFn: () => apiFetch<Dashboard>("/dashboard"),
  });

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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-56" />
          <Skeleton className="h-56 md:col-span-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-64 md:col-span-2" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <EmptyState
        title="Dashboard Unavailable"
        body="We encountered an issue fetching your knowledge genome telemetry."
        action="Retry Connection"
        onAction={() => void refetch()}
      />
    );
  }

  const overallMastery = Math.round(data.overall_mastery);
  const band: MasteryBand =
    overallMastery <= 30
      ? "beginner"
      : overallMastery <= 60
        ? "developing"
        : overallMastery <= 80
          ? "proficient"
          : "mastered";

  return (
    <div className="space-y-8">
      {/* Welcome & Action Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-3xl font-bold sm:text-4xl">
              Hello, {user?.display_name ?? "Learner"}
            </h1>
            <Badge tone="helix">Active Genome</Badge>
          </div>
          <p className="mt-1 text-sm text-muted">
            Here is your real-time comprehension telemetry, weak-link diagnoses, and adaptive next steps.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <Link to="/app/documents">
            <Button variant="secondary" className="text-xs">
              <Upload className="h-3.5 w-3.5" /> Upload Material
            </Button>
          </Link>
          <Link to="/app/genome">
            <Button variant="secondary" className="text-xs">
              <GitGraph className="h-3.5 w-3.5" /> Knowledge Graph
            </Button>
          </Link>
          <Link to="/app/tutor">
            <Button variant="primary" className="text-xs">
              <MessageSquare className="h-3.5 w-3.5" /> Ask AI Tutor
            </Button>
          </Link>
        </div>
      </div>

      {/* Active Ingestion Jobs Notice (if any) */}
      {data.active_jobs && data.active_jobs.length > 0 && (
        <div className="flex items-center justify-between rounded-card border border-helix/40 bg-helix/5 p-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-helix animate-pulse" />
            <span className="font-semibold text-ink">
              Processing Document ({data.active_jobs[0].status}):
            </span>
            <span className="text-muted">Extracting concepts and synthesizing semantic edges...</span>
          </div>
          <Link to={`/app/documents/${data.active_jobs[0].document_id}`} className="text-helix font-semibold hover:underline">
            View Stepper →
          </Link>
        </div>
      )}

      {/* Row 1: Mastery Gauge & Recommended Next */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Overall Mastery Radial Card */}
        <Card className="lg:col-span-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                Overall Genome Mastery
              </span>
              <MasteryChip band={band} />
            </div>

            <div className="mt-6 flex items-center justify-center">
              <div className="relative flex h-36 w-36 items-center justify-center">
                <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    className="stroke-line"
                    strokeWidth="8"
                    fill="transparent"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    className="stroke-helix transition-all duration-1000 ease-out"
                    strokeWidth="8"
                    strokeDasharray={264}
                    strokeDashoffset={264 - (264 * overallMastery) / 100}
                    strokeLinecap="round"
                    fill="transparent"
                  />
                </svg>
                <div className="absolute text-center">
                  <span className="font-display text-4xl font-bold">{overallMastery}</span>
                  <span className="block text-[11px] font-mono text-muted">/ 100</span>
                </div>
              </div>
            </div>

            <p className="mt-4 text-center text-xs text-muted">
              Computed across {Object.values(data.band_counts).reduce((a, b) => a + b, 0)} concepts using the 40/20/20/20 formula.
            </p>
          </div>

          <div className="mt-6 border-t border-line pt-4">
            <span className="text-xs font-semibold text-ink">Concept Band Distribution</span>
            <div className="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
              <div className="rounded-control bg-beginner/10 p-2 border border-beginner/30">
                <span className="block font-bold text-beginner">{data.band_counts.beginner ?? 0}</span>
                <span className="text-[10px] text-muted">Beginner</span>
              </div>
              <div className="rounded-control bg-developing/10 p-2 border border-developing/30">
                <span className="block font-bold text-developing">{data.band_counts.developing ?? 0}</span>
                <span className="text-[10px] text-muted">Developing</span>
              </div>
              <div className="rounded-control bg-proficient/10 p-2 border border-proficient/30">
                <span className="block font-bold text-proficient">{data.band_counts.proficient ?? 0}</span>
                <span className="text-[10px] text-muted">Proficient</span>
              </div>
              <div className="rounded-control bg-mastered/10 p-2 border border-mastered/30">
                <span className="block font-bold text-mastered">{data.band_counts.mastered ?? 0}</span>
                <span className="text-[10px] text-muted">Mastered</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Recommended Next Focus Card */}
        <Card className="lg:col-span-8 flex flex-col justify-between border-helix/40 shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <Badge tone="copper">
                <Sparkles className="mr-1 h-3 w-3 inline" />
                Adaptive Next Step
              </Badge>
              <span className="text-xs font-mono text-muted">Highest Learning Leverage</span>
            </div>

            <div className="mt-4">
              <span className="text-xs font-mono uppercase text-muted">Priority Concept</span>
              <h2 className="font-display text-2xl font-bold sm:text-3xl text-ink">
                {data.recommended.name}
              </h2>
            </div>

            <div className="mt-4 rounded-control border border-line bg-canvas p-4">
              <span className="text-xs font-semibold text-copper">Causal Reason:</span>
              <p className="mt-1 text-sm text-ink/90 leading-relaxed">
                {data.recommended.because}
              </p>
            </div>

            <div className="mt-4 flex items-center gap-4 text-xs text-muted">
              <span className="flex items-center gap-1.5">
                <BookOpen className="h-4 w-4 text-helix" />
                Curriculum: The Elements of Statistical Learning
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-helix" />
                Decision Trees ready
              </span>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <Button
              variant="primary"
              className="px-5 py-2 text-sm font-semibold"
              onClick={() => startLearning.mutate(data.recommended.concept_id)}
              disabled={startLearning.isPending}
            >
              {startLearning.isPending ? "Starting..." : "Start Learning"}
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Link to={`/app/genome?focus=${data.recommended.concept_id}`}>
              <Button variant="secondary" className="text-sm">
                Inspect in Knowledge Graph
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      {/* Row 2: Mini Graph Preview & Growth Curve */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Interactive Mini Knowledge Graph Preview */}
        <Card className="lg:col-span-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <GitGraph className="h-4 w-4 text-helix" />
                <h3 className="font-display text-xl font-bold">Genome Neighbourhood</h3>
              </div>
              <Link to="/app/genome" className="text-xs font-semibold text-helix hover:underline">
                Full Canvas →
              </Link>
            </div>
            <p className="mt-2 text-xs text-muted">
              Live dependency cluster showing current concepts and prerequisite linkages.
            </p>

            <div className="mt-3 rounded-control border border-line bg-canvas p-2">
              <svg viewBox="0 0 400 160" className="w-full" role="img" aria-label="Genome preview">
                {/* Edges */}
                <line x1="80" y1="90" x2="160" y2="50" stroke="var(--mg-line)" strokeWidth="2" strokeDasharray="3 3" />
                <line x1="180" y1="55" x2="260" y2="100" stroke="var(--mg-copper)" strokeWidth="2.5" />
                <line x1="280" y1="100" x2="340" y2="60" stroke="var(--mg-line)" strokeWidth="2" strokeDasharray="3 3" />

                {/* Nodes */}
                <g className="cursor-pointer" onClick={() => navigate("/app/genome")}>
                  <circle cx="70" cy="95" r="20" fill="var(--mg-surface)" stroke="var(--mg-mastered)" strokeWidth="2.5" />
                  <text x="70" y="99" textAnchor="middle" fontSize="8" fontWeight="600" fill="var(--mg-ink)">Trees</text>
                </g>
                <g className="cursor-pointer" onClick={() => navigate("/app/genome")}>
                  <circle cx="170" cy="50" r="22" fill="var(--mg-surface)" stroke="var(--mg-developing)" strokeWidth="2.5" />
                  <text x="170" y="54" textAnchor="middle" fontSize="8" fontWeight="600" fill="var(--mg-ink)">Ensemble</text>
                </g>
                <g className="cursor-pointer" onClick={() => navigate("/app/genome")}>
                  <circle cx="270" cy="105" r="24" fill="var(--mg-surface)" stroke="var(--mg-copper)" strokeWidth="3" />
                  <text x="270" y="109" textAnchor="middle" fontSize="8.5" fontWeight="bold" fill="var(--mg-copper)">GB</text>
                </g>
                <g className="cursor-pointer" onClick={() => navigate("/app/genome")}>
                  <circle cx="345" cy="55" r="18" fill="var(--mg-surface)" stroke="var(--mg-line)" strokeWidth="2" />
                  <text x="345" y="59" textAnchor="middle" fontSize="7.5" fill="var(--mg-muted)">XGBoost</text>
                </g>
              </svg>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-[11px] text-muted">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-copper" /> Prerequisite link under study
            </span>
            <span className="font-mono">4 Connected Nodes</span>
          </div>
        </Card>

        {/* Growth Velocity Chart */}
        <Card className="lg:col-span-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-helix" />
                <h3 className="font-display text-xl font-bold">Mastery Velocity</h3>
              </div>
              <span className="text-xs font-mono text-muted">Past 30 Days</span>
            </div>
            <p className="mt-2 text-xs text-muted">
              Historical mastery index tracking retention curves and quiz validations.
            </p>
            <Suspense fallback={<Skeleton className="h-52 w-full mt-2" />}>
              <GrowthChart data={data.growth} />
            </Suspense>
          </div>

          <div className="mt-2 flex items-center justify-between text-[11px] text-muted border-t border-line pt-2">
            <span>Formula: 40% Acc + 20% Rec + 20% Ret + 20% Diff</span>
            <span className="text-helix font-semibold">Steady Upward Trend</span>
          </div>
        </Card>
      </div>

      {/* Row 3: Weakest Concepts, Revisions Due & Activity */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Weakest Concepts & Root Causes */}
        <Card className="lg:col-span-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-copper" />
                <h3 className="font-display text-lg font-bold">Weakest Concepts</h3>
              </div>
              <span className="text-xs text-muted font-mono">{data.weak_concepts.length} Flagged</span>
            </div>

            <ul className="mt-4 space-y-3">
              {data.weak_concepts.map((concept) => (
                <li
                  key={concept.concept_id}
                  className="flex items-center justify-between rounded-control border border-line bg-canvas p-3"
                >
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-ink">{concept.name}</span>
                    <div className="flex items-center gap-2 text-[10px] text-muted">
                      <span>Acc: {Math.round(concept.quiz_accuracy)}%</span>
                      <span>•</span>
                      <span>Ret: {Math.round(concept.retention)}%</span>
                    </div>
                  </div>
                  <MasteryChip band={concept.band as MasteryBand} score={concept.mastery} />
                </li>
              ))}
            </ul>
          </div>

          <Link to="/app/mastery" className="mt-4 block">
            <Button variant="ghost" className="w-full text-xs">
              View Detailed Mastery Heatmap →
            </Button>
          </Link>
        </Card>

        {/* Spaced Repetition Due */}
        <Card className="lg:col-span-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-helix" />
                <h3 className="font-display text-lg font-bold">Revisions Due</h3>
              </div>
              <Badge tone={data.due_revisions > 0 ? "copper" : "neutral"}>
                {data.due_revisions} Scheduled
              </Badge>
            </div>

            <ul className="mt-4 space-y-3">
              {data.revision_list.map((rev) => (
                <li
                  key={rev.concept_id}
                  className="flex items-center justify-between rounded-control border border-line bg-canvas p-3 text-xs"
                >
                  <div>
                    <span className="font-semibold text-ink">{rev.name}</span>
                    <div className="flex items-center gap-1 text-[10px] text-muted mt-0.5">
                      <Clock className="h-3 w-3" />
                      <span>Due {rev.due}</span>
                    </div>
                  </div>
                  <Button
                    variant="secondary"
                    className="text-[11px] px-2.5 py-1"
                    onClick={() => startLearning.mutate(rev.concept_id)}
                  >
                    Review
                  </Button>
                </li>
              ))}
            </ul>
          </div>

          <Link to="/app/path" className="mt-4 block">
            <Button variant="ghost" className="w-full text-xs">
              Open Adaptive Curriculum Path →
            </Button>
          </Link>
        </Card>

        {/* Recent Audit Activity Stream */}
        <Card className="lg:col-span-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-muted" />
                <h3 className="font-display text-lg font-bold">Recent Activity</h3>
              </div>
              <span className="text-xs text-muted font-mono">Real-time</span>
            </div>

            {data.activity.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted">
                No recent activity. Ingest a document to wake your genome.
              </div>
            ) : (
              <ul className="mt-4 space-y-3">
                {data.activity.map((item) => (
                  <li key={item.id} className="flex items-start gap-2.5 text-xs">
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-helix shrink-0" />
                    <div>
                      <p className="text-ink leading-relaxed">{item.text}</p>
                      <span className="text-[10px] font-mono text-muted">{item.at}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-4 border-t border-line pt-3 text-[11px] text-muted text-center">
            Synchronized with local MSW mock datastore
          </div>
        </Card>
      </div>
    </div>
  );
}
