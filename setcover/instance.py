"""Validated, immutable unweighted Set Cover instances."""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SetCoverInstance:
    """Universe is 0..n-1; sets are indexed in their original order.

    Duplicate and empty sets are legal. An instance may be infeasible; use
    ``is_feasible`` to check whether its set family covers the universe.
    """

    n: int
    sets: tuple[frozenset[int], ...]

    def __post_init__(self) -> None:
        if type(self.n) is not int or self.n < 0:
            raise ValueError("n must be a nonnegative integer")
        try:
            normalized = tuple(frozenset(s) for s in self.sets)
        except (TypeError, ValueError) as exc:
            raise ValueError("sets must be an iterable of element collections") from exc
        for i, subset in enumerate(normalized):
            if any(type(e) is not int or e < 0 or e >= self.n for e in subset):
                raise ValueError(f"set {i} contains an element outside 0..n-1")
        object.__setattr__(self, "sets", normalized)

    @property
    def m(self) -> int:
        return len(self.sets)

    @property
    def is_feasible(self) -> bool:
        return len(set().union(*self.sets)) == self.n

    def to_dict(self) -> dict:
        return {"n": self.n, "sets": [sorted(s) for s in self.sets]}


def validate_solution(instance: SetCoverInstance, indices: Iterable[int]) -> bool:
    """Return whether indices are distinct, in range, and cover the universe."""
    try:
        selected = tuple(indices)
    except TypeError:
        return False
    if any(type(i) is not int or i < 0 or i >= instance.m for i in selected):
        return False
    if len(set(selected)) != len(selected):
        return False
    return len(set().union(*(instance.sets[i] for i in selected))) == instance.n
