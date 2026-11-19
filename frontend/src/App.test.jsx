import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FilterBar, InsightRail } from "./App.jsx";

const filters = {
  start_date: "2025-01-01",
  end_date: "2025-12-31",
  min_magnitude: "",
  max_magnitude: "",
  geographic_assignment_status: "",
};

describe("FilterBar", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("reports edits, submit, and reset actions to the shared state owner", () => {
    const setDraft = vi.fn();
    const onSubmit = vi.fn((event) => event.preventDefault());
    const onReset = vi.fn();
    render(
      <FilterBar
        draft={filters}
        setDraft={setDraft}
        onSubmit={onSubmit}
        onReset={onReset}
        loading={false}
      />,
    );

    fireEvent.change(screen.getByLabelText("Minimum magnitude"), { target: { value: "5" } });
    expect(setDraft).toHaveBeenCalledTimes(1);
    const nextDraft = setDraft.mock.calls[0][0](filters);
    expect(nextDraft).toMatchObject({ min_magnitude: "5" });

    fireEvent.submit(screen.getByRole("button", { name: "Apply filters" }).closest("form"));
    expect(onSubmit).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("disables filter actions while the dashboard is loading", () => {
    render(
      <FilterBar
        draft={filters}
        setDraft={vi.fn()}
        onSubmit={vi.fn()}
        onReset={vi.fn()}
        loading
      />,
    );

    expect(screen.getByRole("button", { name: /Refreshing/ }).disabled).toBe(true);
    expect(screen.getByRole("button", { name: "Reset" }).disabled).toBe(true);
  });
});

describe("InsightRail", () => {
  afterEach(cleanup);

  it("opens a selected peek and toggles it closed when clicked again", () => {
    const onSelect = vi.fn();
    const { rerender } = render(<InsightRail active={null} onSelect={onSelect} />);
    const monthlyButton = screen.getByRole("button", { name: "Open Monthly side peek" });

    fireEvent.click(monthlyButton);
    expect(onSelect).toHaveBeenCalledWith("temporal");

    rerender(<InsightRail active="temporal" onSelect={onSelect} />);
    fireEvent.click(screen.getByRole("button", { name: "Open Monthly side peek" }));
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });
});
