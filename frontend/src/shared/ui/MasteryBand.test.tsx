import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MasteryChip } from "./MasteryBand";

describe("MasteryChip component", () => {
  it("renders beginner band with accessible label and range", () => {
    render(<MasteryChip band="beginner" score={25} />);
    expect(screen.getByText("Beginner")).toBeInTheDocument();
    expect(screen.getByText("25")).toBeInTheDocument();
    expect(screen.getByText("0–30")).toHaveClass("sr-only");
  });

  it("renders proficient band without score when omitted", () => {
    render(<MasteryChip band="proficient" />);
    expect(screen.getByText("Proficient")).toBeInTheDocument();
    expect(screen.getByText("61–80")).toHaveClass("sr-only");
  });

  it("renders insufficient evidence state appropriately", () => {
    render(<MasteryChip band="insufficient_evidence" />);
    expect(screen.getByText("Not enough evidence")).toBeInTheDocument();
  });
});
