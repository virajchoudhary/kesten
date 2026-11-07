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
