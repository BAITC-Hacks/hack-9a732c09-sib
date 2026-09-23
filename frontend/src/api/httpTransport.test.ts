import { describe, expect, it, vi } from "vitest";

import errorFixture from "../../../contracts/examples/error.json";
import runAcceptedFixture from "../../../contracts/examples/run-accepted.json";

import { ApiError } from "./errors";
import { HttpTransport } from "./httpTransport";

describe("HttpTransport", () => {
  it("posts the contract body to an origin-only base URL and requires 202", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(runAcceptedFixture), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const transport = new HttpTransport("http://localhost:8000/", fetchMock);

    await transport.createRun({ seed: 42, mode: "mock" });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/v1/runs");
    expect(options?.method).toBe("POST");
    expect(options?.body).toBe('{"seed":42,"mode":"mock"}');
    expect(new Headers(options?.headers).get("Content-Type")).toBe("application/json");
  });

  it("treats HTTP 200 on POST as a protocol error", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(runAcceptedFixture), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const transport = new HttpTransport("http://localhost:8000", fetchMock);

    await expect(
      transport.createRun({ seed: 42, mode: "mock" }),
    ).rejects.toMatchObject({
      status: 200,
      code: "UNEXPECTED_HTTP_RESPONSE",
    });
  });

  it("preserves structured ErrorResponse fields", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(errorFixture), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const transport = new HttpTransport("http://localhost:8000", fetchMock);

    const request = transport.getRun("missing-run");
    await expect(request).rejects.toBeInstanceOf(ApiError);
    await expect(request).rejects.toMatchObject({
      status: 404,
      code: "RUN_NOT_FOUND",
      message: "Run was not found.",
      details: [],
    });
  });

  it("rejects a base URL that already includes the API prefix", () => {
    expect(
      () => new HttpTransport("http://localhost:8000/api/v1", vi.fn()),
    ).toThrow("must not include /api/v1");
  });

  it("gets the case summary from the API prefix", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ source: "mock_environment" }), { status: 200 }),
    );
    const transport = new HttpTransport("http://localhost:8000", fetchMock);

    await transport.getCaseSummary();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/case/summary",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it.each([
    "relative/path",
    "ftp://localhost:8000",
    "http://user:pass@localhost:8000",
    "http://localhost:8000/other",
    "http://localhost:8000?debug=true",
    "http://localhost:8000#fragment",
  ])("rejects a non-origin API base URL: %s", (baseUrl) => {
    expect(() => new HttpTransport(baseUrl, vi.fn())).toThrow();
  });
});
