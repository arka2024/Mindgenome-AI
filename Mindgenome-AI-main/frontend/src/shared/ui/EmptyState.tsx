import { Button } from "./Button";

export function EmptyState({
  title,
  body,
  action,
  onAction,
}: {
  title: string;
  body: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="rounded-card border border-dashed border-line bg-surface p-8 text-center">
      <h2 className="font-display text-2xl">{title}</h2>
      <p className="mt-2 text-muted">{body}</p>
      {action && onAction ? (
        <Button className="mt-4" onClick={onAction}>
          {action}
        </Button>
      ) : null}
    </div>
  );
}
