import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocumentDetailPage } from "./DocumentDetailPage";
import * as client from "@/api/client";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockDoc = {
  id: "doc-1",
  filename: "Hands-On Machine Learning.pdf",
  status: "ready" as const,
  created_at: new Date().toISOString(),
  page_count: 80,
  job_id: "job-1",
  chapters: [
    { id: "chap-1", title: "Decision Trees & Purity", page_start: 1, page_end: 22 },
    { id: "chap-2", title: "Ensemble Methods & Voting", page_start: 23, page_end: 44 },
    { id: "chap-3", title: "Gradient Boosting & Residuals", page_start: 45, page_end: 68 },
  ],
};

const mockJob = {
  id: "job-1",
  document_id: "doc-1",
  status: "ready" as const,
  progress_pct: 100,
  stage_detail: "ready",
};

function renderWithRoute(ui: React.ReactElement, initialPath = "/app/documents/doc-1") {
  window.history.pushState({}, "Test", initialPath);
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/app/documents/:id" element={ui} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("DocumentDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders document detail, stepper stage, and detected chapters", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockImplementation(async (path) => {
      if (path === "/documents/doc-1") return mockDoc;
      if (path === "/ingestion-jobs/job-1") return mockJob;
      return {};
    });

    renderWithRoute(<DocumentDetailPage />);

    expect(await screen.findByText("Hands-On Machine Learning.pdf")).toBeInTheDocument();
    expect(screen.getByText("80 Total Pages")).toBeInTheDocument();
    expect(screen.getByText("100% Completed")).toBeInTheDocument();
    expect(screen.getByText("Decision Trees & Purity")).toBeInTheDocument();
    expect(screen.getByText("Gradient Boosting & Residuals")).toBeInTheDocument();
    expect(screen.getByText("Pages 45–68 · Semantic Chapter")).toBeInTheDocument();
    expect(
      screen.getByText(/Corpus Ready for Learning & RAG Tutoring/i),
    ).toBeInTheDocument();
  });
});
