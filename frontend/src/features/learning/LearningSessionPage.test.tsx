import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LearningSessionPage } from "./LearningSessionPage";
import * as client from "@/api/client";
import type { LearningSession } from "@/api/schemas";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockSession: LearningSession = {
  id: "session-1",
  mode: "learn",
  status: "active",
  concept_id: "c-gb",
  concept_name: "Gradient Boosting",
  because: "Recommended because it sits on Decision Trees in your graph.",
  current_index: 0,
  current_section: "Additive stage-wise fitting",
  sections: [
    {
      id: "sec-1",
      title: "Additive stage-wise fitting",
      body: "Gradient boosting starts from a constant prediction and adds a new tree that points downhill.",
      understood: false,
    },
    {
      id: "sec-2",
      title: "Residuals are the training signal",
      body: "For squared error, the negative gradient is simply the residual y − ŷ.",
      understood: false,
    },
  ],
};

function renderWithClient(ui: React.ReactElement, initialEntries = ["/app/learn/session-1"]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("LearningSessionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders learning session, navigates sections, marks understood, and triggers quiz", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path.includes("/progress")) {
        return {
          ...mockSession,
          sections: mockSession.sections.map((s, idx) =>
            idx === 0 ? { ...s, understood: true } : s,
          ),
        };
      }
      return mockSession;
    });

    const user = userEvent.setup();
    renderWithClient(
      <Routes>
        <Route path="/app/learn/:id" element={<LearningSessionPage />} />
        <Route path="/app/quiz/:id" element={<div>Quiz Attempt Started</div>} />
      </Routes>,
      ["/app/learn/session-1"],
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Gradient Boosting/i })).toBeInTheDocument();
      expect(screen.getAllByText(/Additive stage-wise fitting/i)[0]).toBeInTheDocument();
    });

    const markBtn = screen.getByRole("button", { name: /Mark as Understood/i });
    await user.click(markBtn);

    await waitFor(() => {
      expect(screen.getByText(/Understood ✓/i)).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole("button", { name: /Next Section/i });
    await user.click(nextBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/Residuals are the training signal/i)[0]).toBeInTheDocument();
    });
  });
});
