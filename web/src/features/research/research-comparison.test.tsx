import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResearchComparison } from "./research-comparison";
import { researchRunFixture } from "./research-test-fixtures";

const CURRENT_ID = "11111111-1111-4111-8111-111111111111";
const LEFT_ID = "22222222-2222-4222-8222-222222222222";
const RIGHT_ID = "44444444-4444-4444-8444-444444444444";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function run(id: string, name: string) {
  return researchRunFixture({ id, name });
}

function comparisonResponse(leftId: string, rightId: string, compatible: boolean) {
  return {
    left_id: leftId,
    right_id: rightId,
    compatible,
    reasons: compatible ? [] : ["Dataset versions differ."],
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("research run comparison", () => {
  it("shows immutable run identities and descriptive deltas for compatible runs", async () => {
    const currentRun = run(CURRENT_ID, "Current synthetic run");
    const comparedRun = run(RIGHT_ID, "Compared synthetic run");
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const path = String(input);
      if (path === `/api/v1/research/runs/${RIGHT_ID}/`) {
        return Promise.resolve(jsonResponse(comparedRun));
      }
      if (path === `/api/v1/research/runs/${CURRENT_ID}/compare/${RIGHT_ID}/`) {
        return Promise.resolve(jsonResponse(comparisonResponse(CURRENT_ID, RIGHT_ID, true)));
      }
      return Promise.resolve(jsonResponse({ code: "unexpected", message: "Unexpected.", field_errors: {}, request_id: "unexpected" }, 500));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <ResearchComparison
        comparisonRunId={RIGHT_ID}
        currentRun={currentRun}
        onClear={vi.fn()}
      />,
    );

    const currentPanel = await screen.findByRole("region", { name: "Current run · left" });
    const comparedPanel = screen.getByRole("region", { name: "Compared run · right" });
    expect(currentPanel).toHaveTextContent(CURRENT_ID);
    expect(currentPanel).toHaveTextContent(currentRun.dataset_version);
    expect(currentPanel).toHaveTextContent("1 next scheduled session");
    expect(comparedPanel).toHaveTextContent(RIGHT_ID);
    expect(comparedPanel).toHaveTextContent(comparedRun.result.protocol.protocol_sha256);
    expect(screen.getByRole("region", { name: "Compatible run metric changes" })).toBeVisible();
    expect(screen.getByText(/Values show the compared run minus the current run/u)).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("shows incompatibility reasons and hides metric deltas", async () => {
    const currentRun = run(CURRENT_ID, "Current run");
    const comparedRun = run(LEFT_ID, "Different dataset version");
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const path = String(input);
      return Promise.resolve(jsonResponse(
        path === `/api/v1/research/runs/${LEFT_ID}/`
          ? comparedRun
          : comparisonResponse(CURRENT_ID, LEFT_ID, false),
      ));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <ResearchComparison
        comparisonRunId={LEFT_ID}
        currentRun={currentRun}
        onClear={vi.fn()}
      />,
    );

    expect(await screen.findByText("These runs are not comparable.")).toBeVisible();
    expect(screen.getByText("Dataset versions differ.")).toBeVisible();
    expect(screen.getByText(
      "Metric changes are hidden because the evaluation conditions differ.",
    )).toBeVisible();
    expect(screen.queryByRole("region", { name: "Compatible run metric changes" })).toBeNull();
  });

  it("reports a mismatched compare response as an API request error", async () => {
    const currentRun = run(CURRENT_ID, "Current run");
    const comparedRun = run(RIGHT_ID, "Compared run");
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const path = String(input);
      return Promise.resolve(jsonResponse(
        path === `/api/v1/research/runs/${RIGHT_ID}/`
          ? comparedRun
          : comparisonResponse(RIGHT_ID, CURRENT_ID, true),
      ));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <ResearchComparison
        comparisonRunId={RIGHT_ID}
        currentRun={currentRun}
        onClear={vi.fn()}
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The API returned a comparison for different saved evaluations.",
    );
    expect(screen.queryByText("These runs use compatible evaluation conditions.")).toBeNull();
  });

  it("keeps the latest comparison when an earlier comparison resolves late", async () => {
    const currentRun = run(CURRENT_ID, "Current run");
    const earlierRun = run(LEFT_ID, "Earlier compared run");
    const latestRun = run(RIGHT_ID, "Latest compared run");
    const deferred: Array<(response: Response) => void> = [];
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((input) => {
      const path = String(input);
      if (
        path === `/api/v1/research/runs/${LEFT_ID}/` ||
        path === `/api/v1/research/runs/${CURRENT_ID}/compare/${LEFT_ID}/`
      ) {
        return new Promise<Response>((resolve) => deferred.push(resolve));
      }
      if (path === `/api/v1/research/runs/${RIGHT_ID}/`) {
        return Promise.resolve(jsonResponse(latestRun));
      }
      if (path === `/api/v1/research/runs/${CURRENT_ID}/compare/${RIGHT_ID}/`) {
        return Promise.resolve(jsonResponse(comparisonResponse(CURRENT_ID, RIGHT_ID, true)));
      }
      return Promise.resolve(jsonResponse({ code: "unexpected", message: "Unexpected.", field_errors: {}, request_id: "unexpected" }, 500));
    });
    vi.stubGlobal("fetch", fetchMock);
    const view = render(
      <ResearchComparison
        comparisonRunId={LEFT_ID}
        currentRun={currentRun}
        onClear={vi.fn()}
      />,
    );

    view.rerender(
      <ResearchComparison
        comparisonRunId={RIGHT_ID}
        currentRun={currentRun}
        onClear={vi.fn()}
      />,
    );
    expect(await screen.findByRole("region", { name: "Compared run · right" }))
      .toHaveTextContent(RIGHT_ID);

    await act(async () => {
      for (const resolve of deferred) {
        resolve(jsonResponse(
          deferred.indexOf(resolve) === 0 ? earlierRun : comparisonResponse(CURRENT_ID, LEFT_ID, true),
        ));
      }
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(screen.getByRole("region", { name: "Compared run · right" })).toHaveTextContent(RIGHT_ID);
      expect(screen.queryByText("Earlier compared run")).toBeNull();
    });
  });
});
