import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.runner import StrategyRunner
from backend.app.service import RunService
from tests.test_contract_fixtures import validator


@pytest.fixture
def client():
    with TestClient(create_app()) as value:
        yield value


def checked(response, status, schema):
    assert response.status_code == status, response.text
    def reject(value):
        raise AssertionError(f"Invalid JSON number: {value}")
    body = json.loads(response.text, parse_constant=reject)
    validator(schema).validate(body)
    return body


def poll(client, run_id):
    deadline = monotonic() + 15
    while monotonic() < deadline:
        body = checked(client.get(f"/api/v1/runs/{run_id}"), 200, "RunSnapshot")
        if body["status"] in ("completed", "failed"):
            return body
        sleep(.01)
    pytest.fail("Run did not finish within 15 seconds")


def submit(client, seed=42):
    return checked(client.post("/api/v1/runs", json={"seed": seed, "mode": "mock"}), 202, "RunAccepted")


def test_health_and_public_summary(client):
    checked(client.get("/api/v1/health"), 200, "Health")
    summary = checked(client.get("/api/v1/case/summary"), 200, "CaseSummary")
    assert summary["source"] == "mock_environment"
    assert summary["subscriber_count"] == 23441
    for aggregates in summary["segments"].values():
        assert sum(row["subscriber_count"] for row in aggregates) == 23441
        assert sum(row["baseline_total_arpu"] for row in aggregates) == pytest.approx(summary["baseline_total_arpu"])
    assert any(row["segment"] == "UNKNOWN" for rows in summary["segments"].values() for row in rows)
    assert "ID_NUMBER" not in json.dumps(summary)


def test_real_run_accounting(client):
    accepted = submit(client)
    assert accepted["source"] == "mock_environment"
    run = poll(client, accepted["run_id"])
    assert run["status"] == "completed"
    assert run["created_at"] == accepted["created_at"] <= run["completed_at"]
    assert 1 <= run["n_pilots"] == len(run["pilots"]) <= 20
    assert 1 <= run["n_campaigns"] == len(run["campaigns"]) <= 10
    assert run["total_contacts"] == sum(d["n_contacts"] for d in run["campaigns_detail"])
    assert run["unique_customers_targeted"] <= run["total_contacts"] <= 15000
    assert run["remaining_contacts"] == 15000 - run["total_contacts"]
    assert run["remaining_budget"] == 100000 - run["total_cost"]
    if run["total_cost"] == 0:
        assert run["roi"] is None and "roi_undefined:zero_total_cost" in run["warnings"]
    else:
        assert run["roi"] == pytest.approx(run["gross_arpu_lift"] / run["total_cost"])
    assert [(d["kind"], d["index"]) for d in run["campaigns_detail"]] == (
        [("pilot", i) for i in range(run["n_pilots"])] + [("final", i) for i in range(run["n_campaigns"])])
    assert run["gross_arpu_lift"] != sum(p["observed_lift_total"] for p in run["pilots"])
    assert run["gross_arpu_lift"] != sum(d["gross_lift"] for d in run["campaigns_detail"])


@pytest.mark.parametrize("seed", [0, 4294967295])
def test_seed_bounds_accepted(client, seed):
    assert poll(client, submit(client, seed)["run_id"])["status"] == "completed"


@pytest.mark.parametrize("body", [
    {}, {"seed": 42}, {"mode": "mock"}, {"seed": 42, "mode": "live"},
    {"seed": 42, "mode": "mock", "extra": "secret"},
    *[{"seed": value, "mode": "mock"} for value in (-1, 4294967296, True, 1.5, 42.0, "42", None)],
])
def test_bad_requests_are_normalized(client, body):
    checked(client.post("/api/v1/runs", json=body), 422, "ErrorResponse")


def test_malformed_json_unknown_and_invalid_uuid(client):
    checked(client.post("/api/v1/runs", content='{ "seed":', headers={"Content-Type": "application/json"}),
            422, "ErrorResponse")
    body = checked(client.get(f"/api/v1/runs/{uuid4()}"), 404, "ErrorResponse")
    assert body["error"]["code"] == "RUN_NOT_FOUND"
    checked(client.get("/api/v1/runs/not-a-uuid"), 422, "ErrorResponse")


def test_parallel_requests_are_isolated_and_repeatable(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        accepted = list(pool.map(lambda _: submit(client), range(2)))
    assert accepted[0]["run_id"] != accepted[1]["run_id"]
    snapshots = [poll(client, row["run_id"]) for row in accepted]
    ignored = {"run_id", "created_at", "completed_at", "duration_ms"}
    assert {k: v for k, v in snapshots[0].items() if k not in ignored} == {
        k: v for k, v in snapshots[1].items() if k not in ignored}


def test_pending_lifecycle_does_not_block_health():
    entered, release = Event(), Event()

    class SlowRunner:
        def run(self, accepted, seed):
            entered.set()
            if not release.wait(10):
                raise RuntimeError("Test runner timed out")
            return StrategyRunner().run(accepted, seed)

    with TestClient(create_app(RunService(SlowRunner()))) as client:
        try:
            first = submit(client)
            assert first["status"] == "queued"
            assert entered.wait(2)
            running = checked(client.get(f"/api/v1/runs/{first['run_id']}"), 200, "RunSnapshot")
            assert running["status"] == "running"
            assert set(running) == {"run_id", "status", "created_at", "source"}
            second = submit(client)
            queued = checked(client.get(f"/api/v1/runs/{second['run_id']}"), 200, "RunSnapshot")
            assert queued["status"] == "queued"
            checked(client.get("/api/v1/health"), 200, "Health")
        finally:
            release.set()
        assert poll(client, first["run_id"])["status"] == "completed"
        assert poll(client, second["run_id"])["status"] == "completed"


def test_failed_is_stored_and_errors_do_not_leak():
    class FailingRunner:
        def run(self, accepted, seed):
            raise RuntimeError("password=private-value")

    with TestClient(create_app(RunService(FailingRunner()))) as client:
        run = poll(client, submit(client)["run_id"])
        assert run["status"] == "failed" and run["error"]["code"] == "RUN_FAILED"
        assert "private-value" not in json.dumps(run)
        assert "net_arpu_gain" not in run


def test_restart_loses_run_and_store_returns_copy(client):
    accepted = submit(client)
    run_id = accepted["run_id"]
    poll(client, run_id)
    from uuid import UUID
    snapshot = client.app.state.runs.get(UUID(run_id))
    snapshot.warnings.append("changed-by-caller")
    assert "changed-by-caller" not in poll(client, run_id)["warnings"]
    with TestClient(create_app()) as restarted:
        checked(restarted.get(f"/api/v1/runs/{run_id}"), 404, "ErrorResponse")


def test_cors_and_normalized_500(monkeypatch):
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://localhost:5173")

    def broken_summary():
        raise RuntimeError("password=private-value")

    with TestClient(create_app(summary_provider=broken_summary)) as client:
        for origin, allowed in [("http://localhost:5173", True), ("https://example.org", False)]:
            response = client.options("/api/v1/runs", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            })
            assert response.status_code == (200 if allowed else 400)
            assert (response.headers.get("access-control-allow-origin") == origin) == allowed
        response = client.get("/api/v1/case/summary", headers={"Origin": "http://localhost:5173"})
        checked(response, 500, "ErrorResponse")
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "private-value" not in response.text
        invalid = client.post("/api/v1/runs", json={}, headers={"Origin": "http://localhost:5173"})
        assert invalid.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.parametrize("origin", ["*", "https://example.org", "http://localhost:5173/path", "http://user@localhost:5173"])
def test_cors_rejects_nonlocal_origins(monkeypatch, origin):
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", origin)
    with pytest.raises(ValueError):
        create_app()
