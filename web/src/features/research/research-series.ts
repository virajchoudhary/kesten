import type { ResearchForecast, ResearchRun } from "./research-schemas";
import { researchRowIdentity } from "./research-row-identity";

export type ReferenceId = ResearchRun["result"]["models"][number]["id"];
export type ResearchPoint = {
  time: string;
  actual: number | null;
  selected: number | null;
  baseline: number | null;
  period: "history" | "forecast" | "validation" | "test";
  origin: string | null;
  cutoff: string | null;
};

export function forecastSeries(
  forecast: ResearchForecast,
  focus: ReferenceId,
): ResearchPoint[] {
  const history = new Map(forecast.history.map((p) => [p.time, p.value]));
  const selected = new Map(
    forecast.models
      .find((m) => m.model_id === focus)
      ?.points.map((p) => [p.time, p.value]),
  );
  const baseline = new Map(
    forecast.models
      .find((m) => m.model_id === "last_close")
      ?.points.map((p) => [p.time, p.value]),
  );
  const dates = [
    ...new Set([...history.keys(), ...selected.keys(), ...baseline.keys()]),
  ].sort();
  return dates.map((time) => ({
    time,
    actual: history.get(time) ?? null,
    selected: selected.get(time) ?? null,
    baseline: baseline.get(time) ?? null,
    period: time > forecast.origin ? "forecast" : "history",
    origin: forecast.origin,
    cutoff: forecast.information_cutoff,
  }));
}

export function evaluationSeries(
  run: ResearchRun,
  focus: ReferenceId,
  errors: boolean,
): ResearchPoint[] {
  const key = researchRowIdentity;
  const baseline = new Map(
    run.result.evaluation_rows
      .filter((r) => r.model_id === "last_close")
      .map((r) => [key(r), r.predicted]),
  );
  return run.result.evaluation_rows
    .filter((r) => r.model_id === focus)
    .map((row): ResearchPoint => {
      const reference = baseline.get(key(row));
      return {
        time: row.target,
        actual: errors ? 0 : row.actual,
        selected: errors ? row.predicted - row.actual : row.predicted,
        baseline:
          reference === undefined
            ? null
            : errors
              ? reference - row.actual
              : reference,
        period: row.partition,
        origin: row.origin,
        cutoff: row.information_cutoff,
      };
    })
    .sort((a, b) => a.time.localeCompare(b.time));
}

export function lineSegments(
  points: readonly ResearchPoint[],
  field: "actual" | "selected" | "baseline",
  x: (index: number) => number,
  y: (value: number) => number,
): string[] {
  const segments: string[] = [];
  let current: string[] = [];
  for (const [index, point] of points.entries()) {
    const value = point[field];
    if (value === null) {
      if (current.length) segments.push(current.join(" "));
      current = [];
    } else current.push(`${x(index)},${y(value)}`);
  }
  if (current.length) segments.push(current.join(" "));
  return segments;
}
