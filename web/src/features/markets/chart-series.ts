import type {
  CandlestickData,
  HistogramData,
  LineData,
  Time,
} from "lightweight-charts";

import type { Bar, IndicatorPoint } from "@/lib/api/schemas";

export type VolumeColors = {
  up: string;
  down: string;
};

export function toCandlestickData(bars: Bar[]): CandlestickData<Time>[] {
  return bars.map((bar) => ({
    time: bar.time,
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
  }));
}

export function toLineData(points: IndicatorPoint[]): LineData<Time>[] {
  return points.map((point) => ({ time: point.time, value: point.value }));
}

export function toVolumeData(bars: Bar[], colors: VolumeColors): HistogramData<Time>[] {
  return bars.map((bar) => ({
    time: bar.time,
    value: bar.volume,
    color: bar.close >= bar.open ? colors.up : colors.down,
  }));
}
