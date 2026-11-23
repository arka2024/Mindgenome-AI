import type { ChatMessage } from "./types";
import type { Citation } from "@/api/schemas";
import { CitationChip } from "./CitationChip";
import { Badge } from "@/shared/ui/Badge";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  GitGraph,
  HelpCircle,
  Sparkles,
  User,
} from "lucide-react";

export function MessageItem({
  message,
  onOpenCitation,
  onSelectFollowup,
}: {
  message: ChatMessage;
  onOpenCitation: (citation: Citation) => void;
  onSelectFollowup: (followup: string) => void;
}) {
  const isUser = message.sender === "user";

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 text-sm">
        <div className="max-w-xl rounded-2xl rounded-tr-none bg-helix text-canvas px-4 py-3 shadow-sm">
          <p className="leading-relaxed whitespace-pre-wrap">{message.text}</p>
          <span className="mt-1 block text-right text-[10px] opacity-75">{message.timestamp}</span>
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface border border-line text-ink">
          <User className="h-4 w-4" />
        </div>
      </div>
    );
  }

  const isLowConfidence = message.confidence === "low" || message.grounded === false;

  return (
    <div className="flex gap-3 text-sm">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-helix/10 text-helix border border-helix/30">
        <Bot className="h-4 w-4" />
      </div>

      <div className="max-w-2xl space-y-3">
        {/* Tutor Message Card */}
        <div
          className={`rounded-2xl rounded-tl-none border p-4 shadow-sm ${
            isLowConfidence
              ? "border-amber-500/40 bg-amber-500/5 text-ink"
              : "border-line bg-surface text-ink"
          }`}
        >
          {/* Grounding Header */}
          <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-xs flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-helix" />
                MindGenome RAG Tutor
              </span>
              {message.confidence && (
                <Badge
                  tone={
                    message.confidence === "high"
                      ? "helix"
                      : message.confidence === "medium"
                        ? "neutral"
                        : "copper"
                  }
                  className="text-[10px]"
                >
                  {message.confidence === "high" && <CheckCircle2 className="h-2.5 w-2.5 mr-1" />}
                  {message.confidence === "low" && <AlertTriangle className="h-2.5 w-2.5 mr-1" />}
                  {message.confidence.toUpperCase()} CONFIDENCE
                </Badge>
              )}
            </div>
            <span className="text-[10px] font-mono text-muted">{message.timestamp}</span>
          </div>

          {/* Low Confidence Alert Callout if ungrounded */}
          {isLowConfidence && (
            <div className="mb-3 flex items-start gap-2 rounded-control bg-amber-500/10 p-2.5 text-xs text-amber-700 dark:text-amber-300">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold block">Not Grounded in Uploaded Materials</span>
                The tutor could not find evidence in your ingested documents for this query. Responses
                are constrained to prevent hallucinations.
              </div>
            </div>
          )}

          {/* Main Prose */}
          <div className="prose prose-sm dark:prose-invert max-w-none text-ink leading-relaxed">
            {message.text.split("\n\n").map((para, i) => (
              <p key={i} className="mb-2 last:mb-0">
                {para}
              </p>
            ))}
          </div>

          {/* Citations Row */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-4 border-t border-line pt-3">
              <span className="block text-[11px] font-semibold uppercase tracking-wider text-muted mb-1.5">
                Source Citations ({message.citations.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {message.citations.map((c, i) => (
                  <CitationChip key={i} citation={c} onSelect={onOpenCitation} />
                ))}
              </div>
            </div>
          )}

          {/* Deep Concept Links into Knowledge Graph */}
          {message.conceptIds && message.conceptIds.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-[11px] font-medium text-muted mr-1">Deep Link:</span>
              {message.conceptIds.map((cid) => (
                <Link
                  key={cid}
                  to={`/app/genome?focus=${cid}`}
                  className="inline-flex items-center gap-1 rounded-control bg-canvas border border-line px-2 py-0.5 text-[11px] text-ink hover:border-helix hover:text-helix transition-colors"
                >
                  <GitGraph className="h-2.5 w-2.5 text-helix" />
                  <span>Inspect in Genome</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Suggested Follow-up Questions */}
        {message.followups && message.followups.length > 0 && (
          <div className="pl-1">
            <span className="text-[11px] font-medium text-muted flex items-center gap-1 mb-1.5">
              <HelpCircle className="h-3 w-3 text-helix" />
              Suggested Follow-up Inquiries:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {message.followups.map((followup, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => onSelectFollowup(followup)}
                  className="rounded-full border border-line bg-surface px-3 py-1 text-xs text-muted hover:border-helix hover:text-ink transition-colors shadow-2xs text-left"
                >
                  {followup} →
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
