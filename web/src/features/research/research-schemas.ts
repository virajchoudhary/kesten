import { z } from "zod";
import { researchRowIdentity } from "./research-row-identity";

const NonEmptyTextSchema = z.string().trim().min(1).max(2048);
const ShortTextSchema = z.string().trim().min(1).max(256);

export const ResearchRunIdSchema = z.string().uuid();
export const ResearchSha256Schema = z.string().regex(/^[a-f0-9]{64}$/u);
export const ResearchInstrumentIdSchema = z
  .string()
  .trim()
  .regex(/^[a-z0-9]+(?:-[a-z0-9]+)+$/u)
  .max(32);
export const ResearchReferenceIdSchema = z.enum([
  "last_close",
  "historical_log_mean",
]);

export const ResearchSessionDateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/u)
  .refine((value) => {
    const timestamp = Date.parse(`${value}T00:00:00Z`);
    return (
      Number.isFinite(timestamp) &&
      new Date(timestamp).toISOString().slice(0, 10) === value
    );
  }, "Enter a valid exchange session date.");

const ResearchDateTimeSchema = z.string().datetime({ offset: true });

export const ResearchDataKindSchema = z.enum([
  "synthetic_fixture",
  "historical",
]);
export const ResearchHorizonSchema = z.union([z.literal(1), z.literal(5)]);

export const ResearchDatasetSchema = z
  .strictObject({
    id: ResearchRunIdSchema,
    name: ShortTextSchema,
    instrument_id: ShortTextSchema,
    data_kind: ResearchDataKindSchema,
    version: ResearchSha256Schema,
    source_id: ShortTextSchema,
    license_reference: NonEmptyTextSchema,
    availability_evidence: NonEmptyTextSchema,
    adjustment_basis: ShortTextSchema,
    calendar: ShortTextSchema,
    observation_count: z.number().int().min(120).max(1500),
    first_session: ResearchSessionDateSchema,
    last_session: ResearchSessionDateSchema,
    created_at: ResearchDateTimeSchema,
  })
  .superRefine((dataset, context) => {
    if (dataset.first_session > dataset.last_session) {
      context.addIssue({
        code: "custom",
        message:
          "The dataset's first session must not follow its last session.",
        path: ["first_session"],
      });
    }
  });

export const ResearchDatasetListSchema = z
  .strictObject({
    items: z.array(ResearchDatasetSchema),
  })
  .superRefine((datasets, context) => {
    const identifiers = new Set<string>();
    for (const [index, dataset] of datasets.items.entries()) {
      if (identifiers.has(dataset.id)) {
        context.addIssue({
          code: "custom",
          message: "Private dataset identifiers must be unique.",
          path: ["items", index, "id"],
        });
      }
      identifiers.add(dataset.id);
    }
  });

const ResearchModelSchema = z.strictObject({
  id: ResearchReferenceIdSchema,
  label: ShortTextSchema,
  version: z.literal("1"),
});

const DirectionCountSchema = z.number().int().nonnegative();
const DirectionConfusionSchema = z.tuple([
  z.tuple([DirectionCountSchema, DirectionCountSchema, DirectionCountSchema]),
  z.tuple([DirectionCountSchema, DirectionCountSchema, DirectionCountSchema]),
  z.tuple([DirectionCountSchema, DirectionCountSchema, DirectionCountSchema]),
]);

const ResearchEvaluationSummarySchema = z
  .strictObject({
    model_id: ResearchReferenceIdSchema,
    partition: z.enum(["validation", "test"]),
    n: z.number().int().positive(),
    mae: z.number().finite().nonnegative(),
    rmse: z.number().finite().nonnegative(),
    return_mae: z.number().finite().nonnegative(),
    return_rmse: z.number().finite().nonnegative(),
    directional_accuracy: z.number().finite().min(0).max(1),
    direction_confusion: DirectionConfusionSchema,
    mae_difference_vs_last_close: z.number().finite(),
  })
  .superRefine((summary, context) => {
    const classifiedRows = summary.direction_confusion
      .flat()
      .reduce((total, count) => total + count, 0);
    if (classifiedRows !== summary.n) {
      context.addIssue({
        code: "custom",
        message: "Direction counts must account for every evaluated row.",
        path: ["direction_confusion"],
      });
    }
  });

const ResearchEvaluationRowSchema = z
  .strictObject({
    model_id: ResearchReferenceIdSchema,
    partition: z.enum(["validation", "test"]),
    origin: ResearchSessionDateSchema,
    target: ResearchSessionDateSchema,
    information_cutoff: ResearchDateTimeSchema,
    origin_value: z.number().finite().positive(),
    predicted: z.number().finite().positive(),
    actual: z.number().finite().positive(),
    input_sha256: ResearchSha256Schema,
  })
  .superRefine((row, context) => {
    if (row.target <= row.origin) {
      context.addIssue({
        code: "custom",
        message: "An evaluation target must follow its forecast origin.",
        path: ["target"],
      });
    }
  });

const ResearchForecastPointSchema = z.strictObject({
  time: ResearchSessionDateSchema,
  value: z.number().finite().positive(),
});

const ResearchForecastModelSchema = z.strictObject({
  model_id: ResearchReferenceIdSchema,
  points: z.array(ResearchForecastPointSchema).min(2).max(6),
});

const ResearchForecastSchema = z.strictObject({
  origin: ResearchSessionDateSchema,
  information_cutoff: ResearchDateTimeSchema,
  history: z.array(ResearchForecastPointSchema).min(1).max(80),
  models: z.array(ResearchForecastModelSchema).min(1).max(2),
});

const ResearchProtocolSchema = z.strictObject({
  id: z.literal("expanding-60-20-20-v1"),
  train_start: ResearchSessionDateSchema,
  train_end: ResearchSessionDateSchema,
  validation_start: ResearchSessionDateSchema,
  validation_end: ResearchSessionDateSchema,
  test_start: ResearchSessionDateSchema,
  test_end: ResearchSessionDateSchema,
  training_policy: NonEmptyTextSchema,
  configuration_trials: z.literal(1),
  directional_policy: NonEmptyTextSchema,
  issue_lag_minutes: z.literal(60),
  protocol_sha256: ResearchSha256Schema,
});

export const ResearchEvaluationSchema = z
  .strictObject({
    schema_version: z.literal(1),
    engine_version: z.literal("baseline-v1"),
    dataset_version: ResearchSha256Schema,
    data_kind: ResearchDataKindSchema,
    empirical_performance_established: z.literal(false),
    evidence_kind: z.enum([
      "synthetic_pipeline_check",
      "historical_walk_forward",
    ]),
    target: z.strictObject({
      name: z.literal("split_neutral_close"),
      horizon_sessions: ResearchHorizonSchema,
      units: z.literal("USD per initial share; dividends excluded"),
      return_convention: z.literal("simple price return"),
    }),
    protocol: ResearchProtocolSchema,
    models: z.array(ResearchModelSchema).length(2),
    evaluation: z.array(ResearchEvaluationSummarySchema).length(4),
    evaluation_rows: z.array(ResearchEvaluationRowSchema).min(1),
    forecast: ResearchForecastSchema,
    limitations: z.array(NonEmptyTextSchema).min(1),
  })
  .superRefine((result, context) => {
    const modelIds = new Set(result.models.map((model) => model.id));
    if (modelIds.size !== result.models.length) {
      context.addIssue({
        code: "custom",
        message: "Each baseline model must have a unique identifier.",
        path: ["models"],
      });
    }

    const expectedEvaluations = new Set(
      result.models.flatMap((model) => [
        `${model.id}:validation`,
        `${model.id}:test`,
      ]),
    );
    const summaries = new Map<string, (typeof result.evaluation)[number]>();
    for (const [index, summary] of result.evaluation.entries()) {
      const key = `${summary.model_id}:${summary.partition}`;
      if (
        !modelIds.has(summary.model_id) ||
        !expectedEvaluations.has(key) ||
        summaries.has(key)
      ) {
        context.addIssue({
          code: "custom",
          message: "Each model must have one validation and one test summary.",
          path: ["evaluation", index],
        });
      }
      summaries.set(key, summary);
    }

    for (const [index, row] of result.evaluation_rows.entries()) {
      if (!modelIds.has(row.model_id)) {
        context.addIssue({
          code: "custom",
          message: "Evaluation rows must refer to a model in the result.",
          path: ["evaluation_rows", index, "model_id"],
        });
      }
    }

    for (const [key, summary] of summaries) {
      const rowCount = result.evaluation_rows.filter(
        (row) => `${row.model_id}:${row.partition}` === key,
      ).length;
      if (rowCount !== summary.n) {
        context.addIssue({
          code: "custom",
          message: "Evaluation row counts must match the partition summary.",
          path: ["evaluation"],
        });
      }
    }

    const referenceRows = new Map(
      result.evaluation_rows
        .filter((row) => row.model_id === "last_close")
        .map((row) => [researchRowIdentity(row), row]),
    );
    for (const modelId of modelIds) {
      const rows = result.evaluation_rows.filter(
        (row) => row.model_id === modelId,
      );
      const identities = new Set(rows.map(researchRowIdentity));
      if (
        identities.size !== rows.length ||
        identities.size !== referenceRows.size ||
        rows.some((row) => {
          const reference = referenceRows.get(researchRowIdentity(row));
          return (
            !reference ||
            reference.actual !== row.actual ||
            reference.origin_value !== row.origin_value
          );
        })
      ) {
        context.addIssue({
          code: "custom",
          message:
            "Reference rows must share unique target, input, cutoff and observed-value identities.",
          path: ["evaluation_rows"],
        });
      }
    }

    const forecastModelIds = new Set(
      result.forecast.models.map((model) => model.model_id),
    );
    if (forecastModelIds.size !== result.forecast.models.length) {
      context.addIssue({
        code: "custom",
        message: "Each forecast model must have a unique identifier.",
        path: ["forecast", "models"],
      });
    }
    if (forecastModelIds.size !== modelIds.size) {
      context.addIssue({
        code: "custom",
        message: "Each result model must have a forecast line.",
        path: ["forecast", "models"],
      });
    }
    for (const [index, modelId] of [...forecastModelIds].entries()) {
      if (!modelIds.has(modelId)) {
        context.addIssue({
          code: "custom",
          message: "Forecast lines must refer to a model in the result.",
          path: ["forecast", "models", index, "model_id"],
        });
      }
    }

    let previousHistoryDate: string | null = null;
    for (const [index, point] of result.forecast.history.entries()) {
      if (previousHistoryDate !== null && point.time <= previousHistoryDate) {
        context.addIssue({
          code: "custom",
          message: "Observed history must be in strict session-date order.",
          path: ["forecast", "history", index, "time"],
        });
      }
      previousHistoryDate = point.time;
    }

    const forecastOrigin = result.forecast.history.at(-1)?.time;
    if (forecastOrigin !== result.forecast.origin) {
      context.addIssue({
        code: "custom",
        message:
          "The final historical observation must match the forecast origin.",
        path: ["forecast", "origin"],
      });
    }

    const expectedPointCount = result.target.horizon_sessions + 1;
    let forecastTimes: string[] | null = null;
    for (const [index, forecastModel] of result.forecast.models.entries()) {
      const times = forecastModel.points.map((point) => point.time);
      if (
        forecastModel.points.length !== expectedPointCount ||
        times[0] !== result.forecast.origin ||
        times.some(
          (time, pointIndex) =>
            pointIndex > 0 && time <= (times[pointIndex - 1] ?? ""),
        )
      ) {
        context.addIssue({
          code: "custom",
          message:
            "Each forecast line must include its origin and every next scheduled session.",
          path: ["forecast", "models", index, "points"],
        });
      }
      if (
        forecastTimes !== null &&
        times.some((time, timeIndex) => time !== forecastTimes?.[timeIndex])
      ) {
        context.addIssue({
          code: "custom",
          message: "Forecast models must use the same scheduled sessions.",
          path: ["forecast", "models", index, "points"],
        });
      }
      forecastTimes ??= times;
    }
  });

const ResearchRuntimeSchema = z.strictObject({
  python: ShortTextSchema,
  engine_source_sha256: ResearchSha256Schema,
  dependency_lock_sha256: ResearchSha256Schema,
  dependencies: z
    .object({
      exchange_calendars: ShortTextSchema,
    })
    .catchall(ShortTextSchema),
  random_seed: z.null(),
  deterministic: z.literal(true),
});

export const ResearchRunSchema = z
  .strictObject({
    id: ResearchRunIdSchema,
    dataset_id: ResearchRunIdSchema,
    dataset_version: ResearchSha256Schema,
    name: ShortTextSchema,
    data_kind: ResearchDataKindSchema,
    instrument_id: ShortTextSchema,
    horizon_sessions: ResearchHorizonSchema,
    status: z.literal("succeeded"),
    result: ResearchEvaluationSchema,
    error_code: z.null(),
    runtime: ResearchRuntimeSchema,
    created_at: ResearchDateTimeSchema,
    started_at: ResearchDateTimeSchema,
    completed_at: ResearchDateTimeSchema,
    attempts: z.literal(1),
  })
  .superRefine((run, context) => {
    if (run.result.dataset_version !== run.dataset_version) {
      context.addIssue({
        code: "custom",
        message: "The evaluation result must match the run's dataset version.",
        path: ["result", "dataset_version"],
      });
    }
    if (run.result.data_kind !== run.data_kind) {
      context.addIssue({
        code: "custom",
        message: "The evaluation result must match the run's dataset kind.",
        path: ["result", "data_kind"],
      });
    }
    if (run.result.target.horizon_sessions !== run.horizon_sessions) {
      context.addIssue({
        code: "custom",
        message: "The evaluation horizon must match the requested run horizon.",
        path: ["result", "target", "horizon_sessions"],
      });
    }

    const expectedEvidenceKind =
      run.data_kind === "synthetic_fixture"
        ? "synthetic_pipeline_check"
        : "historical_walk_forward";
    if (run.result.evidence_kind !== expectedEvidenceKind) {
      context.addIssue({
        code: "custom",
        message: "The evidence kind must match the dataset kind.",
        path: ["result", "evidence_kind"],
      });
    }
  });

export const ResearchDatasetListResponseSchema = ResearchDatasetListSchema;
export const ResearchRunListSchema = z
  .strictObject({
    items: z.array(ResearchRunSchema).max(20),
  })
  .superRefine((runs, context) => {
    const identifiers = new Set<string>();
    for (const [index, run] of runs.items.entries()) {
      if (identifiers.has(run.id)) {
        context.addIssue({
          code: "custom",
          message: "Saved run identifiers must be unique.",
          path: ["items", index, "id"],
        });
      }
      identifiers.add(run.id);
    }
  });

export const ResearchRunRequestSchema = z.strictObject({
  dataset_id: ResearchRunIdSchema,
  horizon_sessions: ResearchHorizonSchema,
  idempotency_key: ResearchRunIdSchema,
});

export const ResearchHistoryQuerySchema = z.strictObject({
  q: z.string().trim().max(128).optional(),
  instrument_id: ResearchInstrumentIdSchema.optional(),
  horizon_sessions: ResearchHorizonSchema.optional(),
  data_kind: ResearchDataKindSchema.optional(),
  offset: z.number().int().nonnegative(),
  limit: z.number().int().min(1).max(50),
});

export const ResearchHistoryItemSchema = z.strictObject({
  id: ResearchRunIdSchema,
  dataset_id: ResearchRunIdSchema,
  dataset_version: ResearchSha256Schema,
  name: ShortTextSchema,
  data_kind: ResearchDataKindSchema,
  instrument_id: ShortTextSchema,
  horizon_sessions: ResearchHorizonSchema,
  created_at: ResearchDateTimeSchema,
  completed_at: ResearchDateTimeSchema,
  status: z.literal("succeeded"),
});

export const ResearchHistoryResponseSchema = z
  .strictObject({
    items: z.array(ResearchHistoryItemSchema).max(50),
    total: z.number().int().nonnegative(),
    offset: z.number().int().nonnegative(),
    limit: z.number().int().min(1).max(50),
  })
  .superRefine((history, context) => {
    if (history.items.length > history.limit) {
      context.addIssue({
        code: "custom",
        message:
          "A history page cannot contain more items than its requested limit.",
        path: ["items"],
      });
    }

    const identifiers = new Set<string>();
    for (const [index, item] of history.items.entries()) {
      if (identifiers.has(item.id)) {
        context.addIssue({
          code: "custom",
          message: "Saved run identifiers must be unique in a history page.",
          path: ["items", index, "id"],
        });
      }
      identifiers.add(item.id);
    }
  });

export const ResearchComparisonResponseSchema = z.strictObject({
  left_id: ResearchRunIdSchema,
  right_id: ResearchRunIdSchema,
  compatible: z.boolean(),
  reasons: z.array(NonEmptyTextSchema).max(20),
});

export const ResearchReplayResponseSchema = z.strictObject({
  run_id: ResearchRunIdSchema,
  result: z.enum(["PASS", "FAIL"]),
  dataset_matches: z.boolean(),
  engine_matches: z.boolean(),
  dependency_lock_matches: z.boolean(),
  runtime_versions_match: z.boolean(),
  result_matches: z.boolean(),
  result_sha256: ResearchSha256Schema,
});

export const ResearchExportResponseSchema = z
  .strictObject({
    format: z.literal("cadrisyn-research-v1"),
    disclosure: z.literal(
      "Synthetic pipeline check. Not empirical market evidence.",
    ),
    dataset: ResearchDatasetSchema,
    run: ResearchRunSchema,
    result_sha256: ResearchSha256Schema,
  })
  .superRefine((exported, context) => {
    if (
      exported.dataset.id !== exported.run.dataset_id ||
      exported.dataset.version !== exported.run.dataset_version
    ) {
      context.addIssue({
        code: "custom",
        message:
          "The exported dataset must match the saved run's immutable dataset identity.",
        path: ["dataset"],
      });
    }
    if (
      exported.dataset.data_kind !== "synthetic_fixture" ||
      exported.run.data_kind !== "synthetic_fixture"
    ) {
      context.addIssue({
        code: "custom",
        message:
          "This export format is reserved for synthetic pipeline checks.",
        path: ["run", "data_kind"],
      });
    }
  });

export type ResearchDataKind = z.infer<typeof ResearchDataKindSchema>;
export type ResearchReferenceId = z.infer<typeof ResearchReferenceIdSchema>;
export type ResearchDataset = z.infer<typeof ResearchDatasetSchema>;
export type ResearchRun = z.infer<typeof ResearchRunSchema>;
export type ResearchEvaluation = z.infer<typeof ResearchEvaluationSchema>;
export type ResearchForecast = z.infer<typeof ResearchForecastSchema>;
export type ResearchRunRequest = z.infer<typeof ResearchRunRequestSchema>;
export type ResearchRunList = z.infer<typeof ResearchRunListSchema>;
export type ResearchDatasetList = z.infer<
  typeof ResearchDatasetListResponseSchema
>;
export type ResearchEvaluationRow = z.infer<typeof ResearchEvaluationRowSchema>;
export type ResearchHistoryQuery = z.infer<typeof ResearchHistoryQuerySchema>;
export type ResearchHistoryItem = z.infer<typeof ResearchHistoryItemSchema>;
export type ResearchHistoryResponse = z.infer<
  typeof ResearchHistoryResponseSchema
>;
export type ResearchComparisonResponse = z.infer<
  typeof ResearchComparisonResponseSchema
>;
export type ResearchReplayResponse = z.infer<
  typeof ResearchReplayResponseSchema
>;
export type ResearchExportResponse = z.infer<
  typeof ResearchExportResponseSchema
>;
