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
from setcover.exact import ExactResult
from setcover.generators import KINDS, generate
from setcover.stats import describe_instance

from .config import BenchmarkConfig
from .opt_cache import OptimumCache

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "smoke.json"


def percentile_nearest_rank(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(fraction * len(values)) - 1)]


def run(config: BenchmarkConfig, cache: OptimumCache | None = None) -> dict:
    records = []
    for number, (kind, instance_seed) in enumerate(config.instance_specs(), start=1):
        instance = generate(kind, config.n, config.m, instance_seed)
        cached = cache.get(instance) if cache is not None else None
        result = evaluate(instance, greedy, config.opt_time_limit_seconds, cached)
        if cache is not None and cached is None and result.opt_status == "optimal":
            cache.add(instance, ExactResult(result.opt_solution, result.opt))
            cache.save()
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
        print(f"Valid = {result.valid}, OPT status = {result.opt_status} "
              f"({result.opt_source})\n")
    evaluations = [record["evaluation"] for record in records]
    ratios = [item["ratio"] for item in evaluations if item["ratio"] is not None]
    summary = {
        "mean_ratio": statistics.mean(ratios) if ratios else None,
        "median_ratio": statistics.median(ratios) if ratios else None,
        "p90_ratio": percentile_nearest_rank(ratios, 0.9),
        "worst_ratio": max(ratios) if ratios else None,
        "valid_solutions": sum(item["valid"] for item in evaluations),
        "opt_proven": sum(item["opt_status"] == "optimal" for item in evaluations),
        "opt_cache_hits": sum(item["opt_source"] == "cache" for item in evaluations),
        "ratios_available": len(ratios),
        "total_instances": len(records),
    }
    by_kind = {}
    for kind in config.kinds:
        subset = [record for record in records if record["kind"] == kind]
        kind_ratios = [record["evaluation"]["ratio"] for record in subset
                       if record["evaluation"]["ratio"] is not None]
        by_kind[kind] = {
            "count": len(subset),
            "mean_ratio": statistics.mean(kind_ratios) if kind_ratios else None,
            "worst_ratio": max(kind_ratios) if kind_ratios else None,
            "mean_density": statistics.mean(record["instance_stats"]["density"]
                                            for record in subset),
            "mean_pairwise_jaccard": statistics.mean(
                record["instance_stats"]["mean_pairwise_jaccard"] for record in subset),
        }
    summary["by_kind"] = by_kind
    print("-----------------------")
    for label, key in (("Mean ratio", "mean_ratio"),
                       ("Median ratio", "median_ratio"),
                       ("P90 ratio", "p90_ratio"),
                       ("Worst ratio", "worst_ratio")):
        value = summary[key]
        print(f"{label}: {value:.4f}" if value is not None else f"{label}: n/a")
    print(f"Valid solutions: {summary['valid_solutions']}/{summary['total_instances']}")
    print(f"Proven OPT: {summary['opt_proven']}/{summary['total_instances']}")
    print(f"OPT cache hits: {summary['opt_cache_hits']}")
    print("By kind (mean ratio, density, pairwise Jaccard):")
    for kind, item in by_kind.items():
        mean_ratio = f"{item['mean_ratio']:.4f}" if item["mean_ratio"] is not None else "n/a"
        print(f"  {kind}: {mean_ratio}, {item['mean_density']:.3f}, "
              f"{item['mean_pairwise_jaccard']:.3f}")
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
    parser.add_argument("--opt-cache", type=Path, default=Path("results/opt_cache.json"),
                        help="cache for proven OPT (default: results/opt_cache.json)")
    parser.add_argument("--no-opt-cache", action="store_true")
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
    cache = None if args.no_opt_cache else OptimumCache(args.opt_cache)
    data = run(config, cache)
    data["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    output = args.output or Path("results") / f"{config.name}_{config.seed_start}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False),
                      encoding="utf-8")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
