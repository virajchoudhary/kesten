"use client";

import { useId } from "react";
import { LoaderCircle, RefreshCw, Star, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { ApiError } from "@/lib/api/client";
import type { Instrument } from "@/lib/api/schemas";
import type { WatchlistState } from "@/features/markets/use-watchlist";
import { InstrumentSearch } from "@/features/markets/instrument-search";

export function WatchlistPanel({
  state,
  pendingId,
  mutationError,
  selectedId,
  onSelect,
  onAdd,
  onRemove,
  onReload,
  onDismiss,
}: {
  state: WatchlistState;
  pendingId: string | null;
  mutationError: ApiError | null;
  selectedId: string | null;
  onSelect: (instrument: Instrument) => void;
  onAdd: (instrument: Instrument) => Promise<boolean>;
  onRemove: (instrumentId: string) => Promise<boolean>;
  onReload: () => void;
  onDismiss?: () => void;
}): React.JSX.Element {
  const titleId = useId();
  const items = state.kind === "ready" ? state.items : [];
  const selectedInWatchlist = selectedId !== null && items.some((item) => item.id === selectedId);

  return (
    <section aria-labelledby={titleId} className="flex h-full min-h-0 flex-col">
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-border-subtle px-3">
        <h2 className="text-sm font-semibold" id={titleId}>
          Watchlist
        </h2>
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                aria-label="Reload watchlist"
                className="size-11 min-[1440px]:size-9"
                disabled={state.kind === "loading" || pendingId !== null}
                onClick={onReload}
                size="icon"
                variant="ghost"
              >
                <RefreshCw
                  aria-hidden="true"
                  className={state.kind === "loading" ? "animate-spin" : undefined}
                  size={15}
                />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Reload watchlist</TooltipContent>
          </Tooltip>
          {onDismiss && (
            <Button
              aria-label="Close watchlist"
              className="size-11"
              onClick={onDismiss}
              size="icon"
              variant="ghost"
            >
              <X aria-hidden="true" size={16} />
            </Button>
          )}
        </div>
      </div>

      <div className="border-b border-border-subtle px-3 py-3">
        <InstrumentSearch
          disabled={pendingId !== null || state.kind === "loading"}
          onSelect={(instrument) => {
            void onAdd(instrument);
            onSelect(instrument);
          }}
        />
      </div>

      {mutationError && (
        <div className="mx-3 mt-3 rounded-control border border-negative/40 bg-negative/10 p-2.5" role="alert">
          <p className="text-xs text-negative">{mutationError.message}</p>
        </div>
      )}

      {state.kind === "loading" && (
        <div className="flex flex-1 items-center justify-center gap-2 text-sm text-secondary" role="status">
          <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
          Loading watchlist
        </div>
      )}

      {state.kind === "failed" && (
        <div className="m-3 rounded-control border border-negative/40 bg-negative/10 p-3" role="alert">
          <p className="text-sm text-negative">{state.error.message}</p>
          {state.error.requestId && (
            <p className="mt-1 font-mono text-xs text-secondary">Request {state.error.requestId}</p>
          )}
          <Button className="mt-3" disabled={pendingId !== null} onClick={onReload} size="sm" variant="outline">
            Retry
          </Button>
        </div>
      )}

      {state.kind === "ready" && state.items.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center px-5 text-center">
          <Star aria-hidden="true" className="mb-3 text-secondary" size={20} />
          <h3 className="text-sm font-medium">No instruments saved</h3>
        </div>
      )}

      {state.kind === "ready" && state.items.length > 0 && (
        <ul aria-label="Saved instruments" className="min-h-0 flex-1 overflow-y-auto py-1">
          {state.items.map((instrument) => (
            <li key={instrument.id}>
              <div
                className={`group flex min-h-11 items-center gap-2 border-l-2 px-3 transition-colors ${
                  instrument.id === selectedId
                    ? "border-accent bg-raised"
                    : "border-transparent hover:bg-raised"
                }`}
              >
                <button
                  aria-current={instrument.id === selectedId ? "true" : undefined}
                  className="flex min-w-0 flex-1 items-center justify-between gap-2 py-1.5 text-left outline-none focus-visible:ring-2 focus-visible:ring-focus"
                  onClick={() => onSelect(instrument)}
                  type="button"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-mono text-sm font-medium">
                      {instrument.symbol}
                    </span>
                    <span className="block truncate text-xs text-secondary">{instrument.name}</span>
                  </span>
                  <span className="shrink-0 text-[11px] text-secondary">{instrument.exchange}</span>
                </button>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      aria-label={`Remove ${instrument.symbol} from watchlist`}
                      className="size-11 min-[1440px]:size-8"
                      disabled={pendingId !== null}
                      onClick={() => void onRemove(instrument.id)}
                      size="icon"
                      variant="ghost"
                    >
                      {pendingId === instrument.id ? (
                        <LoaderCircle aria-hidden="true" className="animate-spin" size={14} />
                      ) : (
                        <X aria-hidden="true" size={14} />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Remove {instrument.symbol}</TooltipContent>
                </Tooltip>
              </div>
            </li>
          ))}
        </ul>
      )}

      {state.kind === "ready" && selectedInWatchlist && (
        <div className="border-t border-border-subtle px-3 py-2">
          <Badge className="w-fit" variant="neutral">
            Private to your account
          </Badge>
        </div>
      )}
    </section>
  );
}
