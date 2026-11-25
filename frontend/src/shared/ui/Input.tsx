import { cn } from "@/shared/lib/cn";
import { forwardRef, type InputHTMLAttributes } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-control border border-line bg-surface px-3 py-2 text-ink placeholder:text-muted",
          className,
        )}
        {...props}
      />
    );
  },
);

export function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-semibold">{label}</span>
      {children}
      {error ? (
        <span className="block text-sm text-danger" role="alert">
          {error}
        </span>
      ) : null}
    </label>
  );
}
