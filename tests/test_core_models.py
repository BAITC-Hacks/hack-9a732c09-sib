import pytest

from false_positive.domain import constraints
from false_positive.domain.models import Campaign, PilotRequest


def test_public_limits_match_organizer():
    import environment
    import scoring_core
    for key in ("MAX_PILOTS", "MIN_PILOT_CUSTOMERS", "MAX_PILOT_CUSTOMERS"):
        assert getattr(constraints, key) == getattr(environment, key)
    for key in ("MAX_CAMPAIGNS", "MAX_CUSTOMERS_PER_CAMPAIGN", "TOTAL_BUDGET", "MAX_TOTAL_CONTACTS"):
        assert getattr(constraints, key) == getattr(scoring_core, key)
    assert set(constraints.CHANNELS) == set(scoring_core.CHANNELS)
    assert {k: set(v) for k, v in constraints.FILTER_VALUES.items()} == scoring_core.FILTER_VALUES


def test_pilot_request_omits_campaign_name():
    request = PilotRequest(Campaign("tariff_1", "push", filter_arpu_segment="MID"), 100)
    assert "campaign_name" not in request.to_kwargs()
    assert request.to_kwargs()["filter_arpu_segment"] == "MID"
    with pytest.raises(ValueError):
        PilotRequest(request.campaign, 201)


@pytest.mark.parametrize("kwargs", [dict(channel="email"), dict(filter_arpu_segment="MEDIUM"),
                                    dict(filter_call_segment="MID"), dict(filter_current_tariff="tariff_1;")])
def test_invalid_campaign_rejected(kwargs):
    with pytest.raises(ValueError):
        Campaign(**dict(dict(target_tariff="tariff_1", channel="push"), **kwargs))
