import { Link, useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { DocumentRecord } from "@/api/types-extra";
import type { IngestionJob, LearningSession } from "@/api/schemas";
import { qk } from "@/shared/lib/queryKeys";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Stepper } from "@/shared/ui/Stepper";
import { Skeleton } from "@/shared/ui/Skeleton";
import { EmptyState } from "@/shared/ui/EmptyState";
import { useToasts } from "@/shared/ui/Toast";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  FileText,
  GitGraph,
  Layers,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";

const STAGE_DESCRIPTIONS: Record<string, string> = {
  queued: "Document is registered and queued for worker execution.",
  parsing: "Extracting structured text, section boundaries, and mathematical notation.",
  chunking: "Partitioning document text into context-rich semantic chunks.",
  embedding: "Generating dense vector embeddings with MiniLM-384 for RAG retrieval.",
  extracting: "Identifying domain concepts, keywords, and entity relationships.",
  graph_built: "Synthesizing directed PREREQUISITE_OF and USES edges into the graph.",
  ready: "Knowledge graph synthesis complete. All concepts and quizzes are active.",
  failed: "Ingestion pipeline encountered an unrecoverable parsing error.",
};

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const pushToast = useToasts((s) => s.push);

  const docQuery = useQuery({
    queryKey: qk.document(id ?? ""),
    queryFn: () => apiFetch<DocumentRecord>(`/documents/${id}`),
    enabled: Boolean(id),
  });

  const jobQuery = useQuery({
    queryKey: qk.job(docQuery.data?.job_id ?? ""),
    queryFn: () => apiFetch<IngestionJob>(`/ingestion-jobs/${docQuery.data?.job_id}`),
    enabled: Boolean(docQuery.data?.job_id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Continue polling every 700ms until job reaches 'ready' or 'failed'
      if (!status || status === "ready" || status === "failed") return false;
      return 700;
    },
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

  if (docQuery.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-10 w-96" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (docQuery.isError || !docQuery.data) {
    return (
      <EmptyState
        title="Document Not Found"
        body="This document may have been deleted or the identifier is invalid."
        action="Back to Library"
        onAction={() => navigate("/app/documents")}
      />
    );
  }

  const doc = docQuery.data;
  const currentStatus = jobQuery.data?.status ?? (doc.status === "ready" ? "ready" : "queued");
  const progressPct = jobQuery.data?.progress_pct ?? (currentStatus === "ready" ? 100 : 10);
  const isReady = currentStatus === "ready";
  const isFailed = currentStatus === "failed";

  return (
    <div className="space-y-8">
      {/* Back Navigation */}
      <Link
        to="/app/documents"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-ink"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Document Library
      </Link>

      {/* Document Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-control bg-canvas border border-line text-helix">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-2xl font-bold sm:text-3xl">{doc.filename}</h1>
              {isReady && <Badge tone="helix">Ready</Badge>}
              {!isReady && !isFailed && (
                <Badge tone="copper">
                  <Loader2 className="mr-1 h-3 w-3 inline animate-spin" />
                  Processing {progressPct}%
                </Badge>
              )}
              {isFailed && <Badge tone="danger">Failed</Badge>}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-4 text-xs text-muted">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                Uploaded {new Date(doc.created_at).toLocaleDateString()}
              </span>
              {typeof doc.page_count === "number" && (
                <span className="flex items-center gap-1">
                  <Layers className="h-3.5 w-3.5" />
                  {doc.page_count} Total Pages
                </span>
              )}
              <span className="font-mono text-[10px]">ID: {doc.id}</span>
            </div>
          </div>
        </div>

        {isReady && (
          <Link to="/app/genome">
            <Button variant="primary" className="text-xs self-start">
              <GitGraph className="h-3.5 w-3.5" /> Explore Synthesized Graph
            </Button>
          </Link>
        )}
      </div>

      {/* Processing Stepper Card */}
      <Card className="space-y-6 p-6 border-helix/30 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-line pb-4">
          <div>
            <h2 className="font-display text-xl font-bold">Ingestion & Synthesis Pipeline</h2>
            <p className="mt-0.5 text-xs text-muted">
              Automated multi-stage NLP pipeline transforming raw text into an adaptive knowledge genome.
            </p>
          </div>
          <span className="text-xs font-mono font-semibold text-helix">
            {progressPct}% Completed
          </span>
        </div>

        {/* Progress bar */}
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-canvas border border-line">
          <div
            className="h-full bg-helix transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {/* 7-Stage Visual Stepper */}
        <Stepper status={currentStatus} />

        {/* Dynamic Stage Description */}
        <div
          className="rounded-control border border-line bg-canvas p-4 text-xs"
          aria-live="polite"
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-ink uppercase tracking-wider text-[11px]">
              Active Stage: {currentStatus.replace("_", " ")}
            </span>
            {!isReady && !isFailed && (
              <span className="flex items-center gap-1 text-[10px] text-muted">
                <Loader2 className="h-3 w-3 animate-spin text-helix" />
                Polling worker status (SSE ready)...
              </span>
            )}
          </div>
          <p className="mt-1.5 text-muted leading-relaxed">
            {STAGE_DESCRIPTIONS[currentStatus] ?? "Processing document..."}
          </p>
        </div>

        {/* Ready Banner */}
        {isReady && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-control border border-proficient/30 bg-proficient/10 p-4 text-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-proficient shrink-0" />
              <div>
                <span className="font-semibold text-ink">
                  Corpus Ready for Learning & RAG Tutoring
                </span>
                <p className="text-muted text-[11px] mt-0.5">
                  Concepts, prerequisites, and citation chunk embeddings are synchronized.
                </p>
              </div>
            </div>
            <Link to="/app/genome">
              <Button variant="primary" className="text-xs font-semibold">
                Open in Graph Canvas <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        )}

        {/* Failed Banner */}
        {isFailed && (
          <div className="flex items-center justify-between rounded-control border border-danger/40 bg-danger/10 p-4 text-xs text-danger">
            <span>Pipeline stalled during concept extraction.</span>
            <Button
              variant="secondary"
              className="text-xs border-danger/40"
              onClick={() => {
                pushToast("Retrying", "Restarting ingestion pipeline worker...");
                void jobQuery.refetch();
              }}
            >
              <RefreshCw className="h-3.5 w-3.5 mr-1" /> Retry Ingestion
            </Button>
          </div>
        )}
      </Card>

      {/* Chapters & Detected Sections */}
      <Card className="p-6">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-helix" />
            <h2 className="font-display text-xl font-bold">Detected Chapters & Modules</h2>
          </div>
          <Badge tone="neutral">
            {(doc.chapters ?? []).length} Structured Chapters
          </Badge>
        </div>

        {(!doc.chapters || doc.chapters.length === 0) ? (
          <div className="py-8 text-center text-xs text-muted">
            Chapters will appear here once text parsing completes.
          </div>
        ) : (
          <div className="mt-4 divide-y divide-line">
            {doc.chapters.map((chapter, idx) => (
              <div
                key={chapter.id}
                className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 py-3.5 first:pt-0 last:pb-0"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-copper">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <span className="text-sm font-semibold text-ink">{chapter.title}</span>
                  </div>
                  <span className="font-mono text-[11px] text-muted block pl-6">
                    Pages {chapter.page_start}–{chapter.page_end} · Semantic Chapter
                  </span>
                </div>

                <div className="flex items-center gap-2 pl-6 sm:pl-0">
                  <Button
                    variant="secondary"
                    className="text-xs"
                    onClick={() => startLearning.mutate(chapter.id)}
                    disabled={startLearning.isPending}
                  >
                    <Sparkles className="h-3 w-3 text-helix mr-1" />
                    Learn Section
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
