import Link from "next/link";
import { brand } from "@/lib/brand";

export function PublicHeader(): React.JSX.Element {
  return (
    <header className="public-header flex h-14 min-w-0 gap-3 items-center justify-between border-b border-border-subtle bg-surface px-4 sm:px-8">
      <Link aria-label={`${brand.name} home`} className="terminal-wordmark" href="/">
        <span aria-hidden="true" className="brand-mark"><span /><span /><span /></span>
        <span>{brand.name}</span>
      </Link>
      <nav aria-label="Main" className="flex min-w-0 items-center gap-1 overflow-x-auto">
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
