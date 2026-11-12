import { describe, expect, it } from "vitest";

import {
  calculateChartStudies,
  indexedComparison,
} from "@/features/markets/chart-studies";
import { defaultChartPreferences } from "@/features/markets/chart-preferences";
import type { MarketResponse } from "@/lib/api/schemas";

function makeBars(
  entries: ReadonlyArray<readonly [time: string, close: number]>,
): MarketResponse["bars"] {
  return entries.map(([time, close]) => ({
    time,
    open: close,
    high: close,
    low: close,
    close,
    volume: 1,
  }));
}

describe("chart studies", () => {
  it("seeds EMA from the first-period SMA and leaves the warmup empty", () => {
    const bars = makeBars([
      ["2026-11-02", 10],
      ["2026-11-03", 13],
      ["2026-11-04", 16],
      ["2026-11-05", 19],
      ["2026-11-06", 22],
    ]);
    const studies = calculateChartStudies(bars, {
      ...defaultChartPreferences,
      emaEnabled: true,
      emaPeriod: 3,
    });

    expect(studies.ema).toEqual([
      { time: "2026-11-04", value: 13 },
      { time: "2026-11-05", value: 16 },
      { time: "2026-11-06", value: 19 },
    ]);
    expect(studies.bands).toEqual({ upper: [], middle: [], lower: [] });
  });

  it("uses a rolling SMA and population deviation for Bollinger bands", () => {
    const bars = makeBars([
      ["2026-11-02", 1_000_000_000_000],
      ["2026-11-03", 1_000_000_000_002],
      ["2026-11-04", 1_000_000_000_006],
    ]);
    const studies = calculateChartStudies(bars, {
      ...defaultChartPreferences,
      bollingerEnabled: true,
      bollingerPeriod: 2,
      bollingerDeviation: 2,
    });

    expect(studies.bands.middle).toEqual([
      { time: "2026-11-03", value: 1_000_000_000_001 },
      { time: "2026-11-04", value: 1_000_000_000_004 },
    ]);
    expect(studies.bands.upper).toEqual([
      { time: "2026-11-03", value: 1_000_000_000_003 },
      { time: "2026-11-04", value: 1_000_000_000_008 },
    ]);
    expect(studies.bands.lower).toEqual([
      { time: "2026-11-03", value: 999_999_999_999 },
      { time: "2026-11-04", value: 1_000_000_000_000 },
    ]);
    expect(studies.ema).toEqual([]);
  });

  it("keeps enabled studies empty until their warmup periods are complete", () => {
    const bars = makeBars([
      ["2026-11-02", 7],
      ["2026-11-03", 7],
    ]);
    const studies = calculateChartStudies(bars, {
      ...defaultChartPreferences,
      emaEnabled: true,
      emaPeriod: 3,
      bollingerEnabled: true,
      bollingerPeriod: 3,
    });

    expect(studies).toEqual({
      ema: [],
      bands: { upper: [], middle: [], lower: [] },
    });
  });

  it("keeps EMA and bands constant for a constant close series", () => {
    const bars = makeBars([
      ["2026-11-02", 42.5],
      ["2026-11-03", 42.5],
      ["2026-11-04", 42.5],
      ["2026-11-05", 42.5],
    ]);
    const studies = calculateChartStudies(bars, {
      ...defaultChartPreferences,
      emaEnabled: true,
      emaPeriod: 2,
      bollingerEnabled: true,
      bollingerPeriod: 2,
    });

    expect(studies.ema).toEqual([
      { time: "2026-11-03", value: 42.5 },
      { time: "2026-11-04", value: 42.5 },
      { time: "2026-11-05", value: 42.5 },
    ]);
    expect(studies.bands.upper).toEqual([
      { time: "2026-11-03", value: 42.5 },
      { time: "2026-11-04", value: 42.5 },
      { time: "2026-11-05", value: 42.5 },
    ]);
    expect(studies.bands.middle).toEqual(studies.bands.upper);
    expect(studies.bands.lower).toEqual(studies.bands.upper);
  });

  it("is prefix-causal and does not mutate bars", () => {
    const bars = makeBars([
      ["2026-11-02", 10],
      ["2026-11-03", 12],
      ["2026-11-04", 13],
      ["2026-11-05", 11],
      ["2026-11-06", 15],
    ]);
    const originalBars = bars.map((bar) => ({ ...bar }));
    const preferences = {
      ...defaultChartPreferences,
      emaEnabled: true,
      emaPeriod: 2,
      bollingerEnabled: true,
      bollingerPeriod: 3,
    };
    const prefix = calculateChartStudies(bars.slice(0, 4), preferences);
    const full = calculateChartStudies(bars, preferences);

    expect(full.ema.slice(0, prefix.ema.length)).toEqual(prefix.ema);
    expect(full.bands.upper.slice(0, prefix.bands.upper.length)).toEqual(
      prefix.bands.upper,
    );
    expect(full.bands.middle.slice(0, prefix.bands.middle.length)).toEqual(
      prefix.bands.middle,
    );
    expect(full.bands.lower.slice(0, prefix.bands.lower.length)).toEqual(
      prefix.bands.lower,
    );
    expect(bars).toEqual(originalBars);
  });
});

describe("indexed comparison", () => {
  it("uses only common sessions and rebases both closes to the first common date", () => {
    const result = indexedComparison(
      makeBars([
        ["2026-11-01", 80],
        ["2026-11-02", 100],
        ["2026-11-03", 110],
        ["2026-11-05", 120],
      ]),
      makeBars([
        ["2026-11-02", 50],
        ["2026-11-04", 60],
        ["2026-11-05", 75],
      ]),
    );

    expect(result).toEqual({
      anchor: "2026-11-02",
      primary: [
        { time: "2026-11-02", value: 100 },
        { time: "2026-11-05", value: 120 },
      ],
      comparison: [
        { time: "2026-11-02", value: 100 },
        { time: "2026-11-05", value: 150 },
      ],
    });
  });

  it("returns empty series when there are no common sessions", () => {
    expect(
      indexedComparison(
        makeBars([["2026-11-02", 100]]),
        makeBars([["2026-11-03", 50]]),
      ),
    ).toEqual({ anchor: null, primary: [], comparison: [] });
  });
});
