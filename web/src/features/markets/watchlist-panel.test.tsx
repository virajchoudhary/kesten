import type { ComponentProps } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api/client";
import { WatchlistPanel } from "./watchlist-panel";

afterEach(cleanup);

it("makes failed-read retry unavailable until an ongoing save settles", () => {
  const props: ComponentProps<typeof WatchlistPanel> = {
    state: {kind: "failed", error: new ApiError({status: 503, code: "unavailable", message: "Watchlist unavailable."})},
    pendingId: "xnas-aapl", mutationError: null, selectedId: null,
    onSelect: vi.fn(), onAdd: async () => true, onRemove: async () => true, onReload: vi.fn(),
  };
  const { rerender } = render(<TooltipProvider><WatchlistPanel {...props} /></TooltipProvider>);
  expect(screen.getByRole("button", {name: "Retry"})).toBeDisabled();
  expect(screen.getByRole("button", {name: "Reload watchlist"})).toBeDisabled();
  expect(screen.getByRole("button", {name: "Add instrument"})).toBeDisabled();
  rerender(<TooltipProvider><WatchlistPanel {...props} pendingId={null} /></TooltipProvider>);
  expect(screen.getByRole("button", {name: "Retry"})).toBeEnabled();
});

it("opens research with the exact saved instrument identity", () => {
  render(<TooltipProvider><WatchlistPanel
    state={{ kind: "ready", items: [{ id: "xnas-aapl", symbol: "AAPL", name: "Apple Inc.", exchange: "XNAS", currency: "USD", timezone: "America/New_York" }] }}
    pendingId={null} mutationError={null} selectedId="xnas-aapl"
    onSelect={vi.fn()} onAdd={async () => true} onRemove={async () => true} onReload={vi.fn()}
  /></TooltipProvider>);
  expect(screen.getByRole("link", { name: "Research AAPL" })).toHaveAttribute("href", "/app/research?instrument=xnas-aapl");
});
