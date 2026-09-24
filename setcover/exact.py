"""Exact unweighted Set Cover via SciPy's open-source MILP solver."""

from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .instance import SetCoverInstance, validate_solution


@dataclass(frozen=True)
class ExactResult:
    indices: tuple[int, ...]
    objective: int


class ExactSolveError(RuntimeError):
    """The MILP solver did not establish an optimum."""

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def solve_exact(instance: SetCoverInstance, time_limit: float | None = None) -> ExactResult:
    """Return a proven optimum; raise if infeasible or optimality is unproven."""
    if not instance.is_feasible:
        raise ValueError("infeasible instance: OPT does not exist")
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be positive and finite")
    if instance.n == 0:
        return ExactResult((), 0)
    matrix = lil_matrix((instance.n, instance.m), dtype=float)
    for j, subset in enumerate(instance.sets):
        for e in subset:
            matrix[e, j] = 1.0
    options = {"disp": False, "mip_rel_gap": 0.0}
    if time_limit is not None:
        options["time_limit"] = time_limit
    result = milp(
        c=np.ones(instance.m),
        integrality=np.ones(instance.m),
        bounds=Bounds(0, 1),
        constraints=LinearConstraint(matrix.tocsr(), np.ones(instance.n), np.inf),
        options=options,
    )
    if result.status != 0 or result.x is None:
        status = "limit" if result.status == 1 else "solver_error"
        raise ExactSolveError(status, f"MILP did not prove optimality: {result.message}")
    indices = tuple(i for i, x in enumerate(result.x) if x > 0.5)
    if not validate_solution(instance, indices):
        raise RuntimeError("MILP returned an invalid cover")
    if abs(result.fun - len(indices)) > 1e-6:
        raise RuntimeError("MILP objective and solution disagree")
    return ExactResult(indices, len(indices))
