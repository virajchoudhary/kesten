"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  ApiError,
  getSession,
  login as loginRequest,
  logout as logoutRequest,
  SESSION_RECHECK_EVENT,
} from "@/lib/api/client";
import type {
  AuthenticatedSession,
  Credentials,
  Session,
} from "@/lib/api/schemas";

export type SessionState =
  | { kind: "checking" }
  | { kind: "authenticated"; session: AuthenticatedSession }
  | { kind: "anonymous"; session: Extract<Session, { authenticated: false }> }
  | { kind: "failed"; error: ApiError };

type ResolvedSessionState = Exclude<SessionState, { kind: "checking" }>;

type SessionResult = {
  attempt: number;
  state: ResolvedSessionState;
};

type SessionContextValue = {
  state: SessionState;
  refresh: () => void;
  authenticate: (credentials: Credentials) => Promise<AuthenticatedSession>;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

function toSessionState(session: Session): ResolvedSessionState {
  if (session.authenticated) {
    return { kind: "authenticated", session };
  }
  return { kind: "anonymous", session };
}

function asApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  return new ApiError({
    status: 500,
    code: "session_error",
    message: "The session could not be updated. Try again.",
  });
}

export function SessionProvider({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<SessionResult | null>(null);
  const sessionChannel = useRef<BroadcastChannel | null>(null);
  const state = useMemo<SessionState>(
    () => (result?.attempt === attempt ? result.state : { kind: "checking" }),
    [attempt, result],
  );

  const refresh = useCallback((): void => {
    setAttempt((current) => current + 1);
  }, []);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    const channel =
      typeof BroadcastChannel === "undefined"
        ? null
        : new BroadcastChannel("cadrisyn-session");
    if (channel) channel.onmessage = refresh;
    sessionChannel.current = channel;
    window.addEventListener(SESSION_RECHECK_EVENT, refresh);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.removeEventListener(SESSION_RECHECK_EVENT, refresh);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", onVisible);
      channel?.close();
      sessionChannel.current = null;
    };
  }, [refresh]);

  useEffect(() => {
    const requestAttempt = attempt;
    const controller = new AbortController();
    void getSession(controller.signal)
      .then((session) => {
        if (!controller.signal.aborted) {
          setResult({
            attempt: requestAttempt,
            state: toSessionState(session),
          });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setResult({
            attempt: requestAttempt,
            state: { kind: "failed", error: asApiError(error) },
          });
        }
      });

    return () => controller.abort();
  }, [attempt]);

  const authenticate = useCallback(
    async (credentials: Credentials): Promise<AuthenticatedSession> => {
      if (state.kind !== "anonymous") {
        throw new ApiError({
          status: 401,
          code: "session_not_ready",
          message: "Refresh the session before signing in.",
        });
      }

      const session = await loginRequest(credentials, state.session.csrf_token);
      if (!session.authenticated) {
        throw new ApiError({
          status: 502,
          code: "login_not_established",
          message: "The API did not establish an authenticated session.",
        });
      }

      setResult({ attempt, state: { kind: "authenticated", session } });
      sessionChannel.current?.postMessage("changed");
      return session;
    },
    [attempt, state],
  );

  const signOut = useCallback(async (): Promise<void> => {
    if (state.kind !== "authenticated") {
      return;
    }
    try {
      const session = await logoutRequest(state.session.csrf_token);
      setResult({ attempt, state: toSessionState(session) });
      sessionChannel.current?.postMessage("changed");
    } catch (error: unknown) {
      throw asApiError(error);
    }
  }, [attempt, state]);

  const value = useMemo(
    () => ({ state, refresh, authenticate, signOut }),
    [state, refresh, authenticate, signOut],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (context === null) {
    throw new Error("useSession must be used within SessionProvider.");
  }
  return context;
}
