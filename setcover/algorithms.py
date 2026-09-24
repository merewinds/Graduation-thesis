"""Greedy algorithm with a narrow scoring-function extension point."""

import math
from collections.abc import Callable

from .instance import SetCoverInstance

ScoreFunction = Callable[[SetCoverInstance, int, frozenset[int]], float]


def coverage_score(instance: SetCoverInstance, index: int, uncovered: frozenset[int]) -> float:
    return float(len(instance.sets[index] & uncovered))


def greedy(instance: SetCoverInstance, score: ScoreFunction = coverage_score) -> tuple[int, ...]:
    """Repeatedly select a set with positive gain; ties use the lower index.

    A custom score can change the priority but never select zero-gain sets.
    The fixed selection loop keeps candidate heuristics valid and terminating.
    """
    if not instance.is_feasible:
        raise ValueError("infeasible instance: some universe elements are uncovered")
    uncovered = set(range(instance.n))
    chosen: list[int] = []
    while uncovered:
        state = frozenset(uncovered)
        candidates = []
        for i, subset in enumerate(instance.sets):
            if not subset & state:
                continue
            value = float(score(instance, i, state))
            if not math.isfinite(value):
                raise ValueError(f"score for set {i} must be finite")
            candidates.append((value, -i, i))
        if not candidates:
            raise RuntimeError("feasible instance has no positive-gain set")
        index = max(candidates)[2]
        chosen.append(index)
        uncovered.difference_update(instance.sets[index])
    return tuple(chosen)
