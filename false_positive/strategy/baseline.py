"""Public-profile cells and simple next-price tariff hypotheses; no effect model."""

from math import isfinite

from false_positive.domain.constraints import CHANNELS, MAX_CUSTOMERS_PER_CAMPAIGN
from false_positive.domain.models import Campaign, Candidate


def generate_candidates(env) -> list[Candidate]:
    tariffs = env.tariffs.sort_values(["price_tariff", "tariff_plan_code"], kind="stable")
    codes = list(tariffs["tariff_plan_code"].astype(str))
    prices = dict(zip(codes, tariffs["price_tariff"].astype(float)))
    available = [c for c in CHANNELS if c in env.channels
                 and isfinite(float(env.channels[c]["cost_per_contact"]))
                 and env.channels[c]["cost_per_contact"] >= 0]
    if not codes or not available:
        raise ValueError("Environment must provide tariffs and supported channels")
    channel = min(available, key=lambda c: (env.channels[c]["cost_per_contact"], c))
    columns = ["current_tariff", "arpu_segment", "data_segment", "call_segment"]
    cells = (env.customer_profile.groupby(columns, observed=True)
             .agg(n=("ID_NUMBER", "size"), arpu=("predicted_arpu", "sum"))
             .reset_index().sort_values(["n"] + columns, ascending=[False] + [True] * 4, kind="stable"))
    candidates = []
    for row in cells.itertuples(index=False):
        if row.current_tariff not in prices or not 1 <= row.n <= MAX_CUSTOMERS_PER_CAMPAIGN:
            continue
        higher = [code for code in codes if prices[code] > prices[row.current_tariff]]
        different = [code for code in codes if code != row.current_tariff]
        target = (higher or different or [row.current_tariff])[0]
        campaign = Campaign(
            target_tariff=target, channel=channel,
            campaign_name=f"baseline_{len(candidates) + 1}",
            filter_current_tariff=str(row.current_tariff),
            filter_arpu_segment=str(row.arpu_segment),
            filter_data_segment=str(row.data_segment),
            filter_call_segment=str(row.call_segment),
        )
        candidates.append(Candidate(campaign, int(row.n), float(row.arpu), float(env.channels[channel]["cost_per_contact"])))
    return candidates
