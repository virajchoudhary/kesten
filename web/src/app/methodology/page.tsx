import type { Metadata } from "next";
import Link from "next/link";

import { PublicPageFrame } from "@/components/public-page-frame";

export const metadata: Metadata = { title: "Methodology" };

export default function MethodologyPage(): React.JSX.Element {
  return (
    <PublicPageFrame>
      <article className="space-y-8">
        <header className="max-w-3xl">
          <p className="text-xs font-medium text-secondary">
            Calculation notes
          </p>
          <h1 className="mt-2 text-2xl font-semibold leading-8">Methodology</h1>
          <p className="mt-3 text-sm leading-6 text-secondary">
            Daily OHLCV, SMA 20/50 and RSI 14 come from the Django API. Optional
            EMA and Bollinger studies are calculated in the browser from those
            returned daily closes. Display studies never change price
            observations or saved research results.
          </p>
        </header>

        <section className="max-w-3xl space-y-3 border-t border-border-subtle pt-5">
          <h2 className="text-base font-semibold">Daily observations</h2>
          <p className="text-sm leading-6 text-secondary">
            Each bar represents one exchange session date. The date is kept as a
            session date instead of being shifted to a browser-local midnight.
            The selected range changes the visible daily history; it does not
            change the interval.
          </p>
        </section>

        <section className="max-w-3xl space-y-3 border-t border-border-subtle pt-5">
          <h2 className="text-base font-semibold">Technical indicators</h2>
          <dl className="grid grid-cols-1 gap-y-3 sm:grid-cols-[140px_minmax(0,1fr)]">
            <dt className="text-sm font-medium">SMA 20 and 50</dt>
            <dd className="m-0 text-sm leading-6 text-secondary">
              Arithmetic means of the latest 20 or 50 daily closes. Values
              appear only after a full window is available.
            </dd>
            <dt className="text-sm font-medium">RSI 14</dt>
            <dd className="m-0 text-sm leading-6 text-secondary">
              Relative Strength Index from 14 daily close changes. The initial
              average gain and loss use 14 observations; subsequent values use
              Wilder smoothing. Index values range from 0 to 100.
            </dd>
            <dt className="text-sm font-medium">Volume</dt>
            <dd className="m-0 text-sm leading-6 text-secondary">
              The bar value is provided by the selected dataset. Synthetic demo
              volume is not observed trading volume.
            </dd>
            <dt className="text-sm font-medium">EMA</dt>
            <dd className="m-0 text-sm leading-6 text-secondary">
              The arithmetic mean of the first full window seeds the series;
              subsequent closes use weight 2/(period+1). The configurable period
              is 2–200 returned sessions.
            </dd>
            <dt className="text-sm font-medium">Bollinger bands</dt>
            <dd className="m-0 text-sm leading-6 text-secondary">
              Rolling mean plus/minus a configurable multiple of the population
              standard deviation, using a full 2–200 session window. Bands
              describe historical dispersion. They are not forecast confidence
              intervals.
            </dd>
          </dl>
        </section>

        <section className="max-w-3xl space-y-3 border-t border-border-subtle pt-5">
          <h2 className="text-base font-semibold">
            Scales, comparisons and measurement
          </h2>
          <p className="text-sm leading-6 text-secondary">
            Percentage and indexed scales anchor all price series and overlays
            to the first returned close. Indexed comparisons use only common
            session dates and normalize both closes to 100 at the displayed
            common anchor. Currency, provider, data category and price basis
            must match; no FX conversion or forward filling is performed.
          </p>
          <p className="text-sm leading-6 text-secondary">
            The ruler measures two selected session closes and the number of
            session intervals between them. Price levels are temporary
            annotations, not orders. Demo comparisons remain synthetic
            demonstrations, not empirical market performance.
          </p>
        </section>

        <section className="max-w-3xl space-y-3 border-y border-border-subtle py-5">
          <h2 className="text-base font-semibold">Reference forecasts</h2>
          <p className="text-sm leading-6 text-secondary">
            Private research compares last-close and expanding
            historical-log-mean references over one or five exchange sessions.
            Frozen daily datasets retain source, availability, corporate-action
            and version information. Prices use initial-share units with causal
            split adjustment; dividends are excluded.
          </p>
          <p className="text-sm leading-6 text-secondary">
            Chronological validation and test results use only inputs available
            at each origin. Synthetic fixture results verify the pipeline and
            establish no empirical forecasting performance. No advanced ML
            model, probability interval or trading strategy is approved.
            Original forecasting and RL implementations remain isolated research
            code.
          </p>
          <Link
            className="inline-flex min-h-11 items-center text-sm text-accent underline"
            href="/app/research"
          >
            Open forecast research
          </Link>
        </section>
        <footer className="max-w-3xl space-y-2 text-xs leading-5 text-secondary">
          <p>
            TradingView Lightweight Charts™
            <br />
            Copyright (с) 2025 TradingView, Inc.{" "}
            <a className="underline" href="https://www.tradingview.com/">
              TradingView
            </a>
          </p>
          <p>
            <a
              className="underline"
              href="/licenses/lightweight-charts-NOTICE.txt"
            >
              Chart notice
            </a>
            {" · "}
            <a
              className="underline"
              href="/licenses/lightweight-charts-LICENSE.txt"
            >
              Chart license
            </a>
            {" · "}
            <a className="underline" href="/licenses/inter-LICENSE.txt">
              Inter license
            </a>
            {" · "}
            <a className="underline" href="/licenses/ibm-plex-mono-LICENSE.txt">
              IBM Plex license
            </a>
          </p>
        </footer>
      </article>
    </PublicPageFrame>
  );
}
