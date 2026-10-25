import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { LoginPage, RegisterPage, ForgotPage } from "./AuthPages";
import * as client from "@/api/client";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

describe("AuthPages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("LoginPage", () => {
    it("renders prefilled demo email and password", () => {
      render(
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>,
      );

      const emailInput = screen.getByDisplayValue("learner@mindgenome.ai");
      expect(emailInput).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /instant demo sign-in/i })).toBeInTheDocument();
    });

    it("toggles password visibility", async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>,
      );

      const toggleBtn = screen.getByRole("button", { name: /show password/i });
      await user.click(toggleBtn);

      expect(screen.getByRole("button", { name: /hide password/i })).toBeInTheDocument();
    });

    it("submits login form and triggers apiFetch", async () => {
      const user = userEvent.setup();
      const mockApiFetch = vi.mocked(client.apiFetch);
      mockApiFetch.mockResolvedValueOnce({
        access_token: "mock-access",
        refresh_token: "mock-refresh",
        expires_in: 3600,
        token_type: "bearer",
      });

      render(
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>,
      );

      const submitBtn = screen.getByRole("button", { name: "Sign In" });
      await user.click(submitBtn);

      expect(mockApiFetch).toHaveBeenCalledWith(
        "/auth/login",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  describe("RegisterPage", () => {
    it("renders registration inputs and prefill helper", async () => {
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <RegisterPage />
        </BrowserRouter>,
      );

      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      const prefillBtn = screen.getByRole("button", { name: /prefill sample details/i });
      await user.click(prefillBtn);

      expect(screen.getByDisplayValue("Alex Rivera")).toBeInTheDocument();
    });
  });

  describe("ForgotPage", () => {
    it("shows confirmation upon successful reset submission", async () => {
      const user = userEvent.setup();
      const mockApiFetch = vi.mocked(client.apiFetch);
      mockApiFetch.mockResolvedValueOnce({
        message: "Password reset link sent to your email.",
      });

      render(
        <BrowserRouter>
          <ForgotPage />
        </BrowserRouter>,
      );

      const emailInput = screen.getByPlaceholderText("you@domain.edu");
      await user.type(emailInput, "alex@institution.edu");

      const submitBtn = screen.getByRole("button", { name: /send reset link/i });
      await user.click(submitBtn);

      expect(
        await screen.findByText("Password reset link sent to your email."),
      ).toBeInTheDocument();
    });
  });
});
