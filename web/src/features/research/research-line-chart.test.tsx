import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResearchLineChart } from "./research-line-chart";
import type { ResearchPoint } from "./research-series";

afterEach(cleanup);

function chartPoints(count: number): ResearchPoint[] {
  return Array.from({ length: count }, (_, index) => ({
    time: new Date(Date.UTC(2025, 8, 1 + index)).toISOString().slice(0, 10),
    actual: 100 + index,
    selected: 101 + index,
    baseline: 100.5 + index,
    period: index < count / 2 ? "validation" : "test",
    origin: "2025-08-29",
    cutoff: "2025-08-29T20:00:00Z",
  }));
}

function chart(points: readonly ResearchPoint[]): React.JSX.Element {
  return (
    <ResearchLineChart
      focusLabel="Selected model"
      points={points}
      title="Evaluation points"
    />
  );
}

function movePointer(svg: HTMLElement, clientX: number): void {
  fireEvent(svg, new MouseEvent("pointermove", { bubbles: true, clientX }));
}

describe("research line chart interaction", () => {
  it("selects 20, 60, or all targets and retains the last-60 label", async () => {
    const user = userEvent.setup();
    render(chart(chartPoints(61)));
    const slider = screen.getByRole("slider", {
      name: "Inspect chart session",
    });
    const last20 = screen.getByRole("button", {
      name: "Show last 20 targets",
    });
    const last60 = screen.getByRole("button", {
      name: "Show last 60 targets",
    });
    const all = screen.getByRole("button", { name: "Show all targets" });

    expect(slider).toHaveAttribute("max", "60");
    await user.click(last20);
    expect(slider).toHaveAttribute("max", "19");
    expect(last20).toHaveAttribute("aria-pressed", "true");
    await user.click(last60);
    expect(slider).toHaveAttribute("max", "59");
    expect(last60).toHaveAttribute("aria-pressed", "true");
    await user.click(all);
    expect(slider).toHaveAttribute("max", "60");
    expect(all).toHaveAttribute("aria-pressed", "true");
  });

  it("snaps pointer inspection to saved points and supports pinning with pointer and keyboard", async () => {
    const user = userEvent.setup();
    render(chart(chartPoints(3)));
    const svg = screen.getByRole("img", {
      name: /^Evaluation points Dataset values/u,
    });
    vi.spyOn(svg, "getBoundingClientRect").mockReturnValue(
      new DOMRect(100, 0, 900, 292),
    );
    const slider = screen.getByRole("slider", {
      name: "Inspect chart session",
    });

    movePointer(svg, 580);
    expect(slider).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("Selected model: $102.00"),
    );
    fireEvent.click(svg, { clientX: 580 });
    expect(
      screen.getByRole("button", { name: "Unpin selected target" }),
    ).toHaveAttribute("aria-pressed", "true");

    movePointer(svg, 982);
    expect(slider).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("Selected model: $102.00"),
    );
    fireEvent.click(svg, { clientX: 982 });
    expect(slider).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("Selected model: $103.00"),
    );
    fireEvent.click(svg, { clientX: 982 });
    expect(
      screen.getByRole("button", { name: "Pin selected target" }),
    ).toHaveAttribute("aria-pressed", "false");

    const pin = screen.getByRole("button", { name: "Pin selected target" });
    pin.focus();
    await user.keyboard("{Enter}");
    expect(
      screen.getByRole("button", { name: "Unpin selected target" }),
    ).toHaveAttribute("aria-pressed", "true");
    const keyboardUnpin = screen.getByRole("button", {
      name: "Unpin selected target",
    });
    keyboardUnpin.focus();
    await user.keyboard("{Enter}");
    expect(
      screen.getByRole("button", { name: "Pin selected target" }),
    ).toHaveAttribute("aria-pressed", "false");

    expect(slider).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("Selected model: $103.00"),
    );
  });

  it("ignores pointer coordinates for a zero-width multi-point chart", () => {
    render(chart(chartPoints(3)));
    const svg = screen.getByRole("img", {
      name: /^Evaluation points Dataset values/u,
    });
    vi.spyOn(svg, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 0, 0, 292),
    );
    const slider = screen.getByRole("slider", {
      name: "Inspect chart session",
    });

    movePointer(svg, 1);
    fireEvent.click(svg, { clientX: 1 });

    expect(slider).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("Selected model: $103.00"),
    );
    expect(
      screen.getByRole("button", { name: "Pin selected target" }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("inspects and pins the sole point without dividing by zero", () => {
    render(chart(chartPoints(1)));
    const svg = screen.getByRole("img", {
      name: /^Evaluation points Dataset values/u,
    });
    vi.spyOn(svg, "getBoundingClientRect").mockReturnValue(
      new DOMRect(0, 0, 0, 292),
    );
    const slider = screen.getByRole("slider", {
      name: "Inspect chart session",
    });

    movePointer(svg, 0);
    fireEvent.click(svg, { clientX: 0 });

    expect(slider).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("Selected model: $101.00"),
    );
    expect(
      screen.getByRole("button", { name: "Unpin selected target" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
