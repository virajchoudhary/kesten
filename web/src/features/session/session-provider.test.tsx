import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { SessionProvider, useSession } from "./session-provider";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function Probe() {
  const { state } = useSession();
  return (
    <p>
      {state.kind === "authenticated"
        ? state.session.user.username
        : state.kind}
    </p>
  );
}

it("hides old private state while a focused tab rechecks changed session cookies", async () => {
  let resolveSession: ((response: Response) => void) | undefined;
  const fetchMock = vi
    .fn<typeof fetch>()
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          authenticated: true,
          user: { username: "first-account", is_staff: false },
          csrf_token: "fixture-csrf",
          market_data_enabled: false,
          legacy_enabled: false,
        }),
      ),
    )
    .mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveSession = resolve;
        }),
    );
  vi.stubGlobal("fetch", fetchMock);
  render(
    <SessionProvider>
      <Probe />
    </SessionProvider>,
  );
  expect(await screen.findByText("first-account")).toBeVisible();
  act(() => window.dispatchEvent(new Event("focus")));
  expect(screen.queryByText("first-account")).toBeNull();
  expect(screen.getByText("checking")).toBeVisible();
  await act(async () => {
    resolveSession?.(
      new Response(
        JSON.stringify({
          authenticated: true,
          user: { username: "second-account", is_staff: false },
          csrf_token: "fixture-next-csrf",
          market_data_enabled: false,
          legacy_enabled: false,
        }),
      ),
    );
  });
  expect(await screen.findByText("second-account")).toBeVisible();
});
