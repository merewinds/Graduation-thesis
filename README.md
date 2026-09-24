# Set Cover research environment — Phase 1

A small, reproducible environment for **unweighted Set Cover**. This is the
experimental foundation for later scoring function search and counterexample
feedback; it does not call an LLM.

Project milestones and upcoming decisions are tracked in [PROGRESS.md](PROGRESS.md).

## Setup

Requires Python 3.10+. From this directory:

```bash
python -m pip install -e .
python -m pip install pytest
```

The only runtime dependency is SciPy (which provides the HiGHS MILP solver).

## Run

```bash
python -m experiments.run_benchmark
python -m experiments.run_benchmark --n 50 --m 100 --per-kind 1 --seed 42
python -m experiments.run_benchmark --kinds random sparse --output results/custom.json
python -m pytest -q
```

The default benchmark runs two instances per distribution (10 total), with
`n=30`, `m=50`, and seed 42. The CLI prints each greedy solution size, exact
OPT, empirical ratio, algorithm runtime, and validity, followed by aggregate
statistics. A JSON file under `results/` contains the configuration, each
instance's complete set family, both solutions, and the summary. The recorded
seed makes the instances reproducible; wall-clock times can vary by machine.

## Modules

- `setcover.instance`: immutable instance, structural validation, feasibility,
  and solution validation. Duplicate and empty sets are allowed. Elements are
  integers `0..n-1`; solutions contain set indices `0..m-1`.
- `setcover.generators`: seeded `random`, `sparse`, `dense`, `high_overlap`, and
  `low_overlap` distributions. Their density/overlap parameters are simple
  starting points, not claims that the samples meet exact structural bounds.
- `setcover.algorithms`: classical greedy, with deterministic index tie breaks.
  `greedy(instance, score=...)` accepts a scoring function of
  `(instance, set_index, uncovered)` while retaining a fixed, terminating loop.
- `setcover.exact`: integer programming model solved with SciPy MILP. It returns
  only a **proven** optimal cover. Infeasible instances and unproven solves raise
  an error; no incumbent is mislabeled as OPT.
- `setcover.evaluation`: injectable algorithm interface, validity check,
  algorithm runtime, exact OPT, and empirical `ALG/OPT`.
- `experiments.run_benchmark`: CLI runner and structured JSON output.

For an empty universe, the empty cover is optimal and its ratio is defined as
1; a redundant nonempty cover is valid but has no finite ratio. Invalid
algorithm outputs have `valid=false` and no ratio. Reported ratios
are **empirical observations**, not approximation guarantees. Exact MILP may
take a long time on harder or larger instances; start with the default sizes.

## Example scoring function

```python
from setcover.algorithms import greedy

def my_score(instance, index, uncovered):
    gain = len(instance.sets[index] & uncovered)
    return gain / (1 + len(instance.sets[index]))

solution = greedy(instance, score=my_score)
```

This extension point supports later algorithm search without replacing the
instance, validity, or exact evaluation code.
