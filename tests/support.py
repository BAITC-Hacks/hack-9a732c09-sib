"""Controlled public-interface double for failure and observation tests only."""

import pandas as pd


class ControlledEnvironment:
    def __init__(self, ratios=None, pilot_error=False):
        self.customer_profile = pd.DataFrame([
            dict(ID_NUMBER=offset + index, current_tariff=tariff, arpu_segment="MID",
                 data_segment="LITE", call_segment="MEDIUM", predicted_arpu=2000.0)
            for tariff, count, offset in [("tariff_1", 30, 0), ("tariff_2", 25, 100), ("tariff_3", 20, 200)]
            for index in range(count)
        ])
        self.tariffs = pd.DataFrame({"tariff_plan_code": ["tariff_1", "tariff_2", "tariff_3"], "price_tariff": [1000, 2000, 3000]})
        self.channels = {"push": {"cost_per_contact": 0, "conversion_multiplier": .5},
                         "sms": {"cost_per_contact": 4, "conversion_multiplier": .65}}
        self.remaining_budget = 100000
        self.remaining_contacts = 15000
        self.pilots_left = 20
        self.pilot_history = []
        self.ratios = ratios or {"tariff_1": .1, "tariff_2": .2, "tariff_3": .3}
        self.pilot_error = pilot_error

    def run_pilot(self, target_tariff, channel, n_customers=100, filter_arpu_segment=None,
                  filter_data_segment=None, filter_call_segment=None, filter_current_tariff=None):
        if self.pilot_error:
            raise RuntimeError("controlled pilot failure")
        assert 10 <= n_customers <= 200
        cost = n_customers * self.channels[channel]["cost_per_contact"]
        self.remaining_budget -= cost
        self.remaining_contacts -= n_customers
        self.pilots_left -= 1
        ratio = self.ratios[filter_current_tariff]
        result = dict(pilot=f"pilot_{len(self.pilot_history) + 1}", target_tariff=target_tariff, channel=channel,
                      n_customers=n_customers, cost=cost, observed_lift_ratio=ratio,
                      observed_lift_total=ratio * n_customers * 2000,
                      remaining_budget=self.remaining_budget, remaining_contacts=self.remaining_contacts)
        self.pilot_history.append(result)
        return result
