import type { RunCompleted, RunFailed, RunStatus, Source } from "./api/types";

export interface DisplayError {
  title: string;
  message: string;
  code?: string;
  status?: number;
  details: string[];
}

export type RunUiState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | {
      kind: "polling";
      runId: string;
      lifecycleStatus: RunStatus;
      source: Source;
    }
  | { kind: "completed"; snapshot: RunCompleted }
  | { kind: "failed"; snapshot: RunFailed }
  | { kind: "timeout"; runId: string; message: string }
  | { kind: "error"; error: DisplayError; runId?: string };
