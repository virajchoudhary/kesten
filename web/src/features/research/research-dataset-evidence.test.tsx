import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import { ResearchDatasetEvidence } from "./research-dataset-evidence";
import { researchProvenanceFixture } from "./research-test-fixtures";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("lazily inspects hashes and declared permissions without calling an intact archive qualified", async () => {
  const evidence = researchProvenanceFixture();
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify(evidence)));
  vi.stubGlobal("fetch", fetchMock);
  render(<ResearchDatasetEvidence datasetId={evidence.dataset.id} datasetVersion={evidence.dataset.version} />);
  expect(fetchMock).not.toHaveBeenCalled();
  await userEvent.click(screen.getByText("Source package and permissions"));
  expect(await screen.findByText("Archived bytes match the intake receipt")).toBeVisible();
  expect(screen.getByText("Operator-declared permissions")).toBeVisible();
  expect(screen.getByText("Not declared allowed")).toBeVisible();
  expect(screen.getByText(/not a receipt linked to a particular saved run/u)).toBeVisible();
  expect(screen.getByText(/Point-in-time qualification has not been independently verified/u)).toBeVisible();
});

it("shows integrity failure without fabricating source metadata and resets for a different dataset", async () => {
  const evidence = researchProvenanceFixture();
  const failed = { ...evidence, intake: { status: "failed", receipt_id: "55555555-5555-4555-8555-555555555555" } };
  const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify(failed)));
  vi.stubGlobal("fetch", fetchMock);
  const view = render(<ResearchDatasetEvidence datasetId={evidence.dataset.id} datasetVersion={evidence.dataset.version} />);
  await userEvent.click(screen.getByText("Source package and permissions"));
  expect(await screen.findByText("Archived source evidence failed its integrity check.")).toBeVisible();
  expect(screen.queryByText("Operator-declared permissions")).not.toBeInTheDocument();
  view.rerender(<ResearchDatasetEvidence datasetId="66666666-6666-4666-8666-666666666666" datasetVersion={evidence.dataset.version} />);
  expect(screen.queryByText("Archived source evidence failed its integrity check.")).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

it("lets a user retry a failed evidence request", async () => {
  const evidence = researchProvenanceFixture();
  vi.stubGlobal("fetch", vi.fn<typeof fetch>()
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce(new Response(JSON.stringify({ ...evidence, intake: { status: "not_archived" } }))));
  render(<ResearchDatasetEvidence datasetId={evidence.dataset.id} datasetVersion={evidence.dataset.version} />);
  await userEvent.click(screen.getByText("Source package and permissions"));
  await userEvent.click(await screen.findByRole("button", { name: "Retry source evidence" }));
  expect(await screen.findByText(/No archived intake receipt. This synthetic dataset/u)).toBeVisible();
});

it("refreshes current receipt integrity without keeping stale permission claims", async () => {
  const evidence = researchProvenanceFixture();
  vi.stubGlobal("fetch", vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(JSON.stringify(evidence)))
    .mockResolvedValueOnce(new Response(JSON.stringify({ ...evidence, intake: { status: "failed", receipt_id: "55555555-5555-4555-8555-555555555555" } }))));
  render(<ResearchDatasetEvidence datasetId={evidence.dataset.id} datasetVersion={evidence.dataset.version} />);
  await userEvent.click(screen.getByText("Source package and permissions"));
  await userEvent.click(await screen.findByRole("button", { name: "Refresh source evidence" }));
  expect(await screen.findByText("Archived source evidence failed its integrity check.")).toBeVisible();
  expect(screen.queryByText("Operator-declared permissions")).not.toBeInTheDocument();
});
