"""Disk cache for proven exact solutions of unchanged instances."""

import hashlib
import json
import os
from pathlib import Path

import scipy

from setcover.exact import ExactResult
from setcover.instance import SetCoverInstance, validate_solution


def instance_fingerprint(instance: SetCoverInstance) -> str:
    payload = json.dumps(instance.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class OptimumCache:
    """Reuse only results that were proved optimal by ``solve_exact``.

    The cache key hashes the complete ordered set family, so changing a
    generator cannot silently reuse an OPT from a different instance.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if (not isinstance(data, dict) or data.get("schema_version") != 1
                    or data.get("solver") != "scipy.milp"
                    or not isinstance(data.get("entries"), dict)):
                raise ValueError(f"invalid OPT cache: {path}")
            self.entries = data["entries"]
        else:
            self.entries: dict[str, dict] = {}

    def get(self, instance: SetCoverInstance) -> ExactResult | None:
        item = self.entries.get(instance_fingerprint(instance))
        if item is None:
            return None
        indices = item.get("indices")
        objective = item.get("objective")
        if (not isinstance(indices, list)
                or type(objective) is not int
                or objective != len(indices)
                or not validate_solution(instance, indices)):
            raise ValueError("cached OPT contains an invalid cover or objective")
        return ExactResult(tuple(indices), objective)

    def add(self, instance: SetCoverInstance, result: ExactResult) -> None:
        if result.objective != len(result.indices) or not validate_solution(instance, result.indices):
            raise ValueError("cannot cache an invalid exact solution")
        self.entries[instance_fingerprint(instance)] = {
            "objective": result.objective,
            "indices": list(result.indices),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "solver": "scipy.milp",
            "scipy_version_last_written": scipy.__version__,
            "entries": self.entries,
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
        os.replace(temporary, self.path)
