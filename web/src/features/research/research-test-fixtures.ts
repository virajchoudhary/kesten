import type {
  ResearchExportResponse,
  ResearchHistoryItem,
  ResearchDataset,
  ResearchRun,
} from "./research-schemas";

const HASH = "a".repeat(64);
const MODEL_IDS: ReadonlyArray<ResearchRun["result"]["models"][number]["id"]> = [
  "last_close",
  "historical_log_mean",
];
const PARTITIONS: ReadonlyArray<ResearchRun["result"]["evaluation"][number]["partition"]> = [
  "validation",
  "test",
];
const DIRECTION_CONFUSION: ResearchRun["result"]["evaluation"][number]["direction_confusion"] = [
  [0, 1, 0],
  [0, 0, 0],
  [0, 0, 0],
];

export function researchDatasetFixture(): ResearchDataset {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    name: "Synthetic pipeline fixture",
    instrument_id: "xnas-aapl",
    data_kind: "synthetic_fixture",
    version: "b".repeat(64),
    source_id: "synthetic-fixture-v1",
    license_reference: "Synthetic data generated for pipeline checks",
    availability_evidence: "Deterministic local synthetic fixture",
    adjustment_basis: "raw_with_causal_splits",
    calendar: "XNYS",
    observation_count: 160,
    first_session: "2025-01-02",
    last_session: "2026-10-02",
    created_at: "2026-11-05T10:00:00Z",
  };
}

export function researchRunFixture(options: {
  id: string;
  name: string;
}): ResearchRun {
  const summaries = MODEL_IDS.flatMap((modelId, index) =>
    PARTITIONS.map((partition) => ({
      model_id: modelId,
      partition,
      n: 1,
      mae: 1 + index,
      rmse: 1 + index,
      return_mae: 0.01 + index * 0.001,
      return_rmse: 0.01 + index * 0.001,
      directional_accuracy: 1,
      direction_confusion: DIRECTION_CONFUSION,
      mae_difference_vs_last_close: index,
    })),
  );
  const evaluationRows = MODEL_IDS.flatMap((modelId) =>
    PARTITIONS.map((partition) => ({
      model_id: modelId,
      partition,
      origin: "2025-09-01",
      target: "2025-09-02",
      information_cutoff: "2025-09-02T20:00:00Z",
      origin_value: 100,
      predicted: 101,
      actual: 102,
      input_sha256: HASH,
    })),
  );

  return {
    id: options.id,
    dataset_id: researchDatasetFixture().id,
    dataset_version: researchDatasetFixture().version,
    name: options.name,
    data_kind: "synthetic_fixture",
    instrument_id: "xnas-aapl",
    horizon_sessions: 1,
    status: "succeeded",
    result: {
      schema_version: 1,
      engine_version: "baseline-v1",
      dataset_version: researchDatasetFixture().version,
      data_kind: "synthetic_fixture",
      empirical_performance_established: false,
      evidence_kind: "synthetic_pipeline_check",
      target: {
        name: "split_neutral_close",
        horizon_sessions: 1,
        units: "USD per initial share; dividends excluded",
        return_convention: "simple price return",
      },
      protocol: {
        id: "expanding-60-20-20-v1",
        train_start: "2025-01-02",
        train_end: "2025-08-29",
        validation_start: "2025-09-01",
        validation_end: "2025-10-31",
        test_start: "2025-11-03",
        test_end: "2026-01-30",
        training_policy: "Expanding prefix through each forecast origin",
        configuration_trials: 1,
        directional_policy: "Negative, zero, and positive simple returns",
        issue_lag_minutes: 60,
        protocol_sha256: HASH,
      },
      models: [
        { id: MODEL_IDS[0], label: "Last close", version: "1" },
        { id: MODEL_IDS[1], label: "Historical log mean", version: "1" },
      ],
      evaluation: summaries,
      evaluation_rows: evaluationRows,
      forecast: {
        origin: "2026-10-02",
        information_cutoff: "2026-10-02T20:00:00Z",
        history: [
          { time: "2026-10-01", value: 99 },
          { time: "2026-10-02", value: 100 },
        ],
        models: [
          {
            model_id: MODEL_IDS[0],
            points: [
              { time: "2026-10-02", value: 100 },
              { time: "2026-10-05", value: 100 },
            ],
          },
          {
            model_id: MODEL_IDS[1],
            points: [
              { time: "2026-10-02", value: 100 },
              { time: "2026-10-05", value: 101 },
            ],
          },
        ],
      },
      limitations: ["Synthetic data is a pipeline check and does not establish forecasting performance."],
    },
    error_code: null,
    runtime: {
      python: "3.12.5",
      engine_source_sha256: HASH,
      dependency_lock_sha256: HASH,
      dependencies: { exchange_calendars: "4.11.1" },
      random_seed: null,
      deterministic: true,
    },
    created_at: "2026-11-05T10:00:00Z",
    started_at: "2026-11-05T10:00:00Z",
    completed_at: "2026-11-05T10:00:01Z",
    attempts: 1,
  };
}

export function researchHistoryItemFixture(
  overrides: Partial<ResearchHistoryItem> = {},
): ResearchHistoryItem {
  const dataset = researchDatasetFixture();
  return {
    id: "22222222-2222-4222-8222-222222222222",
    dataset_id: dataset.id,
    dataset_version: dataset.version,
    name: "Synthetic pipeline fixture",
    data_kind: "synthetic_fixture",
    instrument_id: dataset.instrument_id,
    horizon_sessions: 1,
    created_at: "2026-11-05T10:00:00Z",
    completed_at: "2026-11-05T10:00:01Z",
    status: "succeeded",
    ...overrides,
  };
}

export function researchExportFixture(
  run = researchRunFixture({
    id: "22222222-2222-4222-8222-222222222222",
    name: "Synthetic pipeline fixture",
  }),
  dataset = researchDatasetFixture(),
): ResearchExportResponse {
  return {
    format: "cadrisyn-research-v1",
    disclosure: "Synthetic pipeline check. Not empirical market evidence.",
    dataset,
    run,
    result_sha256: HASH,
  };
}
