import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { QuizPage } from "./QuizPage";
import * as client from "@/api/client";
import type { QuizAttemptView, QuizResult } from "@/api/schemas";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockAttempt: QuizAttemptView = {
  id: "attempt-1",
  concept_id: "c-gb",
  concept_name: "Gradient Boosting",
  feedback_mode: "immediate",
  questions: [
    {
      id: "q-1",
      stem: "What does each new tree in gradient boosting typically fit?",
      choices: [
        "The original labels y",
        "The negative gradient of the loss (residuals for squared error)",
      ],
      difficulty: "easy",
      hint: "Think downhill on the loss, not downhill on y.",
      concept_tags: ["Gradient Boosting", "Residuals"],
    },
  ],
};

const mockResult: QuizResult = {
  attempt_id: "attempt-1",
  correct: 2,
  total: 5,
  per_question: [
    {
      question_id: "q-1",
      selected_index: 0,
      correct_index: 1,
      explanation: "Trees are fit to the negative gradient.",
      is_correct: false,
    },
  ],
  mastery: {
    concept_id: "c-gb",
    name: "Gradient Boosting",
    mastery: 35,
    band: "developing",
    evidence_n: 6,
    quiz_accuracy: 33,
    recent_performance: 30,
    difficulty_adjusted: 32,
    retention: 40,
  },
  deltas: [
    {
      concept_id: "c-gb",
      name: "Gradient Boosting",
      before: 42,
      after: 35,
    },
  ],
  next: {
    mode: "remedial",
    concept_id: "c-ens",
    concept_name: "Ensemble Learning",
    because: "You're weak in Gradient Boosting (2/5). Likely missing prerequisite: Ensemble Learning.",
  },
};

function renderWithClient(ui: React.ReactElement, initialEntries = ["/app/quiz/attempt-1"]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("QuizPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders questions, selects choices, toggles hint, submits and shows diagnosis", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockImplementation(async (path: string) => {
      if (path.includes("/submit")) {
        return mockResult;
      }
      return mockAttempt;
    });

    renderWithClient(
      <Routes>
        <Route path="/app/quiz/:id" element={<QuizPage />} />
      </Routes>,
      ["/app/quiz/attempt-1"],
    );

    // Wait for quiz to load
    await waitFor(() => {
      expect(screen.getAllByRole("heading", { name: /Gradient Boosting/i })[0]).toBeInTheDocument();
      expect(
        screen.getByText(/What does each new tree in gradient boosting typically fit\?/i),
      ).toBeInTheDocument();
    });

    // Test hint toggle
    const hintBtn = screen.getByRole("button", { name: /Need a Hint\?/i });
    fireEvent.click(hintBtn);
    expect(screen.getByText(/Think downhill on the loss, not downhill on y/i)).toBeInTheDocument();

    // Select choice
    const choiceButtons = screen.getAllByRole("radio");
    fireEvent.click(choiceButtons[0]);

    // Wait for submit button to be enabled and click it
    await waitFor(() => {
      const submitBtn = screen.getByRole("button", { name: /Submit Checkpoint Quiz/i });
      expect(submitBtn).not.toBeDisabled();
      fireEvent.click(submitBtn);
    });

    // Results screen & Prerequisite diagnosis!
    await waitFor(() => {
      expect(screen.getByText(/You Scored 2 \/ 5 \(40%\)/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Likely missing prerequisite: Ensemble Learning/i),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Remedial Lesson: Ensemble Learning/i }),
      ).toBeInTheDocument();
    });
  });
});
