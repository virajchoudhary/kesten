import type { ResearchEvaluationRow } from "./research-schemas";

export function researchRowIdentity(row: ResearchEvaluationRow): string {
  return JSON.stringify([
    row.partition,
    row.origin,
    row.target,
    row.input_sha256,
    row.information_cutoff,
  ]);
}
