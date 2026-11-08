import userEvent from "@testing-library/user-event";
import type { ComponentProps } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api/client";
import { WatchlistPanel } from "./watchlist-panel";

afterEach(cleanup);

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
