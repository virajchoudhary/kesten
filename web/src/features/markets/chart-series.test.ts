import { describe, expect, it } from "vitest";

import {
  toCandlestickData,
  toLineData,
  toVolumeData,
} from "@/features/markets/chart-series";
import type { Bar, IndicatorPoint } from "@/lib/api/schemas";

const bars: Bar[] = [
  {
    time: "2026-10-28",
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
];

describe("market chart series", () => {
  it("keeps exchange session dates and maps OHLC values without filling gaps", () => {
    expect(toCandlestickData(bars)).toEqual([
      {
        time: "2026-10-28",
        open: 100,
        high: 103,
        low: 99,
        close: 102,
      },
      {
        time: "2026-10-30",
        open: 102,
        high: 104,
        low: 100,
        close: 101,
      },
    ]);
  });

  it("plots only indicator observations returned by the API", () => {
    const points: IndicatorPoint[] = [{ time: "2026-10-30", value: 101.5 }];

    expect(toLineData(points)).toEqual([{ time: "2026-10-30", value: 101.5 }]);
  });

  it("colors each volume bar from that session's candle direction", () => {
    expect(toVolumeData(bars, { up: "#08734b", down: "#ba2434" })).toEqual([
      { time: "2026-10-28", value: 1200, color: "#08734b" },
      { time: "2026-10-30", value: 900, color: "#ba2434" },
    ]);
  });
});
