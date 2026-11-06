import { z } from "zod";

import type { components, paths } from "./generated";

type BarsQuery = NonNullable<
  NonNullable<paths["/api/v1/instruments/{instrument_id}/bars/"]["get"]["parameters"]["query"]>
>;

export type DataMode = NonNullable<BarsQuery["mode"]>;
export type MarketRange = NonNullable<BarsQuery["range"]>;
export type Instrument = components["schemas"]["Instrument"];
export type Bar = components["schemas"]["Bar"];
export type IndicatorPoint = components["schemas"]["IndicatorPoint"];
export type MarketResponse = components["schemas"]["MarketResponse"];
export type Provenance = components["schemas"]["Provenance"];
export type InstrumentList = components["schemas"]["InstrumentList"];
export type Credentials = components["schemas"]["Login"];
export type Session =
  Omit<components["schemas"]["Session"], "authenticated" | "user"> &
    (
      | { authenticated: true; user: components["schemas"]["User"] }
      | { authenticated: false; user: null }
    );

function isTimeZone(value: string): boolean {
  try {
    new Intl.DateTimeFormat("en", { timeZone: value });
    return true;
  } catch {
    return false;
  }
}

const SessionDateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/)
  .refine((value) => {
    const timestamp = Date.parse(`${value}T00:00:00Z`);
    return Number.isFinite(timestamp) && new Date(timestamp).toISOString().slice(0, 10) === value;
  });

export const InstrumentSchema = z.object({
  id: z.string().min(1),
  symbol: z.string().min(1),
  name: z.string().min(1),
  exchange: z.string().min(1),
  currency: z.string().regex(/^[A-Z]{3}$/),
  timezone: z.string().refine(isTimeZone),
}) satisfies z.ZodType<Instrument>;

const UserSchema: z.ZodType<components["schemas"]["User"]> = z.object({
  username: z.string().min(1),
  is_staff: z.boolean(),
});

const SessionFields = {
  csrf_token: z.string().min(1),
  market_data_enabled: z.boolean(),
  legacy_enabled: z.boolean(),
};

export const SessionSchema: z.ZodType<Session> = z.discriminatedUnion("authenticated", [
  z.object({
    ...SessionFields,
    authenticated: z.literal(true),
    user: UserSchema,
  }),
  z.object({
    ...SessionFields,
    authenticated: z.literal(false),
    user: z.null(),
  }),
]);

const BarSchema: z.ZodType<Bar> = z
  .object({
    time: SessionDateSchema,
    open: z.number().finite(),
    high: z.number().finite(),
    low: z.number().finite(),
    close: z.number().finite(),
    volume: z.number().finite().nonnegative(),
  })
  .superRefine((bar, context) => {
    if (bar.high < Math.max(bar.open, bar.close)) {
      context.addIssue({
        code: "custom",
        message: "The high must be at least the open and close.",
        path: ["high"],
      });
    }
    if (bar.low > Math.min(bar.open, bar.close)) {
      context.addIssue({
        code: "custom",
        message: "The low must be no greater than the open and close.",
        path: ["low"],
      });
    }
    if (bar.high < bar.low) {
      context.addIssue({
        code: "custom",
        message: "The high must be no lower than the low.",
        path: ["high"],
      });
    }
  });

const IndicatorPointObjectSchema = z.object({
  time: SessionDateSchema,
  value: z.number().finite(),
});

export const IndicatorPointSchema =
  IndicatorPointObjectSchema satisfies z.ZodType<IndicatorPoint>;

const IndicatorsSchema: z.ZodType<components["schemas"]["Indicators"]> = z.object({
  sma20: z.array(IndicatorPointSchema),
  sma50: z.array(IndicatorPointSchema),
  rsi14: z.array(IndicatorPointObjectSchema.extend({
    value: z.number().finite().min(0).max(100),
  })),
});

export const ProvenanceSchema = z.object({
  data_mode: z.enum(["demo", "delayed"]),
  source_id: z.string().min(1),
  source_label: z.string().min(1),
  as_of: SessionDateSchema,
  fetched_at: z.string().datetime({ offset: true }),
  price_basis: z.string().min(1),
  freshness_state: z.enum(["current", "stale", "partial", "unavailable"]),
  market_state: z.enum(["open", "closed", "unknown"]),
  delay_seconds: z.number().int().nonnegative().nullable(),
  snapshot_id: z.string().min(1),
  disclaimer: z.string(),
}) satisfies z.ZodType<Provenance>;

export const MarketResponseSchema: z.ZodType<MarketResponse> = z
  .object({
    instrument: InstrumentSchema,
    bars: z.array(BarSchema),
    indicators: IndicatorsSchema,
    provenance: ProvenanceSchema,
  })
  .superRefine((response, context) => {
    const barDates = new Set<string>();
    let previousDate: string | null = null;

    for (const [index, bar] of response.bars.entries()) {
      if (barDates.has(bar.time)) {
        context.addIssue({
          code: "custom",
          message: "Daily bars must not repeat a session date.",
          path: ["bars", index, "time"],
        });
      }
      if (previousDate !== null && bar.time <= previousDate) {
        context.addIssue({
          code: "custom",
          message: "Daily bars must be ordered by exchange session date.",
          path: ["bars", index, "time"],
        });
      }
      barDates.add(bar.time);
      previousDate = bar.time;
    }

    if (response.bars.length > 0 && response.provenance.as_of !== response.bars.at(-1)?.time) {
      context.addIssue({
        code: "custom",
        message: "The provenance date must match the final daily bar.",
        path: ["provenance", "as_of"],
      });
    }

    for (const [name, points] of Object.entries(response.indicators)) {
      let previousPointDate: string | null = null;
      for (const [index, point] of points.entries()) {
        if (!barDates.has(point.time) || (previousPointDate !== null && point.time <= previousPointDate)) {
          context.addIssue({
            code: "custom",
            message: "Indicator dates must be ordered and correspond to a daily bar.",
            path: ["indicators", name, index, "time"],
          });
        }
        previousPointDate = point.time;
      }
    }
  });

const FieldErrorSchema = z.union([z.string(), z.array(z.string())]);

export const ApiErrorResponseSchema = z.object({
  code: z.string().min(1),
  message: z.string().min(1),
  field_errors: z.record(z.string(), FieldErrorSchema),
  request_id: z.string().min(1),
});

export const InstrumentListSchema = z.object({
  items: z.array(InstrumentSchema),
}) satisfies z.ZodType<InstrumentList>;

export const CredentialsSchema: z.ZodType<Credentials> = z.object({
  username: z.string().trim().min(1, "Enter your username."),
  password: z.string().min(1, "Enter your password."),
});

export type ApiErrorResponse = z.infer<typeof ApiErrorResponseSchema>;
export type AuthenticatedSession = Extract<z.infer<typeof SessionSchema>, { authenticated: true }>;
