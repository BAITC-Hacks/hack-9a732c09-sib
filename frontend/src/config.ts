import { AnalystApiClient } from "./api/client";
import { HttpTransport } from "./api/httpTransport";
import { MockTransport, type MockScenario } from "./api/mockTransport";

export interface RuntimeConfig {
  useMocks: boolean;
  apiBaseUrl: string;
}

export function readRuntimeConfig(env: ImportMetaEnv = import.meta.env): RuntimeConfig {
  return {
    useMocks: env.VITE_USE_MOCKS?.trim().toLowerCase() !== "false",
    apiBaseUrl: env.VITE_API_BASE_URL?.trim() || "http://localhost:8000",
  };
}

export function createApiClient(
  config: RuntimeConfig,
  scenario: MockScenario = "completed",
): AnalystApiClient {
  const transport = config.useMocks
    ? new MockTransport({ scenario })
    : new HttpTransport(config.apiBaseUrl);

  return new AnalystApiClient(transport, {
    // The timeout scenario is a UI demonstrator. HTTP and every other mode keep
    // the contract's five-minute deadline.
    timeoutMs: config.useMocks && scenario === "timeout" ? 5_000 : undefined,
  });
}
