import type { Citation } from "@/api/schemas";
import { Dialog } from "@/shared/ui/Dialog";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { Link } from "react-router-dom";
import { BookOpen, ExternalLink, Hash } from "lucide-react";

export function SourceDrawer({
  citation,
  open,
  onOpenChange,
}: {
  citation: Citation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!citation) return null;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={`Source Citation: ${citation.filename}`}
    >
      <div className="space-y-4 text-sm">
        <div className="flex items-center gap-2">
          <Badge tone="helix">Source Grounding</Badge>
          <span className="font-mono text-xs text-muted">RAG Citation Preview</span>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 rounded-control border border-line bg-canvas p-3 text-xs">
          <div>
            <span className="text-muted block text-[10px] uppercase font-semibold">Chapter</span>
            <span className="font-medium text-ink truncate block">
              {citation.chapter_title ?? "General"}
            </span>
          </div>
          <div>
            <span className="text-muted block text-[10px] uppercase font-semibold">Page Span</span>
            <span className="font-mono text-ink">
              pp. {citation.page_start}–{citation.page_end}
            </span>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <span className="text-muted block text-[10px] uppercase font-semibold">Chunk ID</span>
            <span className="font-mono text-[11px] text-muted truncate block">
              {citation.chunk_id.slice(0, 14)}…
            </span>
          </div>
        </div>

        {/* Verbatim Passage Box with Highlight Accent */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <Hash className="h-3 w-3 text-copper" />
              Grounding Excerpt from Document
            </span>
            <span className="text-[11px] text-muted font-mono">Verbatim Extraction</span>
          </div>
          <div className="relative rounded-control border-2 border-helix/30 bg-helix/5 p-4 text-ink leading-relaxed">
            <p className="font-serif text-sm italic sm:text-base leading-relaxed">
              "{citation.passage ?? "Passage text retrieved from vector store chunk."}"
            </p>
          </div>
        </div>

        <div className="rounded-control bg-canvas p-3 border border-line text-xs text-muted flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-helix shrink-0" />
          <span>
            This chunk was parsed and vectorized during document ingestion. All AI Tutor answers are
            strictly bounded by these passages to prevent hallucination.
          </span>
        </div>

        <div className="mt-6 flex items-center justify-between border-t border-line pt-4">
          <Link to={`/app/documents/${citation.document_id}`}>
            <Button variant="secondary" className="text-xs">
              <ExternalLink className="h-3.5 w-3.5 mr-1" />
              Open Document
            </Button>
          </Link>
          <Button variant="primary" onClick={() => onOpenChange(false)} className="text-xs">
            Close Citation
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
