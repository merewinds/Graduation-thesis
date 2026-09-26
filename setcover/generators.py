"""Seeded generators for several Set Cover instance families."""

import random

from .instance import SetCoverInstance

KINDS = ("random", "sparse", "dense", "high_overlap", "low_overlap", "greedy_trap")


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
    if kind == "greedy_trap":
        return _greedy_trap(n, m, rng)
    sets: list[set[int]] = [set() for _ in range(m)]
    if kind == "low_overlap":
        # Sets draw from separate blocks of elements. Multiple sets per block
        # avoid the near-singleton degeneration when m is larger than n.
        block_count = min(m, max(2, n // 5)) if n else 0
        elements = list(range(n))
        rng.shuffle(elements)
        blocks = [set() for _ in range(block_count)]
        for position, e in enumerate(elements):
            blocks[position % block_count].add(e)
        if block_count:
            for j, subset in enumerate(sets):
                subset.update(e for e in blocks[j % block_count] if rng.random() < 0.7)
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


def _greedy_trap(n: int, m: int, rng: random.Random) -> SetCoverInstance:
    """Plant independent 8-element gadgets where greedy needs 3 vs OPT 2.

    Each gadget has two disjoint optimal 4-sets and a 5-set decoy. Remaining
    filler sets stay inside one optimal 4-set, so they cannot erase the gap.
    """
    blocks, remainder = divmod(n, 8)
    required = 3 * blocks + remainder
    if blocks == 0 or m < required:
        raise ValueError("greedy_trap requires n >= 8 and m >= 3*(n//8) + n%8")
    elements = list(range(n))
    rng.shuffle(elements)
    sets: list[set[int]] = []
    sides: list[tuple[int, ...]] = []
    for block in range(blocks):
        group = elements[8 * block:8 * (block + 1)]
        left, right = set(group[:4]), set(group[4:])
        decoy = set(group[:3]) | set(group[4:6])
        sets.extend((left, right, decoy))
        sides.extend((tuple(group[:4]), tuple(group[4:])))
    for e in elements[8 * blocks:]:
        sets.append({e})
    while len(sets) < m:
        side = rng.choice(sides)
        sets.append(set(rng.sample(side, rng.randint(1, 2))))
    return SetCoverInstance(n, tuple(frozenset(s) for s in sets))
