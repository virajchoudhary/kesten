import { useId } from "react";

import { Badge } from "@/components/ui/badge";
import type { Instrument, Provenance } from "@/lib/api/schemas";

function formatSessionDate(value: string): string {
  const date = new Date(`${value}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(date);
}

function formatFetchedAt(value: string, timezone: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
    timeZone: timezone,
  }).format(new Date(value));
}

function formatFreshness(provenance: Provenance): string {
  if (provenance.data_mode === "demo") {
    return "Not applicable to synthetic data";
  }
  return provenance.freshness_state[0]?.toUpperCase() + provenance.freshness_state.slice(1);
}

function formatMarketState(provenance: Provenance): string {
  if (provenance.market_state === "unknown") {
    return provenance.data_mode === "demo" ? "Not applicable" : "Not reported";
  }
  return provenance.market_state === "open" ? "Open" : "Closed";
}

function formatPriceBasis(value: string): string {
  switch (value) {
    case "synthetic":
      return "Synthetic series";
    case "split_and_dividend_adjusted":
      return "Split and dividend adjusted";
    default:
      return value;
  }
}

export function MarketEvidencePanel({
  instrument,
  provenance,
  marketDataEnabled,
}: {
  instrument: Instrument;
  provenance: Provenance;
  marketDataEnabled: boolean;
}): React.JSX.Element {
  const titleId = useId();
  const isDemo = provenance.data_mode === "demo";
  const facts = [
    { label: "Source", value: provenance.source_label },
    { label: "Last session", value: formatSessionDate(provenance.as_of) },
    { label: "Fetched", value: formatFetchedAt(provenance.fetched_at, instrument.timezone) },
    { label: "Price basis", value: formatPriceBasis(provenance.price_basis) },
    { label: "Freshness", value: formatFreshness(provenance) },
    { label: "Market session", value: formatMarketState(provenance) },
    {
      label: "Delay",
      value: provenance.delay_seconds === null
        ? "No guaranteed delay"
        : `${provenance.delay_seconds.toLocaleString("en-US")} seconds`,
    },
  ];

  return (
    <section aria-labelledby={titleId} className="min-w-0">
      <div className="flex h-12 items-center justify-between border-b border-border-subtle px-4">
        <h2 className="text-sm font-semibold" id={titleId}>
          Data evidence
        </h2>
        <Badge variant={isDemo ? "demo" : "neutral"}>
          {isDemo ? "Demo data" : "Delayed data"}
        </Badge>
      </div>

      <dl className="grid grid-cols-[minmax(92px,0.8fr)_minmax(0,1.2fr)] gap-x-3 gap-y-3 px-4 py-4 text-xs">
        {facts.map(({ label, value }) => (
          <div className="contents" key={label}>
            <dt className="text-secondary">{label}</dt>
            <dd className="m-0 min-w-0 break-words text-right text-foreground">{value}</dd>
          </div>
        ))}
      </dl>

      <div className="space-y-2 border-t border-border-subtle px-4 py-3">
        <p
          className={`text-xs leading-5 ${isDemo ? "text-warning" : "text-secondary"}`}
          role={isDemo ? "status" : undefined}
        >
          {provenance.disclaimer}
        </p>
        {!marketDataEnabled && (
          <p className="text-xs leading-5 text-secondary">
            Delayed data is not enabled for this environment.
          </p>
        )}
        <div className="space-y-1 pt-1">
          <p className="text-[11px] text-secondary">Snapshot</p>
          <code className="block break-all font-mono text-[11px] text-secondary">
            {provenance.snapshot_id}
          </code>
          <p className="break-all font-mono text-[11px] text-secondary">
            {provenance.source_id}
          </p>
        </div>
      </div>
    </section>
  );
}
