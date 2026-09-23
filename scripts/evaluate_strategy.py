"""Compare offline strategies, or explicitly enable one LLM provider for a smoke run."""

import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from false_positive.strategy.legacy import LegacyStrategyEngine
from local_eval import evaluate_agent
from runtime.configured import build_engine


class CapturingAgent:
    def __init__(self, factory):
        self.factory = factory
        self.run = None

    def act(self, env):
        self.run = self.factory().run(env)
        return [c.to_dict() for c in self.run.campaigns]


def evaluate(factory, seeds):
    rows = []
    for seed in seeds:
        agent = CapturingAgent(factory)
        score = evaluate_agent(agent, seed=seed, verbose=False)
        if agent.run is None or score is None or len(agent.run.pilots) != score["n_pilots"]:
            raise RuntimeError("Incomplete strategy/evaluator execution")
        rows.append(dict(seed=seed, net=score["net_arpu_gain"], cost=score["total_cost"],
                         contacts=score["total_contacts"], pilots=score["n_pilots"],
                         campaigns=len(agent.run.campaigns), warnings=agent.run.warnings,
                         external_advisor_used=any(e["event"] == "hypotheses_prioritized"
                             and e["payload"].get("source") == "external_advisor" for e in agent.run.trace)))
    net = [r["net"] for r in rows]
    return dict(mean_net=statistics.mean(net), median_net=statistics.median(net), min_net=min(net),
                max_net=max(net), profitable=sum(n > 0 for n in net), runs=len(net), rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("off", "openai"), default="off")
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.runs <= 1000 or not 0 <= args.start_seed <= 4294967295 - args.runs + 1:
        parser.error("Invalid seed range")
    seeds = list(range(args.start_seed, args.start_seed + args.runs))
    report = dict(provider=args.provider, seeds=seeds)
    if args.baseline:
        report["baseline"] = evaluate(LegacyStrategyEngine, seeds)
    report["adaptive"] = evaluate(lambda: build_engine(args.provider), seeds)
    encoded = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
