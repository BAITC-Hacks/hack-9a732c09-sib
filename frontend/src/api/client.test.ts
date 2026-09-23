import { describe, expect, it, vi } from "vitest";

import runAcceptedFixture from "../../../contracts/examples/run-accepted.json";
import runCompletedFixture from "../../../contracts/examples/run-completed.json";
import runFailedFixture from "../../../contracts/examples/run-failed.json";
import runRunningFixture from "../../../contracts/examples/run-running.json";

import { AnalystApiClient } from "./client";
import { RunPollingTimeoutError } from "./errors";
import type {
  ApiTransport,
  CaseSummary,
  RunAccepted,
  RunCompleted,
  RunFailed,
  RunRequest,
  RunSnapshot,
} from "./types";

const accepted = runAcceptedFixture as unknown as RunAccepted;
const completed = runCompletedFixture as unknown as RunCompleted;
const failed = runFailedFixture as unknown as RunFailed;
const running = runRunningFixture as unknown as RunSnapshot;

function transportWith(snapshots: RunSnapshot[], acceptedValue = accepted) {
  const getRun = vi.fn<() => Promise<RunSnapshot>>();
  snapshots.forEach((snapshot) => getRun.mockResolvedValueOnce(snapshot));

  const transport: ApiTransport = {
    getCaseSummary: vi.fn<() => Promise<CaseSummary>>(),
    createRun: vi.fn<(request: RunRequest) => Promise<RunAccepted>>().mockResolvedValue(acceptedValue),
    getRun,
  };
  return { transport, getRun };
}

describe("AnalystApiClient", () => {
  it("always performs GET after a terminal-looking 202 response", async () => {
    const terminalAccepted: RunAccepted = { ...accepted, status: "completed" };
    const { transport, getRun } = transportWith([completed], terminalAccepted);
    const client = new AnalystApiClient(transport);

    const result = await client.createAndPoll({ seed: 42, mode: "mock" });

    expect(result.status).toBe("completed");
    expect(getRun).toHaveBeenCalledTimes(1);
    expect(getRun).toHaveBeenCalledWith(accepted.run_id, expect.anything());
  });

  it("polls pending snapshots and keeps pilots separate from final campaigns", async () => {
    const queued: RunSnapshot = { ...running, status: "queued" };
    const wait = vi.fn<() => Promise<void>>().mockResolvedValue(undefined);
    const { transport, getRun } = transportWith([queued, running, completed]);
    const onSnapshot = vi.fn();
    const client = new AnalystApiClient(transport, { wait });

    const result = await client.createAndPoll(
      { seed: 42, mode: "mock" },
      { onSnapshot },
    );

    expect(result).toEqual(completed);
    expect(getRun).toHaveBeenCalledTimes(3);
    expect(wait).toHaveBeenCalledTimes(2);
    expect(wait).toHaveBeenNthCalledWith(1, 1_000, undefined);
    expect(onSnapshot.mock.calls.map(([snapshot]) => snapshot.status)).toEqual([
      "queued",
      "running",
      "completed",
    ]);
    expect(completed.n_campaigns).toBe(completed.campaigns.length);
    expect(completed.n_pilots).toBe(completed.pilots.length);
  });

  it("returns an execution failure received with HTTP-success semantics", async () => {
    const { transport } = transportWith([failed]);
    const client = new AnalystApiClient(transport);

    await expect(
      client.createAndPoll({ seed: 13, mode: "mock" }),
    ).resolves.toMatchObject({ status: "failed", error: { code: "RUN_FAILED" } });
  });

  it("stops polling at the configured deadline and preserves run id", async () => {
    const { transport, getRun } = transportWith([running]);
    const now = vi
      .fn()
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(5_001);
    const client = new AnalystApiClient(transport, {
      timeoutMs: 5_000,
      now,
      wait: vi.fn(),
    });

    await expect(client.pollRun(accepted.run_id)).rejects.toEqual(
      expect.objectContaining<Partial<RunPollingTimeoutError>>({
        name: "RunPollingTimeoutError",
        runId: accepted.run_id,
      }),
    );
    expect(getRun).toHaveBeenCalledTimes(1);
  });

  it("times out a GET that never settles", async () => {
    const transport: ApiTransport = {
      getCaseSummary: vi.fn<() => Promise<CaseSummary>>(),
      createRun: vi.fn<(request: RunRequest) => Promise<RunAccepted>>(),
      getRun: vi.fn(() => new Promise<RunSnapshot>(() => undefined)),
    };
    const client = new AnalystApiClient(transport, { timeoutMs: 5 });

    await expect(client.pollRun(accepted.run_id)).rejects.toMatchObject({
      name: "RunPollingTimeoutError",
      runId: accepted.run_id,
    });
  });
});
