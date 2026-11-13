import { describe, expect, it } from "vitest";

import {
  MarketResponseSchema,
  SessionSchema,
} from "./schemas";

const validMarketResponse = {
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
    {
      time: "2026-10-30",
      open: 102,
      high: 104,
      low: 100,
      close: 101,
      volume: 900,
    },
  ],
  study_history: [
    { time: "2026-10-28", close: 100 },
    { time: "2026-10-29", close: 102 },
    { time: "2026-10-30", close: 101 },
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
    as_of: "2026-10-30",
    fetched_at: "2026-10-30T21:00:00Z",
    price_basis: "synthetic",
    freshness_state: "stale",
    market_state: "unknown",
    delay_seconds: null,
    snapshot_id: "fixture-snapshot",
    disclaimer: "Synthetic demonstration data.",
  },
};

describe("market response boundary schema", () => {
  it("accepts ordered exchange-session bars with matching provenance", () => {
    expect(MarketResponseSchema.parse(validMarketResponse)).toEqual(validMarketResponse);
  });

  it("rejects an out-of-order or duplicate daily session", () => {
    const reversedBars = {
      ...validMarketResponse,
      bars: [...validMarketResponse.bars].reverse(),
    };
    const duplicateBars = {
      ...validMarketResponse,
      bars: [validMarketResponse.bars[0], validMarketResponse.bars[0]],
    };

    expect(MarketResponseSchema.safeParse(reversedBars).success).toBe(false);
    expect(MarketResponseSchema.safeParse(duplicateBars).success).toBe(false);
  });

  it("rejects invalid close-history ordering, range mismatches, and excessive history", () => {
    const reversedHistory = {
      ...validMarketResponse,
      study_history: [...validMarketResponse.study_history].reverse(),
    };
    const duplicateHistory = {
      ...validMarketResponse,
      study_history: [
        ...validMarketResponse.study_history,
        validMarketResponse.study_history.at(-1),
      ],
    };
    const mismatchedClose = {
      ...validMarketResponse,
      study_history: validMarketResponse.study_history.map((point) =>
        point.time === "2026-10-30" ? { ...point, close: 999 } : point,
      ),
    };
    const olderHistory = Array.from({ length: 998 }, (_, index) => ({
      time: new Date(Date.UTC(2024, 0, index + 1)).toISOString().slice(0, 10),
      close: 100,
    }));
    const excessiveHistory = {
      ...validMarketResponse,
      study_history: [...olderHistory, ...validMarketResponse.study_history],
    };

    expect(MarketResponseSchema.safeParse(reversedHistory).success).toBe(false);
    expect(MarketResponseSchema.safeParse(duplicateHistory).success).toBe(false);
    expect(MarketResponseSchema.safeParse(mismatchedClose).success).toBe(false);
    expect(MarketResponseSchema.safeParse(excessiveHistory).success).toBe(false);
  });

  it("rejects an RSI point outside its published 0–100 domain", () => {
    const responseWithInvalidRsi = {
      ...validMarketResponse,
      indicators: {
        ...validMarketResponse.indicators,
        rsi14: [{ time: "2026-10-30", value: 101 }],
      },
    };

    expect(MarketResponseSchema.safeParse(responseWithInvalidRsi).success).toBe(false);
  });

  it("keeps authenticated and anonymous session variants distinct", () => {
    const common = {
      csrf_token: "csrf",
      market_data_enabled: false,
      legacy_enabled: false,
    };

    expect(
      SessionSchema.safeParse({
        ...common,
        authenticated: true,
        user: null,
      }).success,
    ).toBe(false);
    expect(
      SessionSchema.parse({
        ...common,
        authenticated: false,
        user: null,
      }).authenticated,
    ).toBe(false);
  });
});
