"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

import { lineSegments, type ResearchPoint } from "./research-series";
import { formatSessionDate, formatUtcTimestamp } from "./research-formatters";

const SERIES = [
  {
    field: "actual",
    color: "var(--observed-series)",
    label: "Dataset value",
    dash: undefined,
  },
  {
    field: "selected",
    color: "var(--forecast-series)",
    label: "Selected reference",
    dash: undefined,
  },
  {
    field: "baseline",
    color: "var(--chart-sma20)",
    label: "Last close benchmark",
    dash: "5 4",
  },
] satisfies ReadonlyArray<{
  field: "actual" | "selected" | "baseline";
  color: string;
  label: string;
  dash: string | undefined;
}>;
const exactValue = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 6,
});
const axisValue = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumSignificantDigits: 4,
});

type TargetWindow = "20" | "60" | "all";
const TARGET_WINDOWS: ReadonlyArray<{
  value: TargetWindow;
  label: string;
}> = [
  { value: "20", label: "Show last 20 targets" },
  { value: "60", label: "Show last 60 targets" },
  { value: "all", label: "Show all targets" },
];

export function ResearchLineChart({
  points,
  title,
  focusLabel,
  errors = false,
  compact = false,
}: {
  points: readonly ResearchPoint[];
  title: string;
  focusLabel: string;
  errors?: boolean;
  compact?: boolean;
}): React.JSX.Element {
  const height = compact ? 190 : 292;
  const plotHeight = height - 68;
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(900);
  const [cursor, setCursor] = useState<number | null>(null);
  const [pinnedIndex, setPinnedIndex] = useState<number | null>(null);
  const [targetWindow, setTargetWindow] = useState<TargetWindow>("all");
  const id = useId();
  useEffect(() => {
    const node = container.current;
    if (!node || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(Math.max(280, Math.floor(entry.contentRect.width)));
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  const visible = useMemo(
    () =>
      targetWindow === "all" ? points : points.slice(-Number(targetWindow)),
    [points, targetWindow],
  );
  const geometry = useMemo(() => {
    const values = visible
      .flatMap((p) => [p.actual, p.selected, p.baseline])
      .filter((v) => v !== null);
    const low = Math.min(0, ...values);
    const minimum = errors ? low : Math.min(...values);
    const maximum = Math.max(...values, errors ? 0 : -Infinity);
    const padding =
      (maximum - minimum) * 0.1 || Math.max(Math.abs(maximum) * 0.02, 0.01);
    const bottom = minimum - padding,
      top = maximum + padding;
    const x = (i: number) =>
      78 + (i / Math.max(visible.length - 1, 1)) * (width - 96);
    const y = (v: number) => 24 + ((top - v) / (top - bottom)) * plotHeight;
    return {
      x,
      y,
      top,
      bottom,
      paths: SERIES.map((s) => lineSegments(visible, s.field, x, y)),
    };
  }, [visible, width, errors, plotHeight]);
  const selectedIndex = Math.min(
    pinnedIndex ?? cursor ?? visible.length - 1,
    visible.length - 1,
  );
  const selected = visible[selectedIndex];
  function indexAtPointer(
    event: Pick<React.PointerEvent<SVGSVGElement>, "clientX" | "currentTarget">,
  ): number | null {
    if (visible.length === 0) {
      return null;
    }
    if (visible.length === 1) {
      return 0;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width <= 0) {
      return null;
    }
    const index = Math.round(
      ((((event.clientX - rect.left) / rect.width) * width - 78) /
        (width - 96)) *
        (visible.length - 1),
    );
    return Math.max(0, Math.min(visible.length - 1, index));
  }
  if (!selected)
    return (
      <p className="p-4 text-sm text-secondary">
        No evaluation targets in this view.
      </p>
    );
  const bands = visible.flatMap((point, i) =>
    i === 0 || visible[i - 1]?.period !== point.period
      ? [{ period: point.period, index: i }]
      : [],
  );
  return (
    <div className="min-w-0 px-4 py-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="text-secondary">
          {errors ? "Forecast minus actual" : "Split-neutral close"} · USD per
          initial share
        </span>
        <div
          aria-label="Target window"
          className="flex flex-wrap gap-1"
          role="group"
        >
          {TARGET_WINDOWS.map(({ value, label }) => (
            <button
              aria-pressed={targetWindow === value}
              className={`min-h-9 rounded-control border border-control px-2.5 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
                targetWindow === value
                  ? "bg-raised text-foreground"
                  : "text-secondary"
              }`}
              key={value}
              onClick={() => {
                setTargetWindow(value);
                setCursor(null);
                setPinnedIndex(null);
              }}
              type="button"
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div
        className="flex flex-wrap gap-x-5 gap-y-2 text-xs"
        aria-label="Chart legend"
      >
        {SERIES.map((s) => (
          <span className="inline-flex items-center gap-2" key={s.field}>
            <span
              className="h-0.5 w-5"
              style={{ backgroundColor: s.color }}
              aria-hidden="true"
            />
            {s.field === "selected"
              ? focusLabel
              : s.field === "actual" && errors
                ? "Zero error"
                : s.label}
          </span>
        ))}
      </div>
      <div ref={container} className="mt-2 min-w-0">
        <svg
          className="block w-full"
          style={{ height }}
          role="img"
          aria-labelledby={`${id}-title ${id}-description`}
          viewBox={`0 0 ${width} ${height}`}
          onPointerMove={(event) => {
            if (pinnedIndex !== null) {
              return;
            }
            const index = indexAtPointer(event);
            if (index !== null) {
              setCursor(index);
            }
          }}
          onClick={(event) => {
            const index = indexAtPointer(event);
            if (index !== null) {
              setCursor(index);
              setPinnedIndex((current) => (current === index ? null : index));
            }
          }}
        >
          <title id={`${id}-title`}>{title}</title>
          <desc id={`${id}-description`}>
            Dataset values and reference paths. Inspect exact dates and values
            with the session slider below. Shaded regions distinguish evaluation
            periods. No uncertainty intervals.
          </desc>
          {bands.map((band, i) => (
            <rect
              key={`${band.period}-${band.index}`}
              x={geometry.x(band.index)}
              y={24}
              width={Math.max(
                0,
                geometry.x(bands[i + 1]?.index ?? visible.length - 1) -
                  geometry.x(band.index),
              )}
              height={plotHeight}
              fill={
                band.period === "test" ? "var(--chart-sma50)" : "var(--accent)"
              }
              opacity={band.period === "history" ? 0 : 0.07}
            />
          ))}
          {[0, 1, 2, 3, 4].map((n) => {
            const v = geometry.top - ((geometry.top - geometry.bottom) * n) / 4;
            return (
              <g key={n} aria-hidden="true">
                <line
                  x1={78}
                  x2={width - 18}
                  y1={geometry.y(v)}
                  y2={geometry.y(v)}
                  stroke="var(--chart-grid)"
                />
                <text
                  x={68}
                  y={geometry.y(v) + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="var(--text-secondary)"
                >
                  {axisValue.format(v)}
                </text>
              </g>
            );
          })}
          {SERIES.flatMap((s, i) =>
            geometry.paths[i]?.map((segment, j) => (
              <polyline
                key={`${s.field}-${j}`}
                points={segment}
                fill="none"
                stroke={s.color}
                strokeWidth={s.field === "selected" ? 2.5 : 1.8}
                strokeDasharray={s.dash}
                strokeLinejoin="round"
              />
            )),
          )}
          <line
            x1={geometry.x(selectedIndex)}
            x2={geometry.x(selectedIndex)}
            y1={24}
            y2={height - 44}
            stroke="var(--chart-crosshair)"
            strokeDasharray="3 4"
          />
          {SERIES.map((s) => {
            const v = selected[s.field];
            return v === null ? null : (
              <circle
                key={s.field}
                cx={geometry.x(selectedIndex)}
                cy={geometry.y(v)}
                r={3.5}
                fill={s.color}
                stroke="var(--surface)"
              />
            );
          })}
          {[0, visible.length - 1].map((index, i) => (
            <text
              key={i}
              aria-hidden="true"
              x={geometry.x(index)}
              y={height - 18}
              textAnchor={i === 0 ? "start" : "end"}
              fontSize="11"
              fill="var(--text-secondary)"
            >
              {formatSessionDate(visible[index]?.time ?? selected.time)}
            </text>
          ))}
        </svg>
      </div>
      <label htmlFor={`${id}-session`} className="text-xs font-medium">
        Inspect session · {formatSessionDate(selected.time)} · {selected.period}
        {pinnedIndex !== null ? " · pinned" : ""}
      </label>
      <input
        id={`${id}-session`}
        aria-label="Inspect chart session"
        aria-valuetext={`${formatSessionDate(selected.time)}, ${selected.period}, ${focusLabel}: ${selected.selected === null ? "not available" : exactValue.format(selected.selected)}`}
        className="my-2 block min-h-6 w-full accent-accent"
        type="range"
        min={0}
        max={visible.length - 1}
        value={selectedIndex}
        onChange={(event) => {
          const index = Number(event.currentTarget.value);
          setCursor(index);
          setPinnedIndex((current) => (current === null ? null : index));
        }}
      />
      <button
        aria-pressed={pinnedIndex !== null}
        className={`mb-3 min-h-9 rounded-control border border-control px-3 text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
          pinnedIndex !== null ? "bg-raised text-foreground" : "text-secondary"
        }`}
        onClick={() => {
          if (pinnedIndex === null) {
            setPinnedIndex(selectedIndex);
          } else {
            setCursor(pinnedIndex);
            setPinnedIndex(null);
          }
        }}
        type="button"
      >
        {pinnedIndex === null ? "Pin selected target" : "Unpin selected target"}
      </button>
      <dl className="grid grid-cols-1 gap-3 rounded-control border border-border-subtle bg-raised p-3 text-xs sm:grid-cols-3">
        {SERIES.map((s) => {
          const value = selected[s.field];
          return (
            <div key={s.field}>
              <dt className="text-secondary">
                {s.field === "selected"
                  ? focusLabel
                  : s.field === "actual" && errors
                    ? "Zero error"
                    : s.label}
              </dt>
              <dd className="mt-1 break-all font-mono">
                {value === null ? "Not available" : exactValue.format(value)}
              </dd>
            </div>
          );
        })}
      </dl>
      {selected.origin && (
        <p className="mt-2 break-words text-xs text-secondary">
          Origin {formatSessionDate(selected.origin)}
          {selected.cutoff
            ? ` · information cutoff ${formatUtcTimestamp(selected.cutoff)}`
            : ""}
        </p>
      )}
    </div>
  );
}
