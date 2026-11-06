import { describe, expect, it } from "vitest";

import { researchRunFixture } from "./research-test-fixtures";
import { ResearchRunSchema } from "./research-schemas";

describe("research run contract", () => {
  it("accepts versioned runtime dependencies and rejects non-text package versions", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const versions = { ...run.runtime.dependencies, pandas: "3.1.1", numpy: "2.5.4", tzdata: "2026.6" };
    expect(ResearchRunSchema.safeParse({ ...run, runtime: { ...run.runtime, dependencies: versions } }).success).toBe(true);
    expect(ResearchRunSchema.safeParse({
      ...run, runtime: { ...run.runtime, dependencies: { ...versions, numpy: 2 } },
    }).success).toBe(false);
  });
  it("accepts a complete synthetic pipeline result without empirical claims", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });

    expect(ResearchRunSchema.parse(run)).toEqual(run);
  });

  it("rejects unrecognized fields at the runtime boundary", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const payload: unknown = { ...run, queued_at: "2026-11-05T10:00:00Z" };

    expect(ResearchRunSchema.safeParse(payload).success).toBe(false);
  });

  it("rejects persistent queue states and empirical-performance claims", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const queuedPayload: unknown = { ...run, status: "queued" };
    const empiricalPayload: unknown = {
      ...run,
      result: { ...run.result, empirical_performance_established: true },
    };

    expect(ResearchRunSchema.safeParse(queuedPayload).success).toBe(false);
    expect(ResearchRunSchema.safeParse(empiricalPayload).success).toBe(false);
  });

  it("rejects a synthetic dataset paired with historical walk-forward evidence", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const mismatchedPayload: unknown = {
      ...run,
      result: { ...run.result, evidence_kind: "historical_walk_forward" },
    };

    expect(ResearchRunSchema.safeParse(mismatchedPayload).success).toBe(false);
  });

  it("rejects directional counts that omit evaluated rows", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const evaluation = run.result.evaluation.map((summary, index) =>
      index === 0
        ? { ...summary, direction_confusion: [[0, 0, 0], [0, 0, 0], [0, 0, 0]] }
        : summary,
    );
    const payload: unknown = { ...run, result: { ...run.result, evaluation } };

    expect(ResearchRunSchema.safeParse(payload).success).toBe(false);
  });
});
