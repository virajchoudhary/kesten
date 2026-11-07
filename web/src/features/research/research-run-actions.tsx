"use client";

import { useEffect, useRef, useState } from "react";
import { Download, LoaderCircle, RotateCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getResearchExport, verifyResearchReplay } from "./research-api";
import { asResearchError } from "./research-errors";
import type {
  ResearchExportResponse,
  ResearchReplayResponse,
  ResearchRun,
} from "./research-schemas";
import { ErrorMessage } from "./research-workspace-parts";

type ActionState<T> =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; data: T }
  | { kind: "failed"; error: ReturnType<typeof asResearchError> };

const REPLAY_CHECKS: ReadonlyArray<{
  key: keyof Pick<
    ResearchReplayResponse,
    | "dataset_matches"
    | "engine_matches"
    | "dependency_lock_matches"
    | "runtime_versions_match"
    | "result_matches"
  >;
  label: string;
}> = [
  { key: "dataset_matches", label: "Dataset" },
  { key: "engine_matches", label: "Engine" },
  { key: "dependency_lock_matches", label: "Dependency lock" },
  { key: "runtime_versions_match", label: "Runtime versions" },
  { key: "result_matches", label: "Saved result" },
];

export function researchExportFilename(runId: string): string {
  return `cadrisyn-research-${runId}.json`;
}

export function downloadResearchExport(
  exported: ResearchExportResponse,
  source: string,
): void {
  const blob = new Blob([source], {
    type: "application/json",
  });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = researchExportFilename(exported.run.id);
  anchor.hidden = true;
  document.body.append(anchor);
  try {
    anchor.click();
  } finally {
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
  }
}

export function ResearchRunActions({
  run,
  csrfToken,
}: {
  run: ResearchRun;
  csrfToken: string;
}): React.JSX.Element {
  const [replayState, setReplayState] = useState<
    ActionState<ResearchReplayResponse>
  >({
    kind: "idle",
  });
  const [exportState, setExportState] = useState<
    ActionState<ResearchExportResponse>
  >({
    kind: "idle",
  });
  const replayController = useRef<AbortController | null>(null);
  const exportController = useRef<AbortController | null>(null);
  const synthetic = run.data_kind === "synthetic_fixture";

  useEffect(
    () => () => {
      replayController.current?.abort();
      exportController.current?.abort();
    },
    [],
  );

  async function runReplay(): Promise<void> {
    if (replayState.kind === "loading") {
      return;
    }
    const controller = new AbortController();
    replayController.current = controller;
    setReplayState({ kind: "loading" });
    try {
      const result = await verifyResearchReplay(
        run.id,
        csrfToken,
        controller.signal,
      );
      if (!controller.signal.aborted) {
        setReplayState({ kind: "ready", data: result });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setReplayState({ kind: "failed", error: asResearchError(error) });
      }
    } finally {
      if (replayController.current === controller) {
        replayController.current = null;
      }
    }
  }

  async function exportRun(): Promise<void> {
    if (!synthetic || exportState.kind === "loading") {
      return;
    }
    const controller = new AbortController();
    exportController.current = controller;
    setExportState({ kind: "loading" });
    try {
      const exported = await getResearchExport(run.id, controller.signal);
      if (!controller.signal.aborted) {
        downloadResearchExport(exported.data, exported.source);
        setExportState({ kind: "ready", data: exported.data });
      }
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setExportState({ kind: "failed", error: asResearchError(error) });
      }
    } finally {
      if (exportController.current === controller) {
        exportController.current = null;
      }
    }
  }

  return (
    <section
      aria-label="Saved evaluation actions"
      className="border-b border-border-subtle px-4 py-3"
    >
      <div className="flex flex-wrap items-start gap-4">
        <div className="min-w-0">
          {replayState.kind !== "failed" && (
            <Button
              className="min-h-10"
              disabled={replayState.kind === "loading"}
              onClick={() => void runReplay()}
              variant="outline"
            >
              {replayState.kind === "loading" ? (
                <LoaderCircle
                  aria-hidden="true"
                  className="animate-spin"
                  size={15}
                />
              ) : (
                <RotateCw aria-hidden="true" size={15} />
              )}
              {replayState.kind === "ready"
                ? "Verify replay again"
                : "Verify exact replay"}
            </Button>
          )}
          <p className="mt-1 max-w-sm text-xs text-secondary">
            Read-only verification of the saved result; no new evaluation is
            created.
          </p>
        </div>

        <div className="min-w-0">
          {exportState.kind !== "failed" && (
            <Button
              aria-describedby={
                synthetic ? undefined : "research-export-disabled-reason"
              }
              className="min-h-10"
              disabled={!synthetic || exportState.kind === "loading"}
              onClick={() => void exportRun()}
              variant="outline"
            >
              {exportState.kind === "loading" ? (
                <LoaderCircle
                  aria-hidden="true"
                  className="animate-spin"
                  size={15}
                />
              ) : (
                <Download aria-hidden="true" size={15} />
              )}
              {exportState.kind === "loading"
                ? "Preparing JSON"
                : synthetic
                  ? "Download synthetic run JSON"
                  : "Download JSON unavailable"}
            </Button>
          )}
          {!synthetic && (
            <p
              className="mt-1 max-w-sm text-xs text-secondary"
              id="research-export-disabled-reason"
            >
              Exports are limited to synthetic pipeline checks.
            </p>
          )}
        </div>
      </div>

      {replayState.kind === "ready" && (
        <div
          aria-label="Exact replay verification"
          className={`mt-3 border-l-2 px-3 py-2 ${
            replayState.data.result === "PASS"
              ? "border-positive bg-positive/10"
              : "border-negative bg-negative/10"
          }`}
          role={replayState.data.result === "PASS" ? "status" : "alert"}
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant={
                replayState.data.result === "PASS" ? "neutral" : "warning"
              }
            >
              Replay {replayState.data.result}
            </Badge>
            <span className="text-xs text-secondary">
              Read-only replay checks
            </span>
          </div>
          <ul className="mt-2 grid grid-cols-1 gap-x-4 gap-y-1 text-xs sm:grid-cols-2 lg:grid-cols-3">
            {REPLAY_CHECKS.map(({ key, label }) => (
              <li
                className="flex min-w-0 items-center justify-between gap-2"
                key={key}
              >
                <span>{label}</span>
                <span
                  className={
                    replayState.data[key] ? "text-positive" : "text-negative"
                  }
                >
                  {replayState.data[key] ? "Match" : "Mismatch"}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 break-all font-mono text-[11px] text-secondary">
            Result SHA-256: {replayState.data.result_sha256}
          </p>
        </div>
      )}

      {replayState.kind === "failed" && (
        <ErrorMessage
          error={replayState.error}
          onRetry={() => void runReplay()}
          retryLabel="Retry exact replay"
        />
      )}

      {exportState.kind === "ready" && (
        <p className="mt-3 text-xs text-secondary" role="status">
          Downloaded {researchExportFilename(exportState.data.run.id)} ·{" "}
          {exportState.data.disclosure}
        </p>
      )}

      {exportState.kind === "failed" && (
        <ErrorMessage
          error={exportState.error}
          onRetry={() => void exportRun()}
          retryLabel="Retry JSON export"
        />
      )}
    </section>
  );
}
