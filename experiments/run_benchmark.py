"""Reproducible command-line benchmark: python -m experiments.run_benchmark."""

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from setcover.algorithms import greedy
from setcover.evaluation import evaluate
from setcover.generators import KINDS, generate


def run(n: int, m: int, per_kind: int, seed: int, kinds: tuple[str, ...]) -> dict:
    if per_kind < 1:
        raise ValueError("per_kind must be positive")
    if not kinds or any(kind not in KINDS for kind in kinds):
        raise ValueError(f"kinds must be chosen from {KINDS}")
    records = []
    for number, (kind, repeat) in enumerate(
        ((kind, repeat) for kind in kinds for repeat in range(per_kind)), start=1
    ):
        instance_seed = seed + number - 1
        instance = generate(kind, n, m, instance_seed)
        result = evaluate(instance, greedy)
        record = {"id": number, "kind": kind, "seed": instance_seed,
                  "instance": instance.to_dict(), "evaluation": result.to_dict()}
        records.append(record)
        print(f"Instance {number:03d} ({kind}, seed={instance_seed})")
        print(f"n = {n}, m = {m}")
        print(f"Greedy = {result.alg}, OPT = {result.opt}, Ratio = {result.ratio:.4f}")
        print(f"Runtime = {result.runtime_seconds:.6f} s, Valid = {result.valid}\n")
    ratios = [r["evaluation"]["ratio"] for r in records
              if r["evaluation"]["ratio"] is not None]
    summary = {"mean_ratio": statistics.mean(ratios) if ratios else None,
               "median_ratio": statistics.median(ratios) if ratios else None,
               "worst_ratio": max(ratios) if ratios else None,
               "valid_solutions": sum(r["evaluation"]["valid"] for r in records),
               "total_instances": len(records)}
    print("-----------------------")
    print(f"Mean ratio: {summary['mean_ratio']:.4f}")
    print(f"Median ratio: {summary['median_ratio']:.4f}")
    print(f"Worst ratio: {summary['worst_ratio']:.4f}")
    print(f"Valid solutions: {summary['valid_solutions']}/{summary['total_instances']}")
    print("-----------------------")
    return {"config": {"n": n, "m": m, "per_kind": per_kind,
                       "seed": seed, "kinds": list(kinds)},
            "records": records, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--m", type=int, default=50)
    parser.add_argument("--per-kind", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--kinds", nargs="+", choices=KINDS, default=list(KINDS))
    parser.add_argument("--output", type=Path, default=None,
                        help="JSON path (default: results/benchmark_<seed>.json)")
    args = parser.parse_args()
    data = run(args.n, args.m, args.per_kind, args.seed, tuple(args.kinds))
    data["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    output = args.output or Path("results") / f"benchmark_{args.seed}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
