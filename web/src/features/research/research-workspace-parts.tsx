"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";

import type { ResearchDataset, ResearchRunRequest } from "./research-schemas";

export type LoadState<T> =
  | { kind: "loading" }
  | { kind: "ready"; data: T }
  | { kind: "failed"; error: ApiError };

const HORIZON_OPTIONS: ReadonlyArray<ResearchRunRequest["horizon_sessions"]> = [
  1, 5,
];

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
    <div
      className="border-y border-negative/40 bg-negative/10 px-4 py-4"
      role="alert"
    >
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

export { TerminalHeader as WorkspaceHeader } from "@/components/terminal-header";

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
      <label
        className="mb-1.5 block text-xs font-medium"
        htmlFor="research-dataset-trigger"
      >
        Private research dataset
      </label>
      <Select onValueChange={onChange} value={selectedDatasetId}>
        <SelectTrigger
          aria-label="Private research dataset"
          className="h-11 w-full max-w-xl text-left [&>span:first-child]:truncate min-[768px]:h-9"
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
              value === horizon
                ? "bg-raised font-medium text-foreground"
                : "text-secondary"
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
