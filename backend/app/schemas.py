"""HTTP DTOs for the frozen contracts/openapi.yaml; never imported by core."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Source = Literal["core", "mock_environment", "mock_fixture"]
Status = Literal["queued", "running", "completed", "failed"]
ChannelName = Literal["push", "sms", "digital_ads", "call"]
Nonnegative = Annotated[float, Field(ge=0)]
Count = Annotated[int, Field(ge=0)]
Percentage = Annotated[float, Field(ge=0, le=100)]
TariffCode = Annotated[str, Field(pattern=r"^tariff_[1-9][0-9]*$")]
TariffFilter = Annotated[str, Field(pattern=r"^tariff_[1-9][0-9]*(;tariff_[1-9][0-9]*)*$")]
Nonempty = Annotated[str, Field(min_length=1)]


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Health(DTO):
    status: Literal["ok"] = "ok"
    service: Literal["false-positive-api"] = "false-positive-api"
    version: Nonempty = "0.1.0"


class Error(DTO):
    code: Nonempty
    message: Nonempty
    details: list[str]


class ErrorResponse(DTO):
    error: Error


class Constraints(DTO):
    total_budget: Literal[100000] = 100000
    max_total_contacts: Literal[15000] = 15000
    max_pilots: Literal[20] = 20
    min_pilot_customers: Literal[10] = 10
    max_pilot_customers: Literal[200] = 200
    max_campaigns: Literal[10] = 10
    max_customers_per_campaign: Literal[5000] = 5000


class Channel(DTO):
    name: ChannelName
    cost_per_contact: Nonnegative
    conversion_multiplier: Nonnegative


class SegmentAggregate(DTO):
    segment: Nonempty
    subscriber_count: Count
    baseline_total_arpu: Nonnegative


class SegmentAggregates(DTO):
    arpu_segment: list[SegmentAggregate]
    data_segment: list[SegmentAggregate]
    call_segment: list[SegmentAggregate]


class Tariff(DTO):
    tariff_plan_code: TariffCode
    price_tariff: Nonnegative


class CaseSummary(DTO):
    source: Source
    subscriber_count: Annotated[int, Field(ge=1)]
    baseline_total_arpu: Annotated[float, Field(gt=0)]
    constraints: Constraints
    channels: Annotated[list[Channel], Field(min_length=1)]
    segments: SegmentAggregates
    tariffs: Annotated[list[Tariff], Field(min_length=1)]
    generated_at: datetime


class Filters(DTO):
    filter_arpu_segment: Literal["LOW", "MID", "HIGH"] | None = None
    filter_data_segment: Literal["NON_USER", "LITE", "HEAVY"] | None = None
    filter_call_segment: Literal["LOW", "MEDIUM", "HIGH"] | None = None
    filter_current_tariff: TariffFilter | None = None


class Campaign(Filters):
    target_tariff: TariffCode
    channel: ChannelName
    campaign_name: Nonempty = "baseline"


class PilotObservation(DTO):
    pilot: Nonempty
    target_tariff: TariffCode
    channel: ChannelName
    n_customers: Annotated[int, Field(ge=1, le=200)]
    cost: Nonnegative
    observed_lift_ratio: float
    observed_lift_total: float
    remaining_budget: Nonnegative
    remaining_contacts: Count
    filters: Filters


class CampaignDetail(DTO):
    kind: Literal["pilot", "final"]
    index: Count
    name: str
    channel: ChannelName
    cost: Nonnegative
    n_contacts: Annotated[int, Field(ge=0, le=5000)]
    gross_lift: float
    n_negative: Count
    capped_at_campaign_limit: bool
    capped_at_reach_budget: bool
    capped_at_money_budget: bool


class RunRequest(DTO):
    seed: Annotated[int, Field(ge=0, le=4294967295)]
    mode: Literal["mock"]


class RunAccepted(DTO):
    run_id: UUID
    status: Status
    created_at: datetime
    source: Source


class RunPending(RunAccepted):
    status: Literal["queued", "running"]


class RunFailed(RunAccepted):
    status: Literal["failed"]
    completed_at: datetime
    error: Error
    warnings: list[str]


class RunCompleted(RunAccepted):
    status: Literal["completed"]
    completed_at: datetime
    baseline_total_arpu: Annotated[float, Field(gt=0)]
    gross_arpu_lift: float
    total_cost: Annotated[float, Field(ge=0, le=100000)]
    net_arpu_gain: float
    total_arpu_after: float
    growth_vs_baseline_pct: float
    n_pilots: Annotated[int, Field(ge=0, le=20)]
    n_campaigns: Annotated[int, Field(ge=1, le=10)]
    total_contacts: Annotated[int, Field(ge=0, le=15000)]
    unique_customers_targeted: Count
    coverage_pct: Percentage
    roi: float | None
    risk_score_pct: Percentage | None
    remaining_budget: Annotated[float, Field(ge=0, le=100000)]
    remaining_contacts: Annotated[int, Field(ge=0, le=15000)]
    pilots: Annotated[list[PilotObservation], Field(max_length=20)]
    campaigns: Annotated[list[Campaign], Field(min_length=1, max_length=10)]
    campaigns_detail: Annotated[list[CampaignDetail], Field(max_length=30)]
    warnings: list[str]
    duration_ms: Nonnegative
    error: None


RunSnapshot = Annotated[RunPending | RunCompleted | RunFailed, Field(discriminator="status")]
