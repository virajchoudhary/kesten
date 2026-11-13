import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarketEvidencePanel } from "./market-evidence-panel";
import type { Instrument, Provenance } from "@/lib/api/schemas";

const instrument: Instrument = {
  id: "xnas-aapl", symbol: "AAPL", name: "Apple Inc.", exchange: "XNAS",
  currency: "USD", timezone: "America/New_York",
};
const provenance: Provenance = {
  data_mode: "demo", source_id: "fixture", source_label: "Synthetic demonstration dataset",
  as_of: "2026-10-30", fetched_at: "2026-11-05T13:00:00Z", price_basis: "synthetic",
  freshness_state: "stale", market_state: "unknown", delay_seconds: null,
  snapshot_id: "fixture-snapshot", disclaimer: "Synthetic prices, not observed market prices.",
};

describe("market evidence", () => {
  it("renders the exchange-local fetch time with its time zone", () => {
    render(<MarketEvidencePanel instrument={instrument} provenance={provenance} marketDataEnabled={false} />);
    expect(screen.getByText(/Nov 5, 2026.*8:00.*EST/)).toBeVisible();
    expect(screen.getByText(provenance.disclaimer)).toBeVisible();
    expect(screen.getByText("Demo data")).toBeVisible();
  });
});
