import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResearchRunActions } from "./research-run-actions";
import {
  researchDatasetFixture,
  researchExportFixture,
  researchRunFixture,
} from "./research-test-fixtures";
import { ResearchRunSchema } from "./research-schemas";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("saved run actions", () => {
  it("shows replay mismatches as verification flags and sends a read-only CSRF request", async () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse({
        run_id: run.id,
        result: "FAIL",
        dataset_matches: true,
        engine_matches: true,
        dependency_lock_matches: false,
        runtime_versions_match: true,
        result_matches: false,
        result_sha256: "c".repeat(64),
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<ResearchRunActions csrfToken="fixture-csrf" run={run} />);
    await user.click(
      screen.getByRole("button", { name: "Verify exact replay" }),
    );

    const result = await screen.findByRole("alert", {
      name: "Exact replay verification",
    });
    expect(result).toHaveTextContent("Replay FAIL");
    expect(result).toHaveTextContent("Dependency lock");
    expect(result).toHaveTextContent("Mismatch");
    expect(result).toHaveTextContent("Saved result");
    expect(result).toHaveTextContent("Result SHA-256:");
    const [path, init] = fetchMock.mock.calls[0] ?? [];
    expect(path).toBe(`/api/v1/research/runs/${run.id}/replay/`);
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe("{}");
    expect(new Headers(init?.headers).get("X-CSRFToken")).toBe("fixture-csrf");
  });

  it("keeps a request error distinct from a completed replay mismatch", async () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse(
          {
            code: "replay_unavailable",
            message: "The exact replay could not be started.",
            field_errors: {},
            request_id: "replay-request-7",
          },
          503,
        ),
      ),
    );
    const user = userEvent.setup();

    render(<ResearchRunActions csrfToken="fixture-csrf" run={run} />);
    await user.click(
      screen.getByRole("button", { name: "Verify exact replay" }),
    );

    expect(await screen.findByRole("alert", { name: "" })).toHaveTextContent(
      "The exact replay could not be started.",
    );
    expect(screen.getByText("Request replay-request-7")).toBeVisible();
    expect(screen.queryByText("Mismatch")).toBeNull();
  });

  it("downloads the validated synthetic JSON export with a fixed UUID filename", async () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const exported = researchExportFixture(run, researchDatasetFixture());
    const source = JSON.stringify(exported).replace('"mae":1', '"mae":1.0');
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(source, {
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const NativeURL = URL;
    const createObjectURL = vi.fn<(blob: Blob) => string>(
      () => "blob:research-export",
    );
    const revokeObjectURL = vi.fn();
    class TestURL extends NativeURL {}
    Object.defineProperties(TestURL, {
      createObjectURL: { configurable: true, value: createObjectURL },
      revokeObjectURL: { configurable: true, value: revokeObjectURL },
    });
    vi.stubGlobal("URL", TestURL);
    const downloads: string[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      downloads.push(this.download);
    });
    const user = userEvent.setup();

    render(<ResearchRunActions csrfToken="fixture-csrf" run={run} />);
    await user.click(
      screen.getByRole("button", { name: "Download synthetic run JSON" }),
    );

    expect(
      await screen.findByText(
        `Downloaded cadrisyn-research-${run.id}.json · ${exported.disclosure}`,
      ),
    ).toBeVisible();
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `/api/v1/research/runs/${run.id}/export/`,
    );
    expect(downloads).toEqual([`cadrisyn-research-${run.id}.json`]);
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    const blob = createObjectURL.mock.calls[0]?.[0];
    if (!blob) throw new Error("Missing exported JSON blob");
    const downloadedText = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () =>
        typeof reader.result === "string"
          ? resolve(reader.result)
          : reject(new Error("Not text"));
      reader.onerror = () => reject(reader.error);
      reader.readAsText(blob);
    });
    expect(downloadedText).toBe(source);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:research-export");
  });

  it("disables historical JSON export and explains the restriction", async () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Historical result",
    });
    const historicalRun = ResearchRunSchema.parse({
      ...run,
      data_kind: "historical",
      result: {
        ...run.result,
        data_kind: "historical",
        evidence_kind: "historical_walk_forward",
      },
    });
    const fetchMock = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetchMock);

    render(<ResearchRunActions csrfToken="fixture-csrf" run={historicalRun} />);

    const download = screen.getByRole("button", {
      name: "Download JSON unavailable",
    });
    expect(download).toBeDisabled();
    expect(download).toHaveAccessibleDescription(
      "Exports are limited to synthetic pipeline checks.",
    );
    await userEvent.setup().click(download);
    await waitFor(() => expect(fetchMock).not.toHaveBeenCalled());
  });
});
