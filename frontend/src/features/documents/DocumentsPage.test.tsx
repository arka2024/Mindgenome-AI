import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocumentsPage } from "./DocumentsPage";
import * as client from "@/api/client";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockDocuments = {
  items: [
    {
      id: "doc-1",
      filename: "The Elements of Statistical Learning.pdf",
      status: "ready" as const,
      created_at: new Date().toISOString(),
      page_count: 80,
    },
    {
      id: "doc-2",
      filename: "Ensemble_Methods_Lecture_Notes.docx",
      status: "uploaded" as const,
      created_at: new Date().toISOString(),
      page_count: 24,
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("DocumentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders upload dropzone and document library items", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValueOnce(mockDocuments);

    renderWithClient(<DocumentsPage />);

    expect(screen.getByRole("heading", { name: /document corpus/i })).toBeInTheDocument();
    expect(screen.getByText(/drag and drop your study materials/i)).toBeInTheDocument();

    expect(await screen.findByText("The Elements of Statistical Learning.pdf")).toBeInTheDocument();
    expect(screen.getByText("Ensemble_Methods_Lecture_Notes.docx")).toBeInTheDocument();
    expect(screen.getByText("80 Pages")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("Ingesting")).toBeInTheDocument();
  });

  it("uploads a sample paper when 'Upload Demo ML Paper' is clicked", async () => {
    const user = userEvent.setup();
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch
      .mockResolvedValueOnce(mockDocuments)
      .mockResolvedValueOnce({ document_id: "doc-new", job_id: "job-new", status: "queued" });

    renderWithClient(<DocumentsPage />);

    const sampleBtn = screen.getByRole("button", { name: /upload demo ml paper/i });
    await user.click(sampleBtn);

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/documents",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("deletes a document and triggers refetch", async () => {
    const user = userEvent.setup();
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch
      .mockResolvedValueOnce(mockDocuments)
      .mockResolvedValueOnce({});

    renderWithClient(<DocumentsPage />);

    const deleteBtns = await screen.findAllByRole("button", { name: /delete/i });
    await user.click(deleteBtns[0]);

    expect(mockApiFetch).toHaveBeenCalledWith("/documents/doc-1", { method: "DELETE" });
  });
});
