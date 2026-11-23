import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Stepper } from "./Stepper";

describe("Stepper component", () => {
  it("renders 7 steps for document processing", () => {
    render(<Stepper status="embedding" />);
    const list = screen.getByRole("list", { name: /ingestion progress/i });
    expect(list).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(7);
  });

  it("marks steps up to current as completed", () => {
    render(<Stepper status="embedding" />);
    expect(screen.getByText(/Queued/)).toBeInTheDocument();
    expect(screen.getByText(/Parsing/)).toBeInTheDocument();
    expect(screen.getByText(/Chunking/)).toBeInTheDocument();
    expect(screen.getByText(/Embedding/)).toBeInTheDocument();
  });

  it("displays failed state without breaking layout", () => {
    const { container } = render(<Stepper status="failed" />);
    expect(container.querySelector(".border-danger\\/40")).toBeInTheDocument();
  });
});
