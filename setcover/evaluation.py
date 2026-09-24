"""Per-instance evaluation; solver is injectable for later algorithm search."""

import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass

from .exact import solve_exact
from .instance import SetCoverInstance, validate_solution

Algorithm = Callable[[SetCoverInstance], Iterable[int]]


@dataclass(frozen=True)
class Evaluation:
    alg: int | None
    opt: int
    ratio: float | None
    runtime_seconds: float
    valid: bool
    solution: tuple[int, ...]
    opt_solution: tuple[int, ...]
    error: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["solution"] = list(self.solution)
        data["opt_solution"] = list(self.opt_solution)
        return data


def evaluate(instance: SetCoverInstance, algorithm: Algorithm) -> Evaluation:
    """Measure algorithm time only; OPT is computed separately and exactly.

    Invalid candidates remain visible in results, with no reported ratio.
    An unproven OPT or infeasible instance raises instead of silently using a
    bound as the denominator.
    """
    optimum = solve_exact(instance)
    started = time.perf_counter()
    try:
        solution = tuple(algorithm(instance))
        elapsed = time.perf_counter() - started
        valid = validate_solution(instance, solution)
        error = None if valid else "invalid cover or set indices"
    except Exception as exc:
        elapsed = time.perf_counter() - started
        solution = ()
        valid = False
        error = f"{type(exc).__name__}: {exc}"
    alg = len(solution) if valid else None
    if not valid:
        ratio = None
    elif optimum.objective == 0:
        # A redundant nonempty cover of an empty universe has no finite
        # ALG/OPT ratio. The empty optimal cover is assigned ratio 1.
        ratio = 1.0 if alg == 0 else None
    else:
        ratio = alg / optimum.objective
    return Evaluation(alg, optimum.objective, ratio, elapsed, valid,
                      solution, optimum.indices, error)
