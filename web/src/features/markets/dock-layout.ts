export function dockHeightLimit(height: number, width: number): number {
  return Math.max(220, Math.min(700, height - (width < 1100 ? 520 : 480)));
}
