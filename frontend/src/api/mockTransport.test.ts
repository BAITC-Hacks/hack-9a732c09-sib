import { describe, expect, it } from "vitest";

import { MockTransport } from "./mockTransport";

describe("MockTransport", () => {
  it("uses checked-in fixtures and exposes a queued → running → completed lifecycle", async () => {
    const transport = new MockTransport({ scenario: "completed", latencyMs: 0 });
    const accepted = await transport.createRun({ seed: 42, mode: "mock" });
    const first = await transport.getRun(accepted.run_id);
    const second = await transport.getRun(accepted.run_id);

    expect(accepted).toMatchObject({ status: "queued", source: "mock_fixture" });
    expect(first.status).toBe("running");
    expect(second).toMatchObject({ status: "completed", source: "mock_fixture" });
  });

  it("supports an immediate terminal GET after the accepted response", async () => {
    const transport = new MockTransport({ scenario: "instant", latencyMs: 0 });
    const accepted = await transport.createRun({ seed: 7, mode: "mock" });
    const snapshot = await transport.getRun(accepted.run_id);

    expect(accepted.status).toBe("completed");
    expect(snapshot.status).toBe("completed");
  });

  it("keeps a negative financial outcome completed", async () => {
    const transport = new MockTransport({ scenario: "negative", latencyMs: 0 });
    const accepted = await transport.createRun({ seed: 8, mode: "mock" });
    await transport.getRun(accepted.run_id);
    const snapshot = await transport.getRun(accepted.run_id);

    expect(snapshot.status).toBe("completed");
    if (snapshot.status === "completed") {
      expect(snapshot.net_arpu_gain).toBeLessThan(0);
    }
  });

  it("represents zero-cost ROI as null instead of Infinity", async () => {
    const transport = new MockTransport({ scenario: "zero-cost", latencyMs: 0 });
    const accepted = await transport.createRun({ seed: 9, mode: "mock" });
    await transport.getRun(accepted.run_id);
    const snapshot = await transport.getRun(accepted.run_id);

    expect(snapshot.status).toBe("completed");
    if (snapshot.status === "completed") {
      expect(snapshot.total_cost).toBe(0);
      expect(snapshot.roi).toBeNull();
    }
  });
});
