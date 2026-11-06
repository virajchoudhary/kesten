"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { Check, LoaderCircle, LockKeyhole } from "lucide-react";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSession } from "@/features/session/session-provider";
import { ApiError } from "@/lib/api/client";

import {
  AccountTokenSchema,
  acceptInvitation,
  confirmPasswordReset,
} from "./account-api";
import { fieldError, normalizeAccountError } from "./account-form-utils";

const PasswordPairSchema = z
  .object({
    newPassword: z.string().min(1, "Enter a new password.").max(256, "Password must be 256 characters or fewer."),
    confirmPassword: z.string().min(1, "Confirm your new password.").max(256, "Password must be 256 characters or fewer."),
  })
  .superRefine((values, context) => {
    if (values.newPassword !== values.confirmPassword) {
      context.addIssue({
        code: "custom",
        message: "The passwords do not match.",
        path: ["confirmPassword"],
      });
    }
  });

type TokenFormPurpose = "invitation" | "password-reset";

type TokenState =
  | { kind: "reading" }
  | { kind: "ready"; token: string }
  | { kind: "missing" }
  | { kind: "complete" };

type FragmentRead =
  | { kind: "unread" }
  | { kind: "read"; token: string | null };

type PasswordFieldErrors = {
  newPassword: string | null;
  confirmPassword: string | null;
};

function emptyFieldErrors(): PasswordFieldErrors {
  return { newPassword: null, confirmPassword: null };
}

function consumeFragmentToken(): string | null {
  const fragment = window.location.hash;
  const rawToken = fragment.startsWith("#")
    ? new URLSearchParams(fragment.slice(1)).get("token")
    : null;

  window.history.replaceState(window.history.state, "", window.location.pathname);

  const parsed = AccountTokenSchema.safeParse(rawToken);
  return parsed.success ? parsed.data : null;
}

export function TokenPasswordForm({
  purpose,
}: {
  purpose: TokenFormPurpose;
}): React.JSX.Element {
  const { state: sessionState, refresh } = useSession();
  const [tokenState, setTokenState] = useState<TokenState>({ kind: "reading" });
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [fieldErrors, setFieldErrors] = useState<PasswordFieldErrors>(emptyFieldErrors);
  const fragmentRead = useRef<FragmentRead>({ kind: "unread" });

  useEffect(() => {
    if (fragmentRead.current.kind === "unread") {
      fragmentRead.current = { kind: "read", token: consumeFragmentToken() };
    }
    const token = fragmentRead.current.token;
    const timer = window.setTimeout(() => {
      setTokenState(token === null ? { kind: "missing" } : { kind: "ready", token });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [fragmentRead]);

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setApiError(null);

    const parsed = PasswordPairSchema.safeParse({ newPassword, confirmPassword });
    if (!parsed.success) {
      const newPasswordIssue = parsed.error.issues.find((issue) => issue.path[0] === "newPassword");
      const confirmPasswordIssue = parsed.error.issues.find(
        (issue) => issue.path[0] === "confirmPassword",
      );
      setFieldErrors({
        newPassword: newPasswordIssue?.message ?? null,
        confirmPassword: confirmPasswordIssue?.message ?? null,
      });
      return;
    }

    setFieldErrors(emptyFieldErrors());
    if (tokenState.kind !== "ready") {
      return;
    }
    if (sessionState.kind !== "anonymous" && sessionState.kind !== "authenticated") {
      return;
    }

    setPending(true);
    try {
      const payload = {
        token: tokenState.token,
        new_password: parsed.data.newPassword,
        confirm_password: parsed.data.confirmPassword,
      };
      if (purpose === "invitation") {
        await acceptInvitation(payload, sessionState.session.csrf_token);
      } else {
        await confirmPasswordReset(payload, sessionState.session.csrf_token);
      }
      setNewPassword("");
      setConfirmPassword("");
      setTokenState({ kind: "complete" });
    } catch (error: unknown) {
      const normalized = normalizeAccountError(
        error,
        "The account request could not be completed. Try again.",
      );
      setApiError(normalized);
      if (normalized.code === "csrf_failed") {
        refresh();
      }
      if (
        normalized.code === "invalid_invitation" ||
        normalized.code === "invalid_reset_token"
      ) {
        setTokenState({ kind: "missing" });
      }
    } finally {
      setPending(false);
    }
  }

  if (sessionState.kind === "checking") {
    return (
      <div className="flex min-h-32 items-center justify-center gap-2 text-sm text-secondary" role="status">
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Checking session
      </div>
    );
  }

  if (sessionState.kind === "failed") {
    return (
      <div className="space-y-3" role="alert">
        <p className="text-sm text-negative">{sessionState.error.message}</p>
        <Button onClick={refresh} variant="outline">
          Retry session check
        </Button>
      </div>
    );
  }

  if (tokenState.kind === "reading") {
    return (
      <div className="flex min-h-32 items-center justify-center gap-2 text-sm text-secondary" role="status">
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Preparing account verification
      </div>
    );
  }

  if (tokenState.kind === "missing") {
    return (
      <div className="space-y-3">
        <p className="text-sm text-negative" role="alert">
          {purpose === "invitation"
            ? "This invitation is invalid or expired. Request a new invitation from your account operator."
            : "This reset link is invalid or expired. Request a new reset link from your account operator."}
        </p>
        {apiError?.requestId && (
          <p className="font-mono text-xs text-secondary">Request {apiError.requestId}</p>
        )}
        <Link className="inline-flex text-sm font-medium text-accent underline" href="/sign-in">
          Return to sign in
        </Link>
      </div>
    );
  }

  if (tokenState.kind === "complete") {
    return (
      <div className="space-y-4">
        <p className="flex items-center gap-2 text-sm text-positive" role="status">
          <Check aria-hidden="true" size={16} />
          {purpose === "invitation"
            ? "Your account is active. Sign in with your new password."
            : "Your password has been reset. Sign in with your new password."}
        </p>
        <Link
          className="inline-flex min-h-11 items-center text-sm font-medium text-accent underline underline-offset-4"
          href="/sign-in"
        >
          Continue to sign in
        </Link>
      </div>
    );
  }

  const newPasswordError =
    fieldErrors.newPassword ?? fieldError(apiError, "new_password");
  const confirmPasswordError =
    fieldErrors.confirmPassword ?? fieldError(apiError, "confirm_password");

  return (
    <form className="space-y-4" onSubmit={(event) => void submit(event)}>
      <div className="space-y-1.5">
        <label className="text-sm font-medium" htmlFor="account-new-password">
          New password
        </label>
        <Input
          autoComplete="new-password"
          aria-describedby={newPasswordError ? "account-new-password-error" : undefined}
          aria-invalid={newPasswordError !== null}
          disabled={pending}
          id="account-new-password"
          name="new_password"
          onChange={(event) => setNewPassword(event.currentTarget.value)}
          required
          type="password"
          value={newPassword}
        />
        {newPasswordError && (
          <p className="text-xs text-negative" id="account-new-password-error">
            {newPasswordError}
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium" htmlFor="account-confirm-password">
          Confirm new password
        </label>
        <Input
          autoComplete="new-password"
          aria-describedby={confirmPasswordError ? "account-confirm-password-error" : undefined}
          aria-invalid={confirmPasswordError !== null}
          disabled={pending}
          id="account-confirm-password"
          name="confirm_password"
          onChange={(event) => setConfirmPassword(event.currentTarget.value)}
          required
          type="password"
          value={confirmPassword}
        />
        {confirmPasswordError && (
          <p className="text-xs text-negative" id="account-confirm-password-error">
            {confirmPasswordError}
          </p>
        )}
      </div>

      {apiError && (
        <div className="rounded-control border border-negative/40 bg-negative/10 p-3" role="alert">
          <p className="text-sm text-negative">{apiError.message}</p>
          {apiError.requestId && (
            <p className="mt-1 font-mono text-xs text-secondary">Request {apiError.requestId}</p>
          )}
        </div>
      )}

      <Button className="w-full" disabled={pending} type="submit" variant="primary">
        {pending ? (
          <>
            <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
            {purpose === "invitation" ? "Activating account" : "Resetting password"}
          </>
        ) : (
          <>
            <LockKeyhole aria-hidden="true" size={16} />
            {purpose === "invitation" ? "Activate account" : "Reset password"}
          </>
        )}
      </Button>
    </form>
  );
}
