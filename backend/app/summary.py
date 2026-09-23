"""Aggregate public CSVs, including subscribers with missing segment labels."""

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from mock_environment import CHANNELS

from .schemas import CaseSummary, Constraints

ROOT = Path(__file__).resolve().parents[2]


def build_summary() -> CaseSummary:
    with (ROOT / "customer_profile.csv").open(encoding="utf-8", newline="") as handle:
        profile = list(csv.DictReader(handle))
    with (ROOT / "data" / "dict_tariff.csv").open(encoding="utf-8", newline="") as handle:
        tariffs = [dict(tariff_plan_code=row["tariff_plan_code"], price_tariff=float(row["price_tariff"]))
                   for row in csv.DictReader(handle)]
    segments = {}
    for column in ("arpu_segment", "data_segment", "call_segment"):
        groups = defaultdict(lambda: dict(subscriber_count=0, baseline_total_arpu=0.0))
        for row in profile:
            group = groups[row[column] or "UNKNOWN"]
            group["subscriber_count"] += 1
            group["baseline_total_arpu"] += float(row["predicted_arpu"])
        segments[column] = [dict(segment=key, **value) for key, value in sorted(groups.items())]
    return CaseSummary(
        source="mock_environment", subscriber_count=len(profile),
        baseline_total_arpu=sum(float(row["predicted_arpu"]) for row in profile),
        constraints=Constraints(), channels=[dict(name=key, **value) for key, value in CHANNELS.items()],
        segments=segments, tariffs=tariffs, generated_at=datetime.now(timezone.utc),
    )
