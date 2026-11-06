import type { Metadata } from "next";

import { PublicPageFrame } from "@/components/public-page-frame";

export const metadata: Metadata = { title: "Data" };

export default function DataPage(): React.JSX.Element {
  return (
    <PublicPageFrame>
      <article className="space-y-8">
        <header className="max-w-3xl">
          <p className="text-xs font-medium text-secondary">Coverage and provenance</p>
          <h1 className="mt-2 text-2xl font-semibold leading-8">Market data</h1>
          <p className="mt-3 text-sm leading-6 text-secondary">
            The workspace defaults to synthetic daily history. Every chart shows its data mode,
            source, session date, fetch time, price basis, and freshness beside the observations.
          </p>
        </header>

        <dl className="grid max-w-3xl grid-cols-1 border-y border-border-subtle sm:grid-cols-[180px_minmax(0,1fr)]">
          <dt className="border-b border-border-subtle py-3 text-sm text-secondary sm:border-0">
            Default mode
          </dt>
          <dd className="m-0 border-b border-border-subtle py-3 text-sm sm:border-0">
            Deterministic synthetic demonstration bars on U.S. exchange sessions. They are not
            observed market prices, quotes, or investment results.
          </dd>
          <dt className="border-b border-border-subtle py-3 text-sm text-secondary sm:border-0">
            Optional mode
          </dt>
          <dd className="m-0 border-b border-border-subtle py-3 text-sm sm:border-0">
            An operator may acknowledge and enable delayed daily history for local personal research. The current
            adapter uses Yahoo Finance through yfinance; provider responses carry their own
            source and adjustment details. This adapter is disabled in production; no licensed live feed is configured.
          </dd>
          <dt className="border-b border-border-subtle py-3 text-sm text-secondary sm:border-0">
            Freshness
          </dt>
          <dd className="m-0 border-b border-border-subtle py-3 text-sm sm:border-0">
            The page shows the latest exchange session and fetch time separately. The adapter
            does not guarantee a fixed delay and is not a real-time feed.
          </dd>
          <dt className="py-3 text-sm text-secondary">Entitlement</dt>
          <dd className="m-0 py-3 text-sm">
            A local server setting is not a display or redistribution license. Data rights,
            retention, export, and any external use require separate review and approval.
          </dd>
        </dl>

        <section className="max-w-3xl space-y-3 border-t border-border-subtle pt-5">
          <h2 className="text-base font-semibold">Unavailable data</h2>
          <p className="text-sm leading-6 text-secondary">
            When a delayed-data request fails, the workspace reports the failure. It does not
            replace that response with synthetic history. Select Demo data only when you intend
            to inspect the synthetic demonstration series.
          </p>
        </section>
      </article>
    </PublicPageFrame>
  );
}
