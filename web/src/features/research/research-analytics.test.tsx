import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ResearchAnalytics } from "./research-analytics";
import { researchRunFixture } from "./research-test-fixtures";

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
});
