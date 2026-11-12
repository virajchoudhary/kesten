import { afterEach, describe, expect, it, vi } from "vitest";
afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});
describe("revisable product identity", () => {
  it("defaults to the selected Kerquant identity", async () => {
    vi.stubEnv("NEXT_PUBLIC_PRODUCT_NAME", "");
    vi.stubEnv("NEXT_PUBLIC_PRODUCT_SHORT_NAME", "");
    vi.resetModules();
    expect((await import("./brand")).brand).toMatchObject({
      name: "Kerquant",
      shortName: "Kerquant",
    });
  });
  it("uses the configured full name when no short name is set", async () => {
    vi.stubEnv("NEXT_PUBLIC_PRODUCT_NAME", "  Kerquant Research  ");
    vi.stubEnv("NEXT_PUBLIC_PRODUCT_SHORT_NAME", "");
    vi.resetModules();
    expect((await import("./brand")).brand).toMatchObject({
      name: "Kerquant Research",
      shortName: "Kerquant Research",
    });
  });
  it("respects alternate display names without changing persistent identifiers", async () => {
    vi.stubEnv("NEXT_PUBLIC_PRODUCT_NAME", "  Alternate Research  ");
    vi.stubEnv("NEXT_PUBLIC_PRODUCT_SHORT_NAME", "  AR  ");
    vi.resetModules();
    expect((await import("./brand")).brand).toMatchObject({
      name: "Alternate Research",
      shortName: "AR",
    });
  });
});
