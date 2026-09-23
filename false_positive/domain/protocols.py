"""The organizer's public interface; structural typing, no concrete env import."""

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


class AgentEnvironmentProtocol(Protocol):
    customer_profile: "pd.DataFrame"
    tariffs: "pd.DataFrame"
    channels: dict[str, dict[str, float]]
    remaining_budget: float
    remaining_contacts: int
    pilots_left: int
    pilot_history: list[dict]

    def run_pilot(self, target_tariff: str, channel: str, n_customers: int = 100,
                  filter_arpu_segment: str | None = None,
                  filter_data_segment: str | None = None,
                  filter_call_segment: str | None = None,
                  filter_current_tariff: str | None = None) -> dict: ...


class StrategyObserver(Protocol):
    def record(self, event: str, payload: dict) -> None: ...
