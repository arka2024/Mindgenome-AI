import { useSearchParams, Link } from "react-router-dom";
import { TutorChat } from "./TutorChat";
import { Button } from "@/shared/ui/Button";
import { Badge } from "@/shared/ui/Badge";
import { GitGraph, Sparkles, Upload } from "lucide-react";

export function TutorPage() {
  const [searchParams] = useSearchParams();
  const initialPrompt = searchParams.get("prompt") ?? undefined;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display text-2xl font-bold sm:text-3xl">Grounded AI Tutor</h1>
            <Badge tone="helix">
              <Sparkles className="h-3 w-3 mr-1 inline" />
              Source-Grounded RAG
            </Badge>
          </div>
          <p className="mt-0.5 text-xs text-muted">
            Ask conceptual questions grounded directly in your syllabus and textbook excerpts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/genome">
            <Button variant="secondary" className="text-xs">
              <GitGraph className="h-3.5 w-3.5 mr-1" />
              Open Knowledge Graph
            </Button>
          </Link>
          <Link to="/app/documents">
            <Button variant="secondary" className="text-xs">
              <Upload className="h-3.5 w-3.5 mr-1" />
              Document Library
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Chat Canvas */}
      <div className="flex-1 min-h-0">
        <TutorChat initialPrompt={initialPrompt} />
      </div>
    </div>
  );
}
