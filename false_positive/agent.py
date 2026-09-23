"""Judge adapter; structured traces are available directly through the engine."""

from false_positive.strategy.engine import StrategyEngine


class Agent:
    def act(self, env) -> list[dict]:
        return [campaign.to_dict() for campaign in StrategyEngine().run(env).campaigns]
