import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useSession } from "@/features/session/session-provider";
import { ApiError } from "@/lib/api/client";
import type { AuthenticatedSession } from "@/lib/api/schemas";
import { AccountSecurityPage } from "./account-security-page";

const theme = vi.hoisted(() => ({ setTheme: vi.fn() }));
vi.mock("next-themes", () => ({
  useTheme: () => ({ resolvedTheme: "dark", setTheme: theme.setTheme }),
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn() }) }));
vi.mock("@/features/session/session-provider", () => ({ useSession: vi.fn() }));

const session = {
  authenticated: true,
  user: { username: "account-review", is_staff: false },
  csrf_token: "fixture-csrf",
  market_data_enabled: false,
  legacy_enabled: false,
} satisfies AuthenticatedSession;
const signOut = vi.fn<() => Promise<void>>();

beforeEach(() => {
  signOut.mockReset().mockResolvedValue(undefined);
  vi.mocked(useSession).mockReturnValue({
    state: { kind: "authenticated", session },
    refresh: vi.fn(),
    authenticate: async () => session,
    signOut,
  });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("retains research navigation, theme switching and guidance on the account route", async () => {
  const user = userEvent.setup();
  render(<AccountSecurityPage />);
  expect(screen.getByRole("link", { name: "Research" })).toHaveAttribute(
    "href",
    "/app/research",
  );
  expect(screen.getByRole("link", { name: "Account" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  expect(
    screen.getByRole("link", { name: "Data and licensing" }),
  ).toHaveAttribute("href", "/data");
  await user.click(screen.getByRole("button", { name: "Use light theme" }));
  expect(theme.setTheme).toHaveBeenCalledWith("light");
});

it("keeps the account accessible and permits retry after sign-out fails", async () => {
  const user = userEvent.setup();
  signOut.mockRejectedValueOnce(
    new ApiError({
      status: 503,
      code: "unavailable",
      message: "Sign out unavailable. Try again.",
    }),
  );
  render(<AccountSecurityPage />);
  const button = screen.getByRole("button", { name: "Sign out" });
  await user.click(button);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Sign out unavailable. Try again.",
  );
  expect(
    screen.getByRole("heading", { name: "Account security" }),
  ).toBeVisible();
  await user.click(button);
  expect(signOut).toHaveBeenCalledTimes(2);
  expect(screen.queryByRole("alert")).toBeNull();
});
