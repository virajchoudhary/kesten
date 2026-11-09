"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LoaderCircle } from "lucide-react";
import { TerminalHeader } from "@/components/terminal-header";

import { Button } from "@/components/ui/button";
import { useSession } from "@/features/session/session-provider";

import { AccountSecuritySettings } from "./account-security-settings";
import { normalizeAccountError } from "./account-form-utils";

export function AccountSecurityPage(): React.JSX.Element {
  const { state, refresh, signOut } = useSession();
  const router = useRouter();
  const [signOutPending, setSignOutPending] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);

  useEffect(() => {
    if (state.kind === "anonymous") {
      router.replace("/sign-in");
    }
  }, [router, state.kind]);

  async function handleSignOut(): Promise<void> {
    setSignOutPending(true);
    setSignOutError(null);
    try {
      await signOut();
    } catch (error: unknown) {
      setSignOutError(
        normalizeAccountError(error, "Sign out failed. Try again.").message,
      );
    } finally {
      setSignOutPending(false);
    }
  }

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
      <main
        className="flex min-h-dvh items-center justify-center bg-canvas text-sm text-secondary"
        role="status"
      >
        Sign-in required
      </main>
    );
  }

  return (
    <div className="min-h-dvh bg-canvas text-foreground">
      <a className="skip-link" href="#main-content">
        Skip to account security
      </a>
      <TerminalHeader
        active="Account"
        username={state.session.user.username}
        onSignOut={() => void handleSignOut()}
        signOutPending={signOutPending}
      />
      {signOutError && (
        <p
          role="alert"
          className="border-b border-negative/40 bg-negative/10 px-4 py-2 text-sm text-negative"
        >
          {signOutError}
        </p>
      )}

      <main
        className="mx-auto max-w-4xl px-4 py-7 sm:px-8 sm:py-10"
        id="main-content"
        tabIndex={-1}
      >
        <header className="mb-6">
          <p className="text-xs font-medium text-secondary">
            Workspace profile
          </p>
          <h1 className="mt-1 text-2xl font-semibold leading-8">
            Account security
          </h1>
          <p className="mt-2 text-sm text-secondary">
            Signed in as{" "}
            <span className="font-medium text-foreground">
              {state.session.user.username}
            </span>
          </p>
          <nav
            aria-label="Research guidance"
            className="mt-3 flex gap-4 text-xs text-accent"
          >
            <Link href="/methodology">Methodology</Link>
            <Link href="/data">Data and licensing</Link>
          </nav>
        </header>
        <AccountSecuritySettings session={state.session} />
      </main>
    </div>
  );
}
