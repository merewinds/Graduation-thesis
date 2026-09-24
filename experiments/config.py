"""Small, version-controlled JSON benchmark configurations."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from setcover.generators import KINDS


@dataclass(frozen=True)
class BenchmarkConfig:
    name: str
    split: str
    n: int
    m: int
    per_kind: int
    seed_start: int
    kinds: tuple[str, ...]
    opt_time_limit_seconds: float

    def __post_init__(self) -> None:
        if not self.name or not self.split:
            raise ValueError("name and split must be nonempty")
        for field in ("n", "m", "per_kind", "seed_start"):
            value = getattr(self, field)
            if type(value) is not int or value < (1 if field == "per_kind" else 0):
                raise ValueError(f"{field} must be a nonnegative integer (per_kind > 0)")
        if self.n > 0 and self.m == 0:
            raise ValueError("m must be positive for a nonempty universe")
        if not self.kinds or len(set(self.kinds)) != len(self.kinds):
            raise ValueError("kinds must be nonempty and unique")
        if any(kind not in KINDS for kind in self.kinds):
            raise ValueError(f"kinds must be chosen from {KINDS}")
        if (type(self.opt_time_limit_seconds) not in (int, float)
                or not math.isfinite(self.opt_time_limit_seconds)
                or self.opt_time_limit_seconds <= 0):
            raise ValueError("opt_time_limit_seconds must be positive and finite")

    @classmethod
    def load(cls, path: Path) -> "BenchmarkConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("config must be a JSON object")
        data["kinds"] = tuple(data["kinds"])
        return cls(**data)

    def to_dict(self) -> dict:
        return asdict(self)

    def instance_specs(self):
        """Yield disjoint deterministic seeds in a stable distribution order."""
        for kind_index, kind in enumerate(self.kinds):
            for repeat in range(self.per_kind):
                yield kind, self.seed_start + kind_index * self.per_kind + repeat
