import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SettingsPage } from "./SettingsPage";
import * as client from "@/api/client";
import { useSession } from "@/features/auth/session";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

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

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders profile, toggles quiz options, and triggers store reset", async () => {
    const mockApiFetch = vi.mocked(client.apiFetch);
    mockApiFetch.mockResolvedValue({ ok: true });

    useSession.getState().setUser({
      id: "u-1",
      email: "learner@mindgenome.ai",
      display_name: "Asha Learner",
      roles: ["user"],
    });

    renderWithClient(<SettingsPage />);

    expect(
      screen.getByRole("heading", { name: /Learner Preferences & System/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Asha Learner/i)).toBeInTheDocument();

    // Toggle feedback mode
    const feedbackToggle = screen.getByRole("button", { name: /Feedback/i });
    fireEvent.click(feedbackToggle);
    expect(screen.getByText(/End Feedback/i)).toBeInTheDocument();

    // Reset demo store button
    const resetBtn = screen.getByRole("button", { name: /Reset Demo Story/i });
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith("/store/reset", expect.anything());
      expect(screen.getByText(/Knowledge Genome state reset successfully/i)).toBeInTheDocument();
    });
  });
});
