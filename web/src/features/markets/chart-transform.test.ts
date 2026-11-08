import { describe, expect, it } from "vitest";
import { MarketResponseSchema } from "@/lib/api/schemas";
import { chartValue, comparisonCompatibility } from "./chart-transform";
const primary = MarketResponseSchema.parse({
  instrument: {
    id: "xnas-aapl",
    symbol: "AAPL",
    name: "Apple Inc.",
    exchange: "XNAS",
    currency: "USD",
    timezone: "America/New_York",
  },
  bars: [
    {
      time: "2026-10-29",
      open: 100,
      high: 103,
      low: 99,
      close: 102,
      volume: 1200,
    },
  ],
  indicators: {
    sma20: [],
    sma50: [],
    rsi14: [],
  },
  provenance: {
    data_mode: "demo",
    source_id: "cadrisyn-synthetic-v1",
    source_label: "Synthetic demonstration dataset",
    as_of: "2026-10-29",
    fetched_at: "2026-10-29T22:00:00Z",
    price_basis: "synthetic",
    freshness_state: "stale",
    market_state: "unknown",
    delay_seconds: null,
    snapshot_id: "fixture-snapshot",
    disclaimer: "Synthetic demonstration data.",
  },
});

const comparison = {
  ...primary,
  instrument: { ...primary.instrument, id: "xnas-msft", symbol: "MSFT" },
};
describe("chart scale and comparison contracts", () => {
  it("uses a common anchor across prices and studies", () => {
    expect(chartValue(100, 100, "percent")).toBe(0);
    expect(chartValue(110, 100, "percent")).toBeCloseTo(10);
    expect(chartValue(120, 100, "indexed")).toBe(120);
    expect(chartValue(105, 100, "log")).toBe(105);
    expect(chartValue(105, 100, "normal")).toBe(105);
  });
  it("rejects same-symbol, cross-currency and mixed provenance comparisons", () => {
    expect(comparisonCompatibility(primary, comparison)).toBeNull();
    expect(comparisonCompatibility(primary, primary)).toMatch(/different/);
    expect(
      comparisonCompatibility(primary, {
        ...comparison,
        instrument: { ...comparison.instrument, currency: "INR" },
      }),
    ).toMatch(/currency/);
    for (const patch of [
      { data_mode: "delayed" as const },
      { source_id: "other-provider" },
      { price_basis: "adjusted_close" },
    ]) {
      expect(
        comparisonCompatibility(primary, {
          ...comparison,
          provenance: { ...comparison.provenance, ...patch },
        }),
      ).toMatch(/category, provider and price basis/);
    }
  });
});
