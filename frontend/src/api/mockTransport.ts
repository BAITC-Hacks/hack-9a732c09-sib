import caseSummaryFixture from "../../../contracts/examples/case-summary.json";
import errorFixture from "../../../contracts/examples/error.json";
import runAcceptedFixture from "../../../contracts/examples/run-accepted.json";
import runCompletedFixture from "../../../contracts/examples/run-completed.json";
import runFailedFixture from "../../../contracts/examples/run-failed.json";
import runRunningFixture from "../../../contracts/examples/run-running.json";

import { ApiError } from "./errors";
import type {
  ApiTransport,
  CaseSummary,
  ErrorResponse,
  RunAccepted,
  RunCompleted,
  RunFailed,
  RunRequest,
  RunSnapshot,
} from "./types";

export type MockScenario =
  | "completed"
  | "instant"
  | "zero-cost"
  | "negative"
  | "failed"
  | "http-error"
  | "timeout";

interface MockTransportOptions {
  scenario?: MockScenario;
  latencyMs?: number;
}

interface StoredRun {
  reads: number;
  accepted: RunAccepted;
}

const caseSummary = caseSummaryFixture as unknown as CaseSummary;
const acceptedFixture = runAcceptedFixture as unknown as RunAccepted;
const completedFixture = runCompletedFixture as unknown as RunCompleted;
const failedFixture = runFailedFixture as unknown as RunFailed;
const runningFixture = runRunningFixture as unknown as RunSnapshot;
const notFoundFixture = errorFixture as unknown as ErrorResponse;

function clone<T>(value: T): T {
  return structuredClone(value);
}

function abortError(): DOMException {
  return new DOMException("The operation was aborted.", "AbortError");
}

function fixtureRunId(seed: number): string {
  const suffix = seed.toString(16).padStart(12, "0").slice(-12);
  return `00000000-0000-4000-8000-${suffix}`;
}

function negativeCompletedRun(): RunCompleted {
  const result = clone(completedFixture);
  result.gross_arpu_lift = 2_500;
  result.total_cost = 5_308;
  result.net_arpu_gain = -2_808;
  result.total_arpu_after = 150_638_276.24626842;
  result.growth_vs_baseline_pct = -0.0018640466150071047;
  result.roi = 0.47098681235870384;
  result.risk_score_pct = 18.4;
  result.campaigns_detail = result.campaigns_detail.map((detail) => ({
    ...detail,
    gross_lift: detail.kind === "pilot" ? 500 : 2_500,
    n_negative: detail.kind === "pilot" ? 9 : 226,
  }));
  result.warnings = [
    "Illustrative negative fixture: completed is a lifecycle status, not a profitability label.",
  ];
  return result;
}

function zeroCostCompletedRun(): RunCompleted {
  const result = clone(completedFixture);
  result.total_cost = 0;
  result.net_arpu_gain = 122_700;
  result.total_arpu_after = 150_763_784.24626842;
  result.growth_vs_baseline_pct = 0.08145188320565307;
  result.roi = null;
  result.remaining_budget = 100_000;
  result.pilots = result.pilots.map((pilot) => ({
    ...pilot,
    channel: "push",
    cost: 0,
    remaining_budget: 100_000,
  }));
  result.campaigns = result.campaigns.map((campaign) => ({
    ...campaign,
    channel: "push",
  }));
  result.campaigns_detail = result.campaigns_detail.map((detail) => ({
    ...detail,
    channel: "push",
    cost: 0,
  }));
  result.warnings = [
    "ROI is null because the push-only illustrative fixture has zero cost.",
    "Illustrative fixture, not a strategy execution; risk is not calculated.",
  ];
  return result;
}

export class MockTransport implements ApiTransport {
  private readonly scenario: MockScenario;
  private readonly latencyMs: number;
  private readonly runs = new Map<string, StoredRun>();

  constructor(options: MockTransportOptions = {}) {
    this.scenario = options.scenario ?? "completed";
    this.latencyMs = options.latencyMs ?? 180;
  }

  async getCaseSummary(signal?: AbortSignal): Promise<CaseSummary> {
    await this.delay(signal);
    return clone(caseSummary);
  }

  async createRun(
    request: RunRequest,
    signal?: AbortSignal,
  ): Promise<RunAccepted> {
    await this.delay(signal);
    const runId = fixtureRunId(request.seed);
    const accepted: RunAccepted = {
      ...clone(acceptedFixture),
      run_id: runId,
      status: this.scenario === "instant" ? "completed" : "queued",
    };
    this.runs.set(runId, { reads: 0, accepted });
    return clone(accepted);
  }

  async getRun(runId: string, signal?: AbortSignal): Promise<RunSnapshot> {
    await this.delay(signal);
    const stored = this.runs.get(runId);
    if (!stored) {
      throw new ApiError(notFoundFixture.error.message, {
        status: 404,
        code: notFoundFixture.error.code,
        details: notFoundFixture.error.details,
      });
    }

    stored.reads += 1;
    if (this.scenario === "http-error") {
      throw new ApiError("Mock API is temporarily unavailable.", {
        status: 503,
        code: "MOCK_API_UNAVAILABLE",
      });
    }

    if (
      this.scenario === "timeout" ||
      (stored.reads === 1 && this.scenario !== "instant")
    ) {
      return {
        ...clone(runningFixture),
        run_id: runId,
        created_at: stored.accepted.created_at,
      };
    }

    if (this.scenario === "failed") {
      return this.withIdentity(clone(failedFixture), stored);
    }

    const completed =
      this.scenario === "negative"
        ? negativeCompletedRun()
        : this.scenario === "zero-cost"
          ? zeroCostCompletedRun()
          : clone(completedFixture);
    return this.withIdentity(completed, stored);
  }

  private withIdentity<T extends RunCompleted | RunFailed>(
    snapshot: T,
    stored: StoredRun,
  ): T {
    snapshot.run_id = stored.accepted.run_id;
    snapshot.created_at = stored.accepted.created_at;
    return snapshot;
  }

  private delay(signal?: AbortSignal): Promise<void> {
    if (signal?.aborted) {
      return Promise.reject(signal.reason ?? abortError());
    }

    return new Promise((resolve, reject) => {
      const timer = window.setTimeout(() => {
        signal?.removeEventListener("abort", onAbort);
        resolve();
      }, this.latencyMs);

      function onAbort(): void {
        window.clearTimeout(timer);
        reject(signal?.reason ?? abortError());
      }

      signal?.addEventListener("abort", onAbort, { once: true });
    });
  }
}
