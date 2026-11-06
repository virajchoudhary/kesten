"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, LoaderCircle, LockKeyhole } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import { CredentialsSchema } from "@/lib/api/schemas";
import { useSession } from "@/features/session/session-provider";

function serverFieldError(error: ApiError | null, field: string): string | null {
  if (error === null) {
    return null;
  }
  const value = error.fieldErrors[field];
  if (typeof value === "string") {
    return value;
  }
  if (value !== undefined) {
    return value.join(" ");
  }
  return null;
}

export function SignInForm(): React.JSX.Element {
  const router = useRouter();
  const { state, authenticate, refresh } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    username: string | null;
    password: string | null;
  }>({ username: null, password: null });

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setApiError(null);
    const parsed = CredentialsSchema.safeParse({ username, password });
    if (!parsed.success) {
      const usernameIssue = parsed.error.issues.find((issue) => issue.path[0] === "username");
      const passwordIssue = parsed.error.issues.find((issue) => issue.path[0] === "password");
      setValidationErrors({
        username: usernameIssue?.message ?? null,
        password: passwordIssue?.message ?? null,
      });
      return;
    }

    setValidationErrors({ username: null, password: null });
    setPending(true);
    try {
      await authenticate(parsed.data);
      router.replace("/app/markets");
    } catch (error: unknown) {
      setApiError(
        error instanceof ApiError
          ? error
          : new ApiError({
              status: 500,
              code: "login_error",
              message: "Sign-in could not be completed. Try again.",
            }),
      );
    } finally {
      setPending(false);
    }
  }

  if (state.kind === "checking") {
    return (
      <div className="flex min-h-40 items-center justify-center gap-2 text-sm text-secondary" role="status">
        <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
        Checking session
      </div>
    );
  }

  if (state.kind === "failed") {
    return (
      <div className="space-y-4" role="alert">
        <p className="text-sm text-negative">{state.error.message}</p>
        <Button onClick={() => void refresh()} variant="outline">
          Retry session check
        </Button>
      </div>
    );
  }

  if (state.kind === "authenticated") {
    return (
      <div className="space-y-4">
        <p className="text-sm text-secondary">You are signed in as {state.session.user.username}.</p>
        <Button onClick={() => router.replace("/app/markets")} variant="primary">
          Open Markets <ArrowRight aria-hidden="true" size={16} />
        </Button>
      </div>
    );
  }

  const usernameError = validationErrors.username ?? serverFieldError(apiError, "username");
  const passwordError = validationErrors.password ?? serverFieldError(apiError, "password");

  return (
    <form className="space-y-4" onSubmit={(event) => void submit(event)}>
      <div className="space-y-1.5">
        <label className="text-sm font-medium" htmlFor="sign-in-username">
          Username
        </label>
        <Input
          autoComplete="username"
          aria-describedby={usernameError ? "username-error" : undefined}
          aria-invalid={usernameError !== null}
          id="sign-in-username"
          name="username"
          onChange={(event) => setUsername(event.currentTarget.value)}
          required
          value={username}
        />
        {usernameError && (
          <p className="text-xs text-negative" id="username-error">
            {usernameError}
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium" htmlFor="sign-in-password">
          Password
        </label>
        <Input
          autoComplete="current-password"
          aria-describedby={passwordError ? "password-error" : undefined}
          aria-invalid={passwordError !== null}
          id="sign-in-password"
          name="password"
          onChange={(event) => setPassword(event.currentTarget.value)}
          required
          type="password"
          value={password}
        />
        {passwordError && (
          <p className="text-xs text-negative" id="password-error">
            {passwordError}
          </p>
        )}
      </div>

      {apiError && (
        <div className="rounded-control border border-negative/40 bg-negative/10 p-3" role="alert">
          <p className="text-sm text-negative">{apiError.message}</p>
          {apiError.requestId && (
            <p className="mt-1 font-mono text-xs text-secondary">Request {apiError.requestId}</p>
          )}
          {apiError.code === "csrf_failed" && (
            <Button
              className="mt-2"
              onClick={() => void refresh()}
              size="sm"
              variant="outline"
            >
              Refresh session token
            </Button>
          )}
        </div>
      )}

      <Button className="w-full" disabled={pending} type="submit" variant="primary">
        {pending ? (
          <>
            <LoaderCircle aria-hidden="true" className="animate-spin" size={16} />
            Signing in
          </>
        ) : (
          <>
            <LockKeyhole aria-hidden="true" size={16} />
            Sign in
          </>
        )}
      </Button>
    </form>
  );
}
