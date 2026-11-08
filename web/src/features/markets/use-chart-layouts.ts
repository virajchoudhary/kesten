"use client";

import { useEffect, useState } from "react";
import { z } from "zod";
import {
  ChartPreferencesSchema,
  defaultChartPreferences,
  type ChartPreferences,
} from "./chart-preferences";

const StoredLayoutSchema = z.strictObject({
  version: z.literal(1),
  preferences: ChartPreferencesSchema,
  templates: z
    .array(
      z.strictObject({
        name: z.string().trim().min(1).max(32),
        preferences: ChartPreferencesSchema,
      }),
    )
    .max(8),
});
type Layouts = z.infer<typeof StoredLayoutSchema>;
const defaults: Layouts = {
  version: 1,
  preferences: defaultChartPreferences,
  templates: [],
};
const STORAGE_KEY = "market-workspace.chart-layouts.v1";

export function useChartLayouts() {
  const [store, setStore] = useState<
    { kind: "loading" } | { kind: "ready"; data: Layouts }
  >({ kind: "loading" });
  const [storageError, setStorageError] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        const parsed = StoredLayoutSchema.safeParse(
          raw ? JSON.parse(raw) : defaults,
        );
        setStore({
          kind: "ready",
          data: parsed.success ? parsed.data : defaults,
        });
      } catch {
        setStore({ kind: "ready", data: defaults });
        setStorageError(
          "Browser storage is unavailable. Display changes will last for this session.",
        );
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);
  useEffect(() => {
    if (store.kind !== "ready") return;
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(store.data));
        setStorageError(null);
      } catch {
        setStorageError("Display settings could not be saved in this browser.");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [store]);
  const data = store.kind === "ready" ? store.data : defaults;
  function update(patch: Partial<ChartPreferences>): void {
    setStore((previous) => {
      const data = previous.kind === "ready" ? previous.data : defaults;
      const parsed = ChartPreferencesSchema.safeParse({
        ...data.preferences,
        ...patch,
      });
      return parsed.success
        ? { kind: "ready", data: { ...data, preferences: parsed.data } }
        : previous;
    });
  }
  function saveTemplate(name: string): void {
    const valid = z.string().trim().min(1).max(32).safeParse(name);
    if (!valid.success) return;
    setStore((previous) => {
      const data = previous.kind === "ready" ? previous.data : defaults;
      const templates = data.templates.filter(
        (template) => template.name !== valid.data,
      );
      return {
        kind: "ready",
        data: {
          ...data,
          templates: [
            { name: valid.data, preferences: data.preferences },
            ...templates,
          ].slice(0, 8),
        },
      };
    });
  }
  function removeTemplate(name: string): void {
    setStore((previous) =>
      previous.kind === "ready"
        ? {
            kind: "ready",
            data: {
              ...previous.data,
              templates: previous.data.templates.filter(
                (template) => template.name !== name,
              ),
            },
          }
        : previous,
    );
  }
  return {
    preferences: data.preferences,
    templates: data.templates,
    ready: store.kind === "ready",
    update,
    saveTemplate,
    removeTemplate,
    storageError,
  };
}
