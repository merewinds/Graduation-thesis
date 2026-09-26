import itertools

import pytest

from setcover.algorithms import greedy
from setcover.evaluation import evaluate
from setcover.exact import solve_exact
from setcover.generators import KINDS, generate
from setcover.instance import SetCoverInstance, validate_solution


def brute_force_opt(instance):
    for k in range(instance.m + 1):
        for candidate in itertools.combinations(range(instance.m), k):
            if validate_solution(instance, candidate):
                return k
    raise ValueError("infeasible")


@pytest.mark.parametrize("n,sets", [(-1, []), (2, [{2}]), (2, [{-1}]),
                                        (2, [{True}]), (2, [[0], None])])
def test_malformed_instance(n, sets):
    with pytest.raises(ValueError):
        SetCoverInstance(n, sets)


def test_duplicates_empty_sets_and_solution_validation():
    instance = SetCoverInstance(2, [{0, 1}, {0, 1}, set()])
    assert instance.is_feasible
    assert solve_exact(instance).objective == 1
    assert validate_solution(instance, [1])
    assert not validate_solution(instance, [1, 1])
    assert not validate_solution(instance, [3])
    assert not validate_solution(instance, [True])
    assert not validate_solution(instance, [2])


def test_infeasible_instance():
    instance = SetCoverInstance(2, [{0}, set()])
    assert not instance.is_feasible
    with pytest.raises(ValueError, match="infeasible"):
        greedy(instance)
    with pytest.raises(ValueError, match="infeasible"):
        solve_exact(instance)


def test_trivial_instances():
    empty = SetCoverInstance(0, [])
    assert greedy(empty) == ()
    assert solve_exact(empty).objective == 0
    assert evaluate(empty, greedy).ratio == 1.0
    singleton = SetCoverInstance(1, [{0}])
    assert greedy(singleton) == (0,)
    assert solve_exact(singleton).objective == 1
    empty_with_redundant_set = SetCoverInstance(0, [set()])
    redundant_result = evaluate(empty_with_redundant_set, lambda _: [0])
    assert redundant_result.valid and redundant_result.ratio is None


def test_known_optimum_and_greedy_validity():
    instance = SetCoverInstance(4, [{0, 1, 2}, {0, 1}, {2, 3}, {3}])
    assert solve_exact(instance).objective == 2
    assert validate_solution(instance, greedy(instance))
    assert greedy(instance) == (0, 2)


def test_scoring_extension_and_bad_score():
    instance = SetCoverInstance(3, [{0, 1}, {1, 2}, {0}, {2}])
    selected = greedy(instance, lambda inst, i, uncovered: -len(inst.sets[i] & uncovered))
    assert validate_solution(instance, selected)
    with pytest.raises(ValueError, match="finite"):
        greedy(instance, lambda inst, i, uncovered: float("nan"))


@pytest.mark.parametrize("kind", KINDS)
def test_generator_reproducible_and_feasible(kind):
    first = generate(kind, 16, 24, 123)
    assert first == generate(kind, 16, 24, 123)
    assert first.is_feasible
    assert validate_solution(first, greedy(first))


def test_exact_matches_enumeration_on_small_random_instances():
    for kind in KINDS:
        for seed in range(4):
            instance = generate(kind, 8, 8, seed) if kind == "greedy_trap" else generate(kind, 7, 8, seed)
            assert solve_exact(instance).objective == brute_force_opt(instance)


def test_greedy_trap_has_known_gap():
    instance = generate("greedy_trap", 48, 96, 42)
    assert validate_solution(instance, greedy(instance))
    assert len(greedy(instance)) == 18
    assert solve_exact(instance).objective == 12
    assert evaluate(instance, greedy).ratio == 1.5


def test_greedy_trap_rejects_insufficient_size():
    with pytest.raises(ValueError, match="requires n >= 8"):
        generate("greedy_trap", 7, 10, 1)


def test_invalid_candidate_is_reported_without_ratio():
    instance = SetCoverInstance(2, [{0}, {1}])
    result = evaluate(instance, lambda _: [0])
    assert not result.valid
    assert result.alg is None and result.ratio is None
    assert result.opt == 2
