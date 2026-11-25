import { cn } from "@/shared/lib/cn";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "helix" | "copper" | "danger";
  className?: string;
}) {
  const tones = {
    neutral: "bg-canvas text-muted border-line",
    helix: "bg-helix/10 text-helix border-helix/30",
    copper: "bg-copper/10 text-copper border-copper/30",
    danger: "bg-danger/10 text-danger border-danger/30",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
