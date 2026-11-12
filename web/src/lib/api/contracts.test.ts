import { describe, expect, it } from "vitest";
import { z } from "zod";

import type { components, paths } from "@/lib/api/generated";
import {
  ApiErrorResponseSchema,
  CredentialsSchema,
  InstrumentListSchema,
  InstrumentSchema,
  IndicatorPointSchema,
  MarketResponseSchema,
  ProvenanceSchema,
  SessionSchema,
} from "@/lib/api/schemas";

type IsAssignable<From, To> = [From] extends [To] ? true : false;
type ContractAssertions = [
  IsAssignable<z.infer<typeof InstrumentSchema>, components["schemas"]["Instrument"]>,
  IsAssignable<z.infer<typeof InstrumentListSchema>, components["schemas"]["InstrumentList"]>,
  IsAssignable<z.infer<typeof IndicatorPointSchema>, components["schemas"]["IndicatorPoint"]>,
  IsAssignable<z.infer<typeof MarketResponseSchema>, components["schemas"]["MarketResponse"]>,
  IsAssignable<z.infer<typeof ProvenanceSchema>, components["schemas"]["Provenance"]>,
  IsAssignable<z.infer<typeof SessionSchema>, components["schemas"]["Session"]>,
  IsAssignable<z.infer<typeof CredentialsSchema>, components["schemas"]["Login"]>,
  IsAssignable<z.infer<typeof ApiErrorResponseSchema>, components["schemas"]["Error"]>,
  IsAssignable<
    NonNullable<
      NonNullable<
        paths["/api/v1/instruments/{instrument_id}/bars/"]["get"]["parameters"]["query"]
      >["mode"]
    >,
    "demo" | "market"
  >,
];

const assertions: ContractAssertions = [
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
];

describe("generated OpenAPI contracts", () => {
  it("accepts every runtime schema and the market request variants", () => {
    expect(assertions).toEqual([true, true, true, true, true, true, true, true, true]);
  });
});
