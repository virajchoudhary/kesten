import { z } from "zod";

export const ChartPreferencesSchema = z.strictObject({
  version: z.literal(1),
  chartType: z.enum(["candles", "bars", "line", "area"]).default("candles"),
  scaleMode: z.enum(["normal", "log", "percent", "indexed"]).default("normal"),
  crosshair: z.enum(["normal", "magnet"]).default("normal"),
  showGrid: z.boolean().default(true),
  showVolume: z.boolean().default(true),
  showRsi: z.boolean().default(true),
  showSma20: z.boolean().default(true),
  showSma50: z.boolean().default(true),
  emaEnabled: z.boolean().default(false),
  emaPeriod: z.number().int().min(2).max(200).default(21),
  bollingerEnabled: z.boolean().default(false),
  bollingerPeriod: z.number().int().min(2).max(200).default(20),
  bollingerDeviation: z.number().finite().min(0.5).max(4).default(2),
});

export type ChartPreferences = z.infer<typeof ChartPreferencesSchema>;

export const defaultChartPreferences = ChartPreferencesSchema.parse({ version: 1 });

export function parseChartPreferences(value: unknown): ChartPreferences {
  const result = ChartPreferencesSchema.safeParse(value);
  return result.success
    ? result.data
    : ChartPreferencesSchema.parse({ version: 1 });
}
