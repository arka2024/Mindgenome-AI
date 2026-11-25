import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GenomeGraphPage } from "./GenomeGraphPage";
import * as client from "@/api/client";
import type { GraphPayload } from "./types";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

// Mock CytoscapeCanvas for JSDOM testing
vi.mock("./CytoscapeCanvas", () => ({
  CytoscapeCanvas: ({
    nodes,
    onSelectNode,
  }: {
    nodes: Array<{ id: string; label: string }>;
    onSelectNode: (id: string) => void;
  }) => (
    <div data-testid="mock-cytoscape-canvas">
      {nodes.map((n) => (
        <button key={n.id} onClick={() => onSelectNode(n.id)}>
          Node: {n.label}
        </button>
      ))}
    </div>
  ),
}));

const mockGraphData: GraphPayload = {
  nodes: [
    {
      data: {
        id: "ch-1",
        label: "Chapter 1: Tree Ensembles",
        kind: "chapter",
      },
    },
    {
      data: {
        id: "c-dt",
        label: "Decision Trees",
        kind: "concept",
        mastery: 92,
        band: "mastered",
        definition: "A hierarchical decision model based on feature thresholding.",
      },
    },
    {
      data: {
        id: "c-gb",
        label: "Gradient Boosting",
        kind: "concept",
        mastery: 24,
        band: "beginner",
        definition: "A sequential ensemble that minimizes pseudo-residuals.",
      },
    },
  ],
  edges: [
    { data: { id: "e1", source: "ch-1", target: "c-dt", kind: "PART_OF" } },
    { data: { id: "e2", source: "ch-1", target: "c-gb", kind: "PART_OF" } },
    { data: { id: "e3", source: "c-dt", target: "c-gb", kind: "PREREQUISITE_OF" } },
  ],
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

describe("GenomeGraphPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders graph controls, toggles to accessible tree view, and inspects node", async () => {
    const user = userEvent.setup();
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValueOnce(mockGraphData);

    renderWithClient(<GenomeGraphPage />);

    expect(await screen.findByRole("heading", { name: /knowledge genome/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/filter concepts/i)).toBeInTheDocument();

    // Toggle from Canvas to Accessible Tree View
    const treeTabBtn = screen.getByRole("button", { name: /accessible tree/i });
    await user.click(treeTabBtn);

    expect(screen.getByText("Chapter 1: Tree Ensembles")).toBeInTheDocument();
    expect(screen.getAllByText("Gradient Boosting").length).toBeGreaterThan(0);

    // Select Gradient Boosting to open NodeInspector
    const inspectBtns = screen.getAllByRole("button", { name: /inspect concept/i });
    await user.click(inspectBtns[1]);

    expect(
      screen.getByText("A sequential ensemble that minimizes pseudo-residuals."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /learn gradient boosting/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /checkpoint quiz/i })).toBeInTheDocument();
  });

  it("highlights prerequisite lineage when trace button is clicked", async () => {
    const user = userEvent.setup();
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValueOnce(mockGraphData);

    renderWithClient(<GenomeGraphPage />);

    // Click on Gradient Boosting from mock canvas
    const gbNodeBtn = await screen.findByRole("button", { name: /node: gradient boosting/i });
    await user.click(gbNodeBtn);

    // Inspector opens
    const traceBtn = screen.getByRole("button", { name: /trace prerequisite chain/i });
    await user.click(traceBtn);

    expect(screen.getByRole("button", { name: /clear lineage highlight/i })).toBeInTheDocument();
  });
});
