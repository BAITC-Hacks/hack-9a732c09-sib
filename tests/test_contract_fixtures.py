import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts"
SPEC = yaml.safe_load((CONTRACT / "openapi.yaml").read_text(encoding="utf-8"))


def load(name):
    def reject(value):
        raise ValueError(f"Invalid JSON number: {value}")
    return json.loads((CONTRACT / "examples" / name).read_text(encoding="utf-8"), parse_constant=reject)


def validator(name):
    return Draft202012Validator({"$ref": f"#/components/schemas/{name}", "components": SPEC["components"]}, format_checker=FormatChecker())


def test_openapi_and_standalone_campaign_schema():
    validate(SPEC)
    standalone = json.loads((CONTRACT / "campaign.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(standalone)
    assert {k: v for k, v in standalone.items() if k not in ("$schema", "title")} == SPEC["components"]["schemas"]["Campaign"]


@pytest.mark.parametrize("filename,schema", [
    ("case-summary.json", "CaseSummary"), ("health.json", "Health"), ("error.json", "ErrorResponse"),
    ("run-accepted.json", "RunAccepted"), ("run-accepted.json", "RunSnapshot"),
    ("run-running.json", "RunSnapshot"), ("run-completed.json", "RunSnapshot"), ("run-failed.json", "RunSnapshot"),
])
def test_fixtures_validate(filename, schema):
    validator(schema).validate(load(filename))


def test_fixture_accounting_and_provenance():
    summary, run, accepted = load("case-summary.json"), load("run-completed.json"), load("run-accepted.json")
    assert summary["source"] == run["source"] == accepted["source"] == "mock_fixture"
    assert run["run_id"] == accepted["run_id"]
    assert run["created_at"] == accepted["created_at"] < run["completed_at"]
    assert run["baseline_total_arpu"] == summary["baseline_total_arpu"]
    assert run["n_campaigns"] == len(run["campaigns"])
    assert run["n_pilots"] == len(run["pilots"])
    assert len(run["campaigns_detail"]) == run["n_pilots"] + run["n_campaigns"]
    assert run["total_contacts"] == sum(d["n_contacts"] for d in run["campaigns_detail"])
    assert run["total_cost"] == sum(d["cost"] for d in run["campaigns_detail"])
    assert run["remaining_budget"] == 100000 - run["total_cost"]
    assert run["remaining_contacts"] == 15000 - run["total_contacts"]
    assert run["net_arpu_gain"] == run["gross_arpu_lift"] - run["total_cost"]
    assert run["total_arpu_after"] == run["baseline_total_arpu"] + run["net_arpu_gain"]
    assert run["roi"] == pytest.approx(run["gross_arpu_lift"] / run["total_cost"])
    assert run["growth_vs_baseline_pct"] == pytest.approx(100 * run["net_arpu_gain"] / run["baseline_total_arpu"])
    assert run["coverage_pct"] == pytest.approx(100 * run["unique_customers_targeted"] / summary["subscriber_count"])
    assert run["unique_customers_targeted"] <= min(summary["subscriber_count"], run["total_contacts"])
    for aggregates in summary["segments"].values():
        assert sum(row["subscriber_count"] for row in aggregates) == summary["subscriber_count"]
        assert sum(row["baseline_total_arpu"] for row in aggregates) == pytest.approx(summary["baseline_total_arpu"])
    tariffs = {t["tariff_plan_code"] for t in summary["tariffs"]}
    channels = {c["name"]: c for c in summary["channels"]}
    for campaign in run["campaigns"]:
        assert campaign["target_tariff"] in tariffs and campaign["channel"] in channels
        assert set((campaign.get("filter_current_tariff") or "").split(";")) - {""} <= tariffs
    for detail in run["campaigns_detail"]:
        rows = run["pilots"] if detail["kind"] == "pilot" else run["campaigns"]
        assert 0 <= detail["index"] < len(rows)
        assert detail["cost"] == detail["n_contacts"] * channels[detail["channel"]]["cost_per_contact"]
        assert detail["n_negative"] <= detail["n_contacts"]


def test_incomplete_completed_and_bad_error_are_rejected():
    with pytest.raises(ValidationError):
        validator("RunSnapshot").validate(dict(load("run-accepted.json"), status="completed"))
    with pytest.raises(ValidationError):
        validator("RunSnapshot").validate(dict(load("run-failed.json"), error=None))
