"""Per-instance evaluation; solver is injectable for later algorithm search."""

import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass

from .exact import ExactSolveError, solve_exact
from .instance import SetCoverInstance, validate_solution

Algorithm = Callable[[SetCoverInstance], Iterable[int]]


@dataclass(frozen=True)
class Evaluation:
    alg: int | None
    opt: int | None
    ratio: float | None
    runtime_seconds: float
    opt_runtime_seconds: float
    opt_status: str
    valid: bool
    solution: tuple[int, ...]
    opt_solution: tuple[int, ...]
    error: str | None = None
    opt_error: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["solution"] = list(self.solution)
        data["opt_solution"] = list(self.opt_solution)
        return data


def evaluate(instance: SetCoverInstance, algorithm: Algorithm,
             opt_time_limit: float | None = None) -> Evaluation:
    """Measure algorithm and OPT time separately.

    Invalid candidates remain visible in results, with no reported ratio.
    An unproven OPT is recorded without a ratio; infeasible instances raise.
    """
    if not instance.is_feasible:
        raise ValueError("infeasible instance: OPT does not exist")
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
    opt_started = time.perf_counter()
    try:
        optimum = solve_exact(instance, time_limit=opt_time_limit)
        opt_status = "optimal"
        opt_error = None
    except ExactSolveError as exc:
        optimum = None
        opt_status = exc.status
        opt_error = str(exc)
    opt_elapsed = time.perf_counter() - opt_started
    if not valid or optimum is None:
        ratio = None
    elif optimum.objective == 0:
        # A redundant nonempty cover of an empty universe has no finite
        # ALG/OPT ratio. The empty optimal cover is assigned ratio 1.
        ratio = 1.0 if alg == 0 else None
    else:
        ratio = alg / optimum.objective
    return Evaluation(alg, optimum.objective if optimum else None, ratio,
                      elapsed, opt_elapsed, opt_status, valid, solution,
                      optimum.indices if optimum else (), error, opt_error)
