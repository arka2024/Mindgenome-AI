import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { LandingPage } from "./LandingPage";

describe("LandingPage", () => {
  it("renders main headline and core CTA buttons", () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>,
    );

    expect(
      screen.getByRole("heading", {
        name: /from ai that understands documents to ai that understands the learner/i,
      }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /launch demo lab/i })).toBeInTheDocument();
  });

  it("renders the 5-step loop and allows clicking through steps", async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>,
    );

    expect(screen.getByText("01")).toBeInTheDocument();
    expect(screen.getByText("02")).toBeInTheDocument();
    expect(screen.getByText("03")).toBeInTheDocument();
    expect(screen.getByText("04")).toBeInTheDocument();
    expect(screen.getByText("05")).toBeInTheDocument();

    const step3 = screen.getByText("Focused Learning");
    await user.click(step3);
    expect(screen.getByText("Step 3 of 5")).toBeInTheDocument();
  });

  it("expands and collapses FAQ items on user click", async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>,
    );

    // Question 1 starts open in default state
    expect(screen.getByText(/Standard chatbots treat your notes as a flat text retrieval problem/)).toBeInTheDocument();

    // Click Question 2 to expand it
    const q2 = screen.getByRole("button", { name: /how is concept mastery calculated/i });
    await user.click(q2);

    expect(
      screen.getByText(/We adhere strictly to our explainable 40\/20\/20\/20 formula/),
    ).toBeInTheDocument();
  });
});
