import userEvent from "@testing-library/user-event";
import type { ComponentProps } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api/client";
import { WatchlistPanel } from "./watchlist-panel";
import type { MarketResponse } from "@/lib/api/schemas";

afterEach(cleanup);

it("offers research for the loaded instrument even when it is not saved", () => {
  const snapshot: MarketResponse = {
    instrument: {
      id: "xnys-jpm",
      symbol: "JPM",
      name: "JPMorgan Chase",
      exchange: "XNYS",
      currency: "USD",
      timezone: "America/New_York",
    },
    bars: [
      {
        time: "2026-10-30",
        open: 100,
        high: 102,
        low: 99,
        close: 101,
        volume: 1000,
      },
    ],
    study_history: [{ time: "2026-10-30", close: 101 }],
    indicators: { sma20: [], sma50: [], rsi14: [] },
    provenance: {
      data_mode: "demo",
      source_id: "fixture",
      source_label: "Synthetic fixture",
      as_of: "2026-10-30",
      fetched_at: "2026-11-09T00:00:00Z",
      price_basis: "synthetic",
      freshness_state: "stale",
      market_state: "unknown",
      delay_seconds: null,
      snapshot_id: "fixture",
      disclaimer: "Synthetic prices, not observed market prices.",
    },
  };
  const props: ComponentProps<typeof WatchlistPanel> = {
    state: { kind: "ready", items: [] },
    pendingId: null,
    mutationError: null,
    selectedId: snapshot.instrument.id,
    snapshot,
    onSelect: vi.fn(),
    onAdd: async () => true,
    onRemove: async () => true,
    onReload: vi.fn(),
  };
  const { rerender } = render(
    <TooltipProvider>
      <WatchlistPanel {...props} />
    </TooltipProvider>,
  );
  expect(
    screen.getByRole("link", { name: "Open research for JPM" }),
  ).toHaveAttribute("href", "/app/markets?view=research&instrument=xnys-jpm");
  expect(
    screen.getByText("Synthetic prices. Not observed market data."),
  ).toBeVisible();
  rerender(
    <TooltipProvider>
      <WatchlistPanel {...props} selectedId="xnas-aapl" />
    </TooltipProvider>,
  );
  expect(
    screen.queryByRole("link", { name: "Open research for JPM" }),
  ).toBeNull();
});

it("makes failed-read retry unavailable until an ongoing save settles", () => {
  const props: ComponentProps<typeof WatchlistPanel> = {
    state: {
      kind: "failed",
      error: new ApiError({
        status: 503,
        code: "unavailable",
        message: "Watchlist unavailable.",
      }),
    },
    pendingId: "xnas-aapl",
    mutationError: null,
    selectedId: null,
    onSelect: vi.fn(),
    onAdd: async () => true,
    onRemove: async () => true,
    onReload: vi.fn(),
  };
  const { rerender } = render(
    <TooltipProvider>
      <WatchlistPanel {...props} />
    </TooltipProvider>,
  );
  expect(screen.getByRole("button", { name: "Retry" })).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Reload watchlist" }),
  ).toBeDisabled();
  expect(screen.getByRole("button", { name: "Add instrument" })).toBeDisabled();
  rerender(
    <TooltipProvider>
      <WatchlistPanel {...props} pendingId={null} />
    </TooltipProvider>,
  );
  expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
});

it("opens research with the exact saved instrument identity", () => {
  render(
    <TooltipProvider>
      <WatchlistPanel
        state={{
          kind: "ready",
          items: [
            {
              id: "xnas-aapl",
              symbol: "AAPL",
              name: "Apple Inc.",
              exchange: "XNAS",
              currency: "USD",
              timezone: "America/New_York",
            },
          ],
        }}
        pendingId={null}
        mutationError={null}
        selectedId="xnas-aapl"
        onSelect={vi.fn()}
        onAdd={async () => true}
        onRemove={async () => true}
        onReload={vi.fn()}
      />
    </TooltipProvider>,
  );
  expect(screen.getByRole("link", { name: "Research AAPL" })).toHaveAttribute(
    "href",
    "/app/markets?view=research&instrument=xnas-aapl",
  );
});

it("sorts and navigates only the filtered private instruments", async () => {
  const user = userEvent.setup(),
    onSelect = vi.fn();
  const apple = {
    id: "xnas-aapl",
    symbol: "AAPL",
    name: "Apple Inc.",
    exchange: "XNAS",
    currency: "USD",
    timezone: "America/New_York",
  };
  render(
    <TooltipProvider>
      <WatchlistPanel
        state={{
          kind: "ready",
          items: [
            { ...apple, id: "xnas-msft", symbol: "MSFT", name: "Microsoft" },
            apple,
          ],
        }}
        pendingId={null}
        mutationError={null}
        selectedId="xnas-aapl"
        onSelect={onSelect}
        onAdd={async () => true}
        onRemove={async () => true}
        onReload={vi.fn()}
      />
    </TooltipProvider>,
  );
  await user.selectOptions(screen.getByLabelText("Sort watchlist"), "symbol");
  const buttons = screen
    .getAllByRole("button")
    .filter((button) => button.hasAttribute("data-watchlist-symbol"));
  expect(
    buttons.map((button) => button.getAttribute("data-watchlist-symbol")),
  ).toEqual(["xnas-aapl", "xnas-msft"]);
  buttons[0].focus();
  await user.keyboard("{ArrowDown}");
  expect(onSelect).toHaveBeenLastCalledWith(
    expect.objectContaining({ id: "xnas-msft" }),
  );
  expect(buttons[1]).toHaveFocus();
  await user.type(screen.getByLabelText("Filter watchlist"), "Apple");
  expect(
    screen.getByRole("list", { name: "Saved instruments" }).children,
  ).toHaveLength(1);
});
