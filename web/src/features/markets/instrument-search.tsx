"use client";

import { useEffect, useId, useState, type KeyboardEvent } from "react";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ApiError, searchInstruments } from "@/lib/api/client";
import type { Instrument } from "@/lib/api/schemas";

type SearchState =
  | { kind: "idle" }
  | { kind: "loading"; query: string }
  | { kind: "results"; query: string; items: Instrument[] }
  | { kind: "empty"; query: string }
  | { kind: "failed"; query: string; error: ApiError };

export function InstrumentSearch({
  onSelect,
  disabled = false,
}: {
  onSelect: (instrument: Instrument) => void;
  disabled?: boolean;
}): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const [searchState, setSearchState] = useState<SearchState>({ kind: "idle" });
  const listId = useId();
  const normalizedQuery = query.trim();
  const displayedState: SearchState =
    !open || normalizedQuery.length === 0
      ? { kind: "idle" }
      : searchState.kind !== "idle" && searchState.query === normalizedQuery
        ? searchState
        : { kind: "loading", query: normalizedQuery };

  useEffect(() => {
    if (!open || normalizedQuery.length === 0) {
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void searchInstruments(normalizedQuery, controller.signal)
        .then((result) => {
          if (controller.signal.aborted) {
            return;
          }
          setSearchState(
            result.items.length === 0
              ? { kind: "empty", query: normalizedQuery }
              : { kind: "results", query: normalizedQuery, items: result.items },
          );
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) {
            return;
          }
          setSearchState({
            kind: "failed",
            query: normalizedQuery,
            error:
              error instanceof ApiError
                ? error
                : new ApiError({
                    status: 500,
                    code: "search_error",
                    message: "Instrument search could not be completed.",
                  }),
          });
        });
    }, 180);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [normalizedQuery, open]);

  function handleOpenChange(nextOpen: boolean): void {
    setOpen(nextOpen);
    if (!nextOpen) {
      setQuery("");
      setActiveIndex(-1);
      setSearchState({ kind: "idle" });
    }
  }

  function selectInstrument(instrument: Instrument): void {
    onSelect(instrument);
    setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "ArrowDown" && displayedState.kind === "results") {
      event.preventDefault();
      setActiveIndex((current) => (current + 1) % displayedState.items.length);
    }
    if (event.key === "ArrowUp" && displayedState.kind === "results") {
      event.preventDefault();
      setActiveIndex((current) =>
        current <= 0 ? displayedState.items.length - 1 : current - 1,
      );
    }
    if (event.key === "Enter" && displayedState.kind === "results") {
      const chosenIndex =
        activeIndex >= 0 ? activeIndex : displayedState.items.length === 1 ? 0 : -1;
      if (chosenIndex >= 0) {
        event.preventDefault();
        const instrument = displayedState.items[chosenIndex];
        if (instrument !== undefined) {
          selectInstrument(instrument);
        }
      }
    }
  }

  const activeOptionId =
    displayedState.kind === "results" && activeIndex >= 0
      ? `${listId}-option-${activeIndex}`
      : undefined;

  return (
    <Dialog onOpenChange={handleOpenChange} open={open}>
      <DialogTrigger asChild>
        <Button
          aria-label="Add instrument"
          className="min-h-11 w-full justify-start gap-2 text-secondary min-[1440px]:min-h-9"
          disabled={disabled}
          variant="outline"
        >
          <Search aria-hidden="true" size={15} />
          <span>Add instrument</span>
        </Button>
      </DialogTrigger>
      <DialogContent aria-describedby={`${listId}-description`} className="gap-0 p-0">
        <DialogHeader className="border-b border-border-subtle px-5 pb-4 pt-5">
          <DialogTitle>Find an instrument</DialogTitle>
          <DialogDescription id={`${listId}-description`}>
            Search by symbol or company. Select a venue-qualified result.
          </DialogDescription>
        </DialogHeader>
        <div className="border-b border-border-subtle px-5 py-4">
          <div className="relative">
            <Search
              aria-hidden="true"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary"
              size={16}
            />
            <Input
              aria-activedescendant={activeOptionId}
              aria-autocomplete="list"
              aria-controls={listId}
              aria-expanded={displayedState.kind === "results"}
              aria-label="Search by symbol or company"
              autoFocus
              className="pl-9"
              onChange={(event) => {
                setQuery(event.currentTarget.value);
                setActiveIndex(-1);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Symbol or company name"
              role="combobox"
              value={query}
            />
          </div>
        </div>
        <div
          aria-live="polite"
          className="max-h-[min(54vh,440px)] min-h-28 overflow-y-auto p-2"
          id={listId}
          role="listbox"
        >
          {displayedState.kind === "idle" && (
            <p className="px-3 py-5 text-sm text-secondary">Enter a symbol or company name.</p>
          )}
          {displayedState.kind === "loading" && (
            <p className="px-3 py-5 text-sm text-secondary" role="status">
              Searching instruments…
            </p>
          )}
          {displayedState.kind === "empty" && (
            <p className="px-3 py-5 text-sm text-secondary" role="status">
              No instruments matched this search.
            </p>
          )}
          {displayedState.kind === "failed" && (
            <div className="px-3 py-5" role="alert">
              <p className="text-sm text-negative">{displayedState.error.message}</p>
              {displayedState.error.requestId && (
                <p className="mt-1 font-mono text-xs text-secondary">
                  Request {displayedState.error.requestId}
                </p>
              )}
            </div>
          )}
          {displayedState.kind === "results" &&
            displayedState.items.map((instrument, index) => (
              <div
                aria-selected={index === activeIndex}
                className="flex cursor-pointer items-center justify-between gap-4 rounded-control px-3 py-3 outline-none hover:bg-raised focus:bg-raised data-[selected=true]:bg-raised"
                id={`${listId}-option-${index}`}
                key={instrument.id}
                onClick={() => selectInstrument(instrument)}
                onMouseDown={(event) => event.preventDefault()}
                onMouseMove={() => setActiveIndex(index)}
                role="option"
                tabIndex={-1}
              >
                <div className="min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-sm font-medium">{instrument.symbol}</span>
                    <span className="truncate text-xs text-secondary">{instrument.name}</span>
                  </div>
                </div>
                <span className="shrink-0 text-xs text-secondary">
                  {instrument.exchange} · {instrument.currency}
                </span>
              </div>
            ))}
        </div>
        <div className="flex items-center justify-between border-t border-border-subtle px-5 py-3 text-xs text-secondary">
          <span>↑ ↓ Navigate</span>
          <span>Enter Select · Esc Close</span>
        </div>
      </DialogContent>
    </Dialog>
  );
}
