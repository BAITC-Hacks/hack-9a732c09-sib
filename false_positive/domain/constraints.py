"""Public case limits, cross-checked against the organizer in tests."""

MAX_CAMPAIGNS = 10
MAX_CUSTOMERS_PER_CAMPAIGN = 5_000
TOTAL_BUDGET = 100_000
MAX_TOTAL_CONTACTS = 15_000
MAX_PILOTS = 20
MIN_PILOT_CUSTOMERS = 10
MAX_PILOT_CUSTOMERS = 200
CHANNELS = ("push", "sms", "digital_ads", "call")
FILTER_VALUES = {
    "filter_arpu_segment": ("LOW", "MID", "HIGH"),
    "filter_data_segment": ("NON_USER", "LITE", "HEAVY"),
    "filter_call_segment": ("LOW", "MEDIUM", "HIGH"),
}
