"use client";

import { useEffect, useRef, useState } from "react";
import { X, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  ChartPreferencesSchema,
  type ChartPreferences,
} from "./chart-preferences";
import type { ChartLevel } from "./chart-transform";

export type ChartPanel = "studies" | "display" | "layouts" | "levels";
export function ChartControlPanel({
  panel,
  preferences,
  onUpdate,
  onClose,
  templates,
  onSaveTemplate,
  onRemoveTemplate,
  levels,
  onAddLevel,
  onRemoveLevel,
  storageError,
}: {
  panel: ChartPanel;
  preferences: ChartPreferences;
  onUpdate: (patch: Partial<ChartPreferences>) => void;
  onClose: () => void;
  templates: Array<{ name: string; preferences: ChartPreferences }>;
  onSaveTemplate: (name: string) => void;
  onRemoveTemplate: (name: string) => void;
  levels: ChartLevel[];
  onAddLevel: (price: number) => void;
  onRemoveLevel: (id: string) => void;
  storageError: string | null;
}): React.JSX.Element {
  const [error, setError] = useState<string | null>(null),
    [saved, setSaved] = useState<string | null>(null);
  const panelRef = useRef<HTMLElement>(null);
  useEffect(() => { panelRef.current?.focus(); }, []);
  const title = {
    studies: "Studies",
    display: "Chart settings",
    layouts: "Display layouts",
    levels: "Price levels",
  }[panel];
  return (
    <aside
      ref={panelRef}
      tabIndex={-1}
      className="chart-control-panel"
      id="chart-control-panel"
      aria-label={title}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          onClose();
        }
      }}
    >
      <header>
        <h2>{title}</h2>
        <Button
          aria-label="Close chart panel"
          size="icon"
          variant="ghost"
          onClick={onClose}
        >
          <X size={15} />
        </Button>
      </header>
      {panel === "studies" && (
        <>
          <div className="study-switches">
            {(
              [
                { key: "showSma20", label: "SMA 20" },
                { key: "showSma50", label: "SMA 50" },
                { key: "showRsi", label: "RSI 14" },
                { key: "showVolume", label: "Volume" },
                { key: "emaEnabled", label: `EMA ${preferences.emaPeriod}` },
                { key: "bollingerEnabled", label: "Bollinger bands" },
              ] satisfies Array<{
                key: keyof Pick<
                  ChartPreferences,
                  | "showSma20"
                  | "showSma50"
                  | "showRsi"
                  | "showVolume"
                  | "emaEnabled"
                  | "bollingerEnabled"
                >;
                label: string;
              }>
            ).map(({ key, label }) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={preferences[key]}
                  onChange={(event) =>
                    onUpdate({ [key]: event.currentTarget.checked })
                  }
                />
                {label}
              </label>
            ))}
          </div>
          <form
            key={`${preferences.emaPeriod}-${preferences.bollingerPeriod}-${preferences.bollingerDeviation}`}
            onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              const parsed = ChartPreferencesSchema.safeParse({
                ...preferences,
                emaPeriod: Number(form.get("ema")),
                bollingerPeriod: Number(form.get("period")),
                bollingerDeviation: Number(form.get("deviation")),
              });
              if (!parsed.success) {
                setError(
                  "Use periods from 2 to 200 and a band multiplier from 0.5 to 4.",
                );
                return;
              }
              onUpdate(parsed.data);
              setError(null);
            }}
          >
            <label>
              EMA period
              <input
                name="ema"
                type="number"
                min={2}
                max={200}
                step={1}
                defaultValue={preferences.emaPeriod}
                required
              />
            </label>
            <label>
              Bollinger period
              <input
                name="period"
                type="number"
                min={2}
                max={200}
                step={1}
                defaultValue={preferences.bollingerPeriod}
                required
              />
            </label>
            <label>
              Band multiplier
              <input
                name="deviation"
                type="number"
                min={0.5}
                max={4}
                step={0.5}
                defaultValue={preferences.bollingerDeviation}
                required
              />
            </label>
            <Button type="submit" variant="outline">
              Apply parameters
            </Button>
          </form>
          <p className="control-note">
            EMA uses an SMA seed. Bands use population σ; non-positive band
            values are omitted on log scales. Display studies never alter saved
            research.
          </p>
        </>
      )}
      {panel === "display" && (
        <div className="display-controls">
          <label>
            Price scale
            <select
              aria-label="Price scale"
              value={preferences.scaleMode}
              onChange={(event) => {
                const parsed = ChartPreferencesSchema.shape.scaleMode.safeParse(
                  event.currentTarget.value,
                );
                if (parsed.success) onUpdate({ scaleMode: parsed.data });
              }}
            >
              <option value="normal">Price</option>
              <option value="log">Logarithmic</option>
              <option value="percent">Percentage from first session</option>
              <option value="indexed">Indexed to 100</option>
            </select>
          </label>
          <label>
            Crosshair
            <select
              aria-label="Crosshair"
              value={preferences.crosshair}
              onChange={(event) =>
                onUpdate({
                  crosshair:
                    event.currentTarget.value === "magnet"
                      ? "magnet"
                      : "normal",
                })
              }
            >
              <option value="normal">Free</option>
              <option value="magnet">Magnet to price</option>
            </select>
          </label>
          <label className="check-control">
            <input
              type="checkbox"
              checked={preferences.showGrid}
              onChange={(event) =>
                onUpdate({ showGrid: event.currentTarget.checked })
              }
            />
            Show grid
          </label>
          <p className="control-note">
            Percentage and index scales share the first returned session as
            their anchor across prices and studies.
          </p>
        </div>
      )}
      {panel === "layouts" && (
        <>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget),
                name = String(form.get("name") ?? "").trim();
              if (!name) return;
              onSaveTemplate(name);
              setSaved(name);
              event.currentTarget.reset();
            }}
          >
            <label>
              Layout name
              <input
                name="name"
                maxLength={32}
                required
                placeholder="e.g. Trend study"
              />
            </label>
            <Button type="submit" variant="outline">
              Save current layout
            </Button>
          </form>
          {saved && (
            <p role="status" className="control-note">
              Saved {saved} on this browser.
            </p>
          )}
          <div className="layout-list">
            {templates.map((template) => (
              <div key={template.name}>
                <button
                  type="button"
                  onClick={() => onUpdate(template.preferences)}
                >
                  {template.name}
                  <small>
                    {template.preferences.chartType} ·{" "}
                    {template.preferences.scaleMode}
                  </small>
                </button>
                <Button
                  aria-label={`Remove layout ${template.name}`}
                  size="icon"
                  variant="ghost"
                  onClick={() => onRemoveTemplate(template.name)}
                >
                  <Trash2 size={13} />
                </Button>
              </div>
            ))}
          </div>
          <p className="control-note">
            Up to eight browser-local display layouts. No symbols, prices,
            datasets or credentials are stored.
          </p>
        </>
      )}
      {panel === "levels" && (
        <>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const raw = Number(
                new FormData(event.currentTarget).get("price"),
              );
              if (!Number.isFinite(raw) || raw <= 0) {
                setError("Enter a positive price.");
                return;
              }
              onAddLevel(raw);
              setError(null);
              event.currentTarget.reset();
            }}
          >
            <label>
              Price level
              <input
                name="price"
                type="number"
                min="0.000001"
                step="any"
                required
              />
            </label>
            <Button
              type="submit"
              variant="outline"
              disabled={levels.length >= 12}
            >
              Add horizontal level
            </Button>
          </form>
          <div className="layout-list">
            {levels.map((level) => (
              <div key={level.id}>
                <span>
                  {level.price.toLocaleString("en-US", {
                    maximumFractionDigits: 6,
                  })}
                </span>
                <Button
                  aria-label={`Remove level ${level.price}`}
                  variant="ghost"
                  size="icon"
                  onClick={() => onRemoveLevel(level.id)}
                >
                  <Trash2 size={13} />
                </Button>
              </div>
            ))}
          </div>
          <p className="control-note">
            Session-local levels for this instrument and data mode. They are
            annotations, not orders.
          </p>
        </>
      )}
      {error && (
        <p role="alert" className="text-negative">
          {error}
        </p>
      )}
      {storageError && (
        <p role="status" className="control-note">
          {storageError}
        </p>
      )}
    </aside>
  );
}
