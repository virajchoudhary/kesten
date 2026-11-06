import type { Metadata } from "next";

import { ResearchWorkspace } from "@/features/research/research-workspace";
import { ResearchRunIdSchema } from "@/features/research/research-schemas";

export const metadata: Metadata = { title: "Research" };

type ResearchPageProps = {
  searchParams: Promise<{ run?: string | string[] | undefined }>;
};

export default async function ResearchPage({
  searchParams,
}: ResearchPageProps): Promise<React.JSX.Element> {
  const { run } = await searchParams;
  const parsedRunId = ResearchRunIdSchema.safeParse(typeof run === "string" ? run : null);

  return <ResearchWorkspace requestedRunId={parsedRunId.success ? parsedRunId.data : null} />;
}
