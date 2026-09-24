import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import setcover.exact as exact_module
from experiments.config import BenchmarkConfig
from experiments.run_benchmark import percentile_nearest_rank, run
from setcover.algorithms import greedy
from setcover.evaluation import evaluate
from setcover.generators import generate
from setcover.instance import SetCoverInstance
from setcover.stats import describe_instance

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def test_pilot_splits_use_disjoint_seeds():
    configs = [BenchmarkConfig.load(CONFIGS / f"pilot_{split}.json")
               for split in ("search", "validation", "test")]
    seed_sets = [{seed for _, seed in config.instance_specs()} for config in configs]
    assert [len(seeds) for seeds in seed_sets] == [25, 10, 15]
    assert len(set.union(*seed_sets)) == 50
    assert {config.split for config in configs} == {"search", "validation", "held_out_test"}


@pytest.mark.parametrize("field,value", [("per_kind", 0), ("seed_start", -1),
                                         ("opt_time_limit_seconds", float("nan")),
                                         ("kinds", ("random", "random"))])
def test_invalid_config_rejected(field, value):
    config = BenchmarkConfig.load(CONFIGS / "smoke.json")
    with pytest.raises(ValueError):
        replace(config, **{field: value})


def test_unproven_opt_keeps_valid_alg_without_ratio(monkeypatch):
    def limit_result(**kwargs):
        assert kwargs["options"]["mip_rel_gap"] == 0.0
        assert kwargs["options"]["time_limit"] == 1.0
        return SimpleNamespace(status=1, x=None, message="Time limit reached")

    monkeypatch.setattr(exact_module, "milp", limit_result)
    instance = SetCoverInstance(2, [{0}, {1}])
    result = evaluate(instance, greedy, opt_time_limit=1.0)
    assert result.valid and result.alg == 2
    assert result.opt is None and result.ratio is None
    assert result.opt_status == "limit" and result.opt_error


def test_low_overlap_distribution_is_not_singleton_degenerate():
    low = describe_instance(generate("low_overlap", 50, 100, 42))
    high = describe_instance(generate("high_overlap", 50, 100, 42))
    assert low["mean_set_size"] > 2
    assert low["mean_pairwise_jaccard"] < high["mean_pairwise_jaccard"]


def test_empty_universe_low_overlap():
    assert generate("low_overlap", 0, 5, 1).is_feasible


def test_benchmark_result_is_json_and_counts_are_consistent():
    config = replace(BenchmarkConfig.load(CONFIGS / "smoke.json"),
                     n=8, m=12, per_kind=1)
    data = run(config)
    json.dumps(data, allow_nan=False)
    assert data["summary"]["total_instances"] == 5
    assert data["summary"]["valid_solutions"] == 5
    assert data["summary"]["opt_proven"] == 5
    assert all("instance_stats" in record for record in data["records"])


def test_benchmark_continues_when_opt_is_unproven(monkeypatch):
    monkeypatch.setattr(
        exact_module, "milp",
        lambda **kwargs: SimpleNamespace(status=1, x=None, message="Time limit reached"),
    )
    config = replace(BenchmarkConfig.load(CONFIGS / "smoke.json"),
                     n=4, m=6, per_kind=1, kinds=("random",))
    data = run(config)
    record = data["records"][0]["evaluation"]
    assert record["valid"] and record["opt_status"] == "limit"
    assert record["opt"] is None and record["ratio"] is None
    assert data["summary"]["opt_proven"] == 0
    assert data["summary"]["ratios_available"] == 0


def test_nearest_rank_percentile():
    assert percentile_nearest_rank([1.0, 1.5, 2.0], 0.9) == 2.0
    assert percentile_nearest_rank([], 0.9) is None
