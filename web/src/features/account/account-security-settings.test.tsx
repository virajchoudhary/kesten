import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useSession } from "@/features/session/session-provider";
import type { AuthenticatedSession } from "@/lib/api/schemas";

import { ChangePasswordRequestSchema } from "./account-api";
import { AccountSecuritySettings } from "./account-security-settings";

vi.mock("@/features/session/session-provider", () => ({
  useSession: vi.fn(),
}));

const session = {
  authenticated: true,
  user: { username: "analyst-fixture", is_staff: false },
  csrf_token: "fixture-csrf",
  market_data_enabled: false,
  legacy_enabled: false,
} satisfies AuthenticatedSession;

const refresh = vi.fn();

function prepareSession(): void {
  refresh.mockClear();
  vi.mocked(useSession).mockReturnValue({
    state: { kind: "authenticated", session },
    refresh,
    authenticate: async () => session,
    signOut: async () => {},
  });
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(prepareSession);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("account security settings", () => {
  it("changes the password through the CSRF-protected same-origin API", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({ password_changed: true }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<AccountSecuritySettings session={session} />);

    await user.type(screen.getByLabelText("Current password"), "fixture-current-password");
    await user.type(screen.getByLabelText("New password"), "fixture-replacement-password");
    await user.type(
      screen.getByLabelText("Confirm new password"),
      "fixture-replacement-password",
    );
    await user.click(screen.getByRole("button", { name: "Update password" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Password updated. This session remains active.",
    );
    const request = fetchMock.mock.calls[0];
    expect(request?.[0]).toBe("/api/v1/account/password/change/");
    expect(request?.[1]?.method).toBe("POST");
    expect(request?.[1]?.credentials).toBe("same-origin");
    expect(new Headers(request?.[1]?.headers).get("X-CSRFToken")).toBe("fixture-csrf");

    const serializedBody =
      typeof request?.[1]?.body === "string" ? request[1].body : "{}";
    const requestBody: unknown = JSON.parse(serializedBody);
    expect(ChangePasswordRequestSchema.safeParse(requestBody).success).toBe(true);
  });

  it("revokes only other sessions and retains the returned CSRF token in memory", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        revoked: "others",
        authenticated: true,
        csrf_token: "next-fixture-csrf",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<AccountSecuritySettings session={session} />);
    await user.click(screen.getByRole("button", { name: "Revoke other sessions" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Other sessions have been signed out. This session remains active.",
    );
    const request = fetchMock.mock.calls[0];
    expect(request?.[0]).toBe("/api/v1/account/sessions/revoke/");
    expect(request?.[1]?.method).toBe("POST");
    expect(request?.[1]?.credentials).toBe("same-origin");
    expect(new Headers(request?.[1]?.headers).get("X-CSRFToken")).toBe("fixture-csrf");
  });

  it("refreshes the session when the server reports that authentication has expired", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          code: "not_authenticated",
          message: "Sign in to continue.",
          field_errors: {},
          request_id: "fixture-request-id",
        },
        403,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<AccountSecuritySettings session={session} />);
    await user.click(screen.getByRole("button", { name: "Revoke other sessions" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Sign in to continue.");
    expect(refresh).toHaveBeenCalledTimes(1);
  });
});
