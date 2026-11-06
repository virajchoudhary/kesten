import { afterEach, describe, expect, it, vi } from "vitest";

import {
  acceptInvitation,
  changePassword,
  InvitationAcceptRequestSchema,
  RevokeOtherSessionsRequestSchema,
  revokeOtherSessions,
} from "./account-api";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("account API client", () => {
  it("posts an invitation to the same origin with CSRF and validates the success body", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse({ created: true }, 201));
    vi.stubGlobal("fetch", fetchMock);

    const response = await acceptInvitation(
      {
        token: "fixture-token",
        new_password: "fixture-password",
        confirm_password: "fixture-password",
      },
      "fixture-csrf",
    );

    expect(response.created).toBe(true);
    const request = fetchMock.mock.calls[0];
    expect(request?.[0]).toBe("/api/v1/account/invitations/accept/");
    expect(request?.[1]?.method).toBe("POST");
    expect(request?.[1]?.credentials).toBe("same-origin");
    expect(request?.[1]?.cache).toBe("no-store");
    expect(new Headers(request?.[1]?.headers).get("X-CSRFToken")).toBe("fixture-csrf");

    const serializedBody =
      typeof request?.[1]?.body === "string" ? request[1].body : "{}";
    const requestBody: unknown = JSON.parse(serializedBody);
    expect(InvitationAcceptRequestSchema.safeParse(requestBody).success).toBe(true);
  });

  it("converts a validated server field error into the shared API error shape", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          code: "invalid_current_password",
          message: "The current password is incorrect.",
          field_errors: {
            current_password: ["The current password is incorrect."],
          },
          request_id: "fixture-request-id",
        },
        400,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      changePassword(
        {
          current_password: "fixture-current",
          new_password: "fixture-new",
          confirm_password: "fixture-new",
        },
        "fixture-csrf",
      ),
    ).rejects.toMatchObject({
      status: 400,
      code: "invalid_current_password",
      requestId: "fixture-request-id",
      fieldErrors: {
        current_password: ["The current password is incorrect."],
      },
    });
  });

  it("accepts only an explicit other-session revocation response", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        revoked: "others",
        authenticated: true,
        csrf_token: "next-fixture-csrf",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await revokeOtherSessions("fixture-csrf");

    expect(response.revoked).toBe("others");
    expect(response.authenticated).toBe(true);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/account/sessions/revoke/");
    const serializedBody =
      typeof fetchMock.mock.calls[0]?.[1]?.body === "string"
        ? fetchMock.mock.calls[0][1].body
        : "{}";
    const requestBody: unknown = JSON.parse(serializedBody);
    expect(RevokeOtherSessionsRequestSchema.safeParse(requestBody).success).toBe(true);
  });
});
