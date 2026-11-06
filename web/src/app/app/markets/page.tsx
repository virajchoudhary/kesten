import type { Metadata } from "next";

import { MarketWorkspace } from "@/features/markets/market-workspace";

export const metadata: Metadata = { title: "Markets" };

export default function MarketsPage(): React.JSX.Element {
  return <MarketWorkspace />;
}
