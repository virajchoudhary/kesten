"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChartNoAxesCombined, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useSession } from "@/features/session/session-provider";

import { AccountSecuritySettings } from "./account-security-settings";

export function AccountSecurityPage(): React.JSX.Element {
  const { state, refresh } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (state.kind === "anonymous") {
      router.replace("/sign-in");
    }
  }, [router, state.kind]);

  if (state.kind === "checking") {
    return (
      <main
        className="flex min-h-dvh items-center justify-center gap-2 bg-canvas text-sm text-secondary"
        role="status"
      >
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Checking session
      </main>
    );
  }

  if (state.kind === "failed") {
    return (
      <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-3 px-5">
        <h1 className="text-lg font-semibold">Account settings unavailable</h1>
        <p className="text-sm text-secondary">{state.error.message}</p>
        <Button className="w-fit" onClick={refresh} variant="outline">
          Retry
        </Button>
      </main>
    );
  }

  if (state.kind === "anonymous") {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-canvas text-sm text-secondary" role="status">
        Sign-in required
      </main>
    );
  }

  return (
    <div className="min-h-dvh bg-canvas text-foreground">
      <a className="skip-link" href="#main-content">
        Skip to account security
      </a>
      <header className="flex min-h-12 flex-wrap items-center gap-3 border-b border-border-subtle bg-surface px-3 py-2 sm:px-4">
        <Link
          aria-label="Cadrisyn markets"
          className="inline-flex items-center gap-2 font-semibold"
          href="/app/markets"
        >
          <ChartNoAxesCombined aria-hidden="true" className="text-accent" size={18} />
          <span>Cadrisyn</span>
        </Link>
        <nav aria-label="Workspace" className="flex min-h-9 items-center gap-4 text-xs">
          <Link className="text-secondary hover:text-foreground" href="/app/markets">
            Markets
          </Link>
          <Link className="text-secondary hover:text-foreground" href="/methodology">
            Methodology
          </Link>
          <Link className="text-secondary hover:text-foreground" href="/data">
            Data
          </Link>
          <Link
            aria-current="page"
            className="font-medium text-accent"
            href="/app/account"
          >
            Account
          </Link>
        </nav>
        <span className="ml-auto hidden max-w-40 truncate text-xs text-secondary sm:block">
          {state.session.user.username}
        </span>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-7 sm:px-8 sm:py-10" id="main-content" tabIndex={-1}>
        <header className="mb-6">
          <p className="text-xs font-medium text-secondary">Workspace profile</p>
          <h1 className="mt-1 text-2xl font-semibold leading-8">Account security</h1>
          <p className="mt-2 text-sm text-secondary">
            Signed in as <span className="font-medium text-foreground">{state.session.user.username}</span>
          </p>
        </header>
        <AccountSecuritySettings session={state.session} />
      </main>
    </div>
  );
}
