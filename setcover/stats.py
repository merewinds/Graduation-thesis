"""Simple structural descriptors for checking generated distributions."""

import statistics
from itertools import combinations

from .instance import SetCoverInstance


def describe_instance(instance: SetCoverInstance) -> dict[str, float | int]:
    sizes = [len(subset) for subset in instance.sets]
    frequencies = [sum(e in subset for subset in instance.sets)
                   for e in range(instance.n)]
    jaccards = []
    for left, right in combinations(instance.sets, 2):
        union = left | right
        if union:
            jaccards.append(len(left & right) / len(union))
    return {
        "mean_set_size": statistics.mean(sizes) if sizes else 0.0,
        "density": sum(sizes) / (instance.n * instance.m)
        if instance.n and instance.m else 0.0,
        "mean_element_frequency": statistics.mean(frequencies) if frequencies else 0.0,
        "max_element_frequency": max(frequencies, default=0),
        "mean_pairwise_jaccard": statistics.mean(jaccards) if jaccards else 0.0,
        "empty_sets": sizes.count(0),
        "duplicate_sets": instance.m - len(set(instance.sets)),
    }
