"use client";

import { useCallback, useEffect, useState } from "react";

import {
  addWatchlistInstrument,
  ApiError,
  getWatchlist,
  removeWatchlistInstrument,
} from "@/lib/api/client";
import type { Instrument } from "@/lib/api/schemas";
import { useSession } from "@/features/session/session-provider";

export type WatchlistState =
  | { kind: "loading" }
  | { kind: "ready"; items: Instrument[] }
  | { kind: "failed"; error: ApiError };

type SettledWatchlistState = Exclude<WatchlistState, { kind: "loading" }>;

type WatchlistResult = {
  sessionToken: string;
  attempt: number;
  state: SettledWatchlistState;
};

function normalizeError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  return new ApiError({
    status: 500,
    code: "watchlist_error",
    message: "The watchlist could not be updated. Try again.",
  });
}

export function useWatchlist(): {
  state: WatchlistState;
  pendingId: string | null;
  mutationError: ApiError | null;
  refresh: () => void;
  add: (instrument: Instrument) => Promise<boolean>;
  remove: (instrumentId: string) => Promise<boolean>;
} {
  const { state: sessionState, refresh: refreshSession } = useSession();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<WatchlistResult | null>(null);
  const session = sessionState.kind === "authenticated" ? sessionState.session : null;
  const token = session?.csrf_token ?? null;
  const state: WatchlistState =
    session === null
      ? sessionState.kind === "checking"
        ? { kind: "loading" }
        : { kind: "ready", items: [] }
      : result?.sessionToken === token && result.attempt === attempt
        ? result.state
        : { kind: "loading" };

  const refresh = useCallback((): void => {
    if (pendingId !== null) return;
    setMutationError(null);
    setAttempt((current) => current + 1);
  }, [pendingId]);

  useEffect(() => {
    if (session === null) {
      return;
    }

    const requestSessionToken = session.csrf_token;
    const requestAttempt = attempt;
    const controller = new AbortController();
    void getWatchlist(controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setResult({
            sessionToken: requestSessionToken,
            attempt: requestAttempt,
            state: { kind: "ready", items: response.items },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setResult({
            sessionToken: requestSessionToken,
            attempt: requestAttempt,
            state: { kind: "failed", error: normalizeError(error) },
          });
        }
      });

    return () => controller.abort();
  }, [attempt, session]);

  const add = useCallback(
    async (instrument: Instrument): Promise<boolean> => {
      if (session === null || pendingId !== null || state.kind === "loading") {
        return false;
      }
      setPendingId(instrument.id);
      setMutationError(null);
      try {
        const response = await addWatchlistInstrument(instrument.id, session.csrf_token);
        setResult({
          sessionToken: session.csrf_token,
          attempt,
          state: { kind: "ready", items: response.items },
        });
        return true;
      } catch (error: unknown) {
        const normalized = normalizeError(error);
        setMutationError(normalized);
        if (normalized.status === 401 || normalized.status === 403) {
          void refreshSession();
        }
        return false;
      } finally {
        setPendingId(null);
      }
    },
    [attempt, pendingId, refreshSession, session, state.kind],
  );

  const remove = useCallback(
    async (instrumentId: string): Promise<boolean> => {
      if (session === null || pendingId !== null || state.kind === "loading") {
        return false;
      }
      setPendingId(instrumentId);
      setMutationError(null);
      try {
        await removeWatchlistInstrument(instrumentId, session.csrf_token);
        setResult((current) => {
          const currentItems =
            current?.sessionToken === session.csrf_token &&
            current.attempt === attempt &&
            current.state.kind === "ready"
              ? current.state.items
              : [];
          return {
            sessionToken: session.csrf_token,
            attempt,
            state: {
              kind: "ready",
              items: currentItems.filter((item) => item.id !== instrumentId),
            },
          };
        });
        return true;
      } catch (error: unknown) {
        const normalized = normalizeError(error);
        setMutationError(normalized);
        if (normalized.status === 401 || normalized.status === 403) {
          void refreshSession();
        }
        return false;
      } finally {
        setPendingId(null);
      }
    },
    [attempt, pendingId, refreshSession, session, state.kind],
  );

  return { state, pendingId, mutationError, refresh, add, remove };
}
