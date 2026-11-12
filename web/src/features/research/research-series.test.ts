import { describe, expect, it } from "vitest";
import { researchRunFixture } from "./research-test-fixtures";
import {
  evaluationSeries,
  forecastSeries,
  lineSegments,
} from "./research-series";
import { ResearchRunSchema } from "./research-schemas";

const run = researchRunFixture({
  id: "11111111-1111-4111-8111-111111111111",
  name: "Synthetic check",
});

describe("research chart data", () => {
  it("rejects cross-reference rows with different information cutoffs", () => {
    const altered = structuredClone(run);
    const row = altered.result.evaluation_rows.find(
      (item) => item.model_id === "last_close",
    );
    if (!row) throw new Error("Missing fixture row");
    row.information_cutoff = new Date(
      Date.parse(row.information_cutoff) - 1000,
    ).toISOString();
    expect(ResearchRunSchema.safeParse(altered).success).toBe(false);
  });
  it("does not fabricate future observations or a historical fitted path", () => {
    const series = forecastSeries(run.result.forecast, "historical_log_mean");
    expect(series[0]?.selected).toBeNull();
    expect(series.at(-1)).toMatchObject({
      actual: null,
      selected: 101,
      baseline: 100,
      period: "forecast",
    });
    expect(
      series.find((p) => p.time === run.result.forecast.origin),
    ).toMatchObject({ actual: 100, selected: 100, baseline: 100 });
  });

  it("derives signed errors from the exact saved target and aligns the benchmark", () => {
    const points = evaluationSeries(run, "historical_log_mean", true);
    const rows = run.result.evaluation_rows.filter(
      (r) => r.model_id === "historical_log_mean",
    );
    expect(points).toHaveLength(rows.length);
    for (const row of rows) {
      const p = points.find(
        (p) => p.time === row.target && p.period === row.partition,
      );
      expect(p).toMatchObject({
        actual: 0,
        selected: row.predicted - row.actual,
        origin: row.origin,
        cutoff: row.information_cutoff,
      });
    }
  });

  it("never joins a line across missing values", () => {
    const point = forecastSeries(run.result.forecast, "last_close")[0];
    if (!point) throw new Error("Missing fixture point");
    const points = [
      { ...point, actual: 1 },
      { ...point, actual: null },
      { ...point, actual: 3 },
    ];
    expect(
      lineSegments(
        points,
        "actual",
        (i) => i,
        (v) => v,
      ),
    ).toEqual(["0,1", "2,3"]);
  });
});
