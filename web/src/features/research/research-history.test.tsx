import {
  act,
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { researchHistoryItemFixture } from "./research-test-fixtures";
import { ResearchHistory } from "./research-history";
import { researchWorkspaceHref } from "./research-navigation";
import { formatUtcTimestamp } from "./research-formatters";

const RUN_A = "22222222-2222-4222-8222-222222222222";
const RUN_B = "44444444-4444-4444-8444-444444444444";

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function page(items: ReturnType<typeof researchHistoryItemFixture>[], total: number, offset = 0) {
  return { items, total, offset, limit: 20 };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("research history", () => {
  it("renders dataset identity in a semantic table and retains compact mode", async () => {
    const run = researchHistoryItemFixture({
      id: RUN_A,
      name: "Current evaluation",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse(page([run], 1)),
      ),
    );
    const props: React.ComponentProps<typeof ResearchHistory> = {
      focusModel: "last_close",
      instrumentContext: "xnas-aapl",
      refreshToken: 0,
      selectedCompareId: RUN_A,
      selectedRunId: RUN_B,
      embedded: true,
    };
    const { rerender } = render(<ResearchHistory {...props} />);

    const table = await screen.findByRole("table", {
      name: "Saved evaluations with dataset identity, category, and version.",
    });
    const row = screen.getByRole("row", { name: /Current evaluation/u });
    expect(table).toBeVisible();
    expect(row).toHaveTextContent(run.dataset_id);
    expect(row).toHaveTextContent(run.dataset_version.slice(0, 12));
    expect(row).toHaveTextContent("xnas-aapl");
    expect(row).toHaveTextContent("1 session");
    expect(row).toHaveTextContent("SYNTHETIC");
    expect(
      within(row).getByText(formatUtcTimestamp(run.completed_at)),
    ).toHaveAttribute("datetime", run.completed_at);
    expect(
      screen.getByRole("link", { name: "Open Current evaluation" }),
    ).toHaveAttribute(
      "href",
      researchWorkspaceHref({
        embedded: true,
        runId: RUN_A,
        compareId: RUN_A,
        instrumentId: "xnas-aapl",
        focusModel: "last_close",
      }),
    );
    expect(
      screen.getByRole("link", { name: "Remove comparison" }),
    ).toBeVisible();

    rerender(<ResearchHistory {...props} compact />);
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.getByRole("list")).toBeVisible();
    expect(screen.getByRole("link", { name: /Current evaluation/u })).toBeVisible();
  });

  it("uses the lightweight history endpoint and builds a URL to compare another saved run", async () => {
    const first = researchHistoryItemFixture({ id: RUN_A, name: "Current evaluation" });
    const second = researchHistoryItemFixture({ id: RUN_B, name: "Second evaluation" });
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const url = new URL(String(input), "https://workspace.test");
      expect(url.pathname).toBe("/api/v1/research/history/");
      if (url.searchParams.has("q")) {
        return Promise.resolve(jsonResponse(page([], 0)));
      }
      return Promise.resolve(jsonResponse(page([first, second], 2)));
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(
      <ResearchHistory
        focusModel="last_close"
        instrumentContext="xnas-aapl"
        refreshToken={0}
        selectedCompareId={null}
        selectedRunId={RUN_A}
      />,
    );

    const secondRun = await screen.findByRole("link", { name: /Second evaluation/u });
    const compareLink = await screen.findByRole("link", {
      name: "Compare with open run",
    });
    expect(secondRun).toHaveAttribute("href", expect.stringContaining(`run=${RUN_B}`));
    expect(compareLink).toHaveAttribute(
      "href",
      `/app/research?run=${RUN_A}&compare=${RUN_B}&instrument=xnas-aapl&method=last_close`,
    );
    expect(fetchMock.mock.calls.every(([input]) =>
      String(input).startsWith("/api/v1/research/history/?"),
    )).toBe(true);
    const initialUrl = new URL(String(fetchMock.mock.calls[0]?.[0]), "https://workspace.test");
    expect(initialUrl.searchParams.get("instrument_id")).toBe("xnas-aapl");
    expect(initialUrl.searchParams.get("limit")).toBe("20");

    await user.type(screen.getByRole("searchbox", { name: "Search" }), "pipeline");
    expect(await screen.findByText("No saved evaluations match these filters.")).toBeVisible();
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) => {
          const url = new URL(String(input), "https://workspace.test");
          return url.searchParams.get("q") === "pipeline";
        }),
      ).toBe(true);
    });
  });

  it("paginates with a fixed 20-result page size", async () => {
    const items = Array.from({ length: 20 }, (_, index) =>
      researchHistoryItemFixture({
        id: `00000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
        name: `Evaluation ${index + 1}`,
      }),
    );
    const lastItem = researchHistoryItemFixture({
      id: "00000000-0000-4000-8000-000000000021",
      name: "Evaluation 21",
    });
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const url = new URL(String(input), "https://workspace.test");
      return Promise.resolve(jsonResponse(
        url.searchParams.get("offset") === "20" ? page([lastItem], 21, 20) : page(items, 21),
      ));
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(
      <ResearchHistory
        focusModel="historical_log_mean"
        instrumentContext={null}
        refreshToken={0}
        selectedCompareId={null}
        selectedRunId={null}
      />,
    );

    await screen.findByRole("link", { name: "Open Evaluation 1" });
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(
      await screen.findByRole("link", { name: "Open Evaluation 21" }),
    ).toBeVisible();
    expect(screen.getByRole("button", { name: "Previous" })).toBeEnabled();
    const requestedOffsets = fetchMock.mock.calls.map(([input]) =>
      new URL(String(input), "https://workspace.test").searchParams.get("offset"),
    );
    expect(requestedOffsets).toContain("20");
    expect(fetchMock.mock.calls.every(([input]) =>
      new URL(String(input), "https://workspace.test").searchParams.get("limit") === "20",
    )).toBe(true);
  });

  it("does not show an earlier filtered response after a newer search resolves", async () => {
    const earlier = researchHistoryItemFixture({ id: RUN_A, name: "Earlier filter result" });
    const current = researchHistoryItemFixture({ id: RUN_B, name: "Current filter result" });
    let resolveEarlier: ((response: Response) => void) | undefined;
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const url = new URL(String(input), "https://workspace.test");
      if (url.searchParams.has("q")) {
        return Promise.resolve(jsonResponse(page([current], 1)));
      }
      return new Promise<Response>((resolve) => {
        resolveEarlier = resolve;
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(
      <ResearchHistory
        focusModel="historical_log_mean"
        instrumentContext={null}
        refreshToken={0}
        selectedCompareId={null}
        selectedRunId={null}
      />,
    );
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await user.type(screen.getByRole("searchbox", { name: "Search" }), "current");
    expect(await screen.findByRole("link", { name: /Current filter result/u })).toBeVisible();

    await act(async () => {
      resolveEarlier?.(jsonResponse(page([earlier], 1)));
      await Promise.resolve();
    });

    expect(screen.getByRole("link", { name: /Current filter result/u })).toBeVisible();
    expect(screen.queryByRole("link", { name: /Earlier filter result/u })).toBeNull();
  });

  it("distinguishes a filtered empty result from an empty history", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockImplementation(() => Promise.resolve(jsonResponse(page([], 0)))),
    );

    const view = render(
      <ResearchHistory
        focusModel="historical_log_mean"
        instrumentContext={null}
        refreshToken={0}
        selectedCompareId={null}
        selectedRunId={null}
      />,
    );
    expect(await screen.findByText(
      "No saved evaluations yet. Completed runs will appear here.",
    )).toBeVisible();

    await userEvent.setup().type(screen.getByRole("searchbox", { name: "Search" }), "none");
    expect(await screen.findByText("No saved evaluations match these filters.")).toBeVisible();
    view.unmount();
  });
});
