import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { ToastViewport, useToasts } from "./Toast";

describe("Toast component and store", () => {
  beforeEach(() => {
    act(() => {
      useToasts.setState({ items: [] });
    });
  });

  it("renders toasts when pushed to store and dismisses them", () => {
    render(<ToastViewport />);

    act(() => {
      useToasts.getState().push("Concept mastered", "Gradient Boosting is now at 85%");
    });

    expect(screen.getByText("Concept mastered")).toBeInTheDocument();
    expect(screen.getByText("Gradient Boosting is now at 85%")).toBeInTheDocument();

    const items = useToasts.getState().items;
    expect(items).toHaveLength(1);

    act(() => {
      useToasts.getState().dismiss(items[0].id);
    });

    expect(screen.queryByText("Concept mastered")).not.toBeInTheDocument();
  });
});
