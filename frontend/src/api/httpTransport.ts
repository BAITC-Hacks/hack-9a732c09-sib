import { ApiError, isErrorResponse } from "./errors";
import type {
  ApiTransport,
  CaseSummary,
  RunAccepted,
  RunRequest,
  RunSnapshot,
} from "./types";

type FetchImplementation = typeof fetch;

function normalizeOrigin(origin: string): string {
  const value = origin.trim();
  if (!value) {
    throw new Error("VITE_API_BASE_URL must be a non-empty origin.");
  }

  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("VITE_API_BASE_URL must be an absolute HTTP(S) origin.");
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("VITE_API_BASE_URL must use HTTP or HTTPS.");
  }
  if (url.username || url.password || url.search || url.hash) {
    throw new Error("VITE_API_BASE_URL must be an origin without credentials, query, or fragment.");
  }

  const pathname = url.pathname.replace(/\/+$/, "") || "/";
  if (pathname === "/api/v1") {
    throw new Error("VITE_API_BASE_URL must not include /api/v1.");
  }
  if (pathname !== "/") {
    throw new Error("VITE_API_BASE_URL must be an origin without a path.");
  }
  return url.origin;
}

export class HttpTransport implements ApiTransport {
  private readonly origin: string;

  constructor(
    origin: string,
    private readonly fetchImplementation: FetchImplementation = fetch,
  ) {
    this.origin = normalizeOrigin(origin);
  }

  getCaseSummary(signal?: AbortSignal): Promise<CaseSummary> {
    return this.request<CaseSummary>("/api/v1/case/summary", {
      method: "GET",
      signal,
      expectedStatus: 200,
    });
  }

  createRun(request: RunRequest, signal?: AbortSignal): Promise<RunAccepted> {
    return this.request<RunAccepted>("/api/v1/runs", {
      method: "POST",
      signal,
      expectedStatus: 202,
      body: JSON.stringify(request),
    });
  }

  getRun(runId: string, signal?: AbortSignal): Promise<RunSnapshot> {
    return this.request<RunSnapshot>(
      `/api/v1/runs/${encodeURIComponent(runId)}`,
      { method: "GET", signal, expectedStatus: 200 },
    );
  }

  private async request<T>(
    path: string,
    options: RequestInit & { expectedStatus: number },
  ): Promise<T> {
    const { expectedStatus, ...requestOptions } = options;
    const headers = new Headers(options.headers);
    headers.set("Accept", "application/json");
    if (options.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }

    const response = await this.fetchImplementation(`${this.origin}${path}`, {
      ...requestOptions,
      headers,
    });

    const payload = await this.readJson(response);
    if (!response.ok || response.status !== expectedStatus) {
      if (isErrorResponse(payload)) {
        throw new ApiError(payload.error.message, {
          status: response.status,
          code: payload.error.code,
          details: payload.error.details,
        });
      }

      throw new ApiError(`API вернул HTTP ${response.status}.`, {
        status: response.status,
        code: "UNEXPECTED_HTTP_RESPONSE",
      });
    }

    return payload as T;
  }

  private async readJson(response: Response): Promise<unknown> {
    try {
      return await response.json();
    } catch {
      throw new ApiError("API вернул ответ не в формате JSON.", {
        status: response.status,
        code: "INVALID_JSON_RESPONSE",
      });
    }
  }
}
