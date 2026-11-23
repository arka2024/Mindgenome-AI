import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Tabs } from "./Tabs";

describe("Tabs component", () => {
  const tabs = [
    { value: "tab1", label: "Tab One", content: <div>Content One</div> },
    { value: "tab2", label: "Tab Two", content: <div>Content Two</div> },
  ];

  it("renders active tab content and responds to changes", async () => {
    const handleValueChange = vi.fn();
    const user = userEvent.setup();

    render(
      <Tabs value="tab1" onValueChange={handleValueChange} tabs={tabs} />,
    );

    expect(screen.getByText("Content One")).toBeInTheDocument();
    const tabTwoTrigger = screen.getByRole("tab", { name: /tab two/i });
    await user.click(tabTwoTrigger);

    expect(handleValueChange).toHaveBeenCalledWith("tab2");
  });
});
