import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "./Button";

describe("Button component", () => {
  it("renders with default primary variant", () => {
    render(<Button>Click Me</Button>);
    const btn = screen.getByRole("button", { name: /click me/i });
    expect(btn).toBeInTheDocument();
    expect(btn.className).toContain("bg-helix");
  });

  it("applies secondary and danger variants correctly", () => {
    const { rerender } = render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-surface");

    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-danger");
  });

  it("handles click events and disabled state", async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    const { rerender } = render(<Button onClick={handleClick}>Active</Button>);
    await user.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);

    rerender(<Button disabled onClick={handleClick}>Disabled</Button>);
    const disabledBtn = screen.getByRole("button");
    expect(disabledBtn).toBeDisabled();
    await user.click(disabledBtn);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
