"use client";

import type { ReactNode } from "react";
import { ThemeProvider } from "next-themes";

import { SessionProvider } from "@/features/session/session-provider";
import { TooltipProvider } from "@/components/ui/tooltip";

export function Providers({ children }: { children: ReactNode }): React.JSX.Element {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" disableTransitionOnChange enableSystem storageKey="cadrisyn-theme">
      <SessionProvider>
        <TooltipProvider delayDuration={400}>{children}</TooltipProvider>
      </SessionProvider>
    </ThemeProvider>
  );
}
