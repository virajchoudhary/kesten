import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { useChartLayouts } from "./use-chart-layouts";
import { defaultChartPreferences } from "./chart-preferences";
const key = "market-workspace.chart-layouts.v1";
beforeEach(() => localStorage.clear());
describe("browser display layouts", () => {
  it("loads existing settings without overwriting them with defaults", async () => {
    localStorage.setItem(
      key,
      JSON.stringify({
        version: 1,
        preferences: { ...defaultChartPreferences, chartType: "area" },
        templates: [],
      }),
    );
    const { result } = renderHook(() => useChartLayouts());
    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.preferences.chartType).toBe("area");
    expect(JSON.parse(localStorage.getItem(key)!).preferences.chartType).toBe(
      "area",
    );
  });
  it("stores display preferences and bounded named templates, then restores them", async () => {
    const { result, unmount } = renderHook(() => useChartLayouts());
    await waitFor(() => expect(result.current.ready).toBe(true));
    act(() => result.current.update({ scaleMode: "log", emaEnabled: true }));
    act(() => result.current.saveTemplate("Trend"));
    await waitFor(() =>
      expect(JSON.parse(localStorage.getItem(key)!).templates).toHaveLength(1),
    );
    const persisted = JSON.parse(localStorage.getItem(key)!);
    expect(Object.keys(persisted).sort()).toEqual([
      "preferences",
      "templates",
      "version",
    ]);
    expect(persisted.templates[0].preferences.scaleMode).toBe("log");
    unmount();
    const restored = renderHook(() => useChartLayouts());
    await waitFor(() =>
      expect(restored.result.current.templates[0]?.name).toBe("Trend"),
    );
    act(() => restored.result.current.removeTemplate("Trend"));
    expect(restored.result.current.templates).toHaveLength(0);
  });
  it("recovers from malformed or unsupported browser settings", async () => {
    localStorage.setItem(
      key,
      JSON.stringify({ version: 99, preferences: { chartType: "unsafe" } }),
    );
    const { result } = renderHook(() => useChartLayouts());
    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(result.current.preferences).toEqual(defaultChartPreferences);
  });
});
