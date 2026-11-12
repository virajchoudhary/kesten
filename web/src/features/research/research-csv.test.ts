import { afterEach, describe, expect, it, vi } from "vitest";

import { researchRunFixture } from "./research-test-fixtures";
import {
  downloadResearchEvaluationCsv,
  HISTORICAL_CSV_EXPORT_DISABLED_REASON,
  researchEvaluationCsv,
} from "./research-csv";

afterEach(() => {
  vi.unstubAllGlobals();
});

function parseCsv(source: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < source.length; index += 1) {
    const character = source[index] ?? "";
    if (quoted) {
      if (character === '"' && source[index + 1] === '"') {
        value += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        value += character;
      }
    } else if (character === '"') {
      quoted = true;
    } else if (character === ",") {
      row.push(value);
      value = "";
    } else if (character === "\r" && source[index + 1] === "\n") {
      row.push(value);
      rows.push(row);
      row = [];
      value = "";
      index += 1;
    } else {
      value += character;
    }
  }
  return rows;
}

function csvRecord(csv: string, rowIndex: number): Record<string, string> {
  const [headers, ...rows] = parseCsv(csv);
  const values = rows[rowIndex];
  if (!headers || !values) {
    throw new Error("The requested CSV row is missing.");
  }
  return Object.fromEntries(
    headers.map((header, index) => [header, values[index] ?? ""]),
  );
}

function historicalRun() {
  const run = researchRunFixture({
    id: "55555555-5555-4555-8555-555555555555",
    name: "Historical evaluation",
  });
  run.data_kind = "historical";
  run.result.data_kind = "historical";
  run.result.evidence_kind = "historical_walk_forward";
  return run;
}

describe("research evaluation CSV", () => {
  it("exports exact run, dataset, protocol, model, and benchmark row identities", () => {
    const run = researchRunFixture({
      id: "11111111-1111-4111-8111-111111111111",
      name: "Synthetic evaluation",
    });
    run.result.evaluation_rows = run.result.evaluation_rows.map((row) =>
      row.model_id === "last_close" && row.partition === "test"
        ? { ...row, predicted: 103 }
        : row,
    );
    const selectedRow = run.result.evaluation_rows.find(
      (row) =>
        row.model_id === "historical_log_mean" && row.partition === "test",
    );
    const baselineRow = run.result.evaluation_rows.find(
      (row) => row.model_id === "last_close" && row.partition === "test",
    );
    if (!selectedRow || !baselineRow) {
      throw new Error("Fixture must include selected and benchmark rows.");
    }

    const csv = researchEvaluationCsv({
      run,
      focusModel: "historical_log_mean",
      view: "Errors",
      partition: "test",
    });
    const rows = parseCsv(csv);
    const headers = rows[0];
    const record = csvRecord(csv, 0);
    if (!headers) throw new Error("CSV header is missing.");

    expect(rows).toHaveLength(2);
    expect(headers).toContain("selected_evaluation_row_json");
    expect(headers).toContain("baseline_evaluation_row_json");
    expect(record).toMatchObject({
      format: "cadrisyn-research-view-v1",
      partition_filter: "test",
      run_id: run.id,
      dataset_id: run.dataset_id,
      dataset_version: run.dataset_version,
      data_kind: "synthetic_fixture",
      empirical_performance_established: "false",
      evidence_kind:
        "synthetic_pipeline_check. Synthetic pipeline check only. No empirical forecasting performance established.",
      engine_source_sha256: run.runtime.engine_source_sha256,
      dependency_lock_sha256: run.runtime.dependency_lock_sha256,
      protocol_id: run.result.protocol.id,
      protocol_sha256: run.result.protocol.protocol_sha256,
      model_id: "historical_log_mean",
      model_version: "1",
      baseline_model_id: "last_close",
      baseline_model_version: "1",
      target_name: "split_neutral_close",
      horizon_sessions: "1",
      units:
        "USD per initial share; dividends excluded; forecast error is predicted minus actual",
      target_date: selectedRow.target,
      origin: selectedRow.origin,
      information_cutoff: selectedRow.information_cutoff,
      origin_value: String(selectedRow.origin_value),
      input_sha256: selectedRow.input_sha256,
      period: "test",
      actual: String(selectedRow.actual),
      chart_actual: "0",
      selected: "-1",
      baseline: "1",
      error: "-1",
      baseline_error: "1",
    });
    const selectedRaw: unknown = JSON.parse(
      record.selected_evaluation_row_json,
    );
    const baselineRaw: unknown = JSON.parse(
      record.baseline_evaluation_row_json,
    );
    expect(selectedRaw).toEqual(selectedRow);
    expect(baselineRaw).toEqual(baselineRow);
  });

  it.each(["=2+2", "+SUM(1,1)", "-2+3", "@SUM(A1:A2)", " \t=2+2"])(
    "prefixes spreadsheet formula text in a string field: %s",
    (name) => {
      const run = researchRunFixture({
        id: "22222222-2222-4222-8222-222222222222",
        name,
      });
      const csv = researchEvaluationCsv({
        run,
        focusModel: "historical_log_mean",
        view: "Walk-forward",
        partition: "all",
      });

      expect(csvRecord(csv, 0).run_name).toBe(`'${name}`);
    },
  );

  it("quotes formula names containing commas and embedded quotes", () => {
    const name = '=HYPERLINK("https://example.test","open,me")';
    const run = researchRunFixture({
      id: "33333333-3333-4333-8333-333333333333",
      name,
    });
    const csv = researchEvaluationCsv({
      run,
      focusModel: "historical_log_mean",
      view: "Errors",
      partition: "all",
    });

    expect(csvRecord(csv, 0).run_name).toBe(`'${name}`);
    expect(csvRecord(csv, 0)).toMatchObject({
      units:
        "USD per initial share; dividends excluded; forecast error is predicted minus actual",
      view: "Errors",
      selected: "-1",
      baseline: "-1",
    });
  });

  it("rejects historical export before generating a browser download", () => {
    const run = historicalRun();
    const options = {
      run,
      focusModel: "historical_log_mean",
      view: "Walk-forward",
      partition: "all",
    } satisfies Parameters<typeof researchEvaluationCsv>[0];
    expect(() => researchEvaluationCsv(options)).toThrow(
      HISTORICAL_CSV_EXPORT_DISABLED_REASON,
    );

    const NativeURL = URL;
    const createObjectURL = vi.fn(() => "blob:must-not-exist");
    class TestURL extends NativeURL {}
    Object.defineProperty(TestURL, "createObjectURL", {
      configurable: true,
      value: createObjectURL,
    });
    vi.stubGlobal("URL", TestURL);

    expect(() => downloadResearchEvaluationCsv(options)).toThrow(
      HISTORICAL_CSV_EXPORT_DISABLED_REASON,
    );
    expect(createObjectURL).not.toHaveBeenCalled();
  });
});
