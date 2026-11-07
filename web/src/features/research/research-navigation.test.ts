import { describe, expect, it } from "vitest";

import {
  parseResearchPageSearchParams,
  researchWorkspaceHref,
} from "./research-navigation";

const RUN_A = "22222222-2222-4222-8222-222222222222";
const RUN_B = "44444444-4444-4444-8444-444444444444";

describe("research workspace navigation", () => {
  it("parses bookmarkable run, comparison, watchlist, and display-focus parameters", () => {
    expect(
      parseResearchPageSearchParams({
        run: RUN_A,
        compare: RUN_B,
        instrument: "xnas-aapl",
        method: "last_close",
      }),
    ).toEqual({
      requestedRunId: RUN_A,
      requestedCompareId: RUN_B,
      requestedInstrumentId: "xnas-aapl",
      focusModel: "last_close",
    });
  });

  it("ignores malformed or repeated parameters and defaults to display-only historical log mean", () => {
    expect(
      parseResearchPageSearchParams({
        run: [RUN_A, RUN_B],
        compare: RUN_B,
        instrument: "../../private",
        method: "trained-neural-network",
      }),
    ).toEqual({
      requestedRunId: null,
      requestedCompareId: null,
      requestedInstrumentId: null,
      focusModel: "historical_log_mean",
    });
  });

  it("builds a shareable comparison URL and drops invalid self-comparisons", () => {
    const href = researchWorkspaceHref({
      runId: RUN_A,
      compareId: RUN_B,
      instrumentId: "xnas-aapl",
      focusModel: "last_close",
    });

    expect(href).toBe(
      `/app/research?run=${RUN_A}&compare=${RUN_B}&instrument=xnas-aapl&method=last_close`,
    );
    expect(
      researchWorkspaceHref({
        runId: RUN_A,
        compareId: RUN_A,
        instrumentId: null,
        focusModel: "historical_log_mean",
      }),
    ).toBe(`/app/research?run=${RUN_A}`);
  });
});
