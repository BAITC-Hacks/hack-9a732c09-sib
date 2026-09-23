"""Public-data hypotheses. Prices suggest experiments; only pilots justify scale."""

from dataclasses import replace
from math import isfinite

from false_positive.domain.constraints import CHANNELS, MAX_CUSTOMERS_PER_CAMPAIGN
from false_positive.domain.models import Campaign, Candidate


def audience_key(candidate):
    c = candidate.campaign
    return (c.filter_current_tariff, c.filter_arpu_segment, c.filter_data_segment, c.filter_call_segment)


def available_channels(env):
    return sorted((name for name in CHANNELS if name in env.channels
                   and isfinite(float(env.channels[name]["cost_per_contact"]))
                   and env.channels[name]["cost_per_contact"] >= 0),
                  key=lambda name: (env.channels[name]["cost_per_contact"], name))


def generate_hypotheses(env) -> list[Candidate]:
    tariffs = env.tariffs.sort_values(["price_tariff", "tariff_plan_code"], kind="stable")
    prices = {str(row.tariff_plan_code): float(row.price_tariff) for row in tariffs.itertuples(index=False)
              if isfinite(float(row.price_tariff)) and row.price_tariff >= 0}
    channels = available_channels(env)
    if not prices or not channels:
        raise ValueError("Environment must provide tariffs and supported channels")
    cheapest = channels[0]
    # Aggregate homogeneous tariff/ARPU cells; split large ones by consumption
    # so every possible final audience is disjoint and <=5000 without truncation.
    cells = []
    for (current, arpu), group in env.customer_profile.groupby(["current_tariff", "arpu_segment"], observed=True):
        if current not in prices:
            continue
        groups = [(None, None, group)] if len(group) <= MAX_CUSTOMERS_PER_CAMPAIGN else [
            (data, call, cell) for (data, call), cell in group.groupby(["data_segment", "call_segment"], observed=True)]
        for data, call, cell in groups:
            total = float(cell["predicted_arpu"].sum())
            if 0 < len(cell) <= MAX_CUSTOMERS_PER_CAMPAIGN and isfinite(total) and total > 0:
                cells.append((str(current), str(arpu), data, call, len(cell), total))
    cells.sort(key=lambda row: (-row[5], row[0], row[1], str(row[2]), str(row[3])))
    rounds = [[], []]
    for current, arpu, data, call, count, total in cells:
        mean_arpu = total / count
        higher = [code for code, price in prices.items() if price > prices[current]]
        affordable = [code for code in higher if prices[code] <= 1.25 * max(mean_arpu, prices[current])]
        # Compare a meaningful affordable upgrade with the closest price step.
        # No tariff identifiers or mock effects influence this ordering.
        choices = ([affordable[-1]] if affordable else []) + higher[:1]
        if not choices:
            choices = sorted((code for code in prices if code != current),
                             key=lambda code: (abs(prices[code] - prices[current]), code))[:1]
        for rank, target in enumerate(dict.fromkeys(choices)):
            campaign = Campaign(target_tariff=target, channel=cheapest,
                                campaign_name=f"adaptive_{len(rounds[0]) + 1}_{rank + 1}",
                                filter_current_tariff=current, filter_arpu_segment=arpu,
                                filter_data_segment=None if data is None else str(data),
                                filter_call_segment=None if call is None else str(call))
            rounds[rank].append(Candidate(campaign, count, total, float(env.channels[cheapest]["cost_per_contact"])))
    # First hypotheses cover different audiences, then alternative tariffs.
    return rounds[0] + rounds[1]


def small_fallbacks(env, hypotheses):
    """Real small cells bound exposure when no proposal is confirmed."""
    from .baseline import generate_candidates
    # Keep legacy cell generation solely for a small mandatory final campaign.
    return sorted(generate_candidates(env) + hypotheses,
                  key=lambda c: (c.baseline_arpu + c.n_customers * c.cost_per_contact,
                                 c.n_customers, c.campaign.campaign_name))


def channel_hypothesis(evidence, env):
    """Public multipliers propose a test, never authorize an untested channel."""
    c = evidence.candidate
    base_multiplier = float(env.channels[c.campaign.channel].get("conversion_multiplier", 0))
    if base_multiplier <= 0:
        return None
    base_net = evidence.mean * c.baseline_arpu - c.n_customers * c.cost_per_contact
    alternatives = []
    for channel in available_channels(env):
        if channel == c.campaign.channel:
            continue
        properties = env.channels[channel]
        multiplier = float(properties.get("conversion_multiplier", 0))
        cost = float(properties["cost_per_contact"])
        if not isfinite(multiplier) or multiplier <= base_multiplier:
            continue
        estimated = evidence.lower_ratio() * multiplier / base_multiplier * c.baseline_arpu - c.n_customers * cost
        # A larger multiplier is only a hypothesis: require room for confirmation.
        if estimated > base_net + 480 * cost:
            alternatives.append((estimated - base_net, channel, cost))
    if not alternatives:
        return None
    _, channel, cost = max(alternatives)
    return replace(c, campaign=replace(c.campaign, channel=channel,
                   campaign_name=c.campaign.campaign_name + "_" + channel), cost_per_contact=cost)
