"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Database,
  FlaskConical,
  LoaderCircle,
  Maximize2,
  Settings2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { TerminalHeader } from "@/components/terminal-header";
import { MarketCommandBar } from "./market-command-bar";
import { InstrumentSearch } from "./instrument-search";
import { ResearchWorkspace } from "@/features/research/research-workspace";
import {
  researchWorkspaceHref,
  type ResearchWorkspaceQuery,
} from "@/features/research/research-navigation";
import { useSession } from "@/features/session/session-provider";
import { LightweightMarketChart } from "@/features/markets/lightweight-market-chart";
import { MarketBarsTable } from "@/features/markets/market-bars-table";
import { MarketEvidencePanel } from "@/features/markets/market-evidence-panel";
import { WatchlistPanel } from "@/features/markets/watchlist-panel";
import { useWatchlist } from "@/features/markets/use-watchlist";
import {
  ApiError,
  getMarketBars,
  type DataMode,
  type MarketRange,
} from "@/lib/api/client";
import type {
  AuthenticatedSession,
  Instrument,
  MarketResponse,
} from "@/lib/api/schemas";

type SettledMarketState =
  | { kind: "ready"; data: MarketResponse }
  | { kind: "failed"; instrumentId: string; error: ApiError };

type MarketState =
  | { kind: "empty" }
  | { kind: "loading"; instrumentId: string }
  | SettledMarketState;

type MarketResult = {
  requestKey: string;
  state: SettledMarketState;
};

function asApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  return new ApiError({
    status: 500,
    code: "market_request_failed",
    message: "Daily market history could not be loaded. Try again.",
  });
}

function formatSessionDate(value: string): string {
  const date = new Date(`${value}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(date);
}

function formatPrice(value: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function MarketWorkspaceContent({
  session,
  researchQuery,
  researchView,
  researchEnabled,
}: {
  session: AuthenticatedSession;
  researchQuery: ResearchWorkspaceQuery;
  researchView: boolean;
  researchEnabled: boolean;
}): React.JSX.Element {
  const router = useRouter();
  const {
    state: watchlistState,
    pendingId,
    mutationError,
    refresh,
    add,
    remove,
  } = useWatchlist();
  const { refresh: refreshSession, signOut } = useSession();
  const [range, setRange] = useState<MarketRange>("1y");
  const [mode, setMode] = useState<DataMode>("demo");
  const [marketResult, setMarketResult] = useState<MarketResult | null>(null);
  const [showSma20, setShowSma20] = useState(true);
  const [showSma50, setShowSma50] = useState(true);
  const [showRsi, setShowRsi] = useState(true);
  const [tableOpen, setTableOpen] = useState(false);
  const [watchlistOpen, setWatchlistOpen] = useState(false);
  const [watchlistExpanded, setWatchlistExpanded] = useState(true);
  const [indicatorsOpen, setIndicatorsOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [resetToken, setResetToken] = useState(0);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [signOutPending, setSignOutPending] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);

  const firstWatchlistInstrument =
    watchlistState.kind === "ready" ? watchlistState.items[0] : undefined;
  const activeInstrumentId =
    researchQuery.requestedInstrumentId ?? firstWatchlistInstrument?.id ?? null;
  const marketRequestKey =
    activeInstrumentId === null
      ? null
      : `${activeInstrumentId}:${range}:${mode}:${reloadToken}`;
  const marketState: MarketState =
    activeInstrumentId === null
      ? { kind: "empty" }
      : marketRequestKey !== null &&
          marketResult?.requestKey === marketRequestKey
        ? marketResult.state
        : { kind: "loading", instrumentId: activeInstrumentId };

  useEffect(() => {
    if (activeInstrumentId === null || marketRequestKey === null) {
      return;
    }

    const controller = new AbortController();
    const instrumentId = activeInstrumentId;
    const requestKey = marketRequestKey;

    void getMarketBars({
      instrumentId,
      range,
      mode,
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted) {
          return;
        }
        if (data.instrument.id !== instrumentId) {
          setMarketResult({
            requestKey,
            state: {
              kind: "failed",
              instrumentId,
              error: new ApiError({
                status: 502,
                code: "instrument_mismatch",
                message:
                  "The API returned market history for a different instrument.",
              }),
            },
          });
          return;
        }
        setMarketResult({ requestKey, state: { kind: "ready", data } });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        const normalized = asApiError(error);
        if (normalized.status === 401 || normalized.status === 403) {
          void refreshSession();
        }
        setMarketResult({
          requestKey,
          state: { kind: "failed", instrumentId, error: normalized },
        });
      });

    return () => controller.abort();
  }, [activeInstrumentId, marketRequestKey, mode, range, refreshSession]);

  async function handleSignOut(): Promise<void> {
    setSignOutPending(true);
    setSignOutError(null);
    try {
      await signOut();
    } catch (error: unknown) {
      setSignOutError(asApiError(error).message);
    } finally {
      setSignOutPending(false);
    }
  }

  function selectInstrument(instrument: Instrument): void {
    setWatchlistOpen(false);
    if (instrument.id === activeInstrumentId) return;
    const query = new URLSearchParams({ instrument: instrument.id });
    if (researchView) query.set("view", "research");
    router.replace(`/app/markets?${query.toString()}`, { scroll: false });
  }

  function selectMode(value: string): void {
    if (value !== "demo" && value !== "market") {
      return;
    }
    if (value === "market" && !session.market_data_enabled) {
      return;
    }
    if (value === mode) {
      return;
    }
    setMode(value);
  }

  const readyData =
    marketState.kind === "ready" &&
    activeInstrumentId !== null &&
    marketState.data.instrument.id === activeInstrumentId
      ? marketState.data
      : null;
  const latestBar = readyData?.bars.at(-1);
  const activeInstrument =
    readyData?.instrument ??
    (firstWatchlistInstrument?.id === activeInstrumentId
      ? firstWatchlistInstrument
      : undefined);
  const researchHref = researchWorkspaceHref({
    embedded: true,
    runId: researchQuery.requestedRunId,
    compareId: researchQuery.requestedCompareId,
    instrumentId: researchQuery.requestedInstrumentId ?? activeInstrumentId,
    focusModel: researchQuery.focusModel,
  });
  const chartParams = new URLSearchParams(researchHref.split("?")[1]);
  chartParams.delete("view");
  const chartHref = chartParams.size
    ? `/app/markets?${chartParams.toString()}`
    : "/app/markets";
  const watchlist = (dismiss?: () => void) => (
    <WatchlistPanel
      mutationError={mutationError}
      onAdd={add}
      onReload={() => void refresh()}
      onRemove={remove}
      onSelect={selectInstrument}
      pendingId={pendingId}
      selectedId={activeInstrumentId}
      state={watchlistState}
      onDismiss={dismiss}
    />
  );

  function toggleWatchlist(): void {
    setWatchlistExpanded((value) => !value);
  }

  return (
    <div className="terminal bg-canvas text-foreground">
      <a className="skip-link" href="#main-content">
        Skip to market workspace
      </a>
      <TerminalHeader
        username={session.user.username}
        onSignOut={() => void handleSignOut()}
        signOutPending={signOutPending}
      />
      {signOutError && (
        <p className="px-4 py-2 text-negative" role="alert">
          {signOutError}
        </p>
      )}
      <Dialog open={watchlistOpen} onOpenChange={setWatchlistOpen}>
        <MarketCommandBar
          symbol={activeInstrument?.symbol}
          range={range}
          mode={mode}
          marketEnabled={session.market_data_enabled}
          onSelect={selectInstrument}
          onRangeChange={setRange}
          onModeChange={selectMode}
          watchlistOpen={watchlistExpanded}
          mobileWatchlistOpen={watchlistOpen}
          onWatchlistToggle={toggleWatchlist}
          indicatorsOpen={indicatorsOpen}
          onIndicatorsToggle={() => setIndicatorsOpen((value) => !value)}
        />
        <DialogContent
          id="mobile-watchlist"
          aria-describedby="watchlist-description"
          className="drawer-sheet"
          placement="right"
          hideClose
        >
          <DialogTitle className="sr-only">
            Watchlist and instrument search
          </DialogTitle>
          <p id="watchlist-description" className="sr-only">
            Add or select an instrument.
          </p>
          {watchlist(() => setWatchlistOpen(false))}
        </DialogContent>
      </Dialog>
      <div
        className={`terminal-body ${watchlistExpanded ? "with-watchlist" : ""}`}
      >
        <main id="main-content" tabIndex={-1} className="terminal-main">
          <div className="terminal-view-bar">
            <nav aria-label="Analysis view" className="terminal-view-tabs">
              <Link
                href={chartHref}
                aria-current={!researchView ? "page" : undefined}
              >
                Chart
              </Link>
              {researchEnabled && (
                <Link
                  aria-label="Instrument research"
                  href={researchHref}
                  aria-current={researchView ? "page" : undefined}
                >
                  <FlaskConical size={13} aria-hidden="true" /> Research
                </Link>
              )}
            </nav>
            <div className="terminal-chart-actions">
              <Button
                aria-label="Reset chart view"
                title="Fit all observations"
                size="icon"
                variant="ghost"
                onClick={() => setResetToken((value) => value + 1)}
              >
                <Maximize2 size={14} />
              </Button>
              <Button
                aria-label="Chart settings"
                aria-expanded={settingsOpen}
                size="icon"
                variant="ghost"
                onClick={() => setSettingsOpen((value) => !value)}
              >
                <Settings2 size={14} />
              </Button>
            </div>
          </div>
          {researchView && researchEnabled && (
            <section
              className="terminal-research"
              aria-label="Integrated research"
            >
              <ResearchWorkspace {...researchQuery} embedded />
            </section>
          )}
          <div
            className="terminal-chart-view"
            hidden={researchView && researchEnabled}
          >
            <h1 className="sr-only">Markets</h1>
            {activeInstrumentId === null ? (
              <section className="terminal-empty">
                <h2>No instrument selected</h2>
                <p>Search for an instrument to open its daily chart.</p>
                <InstrumentSearch onSelect={selectInstrument} />
              </section>
            ) : marketState.kind === "failed" ? (
              <section role="alert" className="terminal-empty">
                <h2>Daily history unavailable</h2>
                <p>{marketState.error.message}</p>
                {marketState.error.requestId && (
                  <p className="font-mono text-xs">
                    Request {marketState.error.requestId}
                  </p>
                )}
                <Button
                  onClick={() => setReloadToken((value) => value + 1)}
                  variant="outline"
                >
                  Retry
                </Button>
              </section>
            ) : !readyData ? (
              <div role="status" className="terminal-empty">
                <LoaderCircle className="animate-spin" size={18} /> Loading
                daily history
              </div>
            ) : (
              <>
                <section
                  className="terminal-instrument"
                  aria-labelledby="selected-instrument-title"
                >
                  <div>
                    <h2 id="selected-instrument-title">
                      {readyData.instrument.name}{" "}
                      <span>{readyData.instrument.symbol}</span>
                    </h2>
                    <p>
                      {readyData.instrument.exchange} <span>·</span>{" "}
                      {readyData.instrument.currency} <span>·</span> Daily
                      observations
                    </p>
                  </div>
                  <div className="terminal-last-price">
                    {latestBar && (
                      <>
                        <strong>
                          {formatPrice(
                            latestBar.close,
                            readyData.instrument.currency,
                          )}
                        </strong>
                        <span>
                          Daily close · {formatSessionDate(latestBar.time)}
                        </span>
                      </>
                    )}
                  </div>
                </section>
                <div className="terminal-provenance-strip">
                  <Badge variant={mode === "demo" ? "demo" : "neutral"}>
                    {mode === "demo" ? "Demo" : "Delayed"}
                  </Badge>
                  <span>
                    {mode === "demo"
                      ? "Synthetic demonstration. Not observed market prices."
                      : `As of ${readyData.provenance.as_of}. Delayed market observations.`}
                  </span>
                  <button type="button" onClick={() => setEvidenceOpen(true)}>
                    Data evidence <Database size={12} aria-hidden="true" />
                  </button>
                </div>
                {indicatorsOpen && (
                  <fieldset
                    id="terminal-indicators"
                    className="terminal-indicators"
                  >
                    <legend className="sr-only">Technical indicators</legend>
                    <label>
                      <input
                        type="checkbox"
                        checked={showSma20}
                        onChange={(event) =>
                          setShowSma20(event.currentTarget.checked)
                        }
                      />
                      <i className="bg-[var(--chart-sma20)]" />
                      SMA 20
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={showSma50}
                        onChange={(event) =>
                          setShowSma50(event.currentTarget.checked)
                        }
                      />
                      <i className="bg-[var(--chart-sma50)]" />
                      SMA 50
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={showRsi}
                        onChange={(event) =>
                          setShowRsi(event.currentTarget.checked)
                        }
                      />
                      <i className="bg-[var(--chart-rsi)]" />
                      RSI 14
                    </label>
                  </fieldset>
                )}
                {settingsOpen && (
                  <fieldset className="terminal-indicators">
                    <legend className="sr-only">Chart settings</legend>
                    <label>
                      <input
                        type="checkbox"
                        checked={showGrid}
                        onChange={(event) =>
                          setShowGrid(event.currentTarget.checked)
                        }
                      />
                      Show grid
                    </label>
                    <span className="text-secondary">
                      Drag to pan · Scroll to zoom · Double-click a scale to
                      reset
                    </span>
                  </fieldset>
                )}
                <section
                  aria-label="Historical price"
                  className="terminal-chart-panel"
                >
                  <p className="sr-only" id="market-chart-summary">
                    {readyData.instrument.symbol} daily candles from{" "}
                    {formatSessionDate(
                      readyData.bars[0]?.time ?? readyData.provenance.as_of,
                    )}{" "}
                    to {formatSessionDate(readyData.provenance.as_of)}. Price
                    basis: {readyData.provenance.price_basis}. Exact
                    observations are available in the daily data table.
                  </p>
                  <LightweightMarketChart
                    data={readyData}
                    showRsi={showRsi}
                    showSma20={showSma20}
                    showSma50={showSma50}
                    showGrid={showGrid}
                    resetToken={resetToken}
                  />
                </section>
                <MarketBarsTable
                  bars={readyData.bars}
                  instrument={readyData.instrument}
                  open={tableOpen}
                  onOpenChange={setTableOpen}
                />
              </>
            )}
          </div>
          <footer className="terminal-status">
            <span className="status-dot" />
            {mode === "demo" ? "DEMO ENVIRONMENT" : "DELAYED DATA"}
            <span>1D resolution</span>
            <Link href="/data">Sources & licensing</Link>
          </footer>
        </main>
        {watchlistExpanded && (
          <aside id="terminal-watchlist" className="terminal-watchlist">
            {watchlist(() => setWatchlistExpanded(false))}
          </aside>
        )}
      </div>
      <Dialog open={evidenceOpen} onOpenChange={setEvidenceOpen}>
        <DialogContent
          aria-describedby={undefined}
          className="p-0 [&>section>div:first-child]:pr-14"
        >
          <DialogTitle className="sr-only">Market data evidence</DialogTitle>
          {readyData && (
            <MarketEvidencePanel
              instrument={readyData.instrument}
              marketDataEnabled={session.market_data_enabled}
              provenance={readyData.provenance}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function MarketWorkspace({
  researchQuery,
  researchView,
  researchEnabled,
}: {
  researchQuery: ResearchWorkspaceQuery;
  researchView: boolean;
  researchEnabled: boolean;
}): React.JSX.Element {
  const { state, refresh } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (state.kind === "anonymous") {
      router.replace("/sign-in");
    }
  }, [router, state.kind]);

  if (state.kind === "checking") {
    return (
      <main
        className="flex min-h-dvh items-center justify-center gap-2 bg-canvas text-sm text-secondary"
        role="status"
      >
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Checking session
      </main>
    );
  }

  if (state.kind === "failed") {
    return (
      <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-3 px-5">
        <h1 className="text-lg font-semibold">Workspace unavailable</h1>
        <p className="text-sm text-secondary">{state.error.message}</p>
        <Button
          className="w-fit"
          onClick={() => void refresh()}
          variant="outline"
        >
          Retry
        </Button>
      </main>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <main
        className="flex min-h-dvh items-center justify-center bg-canvas text-sm text-secondary"
        role="status"
      >
        Sign-in required
      </main>
    );
  }

  return (
    <MarketWorkspaceContent
      session={state.session}
      researchQuery={researchQuery}
      researchView={researchView}
      researchEnabled={researchEnabled}
    />
  );
}
