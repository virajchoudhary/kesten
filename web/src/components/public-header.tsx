import Link from "next/link";
import { ChartNoAxesCombined } from "lucide-react";

export function PublicHeader(): React.JSX.Element {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border-subtle bg-surface px-4 sm:px-8">
      <Link aria-label="Cadrisyn home" className="inline-flex items-center gap-2 font-semibold" href="/">
        <ChartNoAxesCombined aria-hidden="true" className="text-accent" size={18} />
        <span>Cadrisyn</span>
      </Link>
      <nav aria-label="Main" className="flex items-center gap-1">
        <Link
          className="rounded-control px-3 py-2 text-sm text-secondary hover:bg-raised hover:text-foreground"
          href="/methodology"
        >
          Methodology
        </Link>
        <Link
          className="rounded-control px-3 py-2 text-sm text-secondary hover:bg-raised hover:text-foreground"
          href="/data"
        >
          Data
        </Link>
        <Link
          className="ml-1 rounded-control bg-action px-3 py-2 text-sm font-medium text-on-action"
          href="/app/markets"
        >
          Workspace
        </Link>
      </nav>
    </header>
  );
}
