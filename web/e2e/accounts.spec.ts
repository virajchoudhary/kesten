import { existsSync, readFileSync } from "node:fs";
import { fixturePath } from "./fixtures";

import { expect, test, type Page, type Route } from "@playwright/test";
import { z } from "zod";

import {
  ChangePasswordRequestSchema,
  InvitationAcceptRequestSchema,
  RevokeOtherSessionsRequestSchema,
} from "../src/features/account/account-api";

const csrfToken = "browser-fixture-csrf";
const accountInvitationFixturePath = fixturePath("account-e2e-invitation.txt");

const AccountInvitationFixtureSchema = z
  .object({
    username: z.string().min(1).max(150),
    token: z.string().min(1).max(128),
  })
  .strict();

type AccountInvitationFixture = z.infer<typeof AccountInvitationFixtureSchema>;

function readAccountInvitationFixture(): AccountInvitationFixture | null {
  if (!existsSync(accountInvitationFixturePath)) {
    return null;
  }

  const contents = readFileSync(accountInvitationFixturePath, "utf8");
  const lines = contents.split(/\r?\n/u);
  const openOnceLine = lines.find((line) => line.startsWith("Open once: "));
  const usernameLine = lines.find((line) => line.startsWith("Reserved username: "));
  if (openOnceLine === undefined || usernameLine === undefined) {
    throw new Error("The local account invitation fixture is invalid.");
  }

  try {
    const invitationUrl = new URL(openOnceLine.slice("Open once: ".length).trim());
    const allowedHost = ["localhost", "127.0.0.1", "::1"].includes(invitationUrl.hostname);
    const token = new URLSearchParams(invitationUrl.hash.slice(1)).get("token");
    const parsed = AccountInvitationFixtureSchema.safeParse({
      username: usernameLine.slice("Reserved username: ".length).trim(),
      token,
    });
    if (
      !allowedHost ||
      invitationUrl.pathname !== "/account/accept/" ||
      invitationUrl.search !== "" ||
      !parsed.success
    ) {
      throw new Error("Invalid fixture.");
    }
    return parsed.data;
  } catch {
    throw new Error("The local account invitation fixture is invalid.");
  }
}

const accountInvitationFixture = readAccountInvitationFixture();

async function stubSession(page: Page, authenticated: boolean): Promise<void> {
  const session = authenticated
    ? {
        authenticated: true,
        user: { username: "browser-fixture-user", is_staff: false },
        csrf_token: csrfToken,
        market_data_enabled: false,
        legacy_enabled: false,
      }
    : {
        authenticated: false,
        user: null,
        csrf_token: csrfToken,
        market_data_enabled: false,
        legacy_enabled: false,
      };

  await page.route("**/api/v1/session/", async (route: Route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(session),
      });
      return;
    }
    await route.continue();
  });
}

test("invitation UI consumes the fragment token and completes the form", async ({ page }) => {
  await stubSession(page, false);
  await page.route("**/api/v1/account/invitations/accept/", async (route: Route) => {
    const requestBody: unknown = route.request().postDataJSON();
    expect(InvitationAcceptRequestSchema.safeParse(requestBody).success).toBe(true);
    expect(route.request().headers()["x-csrftoken"]).toBe(csrfToken);
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ created: true }),
    });
  });

  await page.goto("/account/accept/#token=browser-fixture-invitation");
  await expect(page.getByRole("heading", { name: "Accept account invitation" })).toBeVisible();
  await expect(page.getByLabel("New password", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/account\/accept\/?$/);

  await page.getByLabel("New password", { exact: true }).fill("browser-fixture-password");
  await page.getByLabel("Confirm new password").fill("browser-fixture-password");
  await page.getByRole("button", { name: "Activate account" }).click();

  await expect(page.getByRole("status")).toContainText(
    "Your account is active. Sign in with your new password.",
  );
  await expect(page).toHaveURL(/\/account\/accept\/?$/);
});

test("account page changes a password and revokes only other sessions", async ({ page }) => {
  await stubSession(page, true);
  await page.route("**/api/v1/account/password/change/", async (route: Route) => {
    const requestBody: unknown = route.request().postDataJSON();
    expect(ChangePasswordRequestSchema.safeParse(requestBody).success).toBe(true);
    expect(route.request().headers()["x-csrftoken"]).toBe(csrfToken);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ password_changed: true }),
    });
  });
  await page.route("**/api/v1/account/sessions/revoke/", async (route: Route) => {
    const requestBody: unknown = route.request().postDataJSON();
    expect(RevokeOtherSessionsRequestSchema.safeParse(requestBody).success).toBe(true);
    expect(route.request().headers()["x-csrftoken"]).toBe(csrfToken);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        revoked: "others",
        authenticated: true,
        csrf_token: "browser-fixture-next-csrf",
      }),
    });
  });

  await page.goto("/app/account");
  await expect(page.getByRole("heading", { name: "Account security" })).toBeVisible();
  await page.getByLabel("Current password").fill("browser-fixture-current-password");
  await page.getByLabel("New password", { exact: true }).fill("browser-fixture-replacement-password");
  await page.getByLabel("Confirm new password").fill("browser-fixture-replacement-password");
  await page.getByRole("button", { name: "Update password" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Password updated. This session remains active.",
  );

  await page.getByRole("button", { name: "Revoke other sessions" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Other sessions have been signed out." })).toContainText(
    "Other sessions have been signed out. This session remains active.",
  );
});

test("activates a disposable account through the real API lifecycle", async ({ page }) => {
  if (accountInvitationFixture === null) {
    throw new Error("Run scripts/prepare_browser_fixture.py before lifecycle browser tests.");
  }

  const initialPassword = "Cadrisyn-E2E-Initial-Password-927!";
  const replacementPassword = "Cadrisyn-E2E-Replacement-Password-417!";

  await page.addInitScript((token) => {
    if (window.location.pathname === "/account/accept/") {
      window.history.replaceState(
        window.history.state,
        "",
        `${window.location.pathname}#token=${encodeURIComponent(token)}`,
      );
    }
  }, accountInvitationFixture.token);

  await page.goto("/account/accept/");
  await expect(page.getByRole("heading", { name: "Accept account invitation" })).toBeVisible();
  await page.getByLabel("New password", { exact: true }).fill(initialPassword);
  await page.getByLabel("Confirm new password").fill(initialPassword);
  const invitationRequest = page.waitForRequest(
    (request) =>
      new URL(request.url()).pathname === "/api/v1/account/invitations/accept/" &&
      request.method() === "POST",
  );
  await page.getByRole("button", { name: "Activate account" }).click();
  const acceptedRequest = await invitationRequest;
  const acceptedHeaders = await acceptedRequest.allHeaders();
  expect((acceptedHeaders.referer ?? "").includes(accountInvitationFixture.token)).toBe(false);
  await expect(page.getByRole("status")).toContainText(
    "Your account is active. Sign in with your new password.",
  );

  const tokenPersisted = await page.evaluate((token) => {
    const storedValues = Object.keys(window.localStorage).flatMap((key) => [
      key,
      window.localStorage.getItem(key) ?? "",
    ]);
    return [
      window.location.search,
      window.location.hash,
      document.referrer,
      ...storedValues,
    ].some((value) => value.includes(token));
  }, accountInvitationFixture.token);
  expect(tokenPersisted).toBe(false);

  await page.goto("/sign-in");
  await page.getByLabel("Username").fill(accountInvitationFixture.username);
  await page.getByLabel("Password").fill(initialPassword);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL(/\/app\/markets\/?$/u);

  await page.goto("/app/account");
  await expect(page.getByRole("heading", { name: "Account security" })).toBeVisible();
  await page.getByLabel("Current password").fill(initialPassword);
  await page.getByLabel("New password", { exact: true }).fill(replacementPassword);
  await page.getByLabel("Confirm new password").fill(replacementPassword);
  await page.getByRole("button", { name: "Update password" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Password updated. This session remains active.",
  );
  await page.getByRole("button", { name: "Revoke other sessions" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Other sessions have been signed out." })).toContainText(
    "Other sessions have been signed out. This session remains active.",
  );
});

test("resetting a disposable account revokes its open workspace session", async ({ page, browser, baseURL }) => {
  test.setTimeout(90_000);
  const path = fixturePath("account-e2e-reset.json");
  if (!existsSync(path) || !baseURL) {
    throw new Error("Run scripts/prepare_browser_fixture.py before lifecycle browser tests.");
  }
  const parsed = z.object({ username: z.string().min(1), initial_password: z.string().min(1), token: z.string().min(1) }).safeParse(JSON.parse(readFileSync(path, "utf8")));
  if (!parsed.success) throw new Error("Invalid private reset fixture.");
  const fixture = parsed.data;
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto("/sign-in");
  await page.getByLabel("Username").fill(fixture.username);
  await page.getByLabel("Password", { exact: true }).fill(fixture.initial_password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL(/\/app\/markets\/?$/u);
  await expect(page.getByRole("button", { name: "Reload watchlist" })).toBeEnabled();

  const resetContext = await browser.newContext({ baseURL });
  try {
    await resetContext.addInitScript((token) => {
      if (window.location.pathname === "/account/reset/") {
        window.history.replaceState(window.history.state, "", `${window.location.pathname}#token=${encodeURIComponent(token)}`);
      }
    }, fixture.token);
    const resetPage = await resetContext.newPage();
    await resetPage.goto("/account/reset/");
    const password = "Browser-reset-replacement-927!";
    await resetPage.getByLabel("New password", { exact: true }).fill(password);
    await resetPage.getByLabel("Confirm new password", { exact: true }).fill(password);
    await resetPage.getByRole("button", { name: "Reset password", exact: true }).click();
    await expect(resetPage.getByRole("status")).toContainText("Your password has been reset.");
    await expect(resetPage).toHaveURL(/\/account\/reset\/?$/u);
    await page.getByRole("button", { name: "Reload watchlist" }).click();
    await page.waitForURL(/\/sign-in\/?$/u);
    await resetPage.goto("/sign-in");
    await resetPage.getByLabel("Username").fill(fixture.username);
    await resetPage.getByLabel("Password", { exact: true }).fill(password);
    await resetPage.getByRole("button", { name: "Sign in", exact: true }).click();
    await resetPage.waitForURL(/\/app\/markets\/?$/u);
  } finally {
    await resetContext.close();
  }
});
