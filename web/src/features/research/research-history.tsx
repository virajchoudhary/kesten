"use client";

import { useEffect, useId, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowLeftRight,
  ChevronLeft,
  ChevronRight,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getResearchHistory } from "./research-api";
import { asResearchError } from "./research-errors";
import { formatUtcTimestamp } from "./research-formatters";
import { researchWorkspaceHref } from "./research-navigation";
import {
  ResearchHistoryQuerySchema,
  ResearchInstrumentIdSchema,
  type ResearchHistoryQuery,
  type ResearchReferenceId,
  type ResearchRunRequest,
} from "./research-schemas";
import { ErrorMessage, type LoadState } from "./research-workspace-parts";

const PAGE_SIZE = 20;

export function ResearchHistory({
  refreshToken,
  selectedRunId,
  selectedCompareId,
  instrumentContext,
  focusModel,
  className,
}: {
  refreshToken: number;
  selectedRunId: string | null;
  selectedCompareId: string | null;
  instrumentContext: string | null;
  focusModel: ResearchReferenceId;
  className?: string;
}): React.JSX.Element {
  const ids = useId();
  const [search, setSearch] = useState("");
  const [instrumentId, setInstrumentId] = useState(instrumentContext ?? "");
  const [horizonFilter, setHorizonFilter] = useState<"" | "1" | "5">("");
  const [dataKindFilter, setDataKindFilter] = useState<
    NonNullable<ResearchHistoryQuery["data_kind"]> | "all"
  >("all");
  const [offset, setOffset] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [historyResult, setHistoryResult] = useState<{
    key: string;
    state: LoadState<Awaited<ReturnType<typeof getResearchHistory>>>;
  } | null>(null);

  const normalizedInstrumentId = instrumentId.trim();
  const parsedInstrumentId =
    normalizedInstrumentId === ""
      ? null
      : ResearchInstrumentIdSchema.safeParse(normalizedInstrumentId);
  const invalidInstrumentFilter =
    parsedInstrumentId !== null && !parsedInstrumentId.success;
  const validInstrumentId = parsedInstrumentId?.success
    ? parsedInstrumentId.data
    : null;

  const query = useMemo(() => {
    const filters: ResearchHistoryQuery = { offset, limit: PAGE_SIZE };
    const normalizedSearch = search.trim();
    if (normalizedSearch !== "") {
      filters.q = normalizedSearch;
    }
    if (validInstrumentId !== null) {
      filters.instrument_id = validInstrumentId;
    }
    if (horizonFilter !== "") {
      const horizon: ResearchRunRequest["horizon_sessions"] =
        horizonFilter === "1" ? 1 : 5;
      filters.horizon_sessions = horizon;
    }
    if (dataKindFilter !== "all") {
      filters.data_kind = dataKindFilter;
    }
    return ResearchHistoryQuerySchema.parse(filters);
  }, [dataKindFilter, horizonFilter, offset, search, validInstrumentId]);

  const requestKey = `${JSON.stringify(query)}:${retryCount}:${refreshToken}`;

  useEffect(() => {
    if (invalidInstrumentFilter) {
      return;
    }
    const controller = new AbortController();
    void getResearchHistory(query, controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setHistoryResult({
            key: requestKey,
            state: { kind: "ready", data: response },
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setHistoryResult({
            key: requestKey,
            state: { kind: "failed", error: asResearchError(error) },
          });
        }
      });
    return () => controller.abort();
  }, [invalidInstrumentFilter, query, requestKey]);

  const historyState: LoadState<
    Awaited<ReturnType<typeof getResearchHistory>>
  > = invalidInstrumentFilter
    ? { kind: "loading" }
    : historyResult?.key === requestKey
      ? historyResult.state
      : { kind: "loading" };
  const activeFilters = Boolean(
    search.trim() ||
      normalizedInstrumentId ||
      horizonFilter !== "" ||
      dataKindFilter !== "all",
  );

  function updateSearch(value: string): void {
    setSearch(value);
    setOffset(0);
  }

  function updateInstrument(value: string): void {
    setInstrumentId(value);
    setOffset(0);
  }

  function updateHorizon(value: string): void {
    if (value === "" || value === "1" || value === "5") {
      setHorizonFilter(value);
      setOffset(0);
    }
  }

  function updateDataKind(value: string): void {
    if (
      value === "all" ||
      value === "synthetic_fixture" ||
      value === "historical"
    ) {
      setDataKindFilter(value);
      setOffset(0);
    }
  }

  return (
    <section
      aria-labelledby="research-history-title"
      className={`min-w-0 ${className ?? ""}`}
    >
      <div className="flex min-h-11 items-center justify-between gap-3 border-b border-border-subtle px-4">
        <h2 className="text-sm font-semibold" id="research-history-title">
          Saved evaluations
        </h2>
        <Button
          aria-label="Reload saved evaluations"
          className="size-11 lg:size-9"
          disabled={historyState.kind === "loading" || invalidInstrumentFilter}
          onClick={() => setRetryCount((current) => current + 1)}
          size="icon"
          variant="ghost"
        >
          {historyState.kind === "loading" ? (
            <LoaderCircle
              aria-hidden="true"
              className="animate-spin"
              size={15}
            />
          ) : (
            <RefreshCw aria-hidden="true" size={15} />
          )}
        </Button>
      </div>

      <form
        aria-label="Filter saved evaluations"
        className="grid grid-cols-1 gap-3 border-b border-border-subtle px-4 py-3 sm:grid-cols-2"
        onSubmit={(event) => event.preventDefault()}
      >
        <div className="min-w-0">
          <label
            className="mb-1 block text-xs font-medium"
            htmlFor={`${ids}-search`}
          >
            Search
          </label>
          <Input
            autoComplete="off"
            id={`${ids}-search`}
            maxLength={128}
            onChange={(event) => updateSearch(event.currentTarget.value)}
            placeholder="Dataset or run name"
            type="search"
            value={search}
          />
        </div>
        <div className="min-w-0">
          <label
            className="mb-1 block text-xs font-medium"
            htmlFor={`${ids}-instrument`}
          >
            Instrument
          </label>
          <Input
            aria-describedby={
              invalidInstrumentFilter ? `${ids}-instrument-error` : undefined
            }
            autoComplete="off"
            id={`${ids}-instrument`}
            maxLength={32}
            onChange={(event) => updateInstrument(event.currentTarget.value)}
            placeholder="xnas-aapl"
            value={instrumentId}
          />
          {invalidInstrumentFilter && (
            <p
              className="mt-1 text-xs text-negative"
              id={`${ids}-instrument-error`}
            >
              Enter a curated instrument ID such as xnas-aapl.
            </p>
          )}
        </div>
        <div className="min-w-0">
          <label
            className="mb-1 block text-xs font-medium"
            htmlFor={`${ids}-horizon`}
          >
            Horizon
          </label>
          <select
            className="min-h-10 w-full rounded-control border border-control bg-surface px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
            id={`${ids}-horizon`}
            onChange={(event) => updateHorizon(event.currentTarget.value)}
            value={horizonFilter}
          >
            <option value="">All horizons</option>
            <option value="1">1 session</option>
            <option value="5">5 sessions</option>
          </select>
        </div>
        <div className="min-w-0">
          <label
            className="mb-1 block text-xs font-medium"
            htmlFor={`${ids}-data-kind`}
          >
            Dataset type
          </label>
          <select
            className="min-h-10 w-full rounded-control border border-control bg-surface px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
            id={`${ids}-data-kind`}
            onChange={(event) => updateDataKind(event.currentTarget.value)}
            value={dataKindFilter}
          >
            <option value="all">All dataset types</option>
            <option value="synthetic_fixture">Synthetic fixture</option>
            <option value="historical">Historical</option>
          </select>
        </div>
      </form>

      {invalidInstrumentFilter ? (
        <p className="px-4 py-4 text-sm text-secondary" role="status">
          Saved evaluations are not being searched until the instrument ID is
          corrected.
        </p>
      ) : historyState.kind === "loading" ? (
        <p
          className="flex items-center gap-2 px-4 py-4 text-sm text-secondary"
          role="status"
        >
          <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
          Loading saved evaluations
        </p>
      ) : historyState.kind === "failed" ? (
        <ErrorMessage
          error={historyState.error}
          onRetry={() => setRetryCount((current) => current + 1)}
          retryLabel="Retry saved evaluations"
        />
      ) : historyState.data.items.length === 0 ? (
        <p className="px-4 py-4 text-sm text-secondary" role="status">
          {activeFilters
            ? "No saved evaluations match these filters."
            : "No saved evaluations yet. Completed runs will appear here."}
        </p>
      ) : (
        <>
          <ol className="max-h-[55vh] divide-y divide-border-subtle overflow-y-auto">
            {historyState.data.items.map((run) => {
              const selected = selectedRunId === run.id;
              const comparing = selectedCompareId === run.id;
              const runHref = researchWorkspaceHref({
                runId: run.id,
                compareId: selectedCompareId,
                instrumentId: instrumentContext,
                focusModel,
              });
              const compareHref = researchWorkspaceHref({
                runId: selectedRunId,
                compareId: comparing ? null : run.id,
                instrumentId: instrumentContext,
                focusModel,
              });
              return (
                <li className="min-w-0 px-3 py-2" key={run.id}>
                  <div
                    className={`min-w-0 border-l-2 pl-2 ${
                      selected
                        ? "border-accent bg-raised"
                        : "border-transparent"
                    }`}
                  >
                    <Link
                      aria-current={selected ? "page" : undefined}
                      className="grid min-w-0 gap-1 rounded-control px-2 py-2 text-sm hover:bg-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                      href={runHref}
                      scroll={false}
                    >
                      <span className="flex min-w-0 flex-wrap items-center gap-1.5">
                        <span className="min-w-0 flex-1 truncate font-medium">
                          {run.name}
                        </span>
                        {run.data_kind === "synthetic_fixture" ? (
                          <Badge variant="demo">SYNTHETIC</Badge>
                        ) : (
                          <Badge variant="neutral">HISTORICAL</Badge>
                        )}
                        {selected && <Badge variant="neutral">OPEN</Badge>}
                        {comparing && <Badge variant="neutral">COMPARE</Badge>}
                      </span>
                      <span className="break-words text-xs text-secondary">
                        {run.instrument_id} · {run.horizon_sessions} next{" "}
                        {run.horizon_sessions === 1 ? "session" : "sessions"} ·
                        Succeeded
                      </span>
                      <span className="break-words text-[11px] text-secondary">
                        {formatUtcTimestamp(run.completed_at)} · dataset v
                        {run.dataset_version.slice(0, 12)}
                      </span>
                    </Link>
                    {selectedRunId !== null && selectedRunId !== run.id && (
                      <Link
                        aria-current={comparing ? "true" : undefined}
                        className="mb-1 ml-2 inline-flex min-h-9 items-center gap-1.5 rounded-control px-2 text-xs font-medium text-accent hover:bg-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                        href={compareHref}
                        scroll={false}
                      >
                        <ArrowLeftRight aria-hidden="true" size={14} />
                        <span>
                          {comparing
                            ? "Remove comparison"
                            : "Compare with open run"}
                        </span>
                      </Link>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border-subtle px-4 py-3">
            <p className="text-xs text-secondary" role="status">
              Showing {offset + 1}–
              {Math.min(
                offset + historyState.data.items.length,
                historyState.data.total,
              )}{" "}
              of {historyState.data.total}
            </p>
            <div className="flex gap-2">
              <Button
                disabled={offset === 0}
                onClick={() =>
                  setOffset((current) => Math.max(0, current - PAGE_SIZE))
                }
                size="sm"
                variant="outline"
              >
                <ChevronLeft aria-hidden="true" size={14} />
                Previous
              </Button>
              <Button
                disabled={
                  offset + historyState.data.items.length >=
                  historyState.data.total
                }
                onClick={() => setOffset((current) => current + PAGE_SIZE)}
                size="sm"
                variant="outline"
              >
                Next
                <ChevronRight aria-hidden="true" size={14} />
              </Button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
