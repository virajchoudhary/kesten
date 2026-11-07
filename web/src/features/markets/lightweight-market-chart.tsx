"use client";

import { useEffect, useRef, useState } from "react";
import { useTheme } from "next-themes";
import type { IChartApi, ISeriesApi } from "lightweight-charts";

import {
  toCandlestickData,
  toLineData,
  toVolumeData,
} from "@/features/markets/chart-series";
import type { MarketResponse } from "@/lib/api/schemas";

type MarketChartInstances = {
  library: typeof import("lightweight-charts");
  chart: IChartApi;
  candles: ISeriesApi<"Candlestick">;
  volume: ISeriesApi<"Histogram">;
  sma20: ISeriesApi<"Line">;
  sma50: ISeriesApi<"Line">;
  rsi: ISeriesApi<"Line"> | null;
  rsi30: ISeriesApi<"Line"> | null;
  rsi70: ISeriesApi<"Line"> | null;
};

type VisibleLogicalRange = NonNullable<
  ReturnType<ReturnType<IChartApi["timeScale"]>["getVisibleLogicalRange"]>
>;

type ThemeTokens = {
  surface: string;
  text: string;
  secondary: string;
  border: string;
  grid: string;
  crosshair: string;
  up: string;
  down: string;
  sma20: string;
  sma50: string;
  rsi: string;
  volumeUp: string;
  volumeDown: string;
};

function readToken(name: string): string {
  return window
    .getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

function readThemeTokens(): ThemeTokens {
  return {
    surface: readToken("--surface"),
    text: readToken("--text"),
    secondary: readToken("--text-secondary"),
    border: readToken("--border-subtle"),
    grid: readToken("--chart-grid"),
    crosshair: readToken("--chart-crosshair"),
    up: readToken("--chart-up"),
    down: readToken("--chart-down"),
    sma20: readToken("--chart-sma20"),
    sma50: readToken("--chart-sma50"),
    rsi: readToken("--chart-rsi"),
    volumeUp: readToken("--chart-volume-up"),
    volumeDown: readToken("--chart-volume-down"),
  };
}

function formatPrice(currency: string): (value: number) => string {
  const formatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });
  return (value) => formatter.format(value);
}

function updateChartData(
  instances: MarketChartInstances,
  data: MarketResponse,
  fitContent: boolean,
): void {
  const previousRange = fitContent
    ? null
    : instances.chart.timeScale().getVisibleLogicalRange();
  const tokens = readThemeTokens();
  instances.candles.setData(toCandlestickData(data.bars));
  instances.volume.setData(
    toVolumeData(data.bars, { up: tokens.volumeUp, down: tokens.volumeDown }),
  );
  instances.sma20.setData(toLineData(data.indicators.sma20));
  instances.sma50.setData(toLineData(data.indicators.sma50));

  if (
    instances.rsi !== null &&
    instances.rsi30 !== null &&
    instances.rsi70 !== null
  ) {
    instances.rsi.setData(toLineData(data.indicators.rsi14));
    const thresholds = data.bars.map(({ time }) => ({ time, value: 30 }));
    const upperThresholds = data.bars.map(({ time }) => ({ time, value: 70 }));
    instances.rsi30.setData(thresholds);
    instances.rsi70.setData(upperThresholds);
  }

  if (fitContent) {
    instances.chart.timeScale().fitContent();
  } else if (previousRange !== null) {
    instances.chart.timeScale().setVisibleLogicalRange(previousRange);
  }
}

function updateChartTheme(
  instances: MarketChartInstances,
  data: MarketResponse,
): void {
  const tokens = readThemeTokens();
  instances.chart.applyOptions({
    layout: {
      background: {
        type: instances.library.ColorType.Solid,
        color: tokens.surface,
      },
      textColor: tokens.text,
      fontFamily:
        '"Inter Variable", Inter, ui-sans-serif, system-ui, sans-serif',
      fontSize: 12,
      attributionLogo: true,
    },
    grid: {
      vertLines: { color: tokens.grid },
      horzLines: { color: tokens.grid },
    },
    crosshair: {
      vertLine: {
        color: tokens.crosshair,
        labelBackgroundColor: tokens.secondary,
      },
      horzLine: {
        color: tokens.crosshair,
        labelBackgroundColor: tokens.secondary,
      },
    },
    rightPriceScale: { borderColor: tokens.border },
    timeScale: { borderColor: tokens.border },
    localization: {
      locale: "en-US",
    },
  });
  instances.candles.applyOptions({
    upColor: tokens.up,
    downColor: tokens.down,
    borderUpColor: tokens.up,
    borderDownColor: tokens.down,
    wickUpColor: tokens.up,
    wickDownColor: tokens.down,
  });
  instances.sma20.applyOptions({ color: tokens.sma20 });
  instances.sma50.applyOptions({ color: tokens.sma50 });
  instances.rsi?.applyOptions({ color: tokens.rsi });
  updateChartData(instances, data, false);
}

export function LightweightMarketChart({
  data,
  showSma20,
  showSma50,
  showRsi,
  showGrid = true,
  resetToken = 0,
}: {
  data: MarketResponse;
  showSma20: boolean;
  showSma50: boolean;
  showRsi: boolean;
  showGrid?: boolean;
  resetToken?: number;
}): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const instancesRef = useRef<MarketChartInstances | null>(null);
  const dataRef = useRef(data);
  const visibilityRef = useRef({ showSma20, showSma50 });
  const visibleRangeRef = useRef<VisibleLogicalRange | null>(null);
  const { resolvedTheme } = useTheme();
  const [chartState, setChartState] = useState<"loading" | "ready" | "failed">(
    "loading",
  );
  const [hoveredBar, setHoveredBar] = useState<
    MarketResponse["bars"][number] | null
  >(null);
  const activeBar =
    hoveredBar && data.bars.includes(hoveredBar)
      ? hoveredBar
      : data.bars.at(-1);
  const legendPrice = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  useEffect(() => {
    dataRef.current = data;
    visibilityRef.current = { showSma20, showSma50 };
  }, [data, showSma20, showSma50]);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }

    let cancelled = false;
    setChartState("loading");

    void import("lightweight-charts")
      .then((library) => {
        if (cancelled) {
          return;
        }

        const tokens = readThemeTokens();
        const chart = library.createChart(container, {
          autoSize: true,
          layout: {
            background: {
              type: library.ColorType.Solid,
              color: tokens.surface,
            },
            textColor: tokens.text,
            fontFamily:
              '"Inter Variable", Inter, ui-sans-serif, system-ui, sans-serif',
            fontSize: 12,
            attributionLogo: true,
          },
          grid: {
            vertLines: { color: tokens.grid },
            horzLines: { color: tokens.grid },
          },
          crosshair: {
            mode: library.CrosshairMode.Normal,
            vertLine: {
              color: tokens.crosshair,
              width: 1,
              style: library.LineStyle.Dashed,
              labelBackgroundColor: tokens.secondary,
            },
            horzLine: {
              color: tokens.crosshair,
              width: 1,
              style: library.LineStyle.Dashed,
              labelBackgroundColor: tokens.secondary,
            },
          },
          rightPriceScale: {
            borderColor: tokens.border,
            scaleMargins: { top: 0.12, bottom: 0.08 },
          },
          timeScale: {
            borderColor: tokens.border,
            timeVisible: false,
            secondsVisible: false,
            rightOffset: 4,
          },
          localization: {
            locale: "en-US",
          },
        });
        container.querySelector("table")?.setAttribute("role", "presentation");

        const candles = chart.addSeries(
          library.CandlestickSeries,
          {
            upColor: tokens.up,
            downColor: tokens.down,
            borderUpColor: tokens.up,
            borderDownColor: tokens.down,
            wickUpColor: tokens.up,
            wickDownColor: tokens.down,
            priceLineVisible: false,
            priceFormat: {
              type: "custom",
              minMove: 0.01,
              formatter: formatPrice(dataRef.current.instrument.currency),
            },
          },
          0,
        );
        const sma20 = chart.addSeries(
          library.LineSeries,
          {
            color: tokens.sma20,
            lineWidth: 1,
            title: "SMA 20",
            visible: visibilityRef.current.showSma20,
            lastValueVisible: false,
            priceLineVisible: false,
            crosshairMarkerVisible: false,
          },
          0,
        );
        const sma50 = chart.addSeries(
          library.LineSeries,
          {
            color: tokens.sma50,
            lineWidth: 1,
            title: "SMA 50",
            visible: visibilityRef.current.showSma50,
            lastValueVisible: false,
            priceLineVisible: false,
            crosshairMarkerVisible: false,
          },
          0,
        );
        const volume = chart.addSeries(
          library.HistogramSeries,
          {
            priceScaleId: "volume",
            priceFormat: { type: "volume" },
            priceLineVisible: false,
            lastValueVisible: false,
          },
          1,
        );
        chart.priceScale("volume", 1).applyOptions({
          borderVisible: false,
          scaleMargins: { top: 0.12, bottom: 0 },
        });

        const rsi = !showRsi
          ? null
          : chart.addSeries(
              library.LineSeries,
              {
                color: tokens.rsi,
                lineWidth: 1,
                title: "RSI 14",
                priceLineVisible: false,
                lastValueVisible: true,
                crosshairMarkerVisible: true,
                priceFormat: { type: "price", precision: 1, minMove: 0.1 },
              },
              2,
            );
        const rsi30 = !showRsi
          ? null
          : chart.addSeries(
              library.LineSeries,
              {
                color: tokens.border,
                lineWidth: 1,
                lineStyle: library.LineStyle.Dashed,
                title: "",
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
              },
              2,
            );
        const rsi70 = !showRsi
          ? null
          : chart.addSeries(
              library.LineSeries,
              {
                color: tokens.border,
                lineWidth: 1,
                lineStyle: library.LineStyle.Dashed,
                title: "",
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
              },
              2,
            );

        const [pricePane, volumePane, rsiPane] = chart.panes();
        pricePane?.setStretchFactor(showRsi ? 0.72 : 0.88);
        volumePane?.setStretchFactor(0.1);
        rsiPane?.setStretchFactor(0.18);

        chart.subscribeCrosshairMove((event) => {
          const point = event.seriesData.get(candles);
          if (point && "open" in point) {
            const bar = dataRef.current.bars.find(
              (item) => item.time === point.time,
            );
            setHoveredBar(bar ?? null);
          } else {
            setHoveredBar(null);
          }
        });

        const instances: MarketChartInstances = {
          library,
          chart,
          candles,
          volume,
          sma20,
          sma50,
          rsi,
          rsi30,
          rsi70,
        };
        instancesRef.current = instances;
        chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
          if (range !== null) {
            visibleRangeRef.current = range;
          }
        });
        const restoreRange = visibleRangeRef.current;
        updateChartData(instances, dataRef.current, restoreRange === null);
        if (restoreRange !== null) {
          chart.timeScale().setVisibleLogicalRange(restoreRange);
        }
        setChartState("ready");
      })
      .catch(() => {
        if (!cancelled) {
          setChartState("failed");
        }
      });

    return () => {
      cancelled = true;
      instancesRef.current?.chart.remove();
      instancesRef.current = null;
    };
  }, [data.instrument.currency, showRsi]);

  useEffect(() => {
    if (instancesRef.current !== null) {
      updateChartData(instancesRef.current, data, true);
    }
  }, [data]);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      if (instancesRef.current !== null) {
        updateChartTheme(instancesRef.current, data);
      }
    });
    return () => cancelAnimationFrame(frame);
  }, [data, resolvedTheme]);

  useEffect(() => {
    instancesRef.current?.sma20.applyOptions({ visible: showSma20 });
  }, [showSma20]);

  useEffect(() => {
    instancesRef.current?.sma50.applyOptions({ visible: showSma50 });
  }, [showSma50]);

  useEffect(() => {
    instancesRef.current?.chart.applyOptions({
      grid: {
        vertLines: { visible: showGrid },
        horzLines: { visible: showGrid },
      },
    });
  }, [showGrid, chartState]);

  useEffect(() => {
    instancesRef.current?.chart.timeScale().fitContent();
  }, [resetToken]);

  return (
    <div
      aria-describedby="market-chart-summary"
      aria-label={`${data.instrument.symbol} daily candlestick chart`}
      className="market-chart relative min-w-0"
      role="group"
    >
      <div
        className="chart-host w-full min-w-0"
        data-testid="price-chart"
        ref={containerRef}
      />
      {activeBar && (
        <div className="chart-legend" aria-label="Chart observation">
          <span>{activeBar.time}</span>
          <span>
            O <b>{legendPrice.format(activeBar.open)}</b>
          </span>
          <span>
            H <b>{legendPrice.format(activeBar.high)}</b>
          </span>
          <span>
            L <b>{legendPrice.format(activeBar.low)}</b>
          </span>
          <span>
            C <b>{legendPrice.format(activeBar.close)}</b>
          </span>
          <span>
            Vol{" "}
            <b>
              {new Intl.NumberFormat("en-US", {
                notation: "compact",
                maximumFractionDigits: 2,
              }).format(activeBar.volume)}
            </b>
          </span>
        </div>
      )}
      {chartState === "loading" && (
        <span className="sr-only" role="status">
          Loading chart
        </span>
      )}
      {chartState === "failed" && (
        <div
          className="absolute inset-x-4 top-4 border border-warning/50 bg-surface px-3 py-2 text-sm text-warning"
          role="status"
        >
          Interactive chart unavailable. The session data table remains
          available.
        </div>
      )}
    </div>
  );
}
