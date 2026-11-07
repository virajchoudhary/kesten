"use client";

import { List, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DialogTrigger } from "@/components/ui/dialog";
import { InstrumentSearch } from "./instrument-search";
import type { DataMode, MarketRange } from "@/lib/api/client";
import type { Instrument } from "@/lib/api/schemas";

export const MARKET_RANGES = [
  { value: "1m", label: "1M" },
  { value: "3m", label: "3M" },
  { value: "6m", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "2y", label: "2Y" },
] satisfies ReadonlyArray<{ value: MarketRange; label: string }>;

export function MarketCommandBar({
  symbol,
  range,
  mode,
  marketEnabled,
  onSelect,
  onRangeChange,
  onModeChange,
  watchlistOpen,
  mobileWatchlistOpen,
  onWatchlistToggle,
  indicatorsOpen,
  onIndicatorsToggle,
}: {
  symbol: string | undefined;
  range: MarketRange;
  mode: DataMode;
  marketEnabled: boolean;
  onSelect: (instrument: Instrument) => void;
  onRangeChange: (range: MarketRange) => void;
  onModeChange: (mode: string) => void;
  watchlistOpen: boolean;
  mobileWatchlistOpen: boolean;
  onWatchlistToggle: () => void;
  indicatorsOpen: boolean;
  onIndicatorsToggle: () => void;
}): React.JSX.Element {
  return (
    <div className="market-command-bar">
      <div className="terminal-symbol-search">
        <InstrumentSearch
          label={symbol ? `${symbol} · Search` : "Search instruments"}
          onSelect={onSelect}
        />
      </div>
      <span
        className="daily-interval"
        title="Only daily observations are available"
      >
        1D
      </span>
      <div
        className="terminal-ranges"
        role="group"
        aria-label="Displayed range"
      >
        {MARKET_RANGES.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={range === option.value}
            onClick={() => onRangeChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
      <Button
        aria-label="Indicators"
        className="indicator-trigger"
        variant="ghost"
        aria-expanded={indicatorsOpen}
        aria-controls={indicatorsOpen ? "terminal-indicators" : undefined}
        onClick={onIndicatorsToggle}
      >
        <SlidersHorizontal size={14} aria-hidden="true" />
        <span>Indicators</span>
      </Button>
      <label className="terminal-data-mode">
        <span className="sr-only">Data mode</span>
        <select
          value={mode}
          onChange={(event) => onModeChange(event.currentTarget.value)}
        >
          <option value="demo">Demo data</option>
          <option disabled={!marketEnabled} value="market">
            Delayed data
          </option>
        </select>
      </label>
      <Button
        aria-label="Open watchlist and instrument search"
        className="watchlist-toggle-desktop"
        aria-expanded={watchlistOpen}
        aria-controls={watchlistOpen ? "terminal-watchlist" : undefined}
        onClick={onWatchlistToggle}
        size="icon"
        variant="ghost"
      >
        <List size={18} aria-hidden="true" />
      </Button>
      <DialogTrigger asChild>
        <Button
          aria-label="Open watchlist and instrument search"
          className="watchlist-toggle-mobile"
          aria-expanded={mobileWatchlistOpen}
          aria-controls={mobileWatchlistOpen ? "mobile-watchlist" : undefined}
          size="icon"
          variant="ghost"
        >
          <List size={18} aria-hidden="true" />
        </Button>
      </DialogTrigger>
    </div>
  );
}
