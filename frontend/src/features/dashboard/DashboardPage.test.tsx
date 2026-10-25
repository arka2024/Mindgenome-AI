import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DashboardPage } from "./DashboardPage";
import * as client from "@/api/client";
import type { Dashboard } from "@/api/schemas";

// Mock Recharts since ResponsiveContainer needs DOM layout
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockDashboardData: Dashboard = {
  overall_mastery: 54,
  band_counts: {
    beginner: 12,
    developing: 18,
    proficient: 10,
    mastered: 4,
  },
  weak_concepts: [
    {
      concept_id: "c-gb",
      name: "Gradient Boosting",
      mastery: 24,
      band: "beginner",
      evidence_n: 5,
      quiz_accuracy: 25,
      recent_performance: 20,
      difficulty_adjusted: 22,
      retention: 30,
    },
    {
      concept_id: "c-ens",
      name: "Ensemble Learning",
      mastery: 48,
      band: "developing",
      evidence_n: 8,
      quiz_accuracy: 50,
      recent_performance: 45,
      difficulty_adjusted: 48,
      retention: 52,
    },
  ],
  recommended: {
    concept_id: "c-gb",
    name: "Gradient Boosting",
    because: "Decision Trees are ready and Ensemble Learning is the likely weak link.",
  },
  growth: [
    { date: "Oct 01", mastery: 32 },
    { date: "Oct 15", mastery: 44 },
    { date: "Oct 24", mastery: 54 },
  ],
  due_revisions: 2,
  revision_list: [
    { concept_id: "c-dt", name: "Decision Trees", due: "Today" },
    { concept_id: "c-gini", name: "Gini Impurity", due: "In 2 days" },
  ],
  activity: [
    { id: "act-1", at: "10 mins ago", text: "Checkpoint Quiz completed for Gradient Boosting" },
    { id: "act-2", at: "1 hour ago", text: "Uploaded 'The Elements of Statistical Learning.pdf'" },
  ],
  active_jobs: [],
};

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders overall mastery score, recommended next, and weak concepts", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValue(mockDashboardData);

    renderWithClient(<DashboardPage />);

    expect(await screen.findByText("54")).toBeInTheDocument();
    expect(screen.getAllByText("Developing").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Gradient Boosting").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Decision Trees are ready and Ensemble Learning is the likely weak link/),
    ).toBeInTheDocument();
    expect(screen.getByText("Ensemble Learning")).toBeInTheDocument();
    expect(screen.getByText("Genome Neighbourhood")).toBeInTheDocument();
    expect(screen.getByText("Revisions Due")).toBeInTheDocument();
  });

  it("triggers startLearning mutation when 'Start Learning' is clicked", async () => {
    const user = userEvent.setup();
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockImplementation(async (path) => {
      if (path === "/dashboard") return mockDashboardData;
      if (path === "/learning-sessions") {
        return { id: "session-123", mode: "learn", concept_id: "c-gb" };
      }
      return {};
    });

    renderWithClient(<DashboardPage />);

    const startBtn = await screen.findByRole("button", { name: /start learning/i });
    await user.click(startBtn);

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/learning-sessions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ mode: "learn", concept_id: "c-gb" }),
      }),
    );
  });
});
