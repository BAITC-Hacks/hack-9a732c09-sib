"""Real HTTP smoke: python -m backend.smoke [--base-url http://127.0.0.1:8000]."""

import argparse
import json
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def check_api(base_url, timeout=30):
    def request(path, payload=None):
        data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
        headers = {} if data is None else {"Content-Type": "application/json"}
        req = Request(base_url.rstrip("/") + path, data=data, headers=headers)
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            def reject(value):
                raise ValueError(f"Non-finite JSON: {value}")
            return response.status, json.loads(response.read(), parse_constant=reject)

    status, health = request("/api/v1/health")
    assert status == 200 and health["status"] == "ok"
    status, summary = request("/api/v1/case/summary")
    assert status == 200 and summary["subscriber_count"] == 23441
    status, accepted = request("/api/v1/runs", {"seed": 42, "mode": "mock"})
    assert status == 202 and accepted["source"] == "mock_environment"
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        status, run = request(f"/api/v1/runs/{accepted['run_id']}")
        assert status == 200
        if run["status"] == "failed":
            raise AssertionError(f"Run failed: {run['error']['code']}")
        if run["status"] == "completed":
            assert run["n_pilots"] == len(run["pilots"]) == 3
            assert run["n_campaigns"] == len(run["campaigns"])
            assert run["remaining_contacts"] == 15000 - run["total_contacts"]
            assert run["roi"] is None and run["total_cost"] == 0
            break
        sleep(.1)
    else:
        raise TimeoutError("Run did not finish")
    status, error = request("/api/v1/runs/00000000-0000-4000-8000-000000000000")
    assert status == 404 and error["error"]["code"] == "RUN_NOT_FOUND"
    status, error = request("/api/v1/runs", {"seed": -1, "mode": "mock"})
    assert status == 422 and error["error"]["code"] == "VALIDATION_ERROR"
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    run = check_api(args.base_url)
    print(f"PASS HTTP smoke: {run['n_pilots']} pilots, {run['n_campaigns']} final campaigns, "
          f"{run['total_contacts']} contacts, net={run['net_arpu_gain']:.2f}")


if __name__ == "__main__":
    main()
