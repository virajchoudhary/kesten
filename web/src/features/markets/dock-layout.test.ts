import { describe, expect, it } from "vitest";
import { dockHeightLimit } from "./dock-layout";
describe("research panel viewport budget", () => {
  it("reserves usable chart space at desktop and tablet sizes", () => {
    expect(dockHeightLimit(900, 1440)).toBe(420);
    expect(dockHeightLimit(1080, 1920)).toBe(600);
    expect(dockHeightLimit(1180, 820)).toBe(660);
  });
  it("bounds small and oversized windows", () => {
    expect(dockHeightLimit(600, 1440)).toBe(220);
    expect(dockHeightLimit(2160, 3840)).toBe(700);
  });
});
