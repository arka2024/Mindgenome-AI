import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/api/client";
import type { DocumentRecord, UploadAccepted } from "@/api/types-extra";
import { qk } from "@/shared/lib/queryKeys";
import { validateUpload } from "@/shared/lib/mastery";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Skeleton } from "@/shared/ui/Skeleton";
import { useToasts } from "@/shared/ui/Toast";
import {
  AlertCircle,
  Clock,
  FileText,
  GitGraph,
  Layers,
  Loader2,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react";

type DocumentListResponse = {
  items: DocumentRecord[];
  total: number;
  page: number;
  page_size: number;
};

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const pushToast = useToasts((s) => s.push);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<string[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);

  const documentsQuery = useQuery({
    queryKey: qk.documents,
    queryFn: () => apiFetch<DocumentListResponse>("/documents"),
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const error = validateUpload(file);
      if (error) throw new Error(error);

      const formData = new FormData();
      formData.append("file", file);

      return apiFetch<UploadAccepted>("/documents", {
        method: "POST",
        body: formData,
        idempotent: true,
      });
    },
    onSuccess: async (_res, file) => {
      setUploadQueue((prev) => prev.filter((name) => name !== file.name));
      pushToast("Ingestion Started", `${file.name} queued for semantic concept extraction.`);
      await queryClient.invalidateQueries({ queryKey: qk.documents });
      await queryClient.invalidateQueries({ queryKey: qk.dashboard });
    },
    onError: (err: Error, file) => {
      setUploadQueue((prev) => prev.filter((name) => name !== file.name));
      pushToast("Upload Failed", err.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      return apiFetch(`/documents/${documentId}`, { method: "DELETE" });
    },
    onSuccess: async () => {
      pushToast("Document Deleted", "Removed document and purged from graph index.");
      await queryClient.invalidateQueries({ queryKey: qk.documents });
      await queryClient.invalidateQueries({ queryKey: qk.dashboard });
    },
    onError: () => pushToast("Delete Failed", "Could not remove document."),
  });

  const handleFiles = (files: FileList | null) => {
    setValidationError(null);
    if (!files || files.length === 0) return;

    for (const file of Array.from(files)) {
      const err = validateUpload(file);
      if (err) {
        setValidationError(err);
        continue;
      }
      setUploadQueue((prev) => [...prev, file.name]);
      uploadMutation.mutate(file);
    }
  };

  const handleUploadSample = () => {
    // Generate a mock ML excerpt file for immediate testing
    const sampleBlob = new Blob(
      [
        "Chapter 10: Boosting and Additive Trees. Hastie, Tibshirani, and Friedman. Ensemble Learning, Gradient Boosting, AdaBoost.",
      ],
      { type: "application/pdf" },
    );
    const sampleFile = new File([sampleBlob], "The_Elements_of_Statistical_Learning_Ensembles.pdf", {
      type: "application/pdf",
    });
    handleFiles([sampleFile] as unknown as FileList);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold sm:text-4xl">Document Corpus</h1>
          <p className="mt-1 text-sm text-muted">
            Upload course notes, textbook chapters, or research papers. We extract concepts and construct your knowledge graph.
          </p>
        </div>
        <Button variant="secondary" className="text-xs self-start" onClick={handleUploadSample}>
          <Sparkles className="h-3.5 w-3.5 text-copper" />
          Upload Demo ML Paper
        </Button>
      </div>

      {/* Drag & Drop Upload Zone */}
      <Card
        className={`relative border-2 border-dashed p-8 text-center transition-all ${
          isDragging
            ? "border-helix bg-helix/5 scale-[1.01]"
            : "border-line bg-surface hover:border-helix/50"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-helix/10 text-helix">
          <Upload className="h-6 w-6" />
        </div>
        <h2 className="mt-4 font-display text-xl font-semibold">
          Drag and drop your study materials
        </h2>
        <p className="mt-1 text-xs text-muted max-w-md mx-auto">
          Accepts PDF and DOCX files up to 25 MB. Text extraction, semantic chunking, and concept graph synthesis happen automatically.
        </p>

        <label className="mt-5 inline-block">
          <Button variant="primary" className="cursor-pointer text-xs pointer-events-none">
            Browse Local Files
          </Button>
          <input
            type="file"
            className="sr-only"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            multiple
            onChange={(e) => handleFiles(e.target.files)}
          />
        </label>

        {validationError && (
          <div className="mt-4 flex items-center justify-center gap-1.5 text-xs text-danger" role="alert">
            <AlertCircle className="h-4 w-4" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Upload Queue Indicators */}
        {uploadQueue.length > 0 && (
          <div className="mt-6 border-t border-line pt-4 max-w-lg mx-auto space-y-2">
            <span className="text-xs font-semibold text-muted">Uploading ({uploadQueue.length}):</span>
            {uploadQueue.map((fileName) => (
              <div
                key={fileName}
                className="flex items-center justify-between rounded-control border border-line bg-canvas px-3 py-2 text-xs"
              >
                <div className="flex items-center gap-2 truncate">
                  <Loader2 className="h-3.5 w-3.5 text-helix animate-spin shrink-0" />
                  <span className="truncate font-mono">{fileName}</span>
                </div>
                <span className="text-muted text-[10px]">Processing...</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Document Library Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="font-display text-2xl font-bold">Your Library</h2>
            {documentsQuery.data && (
              <Badge tone="neutral">{documentsQuery.data.items.length} Documents</Badge>
            )}
          </div>
        </div>

        {documentsQuery.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : documentsQuery.isError ? (
          <EmptyState
            title="Library Unavailable"
            body="We could not retrieve your uploaded documents."
            action="Retry"
            onAction={() => void documentsQuery.refetch()}
          />
        ) : documentsQuery.data?.items.length === 0 ? (
          <EmptyState
            title="No documents in your library yet"
            body="Upload your first research paper or course note to start extracting concepts."
            action="Upload Sample Paper"
            onAction={handleUploadSample}
          />
        ) : (
          <div className="grid gap-4">
            {documentsQuery.data?.items.map((doc) => {
              const isReady = doc.status === "ready";
              const isProcessing =
                doc.status === "uploaded" || doc.status === "processing";
              const isFailed = doc.status === "failed" || doc.status === "rejected";

              return (
                <Card
                  key={doc.id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5 transition hover:border-helix/40"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-canvas border border-line text-helix">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/app/documents/${doc.id}`}
                          className="font-semibold text-ink hover:text-helix hover:underline text-sm sm:text-base"
                        >
                          {doc.filename}
                        </Link>
                        {isReady && <Badge tone="helix">Ready</Badge>}
                        {isProcessing && (
                          <Badge tone="copper">
                            <Loader2 className="mr-1 h-3 w-3 inline animate-spin" />
                            Ingesting
                          </Badge>
                        )}
                        {isFailed && <Badge tone="danger">Failed</Badge>}
                        {doc.is_low_text && (
                          <span className="rounded-control bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:text-amber-300 border border-amber-500/20">
                            Low OCR Confidence
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-muted">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {new Date(doc.created_at).toLocaleDateString()}
                        </span>
                        {typeof doc.page_count === "number" && (
                          <span className="flex items-center gap-1">
                            <Layers className="h-3.5 w-3.5" />
                            {doc.page_count} Pages
                          </span>
                        )}
                        <span className="font-mono text-[10px]">ID: {doc.id.slice(0, 8)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <Link to={`/app/documents/${doc.id}`}>
                      <Button variant="secondary" className="text-xs">
                        Inspect Stepper
                      </Button>
                    </Link>

                    {isReady && (
                      <Link to="/app/genome">
                        <Button variant="ghost" className="text-xs">
                          <GitGraph className="h-3.5 w-3.5" /> Graph
                        </Button>
                      </Link>
                    )}

                    <Button
                      variant="ghost"
                      className="text-xs text-muted hover:text-danger"
                      onClick={() => deleteMutation.mutate(doc.id)}
                      disabled={deleteMutation.isPending}
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
