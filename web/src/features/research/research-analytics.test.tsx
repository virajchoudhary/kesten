import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ResearchAnalytics } from "./research-analytics";
import { researchRunFixture } from "./research-test-fixtures";
import { HISTORICAL_CSV_EXPORT_DISABLED_REASON } from "./research-csv";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("interactive research analytics", () => {
  it("switches views, filters evaluation periods, and exposes inspectable exact data", async () => {
    const user = userEvent.setup();
    const run = researchRunFixture({
      id: "11111111-1111-4111-8111-111111111111",
      name: "Synthetic check",
    });
    render(<ResearchAnalytics run={run} />);
    expect(
      screen.getByRole("img", { name: /Dataset history and forecast paths/ }),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Download CSV" })).toBeNull();

    const NativeURL = URL;
    const createObjectURL = vi.fn<(blob: Blob) => string>(
      () => "blob:research-csv",
    );
    const revokeObjectURL = vi.fn();
    class TestURL extends NativeURL {}
    Object.defineProperties(TestURL, {
      createObjectURL: { configurable: true, value: createObjectURL },
      revokeObjectURL: { configurable: true, value: revokeObjectURL },
    });
    vi.stubGlobal("URL", TestURL);
    const downloads: string[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      downloads.push(this.download);
    });

    await user.click(
      screen.getByRole("button", { name: "Walk-forward" }),
    );
    expect(
      screen.getByRole("img", {
        name: /Walk-forward dataset values and predictions/,
      }),
    ).toBeVisible();
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Evaluation period" }),
      "test",
    );
    await user.click(screen.getByRole("button", { name: "Download CSV" }));
    expect(downloads).toEqual([
      "research-11111111-1111-4111-8111-111111111111-walk-forward-test.csv",
    ]);
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    const blob = createObjectURL.mock.calls[0]?.[0];
    if (!blob) throw new Error("Missing evaluation CSV blob");
    const downloadedCsv = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () =>
        typeof reader.result === "string"
          ? resolve(reader.result)
          : reject(new Error("Not text"));
      reader.onerror = () => reject(reader.error);
      reader.readAsText(blob);
    });
    expect(downloadedCsv.trimEnd().split("\r\n")).toHaveLength(2);
    expect(downloadedCsv).toContain('"partition_filter"');
    expect(downloadedCsv).toContain('"test"');
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:research-csv");
    expect(screen.getByLabelText(/Inspect session/)).toHaveAttribute(
      "max",
      "0",
    );
    await user.click(
      screen.getByRole("button", { name: "Errors" }),
    );
    expect(
      screen.getByRole("img", { name: /Walk-forward forecast errors/ }),
    ).toBeVisible();
    expect(screen.getByText(/not trading returns/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Download CSV" }));
    expect(downloads).toHaveLength(2);
    expect(downloads[1]).toBe(
      "research-11111111-1111-4111-8111-111111111111-errors-test.csv",
    );
    fireEvent.change(
      screen.getByRole("slider", { name: "Inspect chart session" }),
      { target: { value: "0" } },
    );
    expect(screen.getByRole("slider")).toHaveAttribute(
      "aria-valuetext",
      expect.stringContaining("test"),
    );
    await user.click(
      screen.getByText("Exact evaluation values", { selector: "summary" }),
    );
    expect(
      screen.getByRole("region", { name: "Exact evaluation values" }),
    ).toBeVisible();
    expect(screen.queryByText(/confidence interval/i)).toBeNull();
  });

  it("withholds CSV for historical datasets and explains the restriction", async () => {
    const user = userEvent.setup();
    const run = researchRunFixture({
      id: "55555555-5555-4555-8555-555555555555",
      name: "Historical evaluation",
    });
    run.data_kind = "historical";
    run.result.data_kind = "historical";
    run.result.evidence_kind = "historical_walk_forward";
    render(<ResearchAnalytics run={run} />);

    await user.click(screen.getByRole("button", { name: "Walk-forward" }));

    expect(
      screen.queryByRole("button", { name: "Download CSV" }),
    ).toBeNull();
    expect(screen.getByRole("note")).toHaveTextContent(
      HISTORICAL_CSV_EXPORT_DISABLED_REASON,
    );
  });
});
