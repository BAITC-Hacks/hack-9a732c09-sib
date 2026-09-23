import { RunPollingTimeoutError } from "./errors";
import type {
  ApiTransport,
  CaseSummary,
  RunAccepted,
  RunRequest,
  RunSnapshot,
  TerminalRun,
} from "./types";

export interface PollOptions {
  signal?: AbortSignal;
  onSnapshot?: (snapshot: RunSnapshot) => void;
}

export interface CreateAndPollOptions extends PollOptions {
  onAccepted?: (accepted: RunAccepted) => void;
}

interface ApiClientOptions {
  pollIntervalMs?: number;
  timeoutMs?: number;
  now?: () => number;
  wait?: (delayMs: number, signal?: AbortSignal) => Promise<void>;
}

function abortError(): DOMException {
  return new DOMException("The operation was aborted.", "AbortError");
}

export function waitFor(delayMs: number, signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) {
    return Promise.reject(signal.reason ?? abortError());
  }

  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, delayMs);

    function onAbort(): void {
      window.clearTimeout(timer);
      reject(signal?.reason ?? abortError());
    }

    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

export class AnalystApiClient {
  private readonly pollIntervalMs: number;
  private readonly timeoutMs: number;
  private readonly now: () => number;
  private readonly wait: (delayMs: number, signal?: AbortSignal) => Promise<void>;

  constructor(
    private readonly transport: ApiTransport,
    options: ApiClientOptions = {},
  ) {
    this.pollIntervalMs = options.pollIntervalMs ?? 1_000;
    this.timeoutMs = options.timeoutMs ?? 5 * 60 * 1_000;
    this.now = options.now ?? Date.now;
    this.wait = options.wait ?? waitFor;
  }

  getCaseSummary(signal?: AbortSignal): Promise<CaseSummary> {
    return this.transport.getCaseSummary(signal);
  }

  async createAndPoll(
    request: RunRequest,
    options: CreateAndPollOptions = {},
  ): Promise<TerminalRun> {
    const accepted = await this.transport.createRun(request, options.signal);
    options.onAccepted?.(accepted);

    // RunAccepted never contains a result. GET is mandatory even when POST says
    // that a synchronous implementation has already completed or failed.
    return this.pollRun(accepted.run_id, options);
  }

  async pollRun(
    runId: string,
    options: PollOptions = {},
  ): Promise<TerminalRun> {
    const startedAt = this.now();

    while (true) {
      const elapsedBeforeRequest = this.now() - startedAt;
      if (elapsedBeforeRequest >= this.timeoutMs) {
        throw new RunPollingTimeoutError(runId);
      }

      const snapshot = await this.getRunBeforeDeadline(
        runId,
        this.timeoutMs - elapsedBeforeRequest,
        options.signal,
      );
      options.onSnapshot?.(snapshot);

      if (snapshot.status === "completed" || snapshot.status === "failed") {
        return snapshot;
      }

      const elapsedMs = this.now() - startedAt;
      if (elapsedMs >= this.timeoutMs) {
        throw new RunPollingTimeoutError(runId);
      }

      await this.wait(
        Math.min(this.pollIntervalMs, this.timeoutMs - elapsedMs),
        options.signal,
      );
    }
  }

  private async getRunBeforeDeadline(
    runId: string,
    remainingMs: number,
    externalSignal?: AbortSignal,
  ): Promise<RunSnapshot> {
    if (externalSignal?.aborted) {
      throw externalSignal.reason ?? abortError();
    }

    const controller = new AbortController();
    let timeoutId: number | undefined;
    let onExternalAbort: (() => void) | undefined;

    const timeoutPromise = new Promise<never>((_, reject) => {
      timeoutId = window.setTimeout(() => {
        const error = new RunPollingTimeoutError(runId);
        controller.abort(error);
        reject(error);
      }, remainingMs);
    });

    const races: Array<Promise<RunSnapshot>> = [
      this.transport.getRun(runId, controller.signal),
      timeoutPromise,
    ];

    if (externalSignal) {
      races.push(
        new Promise<never>((_, reject) => {
          onExternalAbort = () => {
            const reason = externalSignal.reason ?? abortError();
            controller.abort(reason);
            reject(reason);
          };
          externalSignal.addEventListener("abort", onExternalAbort, {
            once: true,
          });
        }),
      );
    }

    try {
      return await Promise.race(races);
    } finally {
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
      if (externalSignal && onExternalAbort) {
        externalSignal.removeEventListener("abort", onExternalAbort);
      }
    }
  }
}
