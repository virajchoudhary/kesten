import { useId } from "react";

import {
  formatSessionDate,
  formatUsd,
} from "./research-formatters";
import type {
  ResearchEvaluation,
  ResearchForecast,
} from "./research-schemas";

const WIDTH = 960;
const HEIGHT = 360;
const PLOT: Readonly<{ left: number; right: number; top: number; bottom: number }> = {
  left: 78,
  right: 20,
  top: 18,
  bottom: 62,
};
const FORECAST_COLORS: readonly string[] = [
  "var(--forecast-series)",
  "var(--chart-sma50)",
  "var(--chart-sma20)",
  "var(--positive)",
];

type PlotPoint = {
  time: string;
  value: number;
  x: number;
  y: number;
};

function plotPoints(
  points: ResearchForecast["history"],
  timeline: readonly string[],
  minimum: number,
  maximum: number,
): PlotPoint[] {
  const plotWidth = WIDTH - PLOT.left - PLOT.right;
  const plotHeight = HEIGHT - PLOT.top - PLOT.bottom;
  const xDenominator = Math.max(timeline.length - 1, 1);
  const ySpan = maximum - minimum;

  return points.map((point) => {
    const timelineIndex = timeline.indexOf(point.time);
    return {
      ...point,
      x: PLOT.left + (timelineIndex / xDenominator) * plotWidth,
      y: PLOT.top + ((maximum - point.value) / ySpan) * plotHeight,
    };
  });
}

function formatChartXLabel(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

export function ResearchForecastChart({
  forecast,
  models,
}: {
  forecast: ResearchForecast;
  models: ResearchEvaluation["models"];
}): React.JSX.Element {
  const titleId = useId();
  const descriptionId = useId();
  const allValues = [
    ...forecast.history.map((point) => point.value),
    ...forecast.models.flatMap((model) => model.points.map((point) => point.value)),
  ];
  const rawMinimum = Math.min(...allValues);
  const rawMaximum = Math.max(...allValues);
  const spread = rawMaximum - rawMinimum;
  const padding = spread > 0 ? spread * 0.08 : Math.max(rawMaximum * 0.02, 0.01);
  const minimum = rawMinimum - padding;
  const maximum = rawMaximum + padding;
  const timeline = [...new Set([
    ...forecast.history.map((point) => point.time),
    ...forecast.models.flatMap((model) => model.points.map((point) => point.time)),
  ])].sort();
  const historyPoints = plotPoints(forecast.history, timeline, minimum, maximum);
  const targetDate = forecast.models[0]?.points.at(-1)?.time ?? forecast.origin;
  const xLabels = [
    { time: forecast.history[0]?.time ?? forecast.origin, label: formatChartXLabel(forecast.history[0]?.time ?? forecast.origin) },
    { time: forecast.origin, label: formatChartXLabel(forecast.origin) },
    { time: targetDate, label: formatChartXLabel(targetDate) },
  ];
  const yLabels = [0, 1, 2, 3].map((step) => {
    const value = maximum - ((maximum - minimum) * step) / 3;
    const y = PLOT.top + ((maximum - value) / (maximum - minimum)) * (HEIGHT - PLOT.top - PLOT.bottom);
    return { value, y };
  });

  function modelLabel(modelId: string): string {
    const label = models.find((model) => model.id === modelId)?.label ?? modelId;
    return modelId === "historical_log_mean"
      ? `${label} · geometric drift path`
      : label;
  }

  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-border-subtle px-4 py-3 text-xs">
        <span className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-0.5 w-5 bg-observed" />
          Dataset history
        </span>
        {forecast.models.map((model, index) => (
          <span className="inline-flex items-center gap-2" key={model.model_id}>
            <span
              aria-hidden="true"
              className="h-0.5 w-5"
              style={{ backgroundColor: FORECAST_COLORS[index % FORECAST_COLORS.length] }}
            />
            {modelLabel(model.model_id)}
          </span>
        ))}
      </div>

      <div className="px-3 py-3 sm:px-4">
        <svg
          aria-labelledby={`${titleId} ${descriptionId}`}
          className="block h-auto w-full"
          role="img"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        >
          <title id={titleId}>Dataset history and forecast paths</title>
          <desc id={descriptionId}>
            Split-neutral dataset history through {formatSessionDate(forecast.origin)} and model forecasts
            from that origin through {formatSessionDate(targetDate)}. Values are USD per initial share;
            dividends are excluded.
          </desc>

          {yLabels.map(({ value, y }) => (
            <g aria-hidden="true" key={value}>
              <line
                stroke="var(--chart-grid)"
                strokeWidth="1"
                x1={PLOT.left}
                x2={WIDTH - PLOT.right}
                y1={y}
                y2={y}
              />
              <text
                fill="var(--text-secondary)"
                fontSize="12"
                textAnchor="end"
                x={PLOT.left - 12}
                y={y + 4}
              >
                {formatUsd(value)}
              </text>
            </g>
          ))}

          <line
            stroke="var(--chart-crosshair)"
            strokeDasharray="4 5"
            strokeWidth="1"
            x1={historyPoints.at(-1)?.x ?? PLOT.left}
            x2={historyPoints.at(-1)?.x ?? PLOT.left}
            y1={PLOT.top}
            y2={HEIGHT - PLOT.bottom}
          />

          <polyline
            fill="none"
            points={historyPoints.map((point) => `${point.x},${point.y}`).join(" ")}
            stroke="var(--observed-series)"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2.5"
          />

          {forecast.models.map((model, index) => {
            const points = plotPoints(model.points, timeline, minimum, maximum);
            const color = FORECAST_COLORS[index % FORECAST_COLORS.length];
            return (
              <g key={model.model_id}>
                <polyline
                  fill="none"
                  points={points.map((point) => `${point.x},${point.y}`).join(" ")}
                  stroke={color}
                  strokeDasharray="7 4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2.5"
                />
                {points.slice(1).map((point) => (
                  <circle
                    cx={point.x}
                    cy={point.y}
                    fill="var(--surface)"
                    key={point.time}
                    r="4"
                    stroke={color}
                    strokeWidth="2"
                  />
                ))}
              </g>
            );
          })}

          {xLabels.map(({ time, label }, index) => {
            const x = PLOT.left + (timeline.indexOf(time) / Math.max(timeline.length - 1, 1)) * (WIDTH - PLOT.left - PLOT.right);
            const anchor = index === 0 ? "start" : index === xLabels.length - 1 ? "end" : "middle";
            return (
              <text
                fill="var(--text-secondary)"
                fontSize="12"
                key={`${time}-${index}`}
                textAnchor={anchor}
                x={x}
                y={HEIGHT - 25}
              >
                {label}
              </text>
            );
          })}

          <text
            fill="var(--text-secondary)"
            fontSize="11"
            textAnchor="middle"
            transform={`translate(18 ${HEIGHT / 2}) rotate(-90)`}
          >
            USD per initial share
          </text>
        </svg>
      </div>

      <details className="border-t border-border-subtle px-4 py-3">
        <summary className="w-fit cursor-pointer text-xs font-medium text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus">
          Show exact chart observations
        </summary>
        <div
          aria-label="Exact chart observations"
          className="mt-3 max-w-full overflow-x-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          role="region"
          tabIndex={0}
        >
          <table className="w-full min-w-[520px] border-collapse text-left text-xs">
            <caption className="sr-only">
              Dataset history and forecast prices in USD per initial share
            </caption>
            <thead className="border-b border-border-subtle text-secondary">
              <tr>
                <th className="px-3 py-2 font-medium" scope="col">Series</th>
                <th className="px-3 py-2 font-medium" scope="col">Session</th>
                <th className="px-3 py-2 text-right font-medium" scope="col">USD per initial share</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {forecast.history.map((point) => (
                <tr key={`history-${point.time}`}>
                  <th className="px-3 py-2 font-medium" scope="row">Dataset history</th>
                  <td className="px-3 py-2">{formatSessionDate(point.time)}</td>
                  <td className="px-3 py-2 text-right font-mono">{formatUsd(point.value)}</td>
                </tr>
              ))}
              {forecast.models.flatMap((model) => model.points.slice(1).map((point) => (
                <tr key={`${model.model_id}-${point.time}`}>
                  <th className="px-3 py-2 font-medium" scope="row">{modelLabel(model.model_id)}</th>
                  <td className="px-3 py-2">{formatSessionDate(point.time)}</td>
                  <td className="px-3 py-2 text-right font-mono">{formatUsd(point.value)}</td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
