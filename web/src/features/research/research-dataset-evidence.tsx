"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { getResearchDatasetProvenance } from "./research-api";
import { asResearchError } from "./research-errors";
import { formatSessionDate, formatUtcTimestamp } from "./research-formatters";
import type { ResearchDatasetProvenance } from "./research-schemas";
import type { LoadState } from "./research-workspace-parts";

const PERMISSION_LABELS = new Map<string, string>([
  ["storage", "Storage"], ["private_research", "Private research"], ["backup", "Backup"],
  ["internal_transfer", "Internal transfer"], ["redistribution", "Redistribution"],
]);

type DatasetEvidenceProps = { datasetId: string; datasetVersion: string; label?: string };

export function ResearchDatasetEvidence(props: DatasetEvidenceProps): React.JSX.Element {
  return <DatasetEvidenceInspector key={`${props.datasetId}:${props.datasetVersion}`} {...props} />;
}

function DatasetEvidenceInspector({ datasetId, datasetVersion, label = "Source package and permissions" }: DatasetEvidenceProps): React.JSX.Element {
  const [state, setState] = useState<LoadState<ResearchDatasetProvenance> | { kind: "idle" }>({ kind: "idle" });
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);

  async function load(): Promise<void> {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setState({ kind: "loading" });
    try {
      const data = await getResearchDatasetProvenance({ datasetId, datasetVersion, signal: request.signal });
      if (!request.signal.aborted) setState({ kind: "ready", data });
    } catch (error: unknown) {
      if (!request.signal.aborted) setState({ kind: "failed", error: asResearchError(error) });
    }
  }

  const evidence = state.kind === "ready" ? state.data : null;
  return (
    <details className="min-w-0 border-t border-border-subtle" onToggle={(event) => {
      if (event.currentTarget.open && state.kind === "idle") void load();
    }}>
      <summary className="cursor-pointer px-4 py-3 text-xs font-medium focus-visible:ring-2 focus-visible:ring-focus">{label}</summary>
      <div className="min-w-0 space-y-3 border-t border-border-subtle px-4 py-3 text-xs">
        <p className="text-warning">Point-in-time qualification has not been independently verified. Archive integrity is a separate check.</p>
        {state.kind === "loading" && <p role="status">Checking archived source evidence</p>}
        {state.kind === "failed" && <div role="alert">
          <p>{state.error.message}</p>
          <Button className="mt-2" size="sm" variant="outline" onClick={() => void load()}>Retry source evidence</Button>
        </div>}
        {evidence !== null && <>
          <Button size="sm" variant="outline" onClick={() => void load()}>Refresh source evidence</Button>
          <dl className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
            {[
              ["Source", evidence.dataset.source_id], ["License reference", evidence.dataset.license_reference],
              ["Availability declaration", evidence.dataset.availability_evidence],
              ["Coverage", `${formatSessionDate(evidence.dataset.first_session)} – ${formatSessionDate(evidence.dataset.last_session)} · ${evidence.dataset.observation_count} observations`],
              ["Calendar / price basis", `${evidence.dataset.calendar} · ${evidence.dataset.adjustment_basis}`],
              ["Dataset ID", evidence.dataset.id],
              ["Dataset SHA-256", evidence.dataset.version],
            ].map(([label, value]) => <div className="min-w-0" key={label}>
              <dt className="text-secondary">{label}</dt><dd className="mt-1 break-words [overflow-wrap:anywhere]">{value}</dd>
            </div>)}
          </dl>
          {evidence.intake.status === "not_archived" && <p role="status" className="text-secondary">
            {evidence.dataset.data_kind === "synthetic_fixture"
              ? "No archived intake receipt. This synthetic dataset is a pipeline check, not market evidence."
              : "No archived intake receipt. New historical evaluations are blocked."}
          </p>}
          {evidence.intake.status === "failed" && <div role="alert">
            <p className="text-negative">Archived source evidence failed its integrity check.</p>
            <p className="mt-1 text-secondary">{evidence.dataset.data_kind === "historical" ? "New historical evaluations are blocked." : "Synthetic outputs remain pipeline checks."}</p>
            <p className="mt-1 break-all font-mono">Receipt {evidence.intake.receipt_id}</p>
          </div>}
          {evidence.intake.status === "verified" && <>
            <p className="font-medium">Archived bytes match the intake receipt</p>
            <p className="text-secondary">This is the latest archive for the dataset, not a receipt linked to a particular saved run.</p>
            <dl className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2">
              {[
                ["Receipt ID", evidence.intake.receipt_id], ["Receipt SHA-256", evidence.intake.receipt_version],
                ["Acquired", formatUtcTimestamp(evidence.intake.acquired_at)],
                ["Source URL", evidence.intake.source_url], ["Terms URL", evidence.intake.terms_url],
                ["Operator review", evidence.intake.review_reference],
                ...Object.entries(evidence.intake.artifact_sha256).map(([name, hash]) => [`${name} SHA-256`, hash]),
              ].map(([label, value]) => <div className="min-w-0" key={label}>
                <dt className="text-secondary">{label}</dt><dd className="mt-1 break-all font-mono">{value}</dd>
              </div>)}
            </dl>
            <h4 className="font-medium">Operator-declared permissions</h4>
            <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {Object.entries(evidence.intake.declared_permissions).map(([name, allowed]) => <div className="flex justify-between gap-3" key={name}>
                <dt>{PERMISSION_LABELS.get(name) ?? name}</dt><dd className="text-secondary">{allowed ? "Declared allowed" : "Not declared allowed"}</dd>
              </div>)}
            </dl>
            <p className="text-secondary">These are operator attestations. Matching hashes do not establish source authority, legal permission, past publication times or predictive validity.</p>
          </>}
        </>}
      </div>
    </details>
  );
}
