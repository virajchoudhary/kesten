"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import {
  ArrowUpRight,
  LoaderCircle,
  LogOut,
  Moon,
  Sun,
  UserRound,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { brand } from "@/lib/brand";
import { BrandMark } from "./brand-mark";

export function TerminalHeader({
  username,
  onSignOut,
  signOutPending,
  active = "Markets",
}: {
  username: string;
  onSignOut: () => void;
  signOutPending: boolean;
  active?: "Markets" | "Research";
}): React.JSX.Element {
  const { resolvedTheme, setTheme } = useTheme();
  const nextTheme = resolvedTheme === "dark" ? "light" : "dark";
  return (
    <header className="terminal-header">
      <Link
        aria-label={`${brand.name} markets`}
        href="/app/markets"
        className="terminal-wordmark"
      >
        <BrandMark />
        <span className="brand-name-wide">{brand.name}</span>
        <span className="brand-name-short">{brand.shortName}</span>
      </Link>
      <nav aria-label="Workspace" className="terminal-navigation">
        {[
          ["/app/markets", "Markets"],
          ["/app/research", "Research"],
        ].map(([href, label]) => (
          <Link
            key={href}
            href={href}
            aria-current={active === label ? "page" : undefined}
          >
            {label}
          </Link>
        ))}
      </nav>
      <div className="terminal-utilities">
        <Link className="terminal-methodology" href="/methodology">
          Methodology <ArrowUpRight size={12} aria-hidden="true" />
        </Link>
        <Link
          href="/app/account"
          aria-label="Account"
          className="terminal-account"
          title={username}
        >
          <UserRound className="account-icon" size={15} aria-hidden="true" />
          <span className="account-label">Account</span>
        </Link>
        <Button
          aria-label={`Use ${nextTheme} theme`}
          size="icon"
          variant="ghost"
          onClick={() => setTheme(nextTheme)}
        >
          {nextTheme === "light" ? <Sun size={16} /> : <Moon size={16} />}
        </Button>
        <Button
          aria-label="Sign out"
          size="icon"
          variant="ghost"
          disabled={signOutPending}
          onClick={onSignOut}
        >
          {signOutPending ? (
            <LoaderCircle size={15} className="animate-spin" />
          ) : (
            <LogOut size={15} />
          )}
        </Button>
      </div>
    </header>
  );
}
