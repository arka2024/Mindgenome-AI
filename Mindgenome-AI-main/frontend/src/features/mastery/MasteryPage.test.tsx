import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MasteryPage } from "./MasteryPage";
import * as client from "@/api/client";
import type { MasteryScore } from "@/api/schemas";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockMasteryItems: MasteryScore[] = [
  {
    concept_id: "c-gb",
    name: "Gradient Boosting",
    mastery: 42,
    band: "developing",
    evidence_n: 5,
    quiz_accuracy: 40,
    recent_performance: 42,
    difficulty_adjusted: 41,
    retention: 45,
  },
  {
    concept_id: "c-dt",
    name: "Decision Trees",
    mastery: 85,
    band: "mastered",
    evidence_n: 8,
    quiz_accuracy: 85,
    recent_performance: 88,
    difficulty_adjusted: 84,
    retention: 82,
  },
];

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("MasteryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders mastery telemetry, filters by band, and opens formula modal", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValue({ items: mockMasteryItems });

    const user = userEvent.setup();
    renderWithClient(<MasteryPage />);

    // Wait for table to load
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Concept Mastery Telemetry/i })).toBeInTheDocument();
      expect(screen.getByText(/Gradient Boosting/i)).toBeInTheDocument();
      expect(screen.getByText(/Decision Trees/i)).toBeInTheDocument();
    });

    // Test band filtering
    const devFilter = screen.getByRole("button", { name: /Developing/i });
    await user.click(devFilter);

    // Test formula modal
    const formulaBtn = screen.getByRole("button", { name: /Explain 40\/20\/20\/20 Formula/i });
    await user.click(formulaBtn);

    await waitFor(() => {
      expect(screen.getByText(/The 40 \/ 20 \/ 20 \/ 20 Mastery Formula/i)).toBeInTheDocument();
      expect(screen.getByText(/40% Quiz Accuracy/i)).toBeInTheDocument();
    });
  });
});
