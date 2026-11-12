import { describe, expect, it } from "vitest";

import {
  formatBasisPoints,
  formatPercentage,
  formatSessionDate,
  formatUsd,
  formatUtcTimestamp,
} from "./research-formatters";

describe("research formatters", () => {
  it("formats session dates in UTC without shifting the exchange date", () => {
    expect(formatSessionDate("2026-11-05")).toBe("Nov 5, 2026");
  });

  it("labels generated timestamps in UTC", () => {
    expect(formatUtcTimestamp("2026-11-05T16:30:00Z")).toMatch(/Nov 5, 2026.*4:30 PM UTC/u);
  });

  it("formats price errors in USD and return errors in basis points", () => {
    expect(formatUsd(123.4567)).toBe("$123.4567");
    expect(formatBasisPoints(0.012345)).toBe("123.45 bps");
  });

  it("formats direction rates as percentages", () => {
    expect(formatPercentage(0.5)).toBe("50.0%");
  });
});
