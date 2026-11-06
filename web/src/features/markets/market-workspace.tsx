"use client";

import {
  useEffect,
  useState,
} from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  BookOpenText,
  ChartNoAxesCombined,
  Database,
  LoaderCircle,
  LogOut,
  Menu,
  Moon,
  Sun,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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

const RANGE_OPTIONS = [
  { value: "1m", label: "1 month" },
  { value: "3m", label: "3 months" },
  { value: "6m", label: "6 months" },
  { value: "1y", label: "1 year" },
  { value: "2y", label: "2 years" },
] satisfies ReadonlyArray<{ value: MarketRange; label: string }>;

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

function WorkspaceHeader({
  session,
  onOpenWatchlist,
  onSignOut,
  signOutPending,
}: {
  session: AuthenticatedSession;
  onOpenWatchlist: () => void;
  onSignOut: () => void;
  signOutPending: boolean;
}): React.JSX.Element {
  const { resolvedTheme, setTheme } = useTheme();
  const currentTheme = resolvedTheme === "dark" ? "dark" : "light";
  const nextTheme = currentTheme === "dark" ? "light" : "dark";

  return (
    <>
      <header className="flex h-12 min-w-0 items-center gap-3 border-b border-border-subtle bg-surface px-3 sm:px-4">
        <Link
          aria-label="Cadrisyn markets"
          className="inline-flex min-w-0 items-center gap-2 font-semibold"
          href="/app/markets"
        >
          <ChartNoAxesCombined aria-hidden="true" className="shrink-0 text-accent" size={18} />
          <span className="truncate">Cadrisyn</span>
        </Link>

        <div className="ml-auto flex shrink-0 items-center gap-1.5">
          <Button
            aria-label="Open watchlist and instrument search"
            onClick={onOpenWatchlist}
            size="icon"
            className="size-11 min-[768px]:size-9 min-[1440px]:hidden"
            variant="outline"
          >
            <Menu aria-hidden="true" size={16} />
          </Button>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                aria-label={`Use ${nextTheme} theme`}
                onClick={() => setTheme(nextTheme)}
                className="size-11 min-[768px]:size-9"
                size="icon"
                variant="ghost"
              >
                {currentTheme === "dark" ? (
                  <Sun aria-hidden="true" size={16} />
                ) : (
                  <Moon aria-hidden="true" size={16} />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>Use {nextTheme} theme</TooltipContent>
          </Tooltip>

          <span className="hidden max-w-40 truncate px-2 text-xs text-secondary md:block">
            {session.user.username}
          </span>
          <Button
            aria-label="Sign out"
            className="min-h-11 min-w-11 min-[768px]:min-h-8 min-[768px]:min-w-0"
            disabled={signOutPending}
            onClick={onSignOut}
            size="sm"
            variant="ghost"
          >
            {signOutPending ? (
              <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
            ) : (
              <LogOut aria-hidden="true" size={14} />
            )}
            <span className="hidden sm:inline">Sign out</span>
          </Button>
        </div>
      </header>

      <nav
        aria-label="Workspace"
        className="flex h-11 items-center gap-5 border-b border-border-subtle bg-surface px-4 text-xs min-[768px]:hidden"
      >
        <Link aria-current="page" className="py-3 font-medium text-accent" href="/app/markets">
          Markets
        </Link>
        <Link className="py-3 text-secondary hover:text-foreground" href="/methodology">
          Methodology
        </Link>
        <Link className="py-3 text-secondary hover:text-foreground" href="/data">
          Data
        </Link>
      </nav>
    </>
  );
}

function WorkspaceRail(): React.JSX.Element {
  return (
    <nav aria-label="Workspace" className="workspace-rail flex min-h-0 flex-col items-center gap-2 border-r border-border-subtle bg-surface py-3">
      <Tooltip>
        <TooltipTrigger asChild>
          <Link
            aria-current="page"
            aria-label="Markets"
            className="flex size-10 items-center justify-center rounded-control bg-raised text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
            href="/app/markets"
          >
            <ChartNoAxesCombined aria-hidden="true" size={18} />
          </Link>
        </TooltipTrigger>
        <TooltipContent side="right">Markets</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Link
            aria-label="Methodology"
            className="flex size-10 items-center justify-center rounded-control text-secondary hover:bg-raised hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
            href="/methodology"
          >
            <BookOpenText aria-hidden="true" size={18} />
          </Link>
        </TooltipTrigger>
        <TooltipContent side="right">Methodology</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Link
            aria-label="Data"
            className="flex size-10 items-center justify-center rounded-control text-secondary hover:bg-raised hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
            href="/data"
          >
            <Database aria-hidden="true" size={18} />
          </Link>
        </TooltipTrigger>
        <TooltipContent side="right">Data</TooltipContent>
      </Tooltip>
    </nav>
  );
}

function MarketWorkspaceContent({
  session,
}: {
  session: AuthenticatedSession;
}): React.JSX.Element {
  const { state: watchlistState, pendingId, mutationError, refresh, add, remove } = useWatchlist();
  const { refresh: refreshSession, signOut } = useSession();
  const [selectedInstrument, setSelectedInstrument] = useState<Instrument | null>(null);
  const [range, setRange] = useState<MarketRange>("1y");
  const [mode, setMode] = useState<DataMode>("demo");
  const [marketResult, setMarketResult] = useState<MarketResult | null>(null);
  const [showSma20, setShowSma20] = useState(true);
  const [showSma50, setShowSma50] = useState(true);
  const [showRsi, setShowRsi] = useState(true);
  const [tableOpen, setTableOpen] = useState(false);
  const [watchlistOpen, setWatchlistOpen] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [signOutPending, setSignOutPending] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);

  const firstWatchlistInstrument =
    watchlistState.kind === "ready" ? watchlistState.items[0] : undefined;
  const activeInstrumentId = selectedInstrument?.id ?? firstWatchlistInstrument?.id ?? null;
  const marketRequestKey =
    activeInstrumentId === null
      ? null
      : `${activeInstrumentId}:${range}:${mode}:${reloadToken}`;
  const marketState: MarketState =
    activeInstrumentId === null
      ? { kind: "empty" }
      : marketRequestKey !== null && marketResult?.requestKey === marketRequestKey
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
                message: "The API returned market history for a different instrument.",
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
    setSelectedInstrument(instrument);
  }

  function selectRange(value: string): void {
    const nextRange = RANGE_OPTIONS.find((option) => option.value === value)?.value;
    if (nextRange === undefined || nextRange === range) {
      return;
    }
    setRange(nextRange);
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
  const rangeLabel = RANGE_OPTIONS.find((option) => option.value === range)?.label ?? range;

  return (
    <div className="min-h-dvh bg-canvas text-foreground">
      <a className="skip-link" href="#main-content">Skip to market workspace</a>
      <WorkspaceHeader
        onOpenWatchlist={() => setWatchlistOpen(true)}
        onSignOut={() => void handleSignOut()}
        session={session}
        signOutPending={signOutPending}
      />
      {signOutError && (
        <div className="border-b border-negative/40 bg-negative/10 px-4 py-2 text-sm text-negative" role="alert">
          {signOutError}
        </div>
      )}

      <div className="grid min-h-[calc(100dvh-48px)] grid-cols-[64px_minmax(0,1fr)] max-[767px]:grid-cols-1">
        <div className="hidden min-[768px]:block">
          <WorkspaceRail />
        </div>

        <div className="workspace-grid min-w-0">
          <aside className="watchlist-desktop min-w-0 border-r border-border-subtle bg-surface">
            <WatchlistPanel
              mutationError={mutationError}
              onAdd={add}
              onReload={() => void refresh()}
              onRemove={remove}
              onSelect={selectInstrument}
              pendingId={pendingId}
              selectedId={activeInstrumentId}
              state={watchlistState}
            />
          </aside>

          <main className="min-w-0" id="main-content" tabIndex={-1}>
            <div className="flex min-h-12 flex-wrap items-center justify-between gap-3 border-b border-border-subtle px-4 py-2">
              <h1 className="text-base font-semibold">Markets</h1>
              <div className="flex flex-wrap items-center gap-2">
                <label className="sr-only" htmlFor="market-range-trigger">
                  Displayed range
                </label>
                <Select onValueChange={selectRange} value={range}>
                  <SelectTrigger
                    aria-label="Displayed range"
                    className="h-11 min-w-32 min-[768px]:h-9"
                    id="market-range-trigger"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RANGE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <label className="sr-only" htmlFor="market-mode-trigger">
                  Data mode
                </label>
                <Select onValueChange={selectMode} value={mode}>
                  <SelectTrigger
                    aria-describedby={!session.market_data_enabled ? "market-mode-unavailable" : undefined}
                    aria-label="Data mode"
                    className="h-11 min-w-32 min-[768px]:h-9"
                    id="market-mode-trigger"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="demo">Demo data</SelectItem>
                    <SelectItem disabled={!session.market_data_enabled} value="market">
                      Delayed data
                    </SelectItem>
                  </SelectContent>
                </Select>
                {!session.market_data_enabled && <p className="sr-only" id="market-mode-unavailable">Delayed data is not enabled for this environment.</p>}
              </div>
            </div>

            {activeInstrumentId === null && watchlistState.kind === "loading" ? (
              <section
                className="flex min-h-[52vh] items-center justify-center gap-2 text-sm text-secondary"
                role="status"
              >
                <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
                Loading private watchlist
              </section>
            ) : activeInstrumentId === null ? (
              <section className="flex min-h-[52vh] flex-col items-center justify-center gap-3 px-5 text-center">
                <h2 className="text-lg font-semibold">No instrument selected</h2>
                <Button onClick={() => setWatchlistOpen(true)} variant="primary">
                  <Menu aria-hidden="true" size={15} />
                  Add instrument
                </Button>
              </section>
            ) : marketState.kind === "failed" &&
              marketState.instrumentId === activeInstrumentId ? (
              <section className="m-4 border-y border-negative/40 py-5" role="alert">
                <h2 className="text-sm font-semibold text-negative">
                  Daily history unavailable
                </h2>
                <p className="mt-1 text-sm text-secondary">{marketState.error.message}</p>
                {marketState.error.requestId && (
                  <p className="mt-1 font-mono text-xs text-secondary">
                    Request {marketState.error.requestId}
                  </p>
                )}
                <Button
                  className="mt-3"
                  onClick={() => {
                    setReloadToken((value) => value + 1);
                  }}
                  size="sm"
                  variant="outline"
                >
                  Retry
                </Button>
              </section>
            ) : marketState.kind === "loading" || readyData === null ? (
              <section className="flex min-h-[50vh] items-center justify-center gap-2 text-sm text-secondary" role="status">
                <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
                Loading daily history
              </section>
            ) : (
              <div className="min-w-0">
                <section aria-labelledby="selected-instrument-title" className="border-b border-border-subtle px-4 py-4">
                  <div className="flex min-w-0 flex-wrap items-end justify-between gap-3">
                    <div className="min-w-0">
                      <p className="flex flex-wrap items-center gap-2 text-xs text-secondary">
                        <span className="font-mono font-medium text-foreground">
                          {readyData.instrument.symbol}
                        </span>
                        <span>{readyData.instrument.exchange}</span>
                        <span>{readyData.instrument.currency}</span>
                      </p>
                      <h2 className="mt-1 truncate text-base font-semibold" id="selected-instrument-title">
                        {readyData.instrument.name}
                      </h2>
                    </div>
                    {latestBar && (
                      <div className="text-right">
                        <p className="font-mono text-lg font-medium">
                          {formatPrice(latestBar.close, readyData.instrument.currency)}
                        </p>
                        <p className="text-xs text-secondary">
                          Daily close · {formatSessionDate(latestBar.time)}
                        </p>
                      </div>
                    )}
                  </div>
                </section>

                <section aria-labelledby="historical-price-title" className="min-w-0">
                  <div className="flex min-h-11 flex-wrap items-center justify-between gap-2 border-b border-border-subtle px-4 py-2">
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-semibold" id="historical-price-title">
                        Historical price
                      </h2>
                      <Badge variant={readyData.provenance.data_mode === "demo" ? "demo" : "neutral"}>
                        {readyData.provenance.data_mode === "demo" ? "Demo" : "Delayed"}
                      </Badge>
                    </div>
                    <span className="text-xs text-secondary">
                      Daily · {rangeLabel}
                    </span>
                  </div>

                  <fieldset className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-border-subtle px-4 py-2">
                    <legend className="sr-only">Technical indicators</legend>
                    <label className="inline-flex min-h-8 items-center gap-2 text-xs">
                      <input
                        checked={showSma20}
                        className="size-4 accent-accent"
                        onChange={(event) => setShowSma20(event.currentTarget.checked)}
                        type="checkbox"
                      />
                      <span className="size-2 rounded-full bg-[var(--chart-sma20)]" />
                      SMA 20
                    </label>
                    <label className="inline-flex min-h-8 items-center gap-2 text-xs">
                      <input
                        checked={showSma50}
                        className="size-4 accent-accent"
                        onChange={(event) => setShowSma50(event.currentTarget.checked)}
                        type="checkbox"
                      />
                      <span className="size-2 rounded-full bg-[var(--chart-sma50)]" />
                      SMA 50
                    </label>
                    <label className="inline-flex min-h-8 items-center gap-2 text-xs">
                      <input
                        checked={showRsi}
                        className="size-4 accent-accent"
                        onChange={(event) => setShowRsi(event.currentTarget.checked)}
                        type="checkbox"
                      />
                      <span className="size-2 rounded-full bg-[var(--chart-rsi)]" />
                      RSI 14
                    </label>
                  </fieldset>

                  <div className="px-2 sm:px-4">
                    <p className="sr-only" id="market-chart-summary">
                      {readyData.instrument.symbol} daily candles from{" "}
                      {formatSessionDate(readyData.bars[0]?.time ?? readyData.provenance.as_of)} to{" "}
                      {formatSessionDate(readyData.provenance.as_of)}. Price basis:{" "}
                      {readyData.provenance.price_basis}. Exact observations are available in the daily data table.
                    </p>
                    <LightweightMarketChart
                      data={readyData}
                      showRsi={showRsi}
                      showSma20={showSma20}
                      showSma50={showSma50}
                    />
                  </div>
                  <MarketBarsTable bars={readyData.bars} instrument={readyData.instrument} open={tableOpen} onOpenChange={setTableOpen} />
                </section>

                <div className="evidence-mobile min-[1440px]:hidden border-t border-border-subtle">
                  <MarketEvidencePanel
                    instrument={readyData.instrument}
                    marketDataEnabled={session.market_data_enabled}
                    provenance={readyData.provenance}
                  />
                </div>
              </div>
            )}
          </main>

          <aside className="evidence-desktop min-w-0 border-l border-border-subtle bg-surface">
            {readyData !== null ? (
              <MarketEvidencePanel
                instrument={readyData.instrument}
                marketDataEnabled={session.market_data_enabled}
                provenance={readyData.provenance}
              />
            ) : (
              <section aria-labelledby="evidence-empty-title">
                <div className="flex h-12 items-center border-b border-border-subtle px-4">
                  <h2 className="text-sm font-semibold" id="evidence-empty-title">Data evidence</h2>
                </div>
                <p className="px-4 py-4 text-xs text-secondary">No market evidence</p>
              </section>
            )}
          </aside>
        </div>
      </div>

      <Dialog open={watchlistOpen} onOpenChange={setWatchlistOpen}>
        <DialogContent
          aria-describedby="mobile-watchlist-description"
          className="drawer-sheet"
          placement="left"
          hideClose
        >
          <DialogTitle className="sr-only">Watchlist and instrument search</DialogTitle>
          <p className="sr-only" id="mobile-watchlist-description">
            Add or select an instrument.
          </p>
          <WatchlistPanel
            mutationError={mutationError}
            onAdd={add}
            onDismiss={() => setWatchlistOpen(false)}
            onReload={() => void refresh()}
            onRemove={remove}
            onSelect={selectInstrument}
            pendingId={pendingId}
            selectedId={activeInstrumentId}
            state={watchlistState}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

export function MarketWorkspace(): React.JSX.Element {
  const { state, refresh } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (state.kind === "anonymous") {
      router.replace("/sign-in");
    }
  }, [router, state.kind]);

  if (state.kind === "checking") {
    return (
      <main className="flex min-h-dvh items-center justify-center gap-2 bg-canvas text-sm text-secondary" role="status">
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
        <Button className="w-fit" onClick={() => void refresh()} variant="outline">
          Retry
        </Button>
      </main>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-canvas text-sm text-secondary" role="status">
        Sign-in required
      </main>
    );
  }

  return <MarketWorkspaceContent session={state.session} />;
}
