import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it } from "vitest";

import { ResearchBaselineSummary } from "./research-baseline-summary";
import { researchRunFixture } from "./research-test-fixtures";

afterEach(cleanup);

it("shows saved benchmark differences with period, units and interpretation", async () => {
  const run = researchRunFixture({ id: "22222222-2222-4222-8222-222222222222", name: "Synthetic check" });
  render(<ResearchBaselineSummary run={run} />);
  const table = screen.getByRole("table", { name: /test errors by model/u });
  expect(within(table).getByRole("columnheader", { name: "Δ MAE vs last close" })).toBeVisible();
  const row = within(table).getByRole("row", { name: /Historical log mean/u });
  expect(within(row).getAllByRole("cell").map((cell) => cell.textContent)).toEqual(["$2.00", "$2.00", "$1.00"]);
  await userEvent.click(screen.getByRole("button", { name: /^Validation$/u }));
  expect(screen.getByRole("table", { name: /validation errors by model/u })).toBeVisible();
  await userEvent.click(screen.getByText("How to read these errors"));
  expect(screen.getByText(/negative value means lower descriptive error/u)).toBeVisible();
  expect(screen.getByText(/synthetic pipeline checks, not empirical prediction results/u)).toBeVisible();
});
