import type { Metadata } from "next";

import { ResearchWorkspace } from "@/features/research/research-workspace";
import { parseResearchPageSearchParams } from "@/features/research/research-navigation";

export const metadata: Metadata = { title: "Research" };

type ResearchPageProps = {
  searchParams: Promise<{
    run?: string | string[] | undefined;
    compare?: string | string[] | undefined;
    instrument?: string | string[] | undefined;
    method?: string | string[] | undefined;
  }>;
};

export default async function ResearchPage({
  searchParams,
}: ResearchPageProps): Promise<React.JSX.Element> {
  const query = parseResearchPageSearchParams(await searchParams);
  return <ResearchWorkspace {...query} />;
}
