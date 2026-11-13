import type { MarketResponse } from "@/lib/api/schemas";

import type { ChartPreferences } from "./chart-preferences";

type StudyPoint = { time: string; value: number };

type BollingerBands = {
  upper: StudyPoint[];
  middle: StudyPoint[];
  lower: StudyPoint[];
};

type AlignedSeries = {
  anchor: string | null;
  primary: StudyPoint[];
  comparison: StudyPoint[];
};

function calculateEma(
  bars: MarketResponse["study_history"],
  period: number,
): StudyPoint[] {
  if (bars.length < period) {
    return [];
  }

  let seedTotal = 0;
  for (let index = 0; index < period; index += 1) {
    seedTotal += bars[index].close;
  }

  let previousValue = seedTotal / period;
  const points: StudyPoint[] = [
    { time: bars[period - 1].time, value: previousValue },
  ];
  const alpha = 2 / (period + 1);

  for (let index = period; index < bars.length; index += 1) {
    const close = bars[index].close;
    previousValue += alpha * (close - previousValue);
    points.push({ time: bars[index].time, value: previousValue });
  }

  return points;
}

function calculateBollingerBands(
  bars: MarketResponse["study_history"],
  period: number,
  deviationMultiplier: number,
): BollingerBands {
  const upper: StudyPoint[] = [];
  const middle: StudyPoint[] = [];
  const lower: StudyPoint[] = [];
  let rollingSum = 0;

  for (let index = 0; index < bars.length; index += 1) {
    rollingSum += bars[index].close;
    if (index >= period) {
      rollingSum -= bars[index - period].close;
    }
    if (index < period - 1) {
      continue;
    }

    const start = index - period + 1;
    const average = rollingSum / period;
    let squaredDifferenceTotal = 0;
    for (let windowIndex = start; windowIndex <= index; windowIndex += 1) {
      const difference = bars[windowIndex].close - average;
      squaredDifferenceTotal += difference * difference;
    }

    const populationDeviation = Math.sqrt(squaredDifferenceTotal / period);
    const time = bars[index].time;
    middle.push({ time, value: average });
    upper.push({
      time,
      value: average + deviationMultiplier * populationDeviation,
    });
    lower.push({
      time,
      value: average - deviationMultiplier * populationDeviation,
    });
  }

  return { upper, middle, lower };
}

function emptyBands(): BollingerBands {
  return { upper: [], middle: [], lower: [] };
}

export function calculateChartStudies(
  bars: MarketResponse["bars"],
  preferences: ChartPreferences,
  history: MarketResponse["study_history"] = bars,
): { ema: StudyPoint[]; bands: BollingerBands } {
  const visibleDates = new Set(bars.map((bar) => bar.time));
  const visible = (points: StudyPoint[]) =>
    points.filter((point) => visibleDates.has(point.time));
  const bands = preferences.bollingerEnabled
    ? calculateBollingerBands(
        history,
        preferences.bollingerPeriod,
        preferences.bollingerDeviation,
      )
    : emptyBands();
  return {
    ema: preferences.emaEnabled
      ? visible(calculateEma(history, preferences.emaPeriod))
      : [],
    bands: {
      upper: visible(bands.upper),
      middle: visible(bands.middle),
      lower: visible(bands.lower),
    },
  };
}

export function indexedComparison(
  primaryBars: MarketResponse["bars"],
  comparisonBars: MarketResponse["bars"],
): AlignedSeries {
  const comparisonByTime = new Map<
    string,
    MarketResponse["bars"][number]
  >();
  for (const bar of comparisonBars) {
    comparisonByTime.set(bar.time, bar);
  }

  const alignedBars: Array<{
    time: string;
    primaryClose: number;
    comparisonClose: number;
  }> = [];
  for (const primaryBar of primaryBars) {
    const comparisonBar = comparisonByTime.get(primaryBar.time);
    if (comparisonBar !== undefined) {
      alignedBars.push({
        time: primaryBar.time,
        primaryClose: primaryBar.close,
        comparisonClose: comparisonBar.close,
      });
    }
  }

  const anchorBar = alignedBars[0];
  if (anchorBar === undefined) {
    return { anchor: null, primary: [], comparison: [] };
  }

  return {
    anchor: anchorBar.time,
    primary: alignedBars.map((bar) => ({
      time: bar.time,
      value: (bar.primaryClose / anchorBar.primaryClose) * 100,
    })),
    comparison: alignedBars.map((bar) => ({
      time: bar.time,
      value: (bar.comparisonClose / anchorBar.comparisonClose) * 100,
    })),
  };
}
