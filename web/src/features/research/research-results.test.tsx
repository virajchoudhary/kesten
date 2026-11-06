import { render, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResearchResults } from "./research-results";
import { researchDatasetFixture, researchRunFixture } from "./research-test-fixtures";

describe("research direction confusion results", () => {
  it("renders asymmetric counts with predicted directions in rows and actual directions in columns", () => {
    const run = researchRunFixture({
      id: "22222222-2222-4222-8222-222222222222",
      name: "Synthetic pipeline fixture",
    });
    const confusionTable = render(
      <ResearchResults
        dataset={researchDatasetFixture()}
        datasetState="ready"
        run={run}
      />,
    ).getByRole("table", { name: /Rows are predicted direction/u });

    expect(
      within(confusionTable)
        .getAllByRole("columnheader")
        .map((header) => header.textContent?.trim()),
    ).toEqual([
      "Model",
      "Partition · predicted",
      "Actual Down",
      "Actual Tie",
      "Actual Up",
    ]);

    const predictedDownRows = within(confusionTable).getAllByRole("row", {
      name: /validation · Down 0 1 0/u,
    });
    expect(predictedDownRows).toHaveLength(2);
    for (const row of predictedDownRows) {
      expect(within(row).getAllByRole("cell").map((cell) => cell.textContent)).toEqual([
        "0",
        "1",
        "0",
      ]);
    }
  });
});
