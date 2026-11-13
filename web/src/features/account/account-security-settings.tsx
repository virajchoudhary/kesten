"use client";

import { useState, type FormEvent } from "react";
import { Check, LoaderCircle, LogOut, LockKeyhole, ShieldCheck } from "lucide-react";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSession } from "@/features/session/session-provider";
import { ApiError } from "@/lib/api/client";
import type { AuthenticatedSession } from "@/lib/api/schemas";

import {
  ChangePasswordRequestSchema,
  changePassword,
  revokeOtherSessions,
} from "./account-api";
import { fieldError, normalizeAccountError } from "./account-form-utils";

const PasswordFormSchema = z
  .object({
    currentPassword: z.string().min(1, "Enter your current password.").max(256, "Password must be 256 characters or fewer."),
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

type PendingAction = "password" | "sessions" | null;

type PasswordFieldErrors = {
  currentPassword: string | null;
  newPassword: string | null;
  confirmPassword: string | null;
};

function emptyFieldErrors(): PasswordFieldErrors {
  return {
    currentPassword: null,
    newPassword: null,
    confirmPassword: null,
  };
}

function AccountError({ error }: { error: ApiError }): React.JSX.Element {
  const { refresh } = useSession();

  return (
    <div className="rounded-control border border-negative/40 bg-negative/10 p-3" role="alert">
      <p className="text-sm text-negative">{error.message}</p>
      {error.requestId && (
        <p className="mt-1 font-mono text-xs text-secondary">Request {error.requestId}</p>
      )}
      {error.code === "csrf_failed" && (
        <Button className="mt-2" onClick={refresh} size="sm" variant="outline">
          Refresh security session
        </Button>
      )}
    </div>
  );
}

export function AccountSecuritySettings({
  session,
}: {
  session: AuthenticatedSession;
}): React.JSX.Element {
  const { refresh } = useSession();
  const [csrfOverride, setCsrfOverride] = useState<{
    sessionToken: string;
    requestToken: string;
  } | null>(null);
  const csrfToken =
    csrfOverride?.sessionToken === session.csrf_token
      ? csrfOverride.requestToken
      : session.csrf_token;
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pending, setPending] = useState<PendingAction>(null);
  const [passwordError, setPasswordError] = useState<ApiError | null>(null);
  const [sessionsError, setSessionsError] = useState<ApiError | null>(null);
  const [fieldErrors, setFieldErrors] = useState<PasswordFieldErrors>(emptyFieldErrors);
  const [passwordNotice, setPasswordNotice] = useState<string | null>(null);
  const [sessionsNotice, setSessionsNotice] = useState<string | null>(null);

  async function submitPassword(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setPasswordError(null);
    setPasswordNotice(null);

    const parsed = PasswordFormSchema.safeParse({
      currentPassword,
      newPassword,
      confirmPassword,
    });
    if (!parsed.success) {
      const currentPasswordIssue = parsed.error.issues.find(
        (issue) => issue.path[0] === "currentPassword",
      );
      const newPasswordIssue = parsed.error.issues.find((issue) => issue.path[0] === "newPassword");
      const confirmPasswordIssue = parsed.error.issues.find(
        (issue) => issue.path[0] === "confirmPassword",
      );
      setFieldErrors({
        currentPassword: currentPasswordIssue?.message ?? null,
        newPassword: newPasswordIssue?.message ?? null,
        confirmPassword: confirmPasswordIssue?.message ?? null,
      });
      return;
    }

    setFieldErrors(emptyFieldErrors());
    const request = ChangePasswordRequestSchema.safeParse({
      current_password: parsed.data.currentPassword,
      new_password: parsed.data.newPassword,
      confirm_password: parsed.data.confirmPassword,
    });
    if (!request.success) {
      setPasswordError(
        new ApiError({
          status: 0,
          code: "invalid_request",
          message: "Review the account form fields and try again.",
        }),
      );
      return;
    }

    setPending("password");
    try {
      await changePassword(request.data, csrfToken);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordNotice("Password updated. This session remains active.");
    } catch (error: unknown) {
      const normalized = normalizeAccountError(
        error,
        "The password could not be updated. Try again.",
      );
      setPasswordError(normalized);
      if (normalized.status === 401 || normalized.code === "not_authenticated") {
        refresh();
      }
    } finally {
      setPending(null);
    }
  }

  async function revokeSessions(): Promise<void> {
    setSessionsError(null);
    setSessionsNotice(null);
    setPending("sessions");
    try {
      const response = await revokeOtherSessions(csrfToken);
      setCsrfOverride({
        sessionToken: session.csrf_token,
        requestToken: response.csrf_token,
      });
      setSessionsNotice("Other sessions have been signed out. This session remains active.");
    } catch (error: unknown) {
      const normalized = normalizeAccountError(
        error,
        "Other sessions could not be revoked. Try again.",
      );
      setSessionsError(normalized);
      if (normalized.status === 401 || normalized.code === "not_authenticated") {
        refresh();
      }
    } finally {
      setPending(null);
    }
  }

  const currentPasswordError =
    fieldErrors.currentPassword ?? fieldError(passwordError, "current_password");
  const newPasswordError =
    fieldErrors.newPassword ?? fieldError(passwordError, "new_password");
  const confirmPasswordError =
    fieldErrors.confirmPassword ?? fieldError(passwordError, "confirm_password");

  return (
    <div className="divide-y divide-border-subtle border-y border-border-subtle">
      <section aria-labelledby="change-password-title" className="space-y-5 py-6">
        <header className="max-w-2xl">
          <h2 className="flex items-center gap-2 text-base font-semibold" id="change-password-title">
            <LockKeyhole aria-hidden="true" className="text-accent" size={17} />
            Change password
          </h2>
          <p className="mt-1 text-sm text-secondary">
            Verify your current password before choosing a replacement.
          </p>
        </header>

        <form className="max-w-xl space-y-4" onSubmit={(event) => void submitPassword(event)}>
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="account-current-password">
              Current password
            </label>
            <Input
              autoComplete="current-password"
              aria-describedby={currentPasswordError ? "account-current-password-error" : undefined}
              aria-invalid={currentPasswordError !== null}
              disabled={pending !== null}
              id="account-current-password"
              name="current_password"
              onChange={(event) => setCurrentPassword(event.currentTarget.value)}
              required
              type="password"
              value={currentPassword}
            />
            {currentPasswordError && (
              <p className="text-xs text-negative" id="account-current-password-error">
                {currentPasswordError}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="account-change-new-password">
              New password
            </label>
            <Input
              autoComplete="new-password"
              aria-describedby={newPasswordError ? "account-change-new-password-error" : undefined}
              aria-invalid={newPasswordError !== null}
              disabled={pending !== null}
              id="account-change-new-password"
              name="new_password"
              onChange={(event) => setNewPassword(event.currentTarget.value)}
              required
              type="password"
              value={newPassword}
            />
            {newPasswordError && (
              <p className="text-xs text-negative" id="account-change-new-password-error">
                {newPasswordError}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="account-change-confirm-password">
              Confirm new password
            </label>
            <Input
              autoComplete="new-password"
              aria-describedby={
                confirmPasswordError ? "account-change-confirm-password-error" : undefined
              }
              aria-invalid={confirmPasswordError !== null}
              disabled={pending !== null}
              id="account-change-confirm-password"
              name="confirm_password"
              onChange={(event) => setConfirmPassword(event.currentTarget.value)}
              required
              type="password"
              value={confirmPassword}
            />
            {confirmPasswordError && (
              <p className="text-xs text-negative" id="account-change-confirm-password-error">
                {confirmPasswordError}
              </p>
            )}
          </div>

          {passwordError && <AccountError error={passwordError} />}
          {passwordNotice && (
            <p className="flex items-center gap-2 text-sm text-positive" role="status">
              <Check aria-hidden="true" size={16} />
              {passwordNotice}
            </p>
          )}

          <Button disabled={pending !== null} type="submit" variant="primary">
            {pending === "password" ? (
              <>
                <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
                Updating password
              </>
            ) : (
              <>
                <LockKeyhole aria-hidden="true" size={16} />
                Update password
              </>
            )}
          </Button>
        </form>
      </section>

      <section aria-labelledby="other-sessions-title" className="space-y-4 py-6">
        <header className="max-w-2xl">
          <h2 className="flex items-center gap-2 text-base font-semibold" id="other-sessions-title">
            <ShieldCheck aria-hidden="true" className="text-accent" size={17} />
            Other sessions
          </h2>
          <p className="mt-1 text-sm text-secondary">
            Revoke other signed-in sessions while keeping this one active.
          </p>
        </header>

        {sessionsError && <AccountError error={sessionsError} />}
        {sessionsNotice && (
          <p className="flex items-center gap-2 text-sm text-positive" role="status">
            <Check aria-hidden="true" size={16} />
            {sessionsNotice}
          </p>
        )}

        <Button
          disabled={pending !== null}
          onClick={() => void revokeSessions()}
          variant="outline"
        >
          {pending === "sessions" ? (
            <>
              <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
              Revoking other sessions
            </>
          ) : (
            <>
              <LogOut aria-hidden="true" size={16} />
              Revoke other sessions
            </>
          )}
        </Button>
      </section>
    </div>
  );
}
