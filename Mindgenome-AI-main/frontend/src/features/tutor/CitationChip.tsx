import type { Citation } from "@/api/schemas";
import { BookOpen } from "lucide-react";

export function CitationChip({
  citation,
  onSelect,
}: {
  citation: Citation;
  onSelect: (citation: Citation) => void;
}) {
  const label = [
    citation.filename.replace(/\.pdf$|\.docx$/i, ""),
    citation.chapter_title ? `§ ${citation.chapter_title}` : null,
    citation.page_start ? `p. ${citation.page_start}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <button
      type="button"
      onClick={() => onSelect(citation)}
      className="inline-flex items-center gap-1.5 rounded-full border border-helix/30 bg-helix/10 px-2.5 py-1 text-[11px] font-medium text-helix transition-colors hover:border-helix hover:bg-helix/20 focus:outline-none focus:ring-2 focus:ring-helix/50"
      title={`Open source citation: ${label}`}
      aria-label={`View source citation from ${label}`}
    >
      <BookOpen className="h-3 w-3 shrink-0" />
      <span className="truncate max-w-[240px]">{label}</span>
    </button>
  );
}
