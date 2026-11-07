import type { Metadata } from "next";
import Link from "next/link";

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
  if (process.env.CADRISYN_WEB_RELEASE_PROFILE === "demo") {
    return (
      <main className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center gap-4 px-5">
        <h1 className="text-xl font-semibold">Demo-only workspace</h1>
        <p className="text-secondary">
          Private datasets, saved evaluations, and historical research are unavailable in this release profile.
        </p>
        <Link
          className="w-fit rounded-control bg-action px-4 py-3 text-on-action focus-visible:ring-2 focus-visible:ring-focus"
          href="/app/markets"
        >
          Open demo markets
        </Link>
      </main>
    );
  }
  const query = parseResearchPageSearchParams(await searchParams);
  return <ResearchWorkspace {...query} />;
}
