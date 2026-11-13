"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  getMarketBars,
  type DataMode,
  type MarketRange,
} from "@/lib/api/client";
import type { Instrument, MarketResponse } from "@/lib/api/schemas";
import { useSession } from "@/features/session/session-provider";
import { comparisonCompatibility } from "./chart-transform";
import { indexedComparison } from "./chart-studies";

type ComparisonState =
  | { kind: "off" }
  | { kind: "loading" }
  | {
      kind: "ready";
      data: MarketResponse;
      anchor: string;
      shared: number;
      omitted: number;
    }
  | { kind: "failed"; error: ApiError };
export function useMarketComparison({
  instrument,
  primary,
  range,
  mode,
}: {
  instrument: Instrument | null;
  primary: MarketResponse | null;
  range: MarketRange;
  mode: DataMode;
}): ComparisonState {
  const [result, setResult] = useState<{
    key: string;
    state: ComparisonState;
  } | null>(null);
  const { refresh } = useSession();
  const key =
    primary && instrument
      ? `${primary.provenance.snapshot_id}:${instrument.id}:${range}:${mode}`
      : null;
  useEffect(() => {
    if (!instrument || !primary || !key) return;
    const controller = new AbortController();
    void getMarketBars({
      instrumentId: instrument.id,
      range,
      mode,
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted) return;
        const error =
          data.instrument.id !== instrument.id
            ? "The comparison response contains a different instrument."
            : comparisonCompatibility(primary, data);
        if (error)
          throw new ApiError({
            status: 502,
            code: "comparison_incompatible",
            message: error,
          });
        const aligned = indexedComparison(primary.bars, data.bars);
        if (!aligned.anchor || aligned.primary.length < 2)
          throw new ApiError({
            status: 422,
            code: "comparison_overlap",
            message:
              "At least two common sessions are required. No values are forward-filled.",
          });
        setResult({
          key,
          state: {
            kind: "ready",
            data,
            anchor: aligned.anchor,
            shared: aligned.primary.length,
            omitted:
              primary.bars.length +
              data.bars.length -
              2 * aligned.primary.length,
          },
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const normalized =
          error instanceof ApiError
            ? error
            : new ApiError({
                status: 500,
                code: "comparison_failed",
                message: "Comparison data could not be loaded.",
              });
        if (normalized.status === 401 || normalized.status === 403)
          void refresh();
        setResult({ key, state: { kind: "failed", error: normalized } });
      });
    return () => controller.abort();
  }, [key, instrument, primary, range, mode, refresh]);
  if (!instrument) return { kind: "off" };
  return key && result?.key === key ? result.state : { kind: "loading" };
}
