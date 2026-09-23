import type { ErrorResponse } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: string[];

  constructor(
    message: string,
    options: { status: number; code: string; details?: string[] },
  ) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details ?? [];
  }
}

export class RunPollingTimeoutError extends Error {
  readonly runId: string;

  constructor(runId: string) {
    super("Сервер не завершил расчёт в отведённое время.");
    this.name = "RunPollingTimeoutError";
    this.runId = runId;
  }
}

export function isErrorResponse(value: unknown): value is ErrorResponse {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }

  const error = value.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string" &&
    "details" in error &&
    Array.isArray(error.details) &&
    error.details.every((detail) => typeof detail === "string")
  );
}
