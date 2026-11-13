import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { MarketBarsTable } from "./market-bars-table";
import type { Instrument } from "@/lib/api/schemas";

it("references its controlled region only while the table is mounted", () => {
  const instrument: Instrument = { id: "xnas-aapl", symbol: "AAPL", name: "Apple Inc.", exchange: "XNAS", currency: "USD", timezone: "America/New_York" };
  const onOpenChange = vi.fn();
  const { rerender } = render(<MarketBarsTable bars={[]} instrument={instrument} open={false} onOpenChange={onOpenChange} />);
  expect(screen.getByRole("button", {name: "Show data table"})).not.toHaveAttribute("aria-controls");
  rerender(<MarketBarsTable bars={[]} instrument={instrument} open onOpenChange={onOpenChange} />);
  const control = screen.getByRole("button", {name: "Hide data table"});
  expect(control).toHaveAttribute("aria-controls", screen.getByRole("region", {name: "AAPL daily observations"}).id);
});
