"""Reproducible command-line benchmark: python -m experiments.run_benchmark."""

import argparse
import json
import math
import platform
import statistics
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import scipy

from setcover.algorithms import greedy
from setcover.evaluation import evaluate
from setcover.generators import KINDS, generate
from setcover.stats import describe_instance

from .config import BenchmarkConfig

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "smoke.json"


def percentile_nearest_rank(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(fraction * len(values)) - 1)]


def run(config: BenchmarkConfig) -> dict:
    records = []
    for number, (kind, instance_seed) in enumerate(config.instance_specs(), start=1):
        instance = generate(kind, config.n, config.m, instance_seed)
        result = evaluate(instance, greedy, config.opt_time_limit_seconds)
        records.append({
            "id": number, "kind": kind, "seed": instance_seed,
            "instance": instance.to_dict(),
            "instance_stats": describe_instance(instance),
            "evaluation": result.to_dict(),
        })
        ratio = f"{result.ratio:.4f}" if result.ratio is not None else "n/a"
        opt = result.opt if result.opt is not None else "unproven"
        print(f"Instance {number:03d} ({kind}, seed={instance_seed})")
        print(f"n = {config.n}, m = {config.m}")
        print(f"Greedy = {result.alg}, OPT = {opt}, Ratio = {ratio}")
        print(f"ALG runtime = {result.runtime_seconds:.6f} s, "
              f"OPT runtime = {result.opt_runtime_seconds:.6f} s")
        print(f"Valid = {result.valid}, OPT status = {result.opt_status}\n")
    evaluations = [record["evaluation"] for record in records]
    ratios = [item["ratio"] for item in evaluations if item["ratio"] is not None]
    summary = {
        "mean_ratio": statistics.mean(ratios) if ratios else None,
        "median_ratio": statistics.median(ratios) if ratios else None,
        "p90_ratio": percentile_nearest_rank(ratios, 0.9),
        "worst_ratio": max(ratios) if ratios else None,
        "valid_solutions": sum(item["valid"] for item in evaluations),
        "opt_proven": sum(item["opt_status"] == "optimal" for item in evaluations),
        "ratios_available": len(ratios),
        "total_instances": len(records),
    }
    print("-----------------------")
    for label, key in (("Mean ratio", "mean_ratio"),
                       ("Median ratio", "median_ratio"),
                       ("P90 ratio", "p90_ratio"),
                       ("Worst ratio", "worst_ratio")):
        value = summary[key]
        print(f"{label}: {value:.4f}" if value is not None else f"{label}: n/a")
    print(f"Valid solutions: {summary['valid_solutions']}/{summary['total_instances']}")
    print(f"Proven OPT: {summary['opt_proven']}/{summary['total_instances']}")
    print("-----------------------")
    return {
        "config": config.to_dict(),
        "software": {"python": platform.python_version(), "scipy": scipy.__version__},
        "records": records,
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--n", type=int)
    parser.add_argument("--m", type=int)
    parser.add_argument("--per-kind", type=int)
    parser.add_argument("--seed", type=int, help="first seed of this run")
    parser.add_argument("--kinds", nargs="+", choices=KINDS)
    parser.add_argument("--opt-time-limit", type=float, help="seconds per instance")
    parser.add_argument("--output", type=Path,
                        help="JSON path (default: results/<config>_<seed>.json)")
    args = parser.parse_args()
    config = BenchmarkConfig.load(args.config)
    overrides = {
        "n": args.n, "m": args.m, "per_kind": args.per_kind,
        "seed_start": args.seed,
        "kinds": tuple(args.kinds) if args.kinds is not None else None,
        "opt_time_limit_seconds": args.opt_time_limit,
    }
    config = replace(config, **{key: value for key, value in overrides.items()
                                if value is not None})
    data = run(config)
    data["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    output = args.output or Path("results") / f"{config.name}_{config.seed_start}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False),
                      encoding="utf-8")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
