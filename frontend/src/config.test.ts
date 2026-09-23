import { describe, expect, it } from "vitest";

import { readRuntimeConfig } from "./config";

describe("readRuntimeConfig", () => {
  it("uses mock data when the mode is omitted", () => {
    expect(readRuntimeConfig({} as ImportMetaEnv)).toMatchObject({
      useMocks: true,
      apiBaseUrl: "http://localhost:8000",
    });
  });

  it("selects the real transport only for an explicit false value", () => {
    expect(
      readRuntimeConfig({
        VITE_USE_MOCKS: " false ",
        VITE_API_BASE_URL: " http://127.0.0.1:8000 ",
      } as ImportMetaEnv),
    ).toEqual({ useMocks: false, apiBaseUrl: "http://127.0.0.1:8000" });
  });

  it("rejects a misspelled mode instead of silently showing fixtures", () => {
    expect(() => readRuntimeConfig({ VITE_USE_MOCKS: "flase" } as ImportMetaEnv)).toThrow(
      "VITE_USE_MOCKS must be either true or false.",
    );
  });
});
