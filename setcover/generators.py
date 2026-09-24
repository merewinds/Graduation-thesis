"""Seeded generators for several Set Cover instance families."""

import random

from .instance import SetCoverInstance

KINDS = ("random", "sparse", "dense", "high_overlap", "low_overlap")


def generate(kind: str, n: int, m: int, seed: int) -> SetCoverInstance:
    """Generate a feasible instance using only a local seeded RNG.

    Every element is assigned to at least one set after sampling. This small
    repair makes feasibility deterministic without requiring singleton sets.
    """
    if type(n) is not int or n < 0 or type(m) is not int or m < 0:
        raise ValueError("n and m must be nonnegative integers")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if n > 0 and m == 0:
        raise ValueError("a nonempty universe requires at least one set")
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; choose from {KINDS}")
    rng = random.Random(seed)
    sets: list[set[int]] = [set() for _ in range(m)]
    if kind == "low_overlap":
        for e in range(n):
            sets[e % m].add(e)
        for e in range(n):
            if m > 1 and rng.random() < 0.10:
                j = rng.randrange(m - 1)
                if j >= e % m:
                    j += 1
                sets[j].add(e)
    elif kind == "high_overlap":
        common = {e for e in range(n) if rng.random() < 0.55}
        for subset in sets:
            subset.update(common)
            subset.update(e for e in range(n) if rng.random() < 0.12)
    else:
        probability = {"random": 0.30, "sparse": 0.08, "dense": 0.70}[kind]
        for subset in sets:
            subset.update(e for e in range(n) if rng.random() < probability)
    covered = set().union(*sets)
    for e in range(n):
        if e not in covered:
            sets[rng.randrange(m)].add(e)
    return SetCoverInstance(n, tuple(frozenset(s) for s in sets))
