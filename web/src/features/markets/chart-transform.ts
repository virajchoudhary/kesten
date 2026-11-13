import type { MarketResponse } from "@/lib/api/schemas";
import type { ChartPreferences } from "./chart-preferences";

export function chartValue(
  value: number,
  base: number,
  scale: ChartPreferences["scaleMode"],
): number {
  return scale === "percent"
    ? (value / base - 1) * 100
    : scale === "indexed"
      ? (value / base) * 100
      : value;
}

export function comparisonCompatibility(
  primary: MarketResponse,
  comparison: MarketResponse,
): string | null {
  if (primary.instrument.id === comparison.instrument.id)
    return "Choose a different comparison instrument.";
  if (primary.instrument.currency !== comparison.instrument.currency)
    return "Comparison requires the same currency; no FX conversion is performed.";
  if (
    primary.provenance.data_mode !== comparison.provenance.data_mode ||
    primary.provenance.source_id !== comparison.provenance.source_id ||
    primary.provenance.price_basis !== comparison.provenance.price_basis
  )
    return "Comparison requires matching data category, provider and price basis.";
  return null;
}

export type ChartLevel = { id: string; price: number };
export type ChartCommand = {
  action: "fit" | "in" | "out" | "latest";
  sequence: number;
};
