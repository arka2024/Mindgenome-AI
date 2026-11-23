import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AccessibleGraphTree } from "./AccessibleGraphTree";
import type { GraphEdgeData, GraphNodeData } from "./types";

const mockNodes: GraphNodeData[] = [
  { id: "chap-1", label: "Chapter 1: Foundations", kind: "chapter" },
  {
    id: "c-dt",
    label: "Decision Trees",
    kind: "concept",
    mastery: 92,
    band: "mastered",
    parent: "chap-1",
  },
  {
    id: "c-gb",
    label: "Gradient Boosting",
    kind: "concept",
    mastery: 24,
    band: "beginner",
    parent: "chap-1",
  },
];

const mockEdges: GraphEdgeData[] = [
  { id: "e1", source: "chap-1", target: "c-dt", kind: "PART_OF" },
  { id: "e2", source: "chap-1", target: "c-gb", kind: "PART_OF" },
  { id: "e3", source: "c-dt", target: "c-gb", kind: "PREREQUISITE_OF" },
];

describe("AccessibleGraphTree", () => {
  it("renders chapters and child concepts with mastery chips", () => {
    const handleSelect = vi.fn();
    render(
      <AccessibleGraphTree
        nodes={mockNodes}
        edges={mockEdges}
        selectedNodeId={null}
        onSelectNode={handleSelect}
      />,
    );

    expect(screen.getByText("Chapter 1: Foundations")).toBeInTheDocument();
    expect(screen.getAllByText("Decision Trees").length).toBeGreaterThan(0);
    expect(screen.getByText("Gradient Boosting")).toBeInTheDocument();
    expect(screen.getByText("Mastered")).toBeInTheDocument();
    expect(screen.getByText("Beginner")).toBeInTheDocument();
  });

  it("selects a concept when inspect button is clicked", async () => {
    const handleSelect = vi.fn();
    const user = userEvent.setup();

    render(
      <AccessibleGraphTree
        nodes={mockNodes}
        edges={mockEdges}
        selectedNodeId={null}
        onSelectNode={handleSelect}
      />,
    );

    const inspectBtns = screen.getAllByRole("button", { name: /inspect concept/i });
    await user.click(inspectBtns[1]);

    expect(handleSelect).toHaveBeenCalledWith("c-gb");
  });
});
