"use client";

import { useId, useState } from "react";

import { formatSessionDate, formatUsd } from "./research-formatters";
import type { ResearchRun } from "./research-schemas";

export function ResearchBaselineSummary({ run, headingId }: { run: ResearchRun; headingId?: string }): React.JSX.Element {
  const generatedHeading = useId();
  const heading = headingId ?? generatedHeading;
  const [partition, setPartition] = useState<"test" | "validation">("test");
  const summaries = run.result.evaluation.filter((row) => row.partition === partition);
  const protocol = run.result.protocol;
  const start = partition === "test" ? protocol.test_start : protocol.validation_start;
  const end = partition === "test" ? protocol.test_end : protocol.validation_end;

  return <section aria-labelledby={heading} className="min-w-0 border-b border-border-subtle">
    <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
      <h3 id={heading} tabIndex={-1} className="scroll-mt-16 text-sm font-semibold">Baseline comparison</h3>
      <div role="group" aria-label="Baseline comparison period" className="flex gap-1">
        <button type="button" aria-pressed={partition === "test"} onClick={() => setPartition("test")} className="min-h-9 rounded-control border border-control px-3 text-xs aria-pressed:bg-raised focus-visible:ring-2 focus-visible:ring-focus">Test</button>
        <button type="button" aria-pressed={partition === "validation"} onClick={() => setPartition("validation")} className="min-h-9 rounded-control border border-control px-3 text-xs aria-pressed:bg-raised focus-visible:ring-2 focus-visible:ring-focus">Validation</button>
      </div>
    </div>
    <p className="px-4 pb-2 text-xs text-warning">{run.data_kind === "synthetic_fixture" ? "Synthetic pipeline check · Not market evidence" : "Exploratory historical data · Point-in-time qualification unverified"}</p>
    <p className="px-4 pb-3 text-xs text-secondary">{formatSessionDate(start)} – {formatSessionDate(end)} · {run.horizon_sessions}-session targets · USD per initial share</p>
    <div role="region" aria-label="Baseline error comparison" tabIndex={0} className="max-w-full overflow-x-auto border-y border-border-subtle focus-visible:ring-2 focus-visible:ring-focus">
      <table className="w-full min-w-[360px] border-collapse text-left text-xs">
        <caption className="sr-only">{partition} errors by model; delta is model MAE minus persistence MAE, in USD per initial share.</caption>
        <thead className="text-secondary"><tr>
          <th scope="col" className="px-3 py-2 font-medium">Reference</th>
          <th scope="col" className="px-2 py-2 text-right font-medium">MAE</th>
          <th scope="col" className="px-2 py-2 text-right font-medium">RMSE</th>
          <th scope="col" className="px-3 py-2 text-right font-medium">Δ MAE vs last close</th>
        </tr></thead>
        <tbody className="divide-y divide-border-subtle">
          {summaries.map((row) => <tr key={row.model_id}>
            <th scope="row" className="px-3 py-2 font-medium">
              {run.result.models.find((model) => model.id === row.model_id)?.label ?? row.model_id}
              <span className="mt-1 block text-[11px] font-normal text-secondary">{row.n} targets{row.model_id === "last_close" && " · benchmark"}</span>
            </th>
            {[row.mae, row.rmse, row.mae_difference_vs_last_close].map((value, index) => <td className="whitespace-nowrap px-2 py-2 text-right font-mono" key={index}><data value={value} title={String(value)}>{formatUsd(value)}</data></td>)}
          </tr>)}
        </tbody>
      </table>
    </div>
    <details className="px-4 py-3 text-xs text-secondary">
      <summary className="cursor-pointer font-medium text-foreground focus-visible:ring-2 focus-visible:ring-focus">How to read these errors</summary>
      <p className="mt-2">MAE is the average absolute error. RMSE gives larger errors more weight. Lower values describe smaller errors in this period. Δ MAE is the model&apos;s MAE minus last-close MAE; a negative value means lower descriptive error, not a trading return or a significance test.</p>
      <p className="mt-2">{run.data_kind === "synthetic_fixture" ? "These are synthetic pipeline checks, not empirical prediction results." : "These exploratory results are not independently point-in-time qualified."}{run.horizon_sessions === 5 && " Five-session targets overlap; the errors are not independent observations."}</p>
    </details>
  </section>;
}
