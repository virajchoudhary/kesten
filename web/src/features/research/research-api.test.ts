import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

import { createResearchRun } from "./research-api";
import {
  ResearchRunRequestSchema,
  type ResearchRunRequest,
} from "./research-schemas";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const request: ResearchRunRequest = {
  dataset_id: "11111111-1111-4111-8111-111111111111",
  horizon_sessions: 5,
  idempotency_key: "33333333-3333-4333-8333-333333333333",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("research API client", () => {
  it("sends a validated request with CSRF and preserves the caller's retry key", async () => {
    const fetchMock = vi.fn<typeof fetch>()
      .mockRejectedValueOnce(new TypeError("connection interrupted"))
      .mockRejectedValueOnce(new TypeError("connection interrupted"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createResearchRun(request, "fixture-csrf")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
    await expect(createResearchRun(request, "fixture-csrf")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const [path, init] of fetchMock.mock.calls) {
      expect(path).toBe("/api/v1/research/runs/");
      expect(init?.method).toBe("POST");
      expect(init?.credentials).toBe("same-origin");
      expect(init?.cache).toBe("no-store");
      expect(new Headers(init?.headers).get("X-CSRFToken")).toBe("fixture-csrf");
      const body: unknown = JSON.parse(typeof init?.body === "string" ? init.body : "{}");
      expect(ResearchRunRequestSchema.parse(body)).toEqual(request);
    }
  });

  it("maps a validated API error into the shared error type with its request ID", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          code: "dataset_unavailable",
          message: "The selected private dataset is unavailable.",
          field_errors: {},
          request_id: "research-request-123",
        },
        409,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const caught = createResearchRun(request, "fixture-csrf").catch((error: unknown) => error);
    await expect(caught).resolves.toBeInstanceOf(ApiError);
    await expect(caught).resolves.toMatchObject({
      status: 409,
      code: "dataset_unavailable",
      requestId: "research-request-123",
    });
  });
});
