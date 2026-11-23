import { Dialog } from "@/shared/ui/Dialog";
import { Input } from "@/shared/ui/Input";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CONCEPTS } from "@/mocks/seed";

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const items = useMemo(() => {
    const pages = [
      { label: "Genome dashboard", to: "/app" },
      { label: "Documents", to: "/app/documents" },
      { label: "Knowledge graph", to: "/app/genome" },
      { label: "Tutor", to: "/app/tutor" },
      { label: "Mastery", to: "/app/mastery" },
      { label: "Adaptive path", to: "/app/path" },
      { label: "Settings", to: "/app/settings" },
    ];
    const concepts = CONCEPTS.map((c) => ({
      label: `Concept: ${c.name}`,
      to: `/app/genome?focus=${c.id}`,
    }));
    const all = [...pages, ...concepts];
    const n = q.trim().toLowerCase();
    return n ? all.filter((i) => i.label.toLowerCase().includes(n)) : all.slice(0, 12);
  }, [q]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Jump anywhere">
      <Input
        autoFocus
        placeholder="Concepts, pages, actions…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Command search"
      />
      <ul className="mt-3 max-h-64 overflow-auto">
        {items.map((i) => (
          <li key={i.to + i.label}>
            <button
              className="w-full rounded-control px-2 py-2 text-left hover:bg-canvas"
              onClick={() => {
                navigate(i.to);
                onOpenChange(false);
              }}
            >
              {i.label}
            </button>
          </li>
        ))}
      </ul>
    </Dialog>
  );
}
