import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TutorPage } from "./TutorPage";
import * as client from "@/api/client";
import type { TutorAnswer } from "@/api/schemas";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockGroundedAnswer: TutorAnswer = {
  grounded: true,
  confidence: "high",
  message:
    "Gradient boosting fits each new tree to the negative gradient of the loss. It is a sequential ensemble.",
  citations: [
    {
      document_id: "doc-1",
      filename: "Hands-On Machine Learning (demo excerpt).pdf",
      chapter_title: "Gradient boosting",
      page_start: 45,
      page_end: 47,
      chunk_id: "c1",
      passage: "Gradient boosting builds an additive model in a forward stage-wise fashion.",
    },
  ],
  concept_ids: ["c-gb"],
  followups: ["Why keep trees shallow?"],
};

const mockUngroundedAnswer: TutorAnswer = {
  grounded: false,
  confidence: "low",
  message: "I cannot ground this in your uploaded material.",
  citations: [],
  followups: ["What is gradient boosting?"],
};

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

describe("TutorPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders tutor interface, sends question, and views grounded citations", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValueOnce(mockGroundedAnswer);

    const user = userEvent.setup();
    renderWithClient(<TutorPage />);

    expect(screen.getByRole("heading", { name: /Grounded AI Tutor/i })).toBeInTheDocument();
    expect(screen.getByText(/Welcome to your MindGenome Grounded Tutor/i)).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Ask anything grounded in your uploaded documents/i);
    await user.type(input, "What is gradient boosting in my notes?{enter}");

    await waitFor(() => {
      expect(screen.getByText(/Gradient boosting fits each new tree/i)).toBeInTheDocument();
    });

    const citationChip = screen.getByRole("button", { name: /View source citation from/i });
    expect(citationChip).toBeInTheDocument();

    await user.click(citationChip);

    await waitFor(() => {
      expect(screen.getByText(/Source Grounding/i)).toBeInTheDocument();
      expect(screen.getByText(/Verbatim Extraction/i)).toBeInTheDocument();
    });
  });

  it("displays low confidence ungrounded alert for out-of-scope questions", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValueOnce(mockUngroundedAnswer);

    const user = userEvent.setup();
    renderWithClient(<TutorPage />);

    const input = screen.getByPlaceholderText(/Ask anything grounded in your uploaded documents/i);
    await user.type(input, "What does quantum annealing do?{enter}");

    await waitFor(() => {
      expect(screen.getByText(/Not Grounded in Uploaded Materials/i)).toBeInTheDocument();
    });
  });
});
