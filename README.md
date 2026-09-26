# Set Cover research environment — Phase 1

A small, reproducible environment for **unweighted Set Cover**. This is the
experimental foundation for later scoring function search and counterexample
feedback; it does not call an LLM.

**No OpenAI API key is required** to install, test, or run this phase.

Project milestones and upcoming decisions are tracked in [PROGRESS.md](PROGRESS.md).

## Setup

Requires Python 3.10+. From this directory:

```bash
python -m pip install -e ".[dev]"
```

The only runtime dependency is SciPy (which provides the HiGHS MILP solver).

## Run

```bash
python -m experiments.run_benchmark
python -m experiments.run_benchmark --config configs/pilot_search.json
python -m experiments.run_benchmark --config configs/pilot_validation.json
python -m experiments.run_benchmark --config configs/pilot_test.json
python -m experiments.run_benchmark --config configs/greedy_trap.json
python -m experiments.run_benchmark --n 50 --m 100 --per-kind 1 --seed 42
python -m experiments.run_benchmark --kinds random sparse --output results/custom.json
python -m experiments.run_benchmark --no-opt-cache
python -m pytest -q
```

The default `configs/smoke.json` runs two instances per distribution (10 total),
with `n=30`, `m=50`. The pilot configurations use the same `n=50`, `m=100`
size and **disjoint seed ranges**: 25 search, 10 validation, and 15 held-out
test instances. Keep the held-out results out of future Agent prompts and
selection decisions. These are pilot sizes, not final thesis sample sizes.
`configs/greedy_trap.json` is a controlled diagnostic family: each 8-element
block makes classical greedy select 3 sets while OPT selects 2. It checks that
the evaluation can expose a known weakness; it is not a representative random
distribution or evidence of a general approximation bound.

The CLI prints each greedy solution size, exact OPT status, empirical ratio,
algorithm runtime, and OPT runtime, followed by aggregate statistics. JSON
under `results/` stores the full configuration, software versions, each
instance and solution, structural descriptors, and summary. Results are
ignored by Git by default; the configuration files are version controlled.
Seeds reproduce instances, while wall-clock times can vary by machine.
The summary also groups empirical ratios and structural descriptors by kind.

Proven optimal solutions are saved by default in `results/opt_cache.json` and
reused when the exact same ordered set family appears again. Use
`--opt-cache PATH` to choose a different cache, or `--no-opt-cache` to solve
every OPT again.
Only solver-proven optima are written. The cache is a trusted local artifact:
validation checks that stored indices form a cover with the stated size, but
cannot independently prove a manually edited entry is optimal. Delete the
cache to force independent recomputation. Cached records have `opt_source` set
to `cache` and zero OPT runtime for that run.

## Modules

- `setcover.instance`: immutable instance, structural validation, feasibility,
  and solution validation. Duplicate and empty sets are allowed. Elements are
  integers `0..n-1`; solutions contain set indices `0..m-1`.
- `setcover.generators`: seeded `random`, `sparse`, `dense`, `high_overlap`, and
  `low_overlap` distributions, plus the controlled `greedy_trap` diagnostic.
  Density/overlap parameters are simple starting points, not claims that the
  samples meet exact structural bounds.
- `setcover.stats`: density, element frequency, set size, duplicate count,
  and mean pairwise Jaccard for inspecting generated distributions.
- `setcover.algorithms`: classical greedy, with deterministic index tie breaks.
  `greedy(instance, score=...)` accepts a scoring function of
  `(instance, set_index, uncovered)` while retaining a fixed, terminating loop.
- `setcover.exact`: integer programming model solved with SciPy MILP. It returns
  only a **proven** optimal cover, with zero MIP gap tolerance. Infeasible
  instances and unproven solves raise an error; no incumbent is mislabeled as OPT.
- `setcover.evaluation`: injectable algorithm interface, validity check,
  algorithm and OPT runtime, exact OPT status, and empirical `ALG/OPT`.
- `experiments.run_benchmark`: CLI runner and structured JSON output.
- `experiments.opt_cache`: local cache of solver-proven optimum covers, keyed
  by a fingerprint of the complete ordered instance.

Each config sets an OPT time limit of 20 seconds per instance. If the solver
reaches a limit, the record retains the algorithm result with `opt=null`,
`ratio=null`, and `opt_status="limit"`; the benchmark continues. The summary
counts how many ratios are available. The limit is a cap per OPT call, not a
guarantee on the total run time.

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

## Agent and API boundary

This repository currently runs local Python code and SciPy only. It does not
import an LLM SDK, read `OPENAI_API_KEY`, or send model requests. Codex helping
develop the repository is separate from the experimental method. A future
Phase 2 implementation will need an explicit model/provider choice, credential
configuration, request logging, and cost controls before model calls begin.
