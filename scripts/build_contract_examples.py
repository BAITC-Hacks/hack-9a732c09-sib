"""Rebuild explicit UI fixtures. No private model and no scored-runtime claims."""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "contracts" / "examples"
STAMP = "2026-09-23T10:00:00Z"
RUN_ID = "00000000-0000-4000-8000-000000000042"


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main():
    with (ROOT / "customer_profile.csv").open(encoding="utf-8", newline="") as handle:
        profile = list(csv.DictReader(handle))
    with (ROOT / "data" / "dict_tariff.csv").open(encoding="utf-8", newline="") as handle:
        tariffs = [{"tariff_plan_code": row["tariff_plan_code"], "price_tariff": float(row["price_tariff"])} for row in csv.DictReader(handle)]
    baseline = sum(float(row["predicted_arpu"]) for row in profile)
    segments = {}
    for column in ("arpu_segment", "data_segment", "call_segment"):
        groups = defaultdict(lambda: {"subscriber_count": 0, "baseline_total_arpu": 0.0})
        for row in profile:
            segment = row[column] or "UNKNOWN"
            groups[segment]["subscriber_count"] += 1
            groups[segment]["baseline_total_arpu"] += float(row["predicted_arpu"])
        segments[column] = [dict(segment=key, **value) for key, value in sorted(groups.items())]
    summary = dict(source="mock_fixture", subscriber_count=len(profile), baseline_total_arpu=baseline,
                   constraints=dict(total_budget=100000, max_total_contacts=15000, max_pilots=20,
                                    min_pilot_customers=10, max_pilot_customers=200,
                                    max_campaigns=10, max_customers_per_campaign=5000),
                   channels=[dict(name=name, cost_per_contact=cost, conversion_multiplier=mult)
                             for name, cost, mult in [("push", 0, .5), ("sms", 4, .65), ("digital_ads", 22, .85), ("call", 160, 1.2)]],
                   segments=segments, tariffs=tariffs, generated_at=STAMP)
    write("case-summary.json", summary)
    accepted = dict(run_id=RUN_ID, status="queued", created_at=STAMP, source="mock_fixture")
    write("run-accepted.json", accepted)
    write("run-running.json", dict(accepted, status="running"))
    campaign = dict(campaign_name="fixture_campaign", filter_arpu_segment="MID", filter_data_segment=None,
                    filter_call_segment=None, filter_current_tariff="tariff_4", target_tariff="tariff_8", channel="sms")
    filters = {k: v for k, v in campaign.items() if k.startswith("filter_")}
    eligible = [row for row in profile if row["current_tariff"] == "tariff_4" and row["arpu_segment"] == "MID"]
    n_final = min(5000, len(eligible))
    n_pilot = min(100, n_final)
    # Illustrative, internally consistent effects: pilot IDs are a subset of final IDs.
    gross = n_final * 100.0
    cost = (n_final + n_pilot) * 4.0
    net = gross - cost
    pilot = dict(pilot="pilot_1", target_tariff="tariff_8", channel="sms", n_customers=n_pilot, cost=n_pilot * 4,
                 observed_lift_ratio=.05, observed_lift_total=5000.0, remaining_budget=100000 - n_pilot * 4,
                 remaining_contacts=15000 - n_pilot, filters=filters)
    details = [dict(kind=kind, index=0, name=name, channel="sms", cost=count * 4, n_contacts=count,
                    gross_lift=count * 100.0, n_negative=0, capped_at_campaign_limit=(kind == "final" and len(eligible) > 5000),
                    capped_at_reach_budget=False, capped_at_money_budget=False)
               for kind, name, count in [("pilot", "pilot_1", n_pilot), ("final", "fixture_campaign", n_final)]]
    completed = dict(accepted, status="completed", completed_at="2026-09-23T10:00:01Z",
                     baseline_total_arpu=baseline, gross_arpu_lift=gross, total_cost=cost,
                     net_arpu_gain=net, total_arpu_after=baseline + net, growth_vs_baseline_pct=100 * net / baseline,
                     n_pilots=1, n_campaigns=1, total_contacts=n_final + n_pilot, unique_customers_targeted=n_final,
                     coverage_pct=100 * n_final / len(profile), roi=gross / cost, risk_score_pct=None,
                     remaining_budget=100000 - cost, remaining_contacts=15000 - n_final - n_pilot,
                     pilots=[pilot], campaigns=[campaign], campaigns_detail=details,
                     warnings=["Illustrative fixture, not a strategy execution; risk is not calculated."], duration_ms=1000.0, error=None)
    write("run-completed.json", completed)
    error = dict(code="RUN_FAILED", message="Demo run could not be completed.", details=[])
    write("run-failed.json", dict(accepted, status="failed", completed_at="2026-09-23T10:00:01Z", error=error, warnings=[]))
    write("error.json", {"error": dict(code="RUN_NOT_FOUND", message="Run was not found.", details=[])})
    write("health.json", dict(status="ok", service="false-positive-api", version="0.1.0"))


if __name__ == "__main__":
    main()
