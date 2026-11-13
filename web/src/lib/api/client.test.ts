import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getMarketBars,
  getWatchlist,
  login,
  SESSION_RECHECK_EVENT,
} from "@/lib/api/client";

const demoPayload = {
  instrument: {
    id: "xnas-aapl",
    symbol: "AAPL",
    name: "Apple Inc.",
    exchange: "XNAS",
    currency: "USD",
    timezone: "America/New_York",
  },
  bars: [
    {
      time: "2026-10-29",
      open: 100,
      high: 103,
      low: 99,
      close: 102,
      volume: 1200,
    },
  ],
  study_history: [{ time: "2026-10-29", close: 102 }],
  indicators: {
    sma20: [],
    sma50: [],
    rsi14: [],
  },
  provenance: {
    data_mode: "demo",
    source_id: "cadrisyn-synthetic-v1",
    source_label: "Synthetic demonstration dataset",
    as_of: "2026-10-29",
    fetched_at: "2026-10-29T22:00:00Z",
    price_basis: "synthetic",
    freshness_state: "stale",
    market_state: "unknown",
    delay_seconds: null,
    snapshot_id: "fixture-snapshot",
    disclaimer: "Synthetic demonstration data.",
  },
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("market API client", () => {
  it("requests a session recheck after authorization expires, preserving the safe error", async () => {
    const recheck = vi.fn();
    window.addEventListener(SESSION_RECHECK_EVENT, recheck);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "permission_denied",
            message: "Sign in again.",
            field_errors: {},
            request_id: "expired-session",
          }),
          { status: 403 },
        ),
      ),
    );
    try {
      await expect(getWatchlist()).rejects.toMatchObject({
        status: 403,
        requestId: "expired-session",
      });
      expect(recheck).toHaveBeenCalledOnce();
    } finally {
      window.removeEventListener(SESSION_RECHECK_EVENT, recheck);
    }
  });

  it("does not request a session recheck for an incorrect password", async () => {
    const recheck = vi.fn();
    window.addEventListener(SESSION_RECHECK_EVENT, recheck);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "invalid_credentials",
            message: "Incorrect credentials.",
            field_errors: {},
            request_id: "invalid-login",
          }),
          { status: 403 },
        ),
      ),
    );
    try {
      await expect(
        login({ username: "analyst", password: "incorrect" }, "csrf"),
      ).rejects.toMatchObject({ code: "invalid_credentials" });
      expect(recheck).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener(SESSION_RECHECK_EVENT, recheck);
    }
  });
  it("sends login on the same origin with the current CSRF token", async () => {
    const authenticatedPayload = {
      authenticated: true,
      user: { username: "analyst", is_staff: false },
      csrf_token: "next-csrf-token",
      market_data_enabled: false,
      legacy_enabled: false,
    };
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(authenticatedPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const session = await login(
      { username: "analyst", password: "secret" },
      "current-csrf-token",
    );
    const request = fetchMock.mock.calls[0];

    expect(session.authenticated).toBe(true);
    expect(request?.[0]).toBe("/api/v1/session/");
    expect(request?.[1]?.method).toBe("POST");
    expect(request?.[1]?.credentials).toBe("same-origin");
    expect(new Headers(request?.[1]?.headers).get("X-CSRFToken")).toBe(
      "current-csrf-token",
    );
  });

  it("keeps requests same-origin and uncached", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(demoPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getMarketBars({
      instrumentId: "xnas-aapl",
      range: "1y",
      mode: "demo",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/instruments/xnas-aapl/bars/?range=1y&mode=demo",
      expect.objectContaining({
        cache: "no-store",
        credentials: "same-origin",
      }),
    );
  });

  it("rejects a demo payload when delayed market data was requested", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(demoPayload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(
      getMarketBars({
        instrumentId: "xnas-aapl",
        range: "1y",
        mode: "market",
      }),
    ).rejects.toMatchObject({ code: "market_mode_mismatch", status: 502 });
  });

  it("rejects delayed provenance when the user explicitly selected demo", async () => {
    const payload = {
      ...demoPayload,
      provenance: {
        ...demoPayload.provenance,
        data_mode: "delayed",
        source_id: "provider-fixture",
        source_label: "Provider contract fixture",
        price_basis: "split_and_dividend_adjusted",
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    await expect(
      getMarketBars({ instrumentId: "xnas-aapl", range: "1y", mode: "demo" }),
    ).rejects.toMatchObject({ code: "market_mode_mismatch", status: 502 });
  });

  it("preserves provider errors instead of substituting demo data", async () => {
    const errorPayload = {
      code: "market_data_unavailable",
      message: "The daily-data provider is unavailable.",
      field_errors: {},
      request_id: "request-123",
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(errorPayload), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      getMarketBars({
        instrumentId: "xnas-aapl",
        range: "1y",
        mode: "market",
      }),
    ).rejects.toMatchObject({
      status: 503,
      code: "market_data_unavailable",
      requestId: "request-123",
    } satisfies Pick<ApiError, "status" | "code" | "requestId">);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
