import { useMemo } from "react";
import { ResearchLineChart } from "./research-line-chart";
import { forecastSeries, type ReferenceId } from "./research-series";
import { formatSessionDate, formatUsd } from "./research-formatters";
import type { ResearchEvaluation, ResearchForecast } from "./research-schemas";

export function ResearchForecastChart({
  forecast,
  models,
  focusModel = "historical_log_mean",
  compact = false,
}: {
  forecast: ResearchForecast;
  models: ResearchEvaluation["models"];
  focusModel?: ReferenceId;
  compact?: boolean;
}): React.JSX.Element {
  const points = useMemo(
    () => forecastSeries(forecast, focusModel),
    [forecast, focusModel],
  );
  function modelLabel(id: string): string {
    const label = models.find((m) => m.id === id)?.label ?? id;
    return id === "historical_log_mean"
      ? `${label} · geometric drift path`
      : label;
  }
  return (
    <div className="min-w-0">
      <ResearchLineChart
        points={points}
        compact={compact}
        title="Dataset history and forecast paths"
        focusLabel={modelLabel(focusModel)}
      />
      <details className="border-t border-border-subtle px-4 py-3">
        <summary className="w-fit cursor-pointer text-xs font-medium text-accent focus-visible:ring-2 focus-visible:ring-focus">
          Show exact chart observations
        </summary>
        <div
          role="region"
          aria-label="Exact chart observations"
          tabIndex={0}
          className="mt-3 max-w-full overflow-x-auto focus-visible:ring-2 focus-visible:ring-focus"
        >
          <table className="w-full min-w-[520px] text-left text-xs">
            <caption className="sr-only">
              Dataset history and forecast prices in USD per initial share
            </caption>
            <thead>
              <tr>
                {["Series", "Session", "USD per initial share"].map((h) => (
                  <th key={h} className="px-3 py-2" scope="col">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {forecast.history.map((p) => (
                <tr key={`history-${p.time}`}>
                  <th scope="row" className="px-3 py-2 font-medium">
                    Dataset history
                  </th>
                  <td className="px-3 py-2">{formatSessionDate(p.time)}</td>
                  <td className="px-3 py-2 font-mono">{formatUsd(p.value)}</td>
                </tr>
              ))}
              {forecast.models.flatMap((m) =>
                m.points.slice(1).map((p) => (
                  <tr key={`${m.model_id}-${p.time}`}>
                    <th scope="row" className="px-3 py-2 font-medium">
                      {modelLabel(m.model_id)}
                    </th>
                    <td className="px-3 py-2">{formatSessionDate(p.time)}</td>
                    <td className="px-3 py-2 font-mono">
                      {formatUsd(p.value)}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
