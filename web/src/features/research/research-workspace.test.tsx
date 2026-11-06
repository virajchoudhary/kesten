import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SessionProvider } from "@/features/session/session-provider";

import { researchDatasetFixture, researchRunFixture } from "./research-test-fixtures";
import { ResearchRunRequestSchema } from "./research-schemas";
import { ResearchWorkspace } from "./research-workspace";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));
vi.mock("next-themes", () => ({
  useTheme: () => ({ resolvedTheme: "light", setTheme: vi.fn() }),
}));

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("research run detail", () => {
  it("keeps the latest selected run when an earlier detail request resolves late", async () => {
    const runA = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Earlier run",
    });
    const runB = researchRunFixture({
      id: "44444444-4444-4444-8444-444444444444",
      name: "Selected run",
    });
    let resolveRunA: ((response: Response) => void) | undefined;
    const pendingRunA = new Promise<Response>((resolve) => {
      resolveRunA = resolve;
    });
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const path = String(input);
      if (path === "/api/v1/session/") {
        return Promise.resolve(jsonResponse({
          authenticated: true,
          user: { username: "research-test", is_staff: false },
          csrf_token: "research-test-csrf",
          market_data_enabled: false,
          legacy_enabled: false,
        }));
      }
      if (path === "/api/v1/research/datasets/") {
        return Promise.resolve(jsonResponse({ items: [researchDatasetFixture()] }));
      }
      if (path === "/api/v1/research/runs/") {
        return Promise.resolve(jsonResponse({ items: [runA, runB] }));
      }
      if (path === `/api/v1/research/runs/${runA.id}/`) {
        return pendingRunA;
      }
      if (path === `/api/v1/research/runs/${runB.id}/`) {
        return Promise.resolve(jsonResponse(runB));
      }
      return Promise.resolve(jsonResponse({
        code: "unexpected_request",
        message: "Unexpected test request.",
        field_errors: {},
        request_id: "research-test-request",
      }, 500));
    });
    vi.stubGlobal("fetch", fetchMock);
    const view = render(
      <SessionProvider>
        <ResearchWorkspace requestedRunId={runA.id} />
      </SessionProvider>,
    );
    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([input]) =>
        String(input) === `/api/v1/research/runs/${runA.id}/`,
      )).toBe(true);
    });

    view.rerender(
      <SessionProvider>
        <ResearchWorkspace requestedRunId={runB.id} />
      </SessionProvider>,
    );
    expect(await screen.findByRole("heading", { name: "Selected run" })).toBeVisible();
    expect(
      screen.getAllByText("Historical log mean · geometric drift path").length,
    ).toBeGreaterThan(0);

    await act(async () => {
      resolveRunA?.(jsonResponse(runA));
      await Promise.resolve();
    });
    expect(screen.getByRole("heading", { name: "Selected run" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Earlier run" })).toBeNull();
  });
});

describe("research evaluation submission", () => {
  it("reuses the same idempotency key when retrying after a network error", async () => {
    const dataset = researchDatasetFixture();
    const createdRun = researchRunFixture({
      id: "66666666-6666-4666-8666-666666666666",
      name: "Retry idempotency fixture",
    });
    const requestBodies: unknown[] = [];
    let runListRequests = 0;
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input, init) => {
      const path = String(input);
      const method = init?.method ?? "GET";
      if (path === "/api/v1/session/") {
        return Promise.resolve(jsonResponse({
          authenticated: true,
          user: { username: "research-test", is_staff: false },
          csrf_token: "research-test-csrf",
          market_data_enabled: false,
          legacy_enabled: false,
        }));
      }
      if (path === "/api/v1/research/datasets/") {
        return Promise.resolve(jsonResponse({ items: [dataset] }));
      }
      if (path === "/api/v1/research/runs/" && method === "GET") {
        runListRequests += 1;
        return Promise.resolve(jsonResponse({
          items: runListRequests === 1 ? [] : [createdRun],
        }));
      }
      if (path === "/api/v1/research/runs/" && method === "POST") {
        const body: unknown = JSON.parse(typeof init?.body === "string" ? init.body : "{}");
        requestBodies.push(body);
        return requestBodies.length === 1
          ? Promise.reject(new TypeError("connection interrupted"))
          : Promise.resolve(jsonResponse(createdRun, 201));
      }
      return Promise.resolve(jsonResponse({
        code: "unexpected_request",
        message: "Unexpected test request.",
        field_errors: {},
        request_id: "research-test-request",
      }, 500));
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    render(
      <SessionProvider>
        <ResearchWorkspace requestedRunId={null} />
      </SessionProvider>,
    );
    const submit = await screen.findByRole("button", { name: "Run evaluation" });
    await waitFor(() => expect(submit).toBeEnabled());
    await user.click(submit);
    const retry = await screen.findByRole("button", { name: "Retry evaluation" });
    await user.click(retry);

    expect(await screen.findByRole("link", { name: /Retry idempotency fixture/u }))
      .toBeVisible();
    expect(requestBodies).toHaveLength(2);
    const firstRequest = ResearchRunRequestSchema.parse(requestBodies[0]);
    const secondRequest = ResearchRunRequestSchema.parse(requestBodies[1]);
    expect(firstRequest).toEqual(secondRequest);
  });
});
