import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import { ResearchEvaluationSetup } from "./research-evaluation-setup";
import {
  researchDatasetFixture,
  researchRunFixture,
} from "./research-test-fixtures";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows source coverage before execution and blocks a hidden selection while filtering", async () => {
  const dataset = researchDatasetFixture();
  render(<ResearchEvaluationSetup datasetsState={{ kind: "ready", data: [dataset] }} requestedInstrumentId={null}
    selectedDatasetId={dataset.id} horizon={1} csrfToken="fixture-csrf" onCreated={vi.fn()}
    onDatasetChange={vi.fn()} onHorizonChange={vi.fn()} onRetryDatasets={vi.fn()} />);
  expect(screen.getByText(/160 observations · XNYS/u)).toBeVisible();
  expect(screen.getByText(/Source: synthetic-fixture-v1/u)).toBeVisible();
  const search = screen.getByRole("searchbox", { name: "Find a private dataset" });
  await userEvent.type(search, "absent-source");
  expect(screen.getByRole("button", { name: "Run evaluation" })).toBeDisabled();
  expect(screen.getByText("No matching datasets in the available private list.")).toBeVisible();
  await userEvent.clear(search);
  expect(screen.getByRole("button", { name: "Run evaluation" })).toBeEnabled();
});

it("discloses that the picker does not search beyond the newest hundred datasets", () => {
  const dataset = researchDatasetFixture();
  const items = Array.from({ length: 100 }, (_, index) => ({ ...dataset,
    id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`,
    version: index.toString(16).padStart(64, "0"), name: `Synthetic dataset ${index}`,
  }));
  render(<ResearchEvaluationSetup datasetsState={{ kind: "ready", data: items }} requestedInstrumentId={null}
    selectedDatasetId={items[0]?.id ?? ""} horizon={1} csrfToken="fixture-csrf" onCreated={vi.fn()}
    onDatasetChange={vi.fn()} onHorizonChange={vi.fn()} onRetryDatasets={vi.fn()} />);
  expect(screen.getByRole("note")).toHaveTextContent("The picker searches the 100 newest private datasets.");
});

it("does not navigate from a completed request after its setup is unmounted", async () => {
  const dataset = researchDatasetFixture();
  const onCreated = vi.fn();
  let resolveRequest: ((response: Response) => void) | undefined;
  let requestSignal: AbortSignal | null | undefined;
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof fetch>().mockImplementation((_path, init) => {
      requestSignal = init?.signal;
      return new Promise<Response>((resolve) => {
        resolveRequest = resolve;
      });
    }),
  );
  const view = render(
    <ResearchEvaluationSetup
      datasetsState={{ kind: "ready", data: [dataset] }}
      requestedInstrumentId={null}
      selectedDatasetId={dataset.id}
      horizon={1}
      csrfToken="fixture-csrf"
      onCreated={onCreated}
      onDatasetChange={vi.fn()}
      onHorizonChange={vi.fn()}
      onRetryDatasets={vi.fn()}
    />,
  );
  await userEvent
    .setup()
    .click(screen.getByRole("button", { name: "Run evaluation" }));
  await waitFor(() => expect(resolveRequest).toBeDefined());
  view.unmount();
  await act(async () => {
    resolveRequest?.(
      new Response(
        JSON.stringify(
          researchRunFixture({
            id: "22222222-2222-4222-8222-222222222222",
            name: "Late result",
          }),
        ),
      ),
    );
  });
  expect(onCreated).not.toHaveBeenCalled();
  expect(requestSignal?.aborted).toBe(true);
});
