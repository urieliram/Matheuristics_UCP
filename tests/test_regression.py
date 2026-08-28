"""End-to-end regression guard for the refactor.

The contract this suite defends: refactoring must not move a single objective value.
Golden values for uc_057 (8 generators, 24 periods) live in tests/data/golden_uc_057.csv.
Regenerated 2026-08-25 after registering eq.(56) (start-up costs now priced) and wiring
constraint (Startcost4): z moved from 571490.7 to 573630.7 (+2140.00, the start-up cost
of the same 5 starts).

Columns of the stat.csv row are documented in main.py just above the `row = [...]` assembly.
Wall-clock columns and the timestamp are excluded from the comparison: they legitimately vary
between runs (and a faster refactor is the goal). Everything else must match exactly.
"""
import csv
from pathlib import Path

import pytest

GOLDEN = Path(__file__).parent / "data" / "golden_uc_057.csv"

# stat.csv column indices, per the header comment in main.py.
COL_LOCALTIME = 1
COL_TIMES = range(19, 30)          # t_lp .. t_
VOLATILE = {COL_LOCALTIME} | set(COL_TIMES)

NAMES = (
    "ambiente localtime nameins T G gap timeconst timefull "
    "z_lp z_milp z_milp2 z_harjk z_hard3 z_lbc1 z_lbc2 z_lbc3 z_lbc4 z_ks z_ "
    "t_lp t_milp t_milp2 t_harjk t_hard3 t_lbc1 t_lbc2 t_lbc3 t_lbc4 t_ks t_ "
    "lb_milp g_milp g_milp2 g_harjk g_hard3 g_lbc1 g_lbc2 g_lbc3 g_lbc4 g_ks g_ "
    "lb_milp2 k emphasizeMILP symmetryMILP strategyMILP lbheurMILP "
    "emphasizeHEUR symmetryHEUR strategyHEUR lbheurHEUR comment"
).split()

# The short-horizon configuration the golden row was captured under.
GOLDEN_CONFIG = dict(timelp=60, timeconst=60, timefull=120, KS="False")


@pytest.fixture(scope="module")
def golden():
    return next(csv.reader(GOLDEN.open()))


@pytest.mark.slow
def test_uc_057_results_unchanged(run_instance, golden):
    """A full solve of uc_057 reproduces every published number."""
    proc, row = run_instance("uc_057.json", **GOLDEN_CONFIG)

    assert proc.returncode == 0, f"main.py failed:\n{proc.stdout[-4000:]}"
    assert row is not None, "no stat.csv was written"
    assert len(row) == len(golden) == len(NAMES)

    drift = [
        f"{NAMES[i]}: golden={g!r} got={r!r}"
        for i, (g, r) in enumerate(zip(golden, row))
        if i not in VOLATILE and g != r
    ]
    assert not drift, "results drifted:\n  " + "\n  ".join(drift)


@pytest.mark.slow
def test_uc_057_reports_optimal_milp(run_instance):
    """The MILP leg still proves optimality, not just some feasible point."""
    proc, row = run_instance("uc_057.json", **GOLDEN_CONFIG)
    assert proc.returncode == 0
    assert float(row[NAMES.index("g_milp")]) == 0.0
    assert float(row[NAMES.index("z_milp")]) == pytest.approx(573630.7)


@pytest.mark.slow
def test_kernel_search_completes(run_instance):
    """Regression: KS used to die with IndexError once it ran out of buckets.

    `iterstop` was derived from Sturges' n, but the number of bucket boundaries actually
    built (len(k_)-1) can be smaller, so `k_[iter_bk + 1]` ran off the end. It only bit on
    small instances: with ~500 free variables the two numbers coincide, which is why the
    published large-instance runs never hit it.
    """
    proc, row = run_instance("uc_057.json", timelp=30, timeconst=15, timefull=45, KS="True")

    assert "IndexError" not in proc.stdout, "KS bucket loop overran k_ again"
    assert proc.returncode == 0, f"main.py failed:\n{proc.stdout[-3000:]}"
    assert row is not None, "KS crashed before stat.csv was written"
    assert "KS end" in proc.stdout


@pytest.mark.slow
def test_reported_gaps_match_reported_incumbents(run_instance):
    """Every gap in the stat.csv row must belong to the objective printed beside it.

    Regression: inside the KS and LB loops each iteration does `z, g = sol.solve_problem()`,
    so `g` ended up holding the gap of the *last* subproblem while `z` was rescued from the
    incumbent. A bucket that found nothing left `g_ks = 1e+75` next to a perfectly good
    `z_ks`. Both blocks now recompute the gap against the incumbent they report.

    The heuristic legs all measure against `lb_best`, which at that point in the run is the
    LP bound (`lb_best = max(z_lp, lb_best)`; only SM1 raises it afterwards, at line 588).
    `g_milp` is excluded because it is the one gap measured against `lb_milp`.
    """
    proc, row = run_instance("uc_057.json", timelp=30, timeconst=15, timefull=45, KS="True")

    assert proc.returncode == 0, f"main.py failed:\n{proc.stdout[-3000:]}"
    lb_best = float(row[NAMES.index("z_lp")])

    mismatched = []
    for method in ("ks", "lbc1", "lbc2", "lbc3", "lbc4", "hard3", "harjk"):
        z = float(row[NAMES.index("z_" + method)])
        g = float(row[NAMES.index("g_" + method)])
        if z >= 1e75:                 # sin incumbente: el centinela es la respuesta correcta
            assert g >= 1e75, f"{method}: no incumbent (z={z}) but a finite gap {g}"
            continue
        if z == 0:                    # metodo desactivado en esta corrida
            continue
        expected = abs(lb_best - z) / (1e-10 + abs(z))
        if abs(g - expected) > 1e-6:
            mismatched.append(
                f"{method}: z={z} lb_best={lb_best} -> expected g={expected:.8f}, got {g}"
            )

    assert not mismatched, "gap/objective mismatch in stat.csv:\n  " + "\n  ".join(mismatched)
