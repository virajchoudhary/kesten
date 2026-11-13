import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { InstrumentSearch } from "./instrument-search";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("starts a fresh keyboard search after choosing a result", async () => {
  const user = userEvent.setup();
  const onSelect = vi.fn();
  const instrument = {
    id: "xnas-msft",
    symbol: "MSFT",
    name: "Microsoft Corporation",
    exchange: "XNAS",
    currency: "USD",
    timezone: "America/New_York",
  };
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ items: [instrument] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
  render(<InstrumentSearch onSelect={onSelect} />);
  await user.click(screen.getByRole("button", { name: "Add instrument" }));
  await user.type(
    screen.getByRole("combobox", { name: "Search by symbol or company" }),
    "MSFT",
  );
  await screen.findByRole("option", { name: /Microsoft/u });
  await user.keyboard("{ArrowDown}{Enter}");
  expect(onSelect).toHaveBeenCalledExactlyOnceWith(instrument);
  await user.click(screen.getByRole("button", { name: "Add instrument" }));
  const search = screen.getByRole("combobox", {
    name: "Search by symbol or company",
  });
  expect(search).toHaveValue("");
  expect(search).not.toHaveAttribute("aria-activedescendant");
  expect(screen.queryByRole("option")).toBeNull();
});
