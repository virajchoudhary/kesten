import type { ReactNode } from "react";

import { PublicHeader } from "@/components/public-header";

export function PublicPageFrame({ children }: { children: ReactNode }): React.JSX.Element {
  return (
    <div className="min-h-dvh bg-canvas text-foreground">
      <PublicHeader />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-8 sm:py-12">{children}</main>
    </div>
  );
}
