import type { Metadata } from "next";

import { MarketWorkspace } from "@/features/markets/market-workspace";
import {
  parseResearchPageSearchParams,
  type ResearchPageSearchParams,
} from "@/features/research/research-navigation";

export const metadata: Metadata = { title: "Markets" };

export default async function MarketsPage({
  searchParams,
}: {
  searchParams: Promise<ResearchPageSearchParams & { view?: string }>;
}): Promise<React.JSX.Element> {
  const params = await searchParams;
  return (
    <MarketWorkspace
      researchQuery={parseResearchPageSearchParams(params)}
      researchView={params.view === "research"}
      researchEnabled={process.env.CADRISYN_WEB_RELEASE_PROFILE !== "demo"}
    />
  );
}
