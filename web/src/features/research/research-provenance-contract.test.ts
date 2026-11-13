import { expect, it } from "vitest";

import type { components } from "@/lib/api/generated";
import { researchProvenanceFixture } from "./research-test-fixtures";

it("retains usable status narrowing in the generated provenance contract", () => {
  const evidence: components["schemas"]["DatasetProvenance"] = researchProvenanceFixture();
  const intake = evidence.intake;
  switch (intake.status) {
    case "verified":
      expect(intake.receipt_version).toBe("a".repeat(64));
      expect(intake.declared_permissions.redistribution).toBe(false);
      break;
    case "failed":
      expect(intake.receipt_id).toBeDefined();
      break;
    case "not_archived":
      expect(intake).not.toHaveProperty("receipt_version");
      break;
    default: {
      const exhaustive: never = intake;
      throw new Error(String(exhaustive));
    }
  }
});
