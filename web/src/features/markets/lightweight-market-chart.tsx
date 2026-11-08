"use client";

import { useEffect, useCallback, useRef, useState } from "react";
import { useTheme } from "next-themes";
import type {
  IChartApi,
  ISeriesApi,
  IPriceLine,
  Time,
} from "lightweight-charts";
import type { MarketResponse } from "@/lib/api/schemas";
import type { ChartPreferences } from "./chart-preferences";
import { calculateChartStudies, indexedComparison } from "./chart-studies";
import {
  chartValue,
  type ChartLevel,
  type ChartCommand,
} from "./chart-transform";
import { toVolumeData } from "./chart-series";

type PriceSeries =
  | ISeriesApi<"Candlestick">
  | ISeriesApi<"Bar">
  | ISeriesApi<"Line">
  | ISeriesApi<"Area">;
type Instances = {
  library: typeof import("lightweight-charts");
  chart: IChartApi;
  candles: ISeriesApi<"Candlestick">;
  bars: ISeriesApi<"Bar">;
  line: ISeriesApi<"Line">;
  area: ISeriesApi<"Area">;
  sma20: ISeriesApi<"Line">;
  sma50: ISeriesApi<"Line">;
  ema: ISeriesApi<"Line">;
  upper: ISeriesApi<"Line">;
  middle: ISeriesApi<"Line">;
  lower: ISeriesApi<"Line">;
  volume: ISeriesApi<"Histogram"> | null;
  rsi: ISeriesApi<"Line"> | null;
  comparePrimary: ISeriesApi<"Line"> | null;
  compareSecondary: ISeriesApi<"Line"> | null;
  ruler: ISeriesApi<"Line">;
};
type Bar = MarketResponse["bars"][number];
type Measurement =
  | { kind: "empty" }
  | { kind: "start"; start: Bar }
  | { kind: "complete"; start: Bar; end: Bar };
const EMPTY_MEASUREMENT: Measurement = { kind: "empty" };
const token = (name: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim();
function session(time: Time | undefined): string | null {
  if (time === undefined) return null;
  if (typeof time === "string") return time;
  if (typeof time === "number")
    return new Date(time * 1000).toISOString().slice(0, 10);
  return `${time.year}-${String(time.month).padStart(2, "0")}-${String(time.day).padStart(2, "0")}`;
}
function priceSeries(
  i: Instances,
  type: ChartPreferences["chartType"],
): PriceSeries {
  switch (type) {
    case "candles":
      return i.candles;
    case "bars":
      return i.bars;
    case "line":
      return i.line;
    case "area":
      return i.area;
  }
}
function update(
  i: Instances,
  data: MarketResponse,
  p: ChartPreferences,
  comparison: MarketResponse | null,
  fit: boolean,
): void {
  const base = data.bars[0]?.close ?? 1;
  const transform = (value: number) => chartValue(value, base, p.scaleMode);
  const candles = data.bars.map((bar) => ({
    ...bar,
    open: transform(bar.open),
    high: transform(bar.high),
    low: transform(bar.low),
    close: transform(bar.close),
  }));
  const closes = data.bars.map((bar) => ({
    time: bar.time,
    value: transform(bar.close),
  }));
  const points = (values: Array<{ time: string; value: number }>) =>
    values.map((point) =>
      p.scaleMode === "log" && point.value <= 0
        ? { time: point.time }
        : { time: point.time, value: transform(point.value) },
    );
  i.candles.setData(candles);
  i.bars.setData(candles);
  i.line.setData(closes);
  i.area.setData(closes);
  i.sma20.setData(points(data.indicators.sma20));
  i.sma50.setData(points(data.indicators.sma50));
  const studies = calculateChartStudies(data.bars, p);
  i.ema.setData(points(studies.ema));
  i.upper.setData(points(studies.bands.upper));
  i.middle.setData(points(studies.bands.middle));
  i.lower.setData(points(studies.bands.lower));
  i.volume?.setData(
    toVolumeData(data.bars, {
      up: token("--chart-volume-up"),
      down: token("--chart-volume-down"),
    }),
  );
  i.rsi?.setData(data.indicators.rsi14);
  if (comparison) {
    const aligned = indexedComparison(data.bars, comparison.bars);
    i.comparePrimary?.setData(aligned.primary);
    i.compareSecondary?.setData(aligned.comparison);
  }
  i.candles.applyOptions({ visible: p.chartType === "candles" });
  i.bars.applyOptions({ visible: p.chartType === "bars" });
  i.line.applyOptions({ visible: p.chartType === "line" });
  i.area.applyOptions({ visible: p.chartType === "area" });
  i.sma20.applyOptions({ visible: p.showSma20 });
  i.sma50.applyOptions({ visible: p.showSma50 });
  i.ema.applyOptions({ visible: p.emaEnabled });
  for (const series of [i.upper, i.middle, i.lower])
    series.applyOptions({ visible: p.bollingerEnabled });
  const format = new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });
  const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: data.instrument.currency,
    maximumFractionDigits: 2,
  });
  const formatter = (value: number) =>
    p.scaleMode === "percent"
      ? `${format.format(value)}%`
      : p.scaleMode === "indexed"
        ? format.format(value)
        : money.format(value);
  for (const series of [i.candles, i.bars, i.line, i.area])
    series.applyOptions({
      priceFormat: { type: "custom", minMove: 0.01, formatter },
    });
  i.chart.applyOptions({
    grid: {
      vertLines: { visible: p.showGrid },
      horzLines: { visible: p.showGrid },
    },
    crosshair: {
      mode:
        p.crosshair === "magnet"
          ? i.library.CrosshairMode.Magnet
          : i.library.CrosshairMode.Normal,
    },
  });
  i.chart.priceScale("right", 0).applyOptions({
    mode:
      p.scaleMode === "log"
        ? i.library.PriceScaleMode.Logarithmic
        : i.library.PriceScaleMode.Normal,
  });
  if (fit) i.chart.timeScale().fitContent();
}
function theme(i: Instances): void {
  const up = token("--chart-up"),
    down = token("--chart-down"),
    accent = token("--accent");
  i.chart.applyOptions({
    layout: {
      background: {
        type: i.library.ColorType.Solid,
        color: token("--surface"),
      },
      textColor: token("--text-secondary"),
      attributionLogo: true,
    },
    grid: {
      vertLines: { color: token("--chart-grid") },
      horzLines: { color: token("--chart-grid") },
    },
    crosshair: {
      vertLine: {
        color: token("--chart-crosshair"),
        labelBackgroundColor: token("--text-secondary"),
      },
      horzLine: {
        color: token("--chart-crosshair"),
        labelBackgroundColor: token("--text-secondary"),
      },
    },
    rightPriceScale: { borderColor: token("--border-subtle") },
    timeScale: { borderColor: token("--border-subtle") },
  });
  i.candles.applyOptions({
    upColor: up,
    downColor: down,
    borderUpColor: up,
    borderDownColor: down,
    wickUpColor: up,
    wickDownColor: down,
  });
  i.bars.applyOptions({ upColor: up, downColor: down });
  i.line.applyOptions({ color: accent });
  i.area.applyOptions({
    lineColor: accent,
    topColor: token("--area-fill"),
    bottomColor: token("--surface"),
  });
  i.sma20.applyOptions({ color: token("--chart-sma20") });
  i.sma50.applyOptions({ color: token("--chart-sma50") });
  i.ema.applyOptions({ color: token("--chart-ema") });
  for (const series of [i.upper, i.middle, i.lower])
    series.applyOptions({ color: token("--chart-bands") });
  i.rsi?.applyOptions({ color: token("--chart-rsi") });
  i.comparePrimary?.applyOptions({ color: accent });
  i.compareSecondary?.applyOptions({ color: token("--chart-sma20") });
  i.ruler.applyOptions({ color: token("--warning") });
}

export function LightweightMarketChart({
  data,
  preferences,
  comparison = null,
  command,
  levels,
  measureEnabled,
}: {
  data: MarketResponse;
  preferences: ChartPreferences;
  comparison?: MarketResponse | null;
  command: ChartCommand;
  levels: ChartLevel[];
  measureEnabled: boolean;
}): React.JSX.Element {
  const host = useRef<HTMLDivElement>(null),
    instances = useRef<Instances | null>(null);
  const current = useRef({ data, preferences, comparison, measureEnabled });
  useEffect(() => {
    current.current = { data, preferences, comparison, measureEnabled };
  }, [data, preferences, comparison, measureEnabled]);
  const range =
    useRef<
      ReturnType<ReturnType<IChartApi["timeScale"]>["getVisibleLogicalRange"]>
    >(null);
  const [generation, setGeneration] = useState(0);
  const [state, setState] = useState<"loading" | "ready" | "failed">("loading");
  const [hover, setHover] = useState<string | null>(null);
  const [savedMeasurement, setSavedMeasurement] = useState<{
    snapshot: string;
    value: Measurement;
  }>({ snapshot: data.provenance.snapshot_id, value: { kind: "empty" } });
  const measurement: Measurement =
    savedMeasurement.snapshot === data.provenance.snapshot_id
      ? savedMeasurement.value
      : EMPTY_MEASUREMENT;
  const setMeasurement = useCallback(
    (value: Measurement) =>
      setSavedMeasurement({ snapshot: data.provenance.snapshot_id, value }),
    [data.provenance.snapshot_id],
  );
  const { resolvedTheme } = useTheme();
  const selected =
    data.bars.find((bar) => bar.time === hover) ?? data.bars.at(-1);
  const hasComparison = comparison !== null;
  const choose = useCallback(
    (bar: Bar) =>
      setSavedMeasurement((previous) => {
        const value =
          previous.snapshot === data.provenance.snapshot_id
            ? previous.value
            : ({ kind: "empty" } as const);
        return {
          snapshot: data.provenance.snapshot_id,
          value:
            value.kind !== "start"
              ? { kind: "start", start: bar }
              : value.start.time === bar.time
                ? value
                : { kind: "complete", start: value.start, end: bar },
        };
      }),
    [data.provenance.snapshot_id],
  );
  const chooseRef = useRef(choose);
  useEffect(() => {
    chooseRef.current = choose;
  }, [choose]);

  useEffect(() => {
    if (!host.current) return;
    const container = host.current;
    let cancelled = false;

    void import("lightweight-charts")
      .then((lib) => {
        if (cancelled) return;
        const chart = lib.createChart(container, {
          autoSize: true,
          layout: {
            attributionLogo: true,
            fontFamily: '"IBM Plex Mono", monospace',
            fontSize: 10,
          },
          timeScale: { rightOffset: 3, timeVisible: false },
          rightPriceScale: {
            minimumWidth: 70,
            scaleMargins: { top: 0.16, bottom: 0.08 },
          },
          crosshair: {
            vertLine: { style: lib.LineStyle.Dashed },
            horzLine: { style: lib.LineStyle.Dashed },
          },
        });
        container.querySelector("table")?.setAttribute("role", "presentation");
        const candles = chart.addSeries(lib.CandlestickSeries, {
          priceLineVisible: true,
        });
        const bars = chart.addSeries(lib.BarSeries, {
          visible: false,
          priceLineVisible: true,
          thinBars: true,
        });
        const line = chart.addSeries(lib.LineSeries, {
          visible: false,
          lineWidth: 2,
          priceLineVisible: true,
        });
        const area = chart.addSeries(lib.AreaSeries, {
          visible: false,
          lineWidth: 2,
          priceLineVisible: true,
        });
        const study = (color: string, style = lib.LineStyle.Solid) =>
          chart.addSeries(lib.LineSeries, {
            color,
            lineWidth: 1,
            lineStyle: style,
            lastValueVisible: false,
            priceLineVisible: false,
            crosshairMarkerVisible: false,
          });
        const sma20 = study(token("--chart-sma20")),
          sma50 = study(token("--chart-sma50")),
          ema = study(token("--chart-ema"));
        const upper = study(token("--chart-bands"), lib.LineStyle.Dashed),
          middle = study(token("--chart-bands")),
          lower = study(token("--chart-bands"), lib.LineStyle.Dashed);
        const ruler = study(token("--warning"), lib.LineStyle.Dashed);
        let pane = 1;
        const volume = preferences.showVolume
          ? chart.addSeries(
              lib.HistogramSeries,
              {
                priceFormat: { type: "volume" },
                priceLineVisible: false,
                lastValueVisible: false,
              },
              pane++,
            )
          : null;
        const rsi = preferences.showRsi
          ? chart.addSeries(
              lib.LineSeries,
              {
                title: "RSI 14",
                lineWidth: 1,
                priceLineVisible: false,
                priceFormat: { type: "price", precision: 1, minMove: 0.1 },
                autoscaleInfoProvider: () => ({
                  priceRange: { minValue: 0, maxValue: 100 },
                }),
              },
              pane++,
            )
          : null;
        rsi?.createPriceLine({
          price: 30,
          color: token("--chart-rsi-threshold"),
          lineWidth: 1,
          lineStyle: lib.LineStyle.Dashed,
          axisLabelVisible: false,
        });
        rsi?.createPriceLine({
          price: 70,
          color: token("--chart-rsi-threshold"),
          lineWidth: 1,
          lineStyle: lib.LineStyle.Dashed,
          axisLabelVisible: false,
        });
        const comparePrimary = hasComparison
          ? chart.addSeries(
              lib.LineSeries,
              {
                title: data.instrument.symbol,
                lineWidth: 1,
                priceLineVisible: false,
                priceFormat: { type: "price", precision: 2, minMove: 0.01 },
              },
              pane,
            )
          : null;
        const compareSecondary = hasComparison
          ? chart.addSeries(
              lib.LineSeries,
              {
                title: comparison?.instrument.symbol,
                lineWidth: 2,
                priceLineVisible: false,
                priceFormat: { type: "price", precision: 2, minMove: 0.01 },
              },
              pane,
            )
          : null;
        chart.panes()[0]?.setStretchFactor(7);
        let next = 1;
        if (volume) chart.panes()[next++]?.setStretchFactor(1);
        if (rsi) chart.panes()[next++]?.setStretchFactor(2);
        if (hasComparison) chart.panes()[next]?.setStretchFactor(2.5);
        const i: Instances = {
          library: lib,
          chart,
          candles,
          bars,
          line,
          area,
          sma20,
          sma50,
          ema,
          upper,
          middle,
          lower,
          volume,
          rsi,
          comparePrimary,
          compareSecondary,
          ruler,
        };
        instances.current = i;
        theme(i);
        chart.timeScale().subscribeVisibleLogicalRangeChange((value) => {
          if (value) range.current = value;
        });
        const before = range.current;
        update(
          i,
          current.current.data,
          current.current.preferences,
          current.current.comparison,
          before === null,
        );
        if (before) chart.timeScale().setVisibleLogicalRange(before);
        chart.subscribeCrosshairMove((event) => setHover(session(event.time)));
        chart.subscribeClick((event) => {
          if (current.current.measureEnabled) {
            const bar = current.current.data.bars.find(
              (bar) => bar.time === session(event.time),
            );
            if (bar) chooseRef.current(bar);
          }
        });
        setState("ready");
        setGeneration((value) => value + 1);
      })
      .catch(() => {
        if (!cancelled) setState("failed");
      });
    return () => {
      cancelled = true;
      instances.current?.chart.remove();
      instances.current = null;
    };
  }, [
    data.instrument.currency,
    data.instrument.symbol,
    comparison?.instrument.symbol,
    preferences.showRsi,
    preferences.showVolume,
    hasComparison,
  ]);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const i = instances.current;
      if (i)
        update(
          i,
          data,
          current.current.preferences,
          current.current.comparison,
          true,
        );
    });
    return () => cancelAnimationFrame(frame);
  }, [data]);
  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const i = instances.current;
      if (i) {
        theme(i);
        update(i, data, preferences, comparison, false);
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [preferences, comparison, resolvedTheme, data, generation]);
  useEffect(() => {
    const i = instances.current;
    if (!i) return;
    const scale = i.chart.timeScale();
    const visible = scale.getVisibleLogicalRange();
    if (command.action === "fit") {
      for (const pane of i.chart.panes())
        pane.priceScale("right").applyOptions({ autoScale: true });
      scale.fitContent();
    } else if (command.action === "latest") scale.scrollToPosition(3, false);
    else if (visible) {
      const inset =
        (visible.to - visible.from) * 0.18 * (command.action === "in" ? 1 : -1);
      if (visible.to - visible.from > 5 || command.action === "out")
        scale.setVisibleLogicalRange({
          from: visible.from + inset,
          to: visible.to - inset,
        });
    }
  }, [command]);
  useEffect(() => {
    const i = instances.current;
    if (!i) return;
    const series = priceSeries(i, preferences.chartType),
      base = data.bars[0]?.close ?? 1;
    const drawn: IPriceLine[] = levels.map((level) =>
      series.createPriceLine({
        price: chartValue(level.price, base, preferences.scaleMode),
        color: token("--chart-level"),
        lineWidth: 1,
        lineStyle: i.library.LineStyle.Dashed,
        axisLabelVisible: true,
        title: `Level ${data.instrument.currency} ${level.price.toFixed(2)} (raw)`,
      }),
    );
    return () => {
      if (instances.current === i)
        for (const line of drawn) series.removePriceLine(line);
    };
  }, [
    levels,
    preferences.chartType,
    preferences.scaleMode,
    data,
    resolvedTheme,
    generation,
  ]);
  useEffect(() => {
    const i = instances.current;
    if (!i) return;
    const anchors =
      measurement.kind === "complete"
        ? [measurement.start, measurement.end].sort((a, b) =>
            a.time.localeCompare(b.time),
          )
        : [];
    i.ruler.setData(
      anchors.map((bar) => ({
        time: bar.time,
        value: chartValue(
          bar.close,
          data.bars[0]?.close ?? 1,
          preferences.scaleMode,
        ),
      })),
    );
  }, [measurement, preferences.scaleMode, data, generation]);
  const measuredSessions =
    measurement.kind === "complete"
      ? Math.abs(
          data.bars.findIndex((bar) => bar.time === measurement.end.time) -
            data.bars.findIndex((bar) => bar.time === measurement.start.time),
        )
      : 0;
  const fmt = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return (
    <div
      className={`market-chart ${measureEnabled ? "is-measuring" : ""}`}
      role="group"
      tabIndex={0}
      aria-label={`${data.instrument.symbol} daily ${preferences.chartType === "candles" ? "candlestick" : preferences.chartType} chart`}
      aria-describedby="market-chart-summary"
      aria-keyshortcuts="ArrowLeft ArrowRight Enter Escape"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setMeasurement({ kind: "empty" });
          return;
        }
        if (event.key === "Enter" && measureEnabled && selected) {
          event.preventDefault();
          choose(selected);
        }
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault();
          const position = selected
            ? data.bars.findIndex((bar) => bar.time === selected.time)
            : data.bars.length - 1;
          const bar =
            data.bars[
              Math.max(
                0,
                Math.min(
                  data.bars.length - 1,
                  position + (event.key === "ArrowLeft" ? -1 : 1),
                ),
              )
            ];
          if (bar) {
            setHover(bar.time);
            const i = instances.current;
            if (i)
              i.chart.setCrosshairPosition(
                chartValue(
                  bar.close,
                  data.bars[0]?.close ?? 1,
                  preferences.scaleMode,
                ),
                bar.time,
                priceSeries(i, preferences.chartType),
              );
          }
        }
      }}
    >
      <div
        className="chart-host"
        ref={host}
        data-testid="price-chart"
        data-chart-state={state}
      />
      {selected && (
        <div className="chart-legend" aria-label="Chart observation">
          <span>{selected.time}</span>
          {[
            ["O", selected.open],
            ["H", selected.high],
            ["L", selected.low],
            ["C", selected.close],
          ].map(([name, value]) => (
            <span key={name}>
              {name}{" "}
              <b>{typeof value === "number" ? fmt.format(value) : value}</b>
            </span>
          ))}
          <span>
            Vol{" "}
            <b>
              {new Intl.NumberFormat("en-US", {
                notation: "compact",
                maximumFractionDigits: 2,
              }).format(selected.volume)}
            </b>
          </span>
          <span className="legend-unit">
            {data.instrument.currency} · daily
          </span>
        </div>
      )}
      <div className="chart-study-legend">
        <span>
          Price ·{" "}
          {preferences.scaleMode === "log"
            ? "Log"
            : preferences.scaleMode === "percent"
              ? `% from ${data.bars[0]?.time}`
              : preferences.scaleMode === "indexed"
                ? `100 at ${data.bars[0]?.time}`
                : data.instrument.currency}
        </span>
        {preferences.showSma20 && <span className="study-sma20">SMA 20</span>}
        {preferences.showSma50 && <span className="study-sma50">SMA 50</span>}
        {preferences.emaEnabled && (
          <span className="study-ema">EMA {preferences.emaPeriod}</span>
        )}
        {preferences.bollingerEnabled && (
          <span>
            BB {preferences.bollingerPeriod} · {preferences.bollingerDeviation}σ
          </span>
        )}
      </div>
      {measureEnabled && (
        <div className="measurement-readout" role="status">
          {measurement.kind === "empty"
            ? "Measure closes · select two sessions. Arrow keys + Enter also work."
            : measurement.kind === "start"
              ? `Start ${measurement.start.time} · select the end session`
              : `${measurement.start.time} → ${measurement.end.time} · ${measuredSessions} ${measuredSessions === 1 ? "session" : "sessions"} · Δ ${fmt.format(measurement.end.close - measurement.start.close)} ${data.instrument.currency} (${fmt.format((measurement.end.close / measurement.start.close - 1) * 100)}%)`}
        </div>
      )}
      {state === "failed" && (
        <p className="chart-failure" role="status">
          Interactive chart unavailable. Exact session values remain available
          in the data table.
        </p>
      )}
      {state === "loading" && (
        <span className="sr-only" role="status">
          Loading chart
        </span>
      )}
    </div>
  );
}
