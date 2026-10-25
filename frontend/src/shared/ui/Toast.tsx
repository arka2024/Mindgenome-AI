import * as ToastPrimitive from "@radix-ui/react-toast";
import { create } from "zustand";

type ToastItem = { id: string; title: string; body?: string };

type ToastState = {
  items: ToastItem[];
  push: (title: string, body?: string) => void;
  dismiss: (id: string) => void;
};

export const useToasts = create<ToastState>((set) => ({
  items: [],
  push: (title, body) =>
    set((s) => ({ items: [...s.items, { id: crypto.randomUUID(), title, body }] })),
  dismiss: (id) => set((s) => ({ items: s.items.filter((t) => t.id !== id) })),
}));

export function ToastViewport() {
  const items = useToasts((s) => s.items);
  const dismiss = useToasts((s) => s.dismiss);
  return (
    <ToastPrimitive.Provider swipeDirection="right">
      {items.map((t) => (
        <ToastPrimitive.Root
          key={t.id}
          duration={4000}
          onOpenChange={(open) => {
            if (!open) dismiss(t.id);
          }}
          className="rounded-card border border-line bg-surface p-3 shadow-card"
        >
          <ToastPrimitive.Title className="font-semibold">{t.title}</ToastPrimitive.Title>
          {t.body ? (
            <ToastPrimitive.Description className="text-sm text-muted">
              {t.body}
            </ToastPrimitive.Description>
          ) : null}
        </ToastPrimitive.Root>
      ))}
      <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-[60] flex w-80 flex-col gap-2" />
    </ToastPrimitive.Provider>
  );
}
