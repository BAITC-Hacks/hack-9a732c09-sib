"""Stable judge entry point; external advice requires explicit opt-in."""

from runtime.configured import build_engine


class Agent:
    def act(self, env) -> list[dict]:
        return [campaign.to_dict() for campaign in build_engine().run(env).campaigns]

__all__ = ["Agent"]
