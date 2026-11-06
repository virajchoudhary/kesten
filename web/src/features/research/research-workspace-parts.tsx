"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import {
  ChartNoAxesCombined,
  LoaderCircle,
  LogOut,
  Moon,
  Sun,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";

import type {
  ResearchDataset,
  ResearchRunList,
  ResearchRunRequest,
} from "./research-schemas";

export type LoadState<T> =
  | { kind: "loading" }
  | { kind: "ready"; data: T }
  | { kind: "failed"; error: ApiError };

const HORIZON_OPTIONS: ReadonlyArray<ResearchRunRequest["horizon_sessions"]> = [1, 5];

export function ErrorMessage({
  error,
  onRetry,
  retryLabel,
}: {
  error: ApiError;
  onRetry: () => void;
  retryLabel: string;
}): React.JSX.Element {
  return (
    <div className="border-y border-negative/40 bg-negative/10 px-4 py-4" role="alert">
      <p className="text-sm text-negative">{error.message}</p>
      {error.requestId && (
        <p className="mt-1 break-all font-mono text-xs text-secondary">
          Request {error.requestId}
        </p>
      )}
      <Button className="mt-3" onClick={onRetry} size="sm" variant="outline">
        {retryLabel}
      </Button>
    </div>
  );
}

export function WorkspaceHeader({
  username,
  onSignOut,
  signOutPending,
}: {
  username: string;
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

        <nav aria-label="Workspace" className="hidden min-w-0 items-center gap-4 px-2 text-xs min-[768px]:flex">
          <Link className="text-secondary hover:text-foreground" href="/app/markets">
            Markets
          </Link>
          <span aria-current="page" className="font-medium text-accent">Research</span>
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-1.5">
          <Link className="hidden px-2 py-3 text-xs text-secondary hover:text-foreground sm:inline" href="/app/account">
            Account
          </Link>
          <span className="hidden max-w-40 truncate px-2 text-xs text-secondary md:block">
            {username}
          </span>
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
        className="flex h-11 items-center gap-5 overflow-x-auto border-b border-border-subtle bg-surface px-4 text-xs min-[768px]:hidden"
      >
        <Link className="shrink-0 py-3 text-secondary hover:text-foreground" href="/app/markets">
          Markets
        </Link>
        <span aria-current="page" className="shrink-0 py-3 font-medium text-accent">Research</span>
        <Link className="shrink-0 py-3 text-secondary hover:text-foreground" href="/methodology">
          Methodology
        </Link>
        <Link className="shrink-0 py-3 text-secondary hover:text-foreground" href="/data">
          Data
        </Link>
      </nav>
    </>
  );
}

export function DatasetSelector({
  datasets,
  selectedDatasetId,
  onChange,
  disabled,
}: {
  datasets: readonly ResearchDataset[];
  selectedDatasetId: string;
  onChange: (value: string) => void;
  disabled: boolean;
}): React.JSX.Element {
  return (
    <div className="min-w-0 flex-1 basis-72">
      <label className="mb-1.5 block text-xs font-medium" htmlFor="research-dataset-trigger">
        Private research dataset
      </label>
      <Select onValueChange={onChange} value={selectedDatasetId}>
        <SelectTrigger
          aria-label="Private research dataset"
          className="h-11 w-full max-w-xl min-[768px]:h-9"
          disabled={disabled}
          id="research-dataset-trigger"
        >
          <SelectValue placeholder="Select a dataset" />
        </SelectTrigger>
        <SelectContent>
          {datasets.map((dataset) => (
            <SelectItem key={dataset.id} value={dataset.id}>
              {dataset.name} · {dataset.instrument_id}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function HorizonSelector({
  value,
  onChange,
  disabled,
}: {
  value: ResearchRunRequest["horizon_sessions"];
  onChange: (value: ResearchRunRequest["horizon_sessions"]) => void;
  disabled: boolean;
}): React.JSX.Element {
  return (
    <fieldset className="min-w-0" disabled={disabled}>
      <legend className="mb-1.5 text-xs font-medium">Forecast horizon</legend>
      <div className="flex min-h-11 items-center gap-1 rounded-control border border-control bg-surface p-1 min-[768px]:min-h-9">
        {HORIZON_OPTIONS.map((horizon) => (
          <label
            className={`flex min-h-9 cursor-pointer items-center gap-2 rounded-control px-2.5 text-xs focus-within:ring-2 focus-within:ring-focus ${
              value === horizon ? "bg-raised font-medium text-foreground" : "text-secondary"
            }`}
            key={horizon}
          >
            <input
              checked={value === horizon}
              className="size-4 accent-accent"
              name="research-horizon"
              onChange={() => onChange(horizon)}
              type="radio"
              value={horizon}
            />
            {horizon} next {horizon === 1 ? "session" : "sessions"}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function RunHistory({
  state,
  selectedRunId,
  datasets,
  onRetry,
}: {
  state: LoadState<ResearchRunList>;
  selectedRunId: string | null;
  datasets: readonly ResearchDataset[];
  onRetry: () => void;
}): React.JSX.Element {
  if (state.kind === "loading") {
    return (
      <p className="flex items-center gap-2 px-4 py-4 text-sm text-secondary" role="status">
        <LoaderCircle aria-hidden="true" className="animate-spin" size={15} />
        Loading saved runs
      </p>
    );
  }

  if (state.kind === "failed") {
    return (
      <ErrorMessage
        error={state.error}
        onRetry={onRetry}
        retryLabel="Retry run history"
      />
    );
  }

  if (state.data.items.length === 0) {
    return (
      <p className="px-4 py-4 text-sm text-secondary">
        No saved evaluations yet. Completed runs will appear here.
      </p>
    );
  }

  return (
    <ol className="max-h-80 overflow-y-auto divide-y divide-border-subtle">
      {state.data.items.map((run) => {
        const dataset = datasets.find(
          (item) => item.id === run.dataset_id && item.version === run.dataset_version,
        );
        const selected = selectedRunId === run.id;
        return (
          <li key={run.id}>
            <Link
              aria-current={selected ? "page" : undefined}
              className={`grid min-w-0 gap-1 px-4 py-3 text-sm hover:bg-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus ${
                selected ? "bg-raised" : ""
              }`}
              href={`/app/research?run=${encodeURIComponent(run.id)}`}
              scroll={false}
            >
              <span className="flex min-w-0 flex-wrap items-center gap-2">
                <span className="truncate font-medium">{run.name}</span>
                {run.data_kind === "synthetic_fixture" && <Badge variant="demo">SYNTHETIC FIXTURE</Badge>}
                <Badge variant="neutral">Succeeded</Badge>
              </span>
              <span className="break-words text-xs text-secondary">
                {run.instrument_id} · {run.horizon_sessions} next{" "}
                {run.horizon_sessions === 1 ? "session" : "sessions"} ·{" "}
                {dataset?.source_id ?? run.dataset_version.slice(0, 12)}
              </span>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
