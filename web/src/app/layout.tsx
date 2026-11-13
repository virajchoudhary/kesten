import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";

import { Providers } from "@/components/providers";
import { brand } from "@/lib/brand";

import "./globals.css";
import "./terminal-polish.css";
import "@/features/research/research-polish.css";

export const metadata: Metadata = {
  applicationName: brand.name,
  title: {
    default: `${brand.name} | Markets`,
    template: `%s | ${brand.name}`,
  },
  description: "A private market research workspace.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): React.JSX.Element {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
