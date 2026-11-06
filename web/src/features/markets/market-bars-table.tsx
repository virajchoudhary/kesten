"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Bar, Instrument } from "@/lib/api/schemas";

const PAGE_SIZE = 20;

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

function formatVolume(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function MarketBarsTable({
  bars,
  instrument,
  open,
  onOpenChange,
}: {
  bars: Bar[];
  instrument: Instrument;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}): React.JSX.Element {
  const [page, setPage] = useState(0);
  const newestFirst = useMemo(() => [...bars].reverse(), [bars]);
  const pageCount = Math.max(1, Math.ceil(newestFirst.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const visibleBars = newestFirst.slice(
    currentPage * PAGE_SIZE,
    (currentPage + 1) * PAGE_SIZE,
  );

  const firstRow = newestFirst.length === 0 ? 0 : currentPage * PAGE_SIZE + 1;
  const lastRow = Math.min((currentPage + 1) * PAGE_SIZE, newestFirst.length);

  return (
    <section aria-labelledby="market-table-title" className="border-t border-border-subtle">
      <div className="flex min-h-12 flex-wrap items-center justify-between gap-2 px-4 py-2">
        <h2 className="text-sm font-semibold" id="market-table-title">
          Daily data
        </h2>
        <Button
          aria-expanded={open}
          aria-controls={open ? "daily-bars-table" : undefined}
          onClick={() => onOpenChange(!open)}
          size="sm"
          variant="outline"
        >
          {open ? "Hide data table" : "Show data table"}
        </Button>
      </div>

      {open && (
        <div className="min-w-0">
          <p className="px-4 pb-2 text-xs text-secondary" id="daily-bars-summary">
            {instrument.symbol} daily OHLCV, most recent sessions first.
          </p>
          <div
            aria-label={`${instrument.symbol} daily observations`}
            className="max-w-full overflow-x-auto"
            id="daily-bars-table"
            role="region"
            tabIndex={0}
          >
            <table
              aria-label={`${instrument.symbol} daily OHLCV`}
              aria-describedby="daily-bars-summary"
              className="w-full min-w-[680px] border-collapse text-left text-xs"
            >
              <thead className="bg-raised text-secondary">
                <tr>
                  <th className="px-4 py-2 font-medium" scope="col">Session</th>
                  <th className="px-4 py-2 text-right font-medium" scope="col">Open</th>
                  <th className="px-4 py-2 text-right font-medium" scope="col">High</th>
                  <th className="px-4 py-2 text-right font-medium" scope="col">Low</th>
                  <th className="px-4 py-2 text-right font-medium" scope="col">Close</th>
                  <th className="px-4 py-2 text-right font-medium" scope="col">Volume</th>
                </tr>
              </thead>
              <tbody>
                {visibleBars.map((bar) => (
                  <tr className="border-t border-border-subtle" key={bar.time}>
                    <th className="px-4 py-2 font-medium" scope="row">
                      {formatSessionDate(bar.time)}
                    </th>
                    <td className="px-4 py-2 text-right font-mono">{formatPrice(bar.open, instrument.currency)}</td>
                    <td className="px-4 py-2 text-right font-mono">{formatPrice(bar.high, instrument.currency)}</td>
                    <td className="px-4 py-2 text-right font-mono">{formatPrice(bar.low, instrument.currency)}</td>
                    <td className="px-4 py-2 text-right font-mono">{formatPrice(bar.close, instrument.currency)}</td>
                    <td className="px-4 py-2 text-right font-mono">{formatVolume(bar.volume)}</td>
                  </tr>
                ))}
                {visibleBars.length === 0 && (
                  <tr>
                    <td className="px-4 py-6 text-secondary" colSpan={6}>
                      No daily observations are available for this range.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-border-subtle px-4 py-2">
            <p aria-live="polite" className="text-xs text-secondary">
              {firstRow}-{lastRow} of {newestFirst.length}
            </p>
            <div className="flex items-center gap-1">
              <Button
                aria-label="Previous data page"
                className="size-11 min-[768px]:size-9"
                disabled={currentPage === 0}
                onClick={() => setPage((value) => Math.max(0, value - 1))}
                size="icon"
                variant="ghost"
              >
                <ChevronLeft aria-hidden="true" size={16} />
              </Button>
              <span className="min-w-14 text-center text-xs text-secondary">
                {currentPage + 1} / {pageCount}
              </span>
              <Button
                aria-label="Next data page"
                className="size-11 min-[768px]:size-9"
                disabled={currentPage >= pageCount - 1}
                onClick={() => setPage((value) => Math.min(pageCount - 1, value + 1))}
                size="icon"
                variant="ghost"
              >
                <ChevronRight aria-hidden="true" size={16} />
              </Button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
