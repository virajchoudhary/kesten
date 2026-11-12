import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { addWatchlistInstrument, getWatchlist, removeWatchlistInstrument } from "@/lib/api/client";
import type { AuthenticatedSession, Instrument, InstrumentList } from "@/lib/api/schemas";
import { useSession } from "@/features/session/session-provider";
import { useWatchlist } from "./use-watchlist";

vi.mock("@/features/session/session-provider", () => ({ useSession: vi.fn() }));
vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return { ...actual, getWatchlist: vi.fn(), addWatchlistInstrument: vi.fn(), removeWatchlistInstrument: vi.fn() };
});

const apple: Instrument = { id: "xnas-aapl", symbol: "AAPL", name: "Apple Inc.", exchange: "XNAS", currency: "USD", timezone: "America/New_York" };
const session: AuthenticatedSession = { authenticated: true, user: {username: "analyst", is_staff: false}, csrf_token: "fixture-csrf", market_data_enabled: false, legacy_enabled: false };

beforeEach(() => {
  vi.mocked(useSession).mockReturnValue({ state: {kind: "authenticated", session}, refresh: async () => {}, authenticate: async () => session, signOut: async () => {} });
  vi.mocked(addWatchlistInstrument).mockResolvedValue({items: [apple]});
});

describe("watchlist request ordering", () => {
  it("settles the initial read before accepting a mutation", async () => {
    const initial = Promise.withResolvers<InstrumentList>();
    vi.mocked(getWatchlist).mockReturnValue(initial.promise);
    const { result } = renderHook(useWatchlist);
    await act(async () => {
      expect(await result.current.add(apple)).toBe(false);
      expect(await result.current.remove(apple.id)).toBe(false);
    });
    expect(addWatchlistInstrument).not.toHaveBeenCalled();
    expect(removeWatchlistInstrument).not.toHaveBeenCalled();
    await act(async () => initial.resolve({items: []}));
    await waitFor(() => expect(result.current.state.kind).toBe("ready"));
    await act(async () => { expect(await result.current.add(apple)).toBe(true); });
    expect(result.current.state).toEqual({kind: "ready", items: [apple]});
  });

  it("prevents reload from racing an in-flight save", async () => {
    vi.mocked(getWatchlist).mockResolvedValue({items: []});
    const save = Promise.withResolvers<InstrumentList>();
    vi.mocked(addWatchlistInstrument).mockReturnValue(save.promise);
    const { result } = renderHook(useWatchlist);
    await waitFor(() => expect(result.current.state.kind).toBe("ready"));
    act(() => { void result.current.add(apple); });
    expect(result.current.pendingId).toBe(apple.id);
    act(() => result.current.refresh());
    expect(getWatchlist).toHaveBeenCalledTimes(1);
    await act(async () => save.resolve({items: [apple]}));
    expect(result.current.pendingId).toBeNull();
    expect(result.current.state).toEqual({kind: "ready", items: [apple]});
  });
});
