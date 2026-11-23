import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LearningPathPage } from "./LearningPathPage";
import * as client from "@/api/client";
import type { LearningPath } from "@/api/schemas";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockLearningPath: LearningPath = {
  items: [
    {
      concept_id: "c-ens",
      name: "Ensemble Learning",
      because: "Recommended because Gradient Boosting depends on it and mastery is low.",
      kind: "remedial",
      band: "beginner",
    },
    {
      concept_id: "c-gb",
      name: "Gradient Boosting",
      because: "Recommended next in the curriculum chain.",
      kind: "learn",
      band: "developing",
    },
    {
      concept_id: "c-xgb",
      name: "XGBoost",
      because: "Next concept once GB is proficient.",
      kind: "next",
      band: "insufficient_evidence",
    },
  ],
};

function renderWithClient(ui: React.ReactElement, initialEntries = ["/app/path"]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("LearningPathPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders adaptive learning path with ordered concept roadmap", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path.includes("/learning-sessions")) {
        return { id: "s-1", mode: "remedial" };
      }
      return mockLearningPath;
    });

    renderWithClient(
      <Routes>
        <Route path="/app/path" element={<LearningPathPage />} />
        <Route path="/app/learn/:id" element={<div>Learning Mode Launched</div>} />
      </Routes>,
      ["/app/path"],
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Adaptive Learning Path/i })).toBeInTheDocument();
      expect(screen.getAllByText(/Ensemble Learning/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Gradient Boosting/i)[0]).toBeInTheDocument();
      expect(screen.getByText(/XGBoost/i)).toBeInTheDocument();
    });

    const actionBtn = screen.getByRole("button", { name: /Start Remedial Lesson/i });
    expect(actionBtn).toBeInTheDocument();
    fireEvent.click(actionBtn);

    await waitFor(() => {
      expect(screen.getByText(/Learning Mode Launched/i)).toBeInTheDocument();
    });
  });
});
