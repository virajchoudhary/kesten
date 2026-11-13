import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useSession } from "@/features/session/session-provider";
import type { Session } from "@/lib/api/schemas";

import { InvitationAcceptRequestSchema } from "./account-api";
import { TokenPasswordForm } from "./token-password-form";

vi.mock("@/features/session/session-provider", () => ({
  useSession: vi.fn(),
}));

const anonymousSession = {
  authenticated: false,
  user: null,
  csrf_token: "fixture-csrf",
  market_data_enabled: false,
  legacy_enabled: false,
} satisfies Extract<Session, { authenticated: false }>;

function prepareSession(): void {
  vi.mocked(useSession).mockReturnValue({
    state: { kind: "anonymous", session: anonymousSession },
    refresh: vi.fn(),
    authenticate: async () => {
      throw new Error("Not used by account forms.");
    },
    signOut: async () => {},
  });
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  prepareSession();
  window.history.replaceState(window.history.state, "", "/account/accept/#token=fixture-invitation");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.history.replaceState(window.history.state, "", "/");
});

describe("operator-issued account token forms", () => {
  it("consumes an invitation fragment, removes it from browser history, and completes setup", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({ created: true }, 201),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(
      <StrictMode>
        <TokenPasswordForm purpose="invitation" />
      </StrictMode>,
    );

    const password = await screen.findByLabelText("New password");
    await waitFor(() => {
      expect(window.location.hash).toBe("");
      expect(window.location.search).toBe("");
    });
    await user.type(password, "fixture-strong-password");
    await user.type(screen.getByLabelText("Confirm new password"), "fixture-strong-password");
    await user.click(screen.getByRole("button", { name: "Activate account" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Your account is active. Sign in with your new password.",
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const request = fetchMock.mock.calls[0];
    expect(request?.[0]).toBe("/api/v1/account/invitations/accept/");
    expect(request?.[1]?.method).toBe("POST");
    expect(request?.[1]?.credentials).toBe("same-origin");
    expect(new Headers(request?.[1]?.headers).get("X-CSRFToken")).toBe("fixture-csrf");

    const serializedBody =
      typeof request?.[1]?.body === "string" ? request[1].body : "{}";
    const requestBody: unknown = JSON.parse(serializedBody);
    expect(InvitationAcceptRequestSchema.safeParse(requestBody).success).toBe(true);
    expect(window.location.href).not.toContain("fixture-invitation");
  });

  it("rejects query-only tokens and clears them without making a request", async () => {
    window.history.replaceState(
      window.history.state,
      "",
      "/account/accept/?token=fixture-query-token",
    );
    const fetchMock = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetchMock);

    render(<TokenPasswordForm purpose="invitation" />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This invitation is invalid or expired.",
    );
    await waitFor(() => expect(window.location.search).toBe(""));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders validated server password-policy feedback", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          code: "password_policy",
          message: "Choose a password that meets the account requirements.",
          field_errors: {
            new_password: ["Choose a longer passphrase."],
          },
          request_id: "fixture-request-id",
        },
        400,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<TokenPasswordForm purpose="password-reset" />);

    await user.type(await screen.findByLabelText("New password"), "fixture-password");
    await user.type(screen.getByLabelText("Confirm new password"), "fixture-password");
    await user.click(screen.getByRole("button", { name: "Reset password" }));

    expect(await screen.findByText("Choose a longer passphrase.")).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose a password that meets the account requirements.",
    );
  });

  it("shows a mismatch error before sending account credentials", async () => {
    const fetchMock = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<TokenPasswordForm purpose="password-reset" />);

    await user.type(await screen.findByLabelText("New password"), "fixture-password-one");
    await user.type(screen.getByLabelText("Confirm new password"), "fixture-password-two");
    await user.click(screen.getByRole("button", { name: "Reset password" }));

    expect(await screen.findByText("The passwords do not match.")).toBeVisible();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
