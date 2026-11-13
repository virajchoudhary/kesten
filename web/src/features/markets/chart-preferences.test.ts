import { describe, expect, it } from "vitest";

import {
  ChartPreferencesSchema,
  defaultChartPreferences,
  parseChartPreferences,
} from "@/features/markets/chart-preferences";

describe("chart preferences", () => {
  it("provides the versioned defaults", () => {
    expect(defaultChartPreferences).toEqual({
      version: 1,
      chartType: "candles",
      scaleMode: "normal",
      crosshair: "normal",
      showGrid: true,
      showVolume: true,
      showRsi: true,
      showSma20: true,
      showSma50: true,
      emaEnabled: false,
      emaPeriod: 21,
      bollingerEnabled: false,
      bollingerPeriod: 20,
      bollingerDeviation: 2,
    });
  });

  it("applies defaults to valid partial preferences", () => {
    expect(
      ChartPreferencesSchema.parse({
        version: 1,
        chartType: "area",
        emaEnabled: true,
      }),
    ).toEqual({
      ...defaultChartPreferences,
      chartType: "area",
      emaEnabled: true,
    });
  });

  it("rejects malformed values and unsupported persisted versions", () => {
    const invalidPeriod = { ...defaultChartPreferences, emaPeriod: 1 };
    const unsupportedVersion = { ...defaultChartPreferences, version: 2 };
    const missingVersion = { chartType: "area" };
    const unknownPreference = { ...defaultChartPreferences, futureSetting: true };

    expect(ChartPreferencesSchema.safeParse(invalidPeriod).success).toBe(false);
    expect(ChartPreferencesSchema.safeParse(unsupportedVersion).success).toBe(false);
    expect(ChartPreferencesSchema.safeParse(missingVersion).success).toBe(false);
    expect(ChartPreferencesSchema.safeParse(unknownPreference).success).toBe(false);
    expect(parseChartPreferences(invalidPeriod)).toEqual(defaultChartPreferences);
    expect(parseChartPreferences(unsupportedVersion)).toEqual(defaultChartPreferences);
    expect(parseChartPreferences(missingVersion)).toEqual(defaultChartPreferences);
    expect(parseChartPreferences(null)).toEqual(defaultChartPreferences);
  });

  it("falls back for invalid enum and non-finite deviation values", () => {
    expect(
      parseChartPreferences({ ...defaultChartPreferences, scaleMode: "square-root" }),
    ).toEqual(defaultChartPreferences);
    expect(
      parseChartPreferences({
        ...defaultChartPreferences,
        bollingerDeviation: Number.POSITIVE_INFINITY,
      }),
    ).toEqual(defaultChartPreferences);
  });
});
