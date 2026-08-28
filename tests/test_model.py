"""Pins the MILP that uc_Co.uc() emits, byte for byte.

Refactoring a 1216-line model builder is only safe if you can prove the model did not move.
Exporting to LP with symbolic labels and hashing it does exactly that: constraint count,
constraint order, coefficients and variable domains all feed the digest. Anything that
changes the emitted model changes the hash.

The digests are Pyomo-version dependent (captured on Pyomo 6.4.4). If they drift after a
deliberate model change — or a Pyomo upgrade — regenerate them on purpose:

    python3 -c "import tests.regen_lp_digest as r; r.main()"

and say in the commit message which it was.
"""
import hashlib
import json
import tempfile
from pathlib import Path

import pytest

DIGESTS = Path(__file__).parent / "data" / "model_lp_sha256_uc_057.json"


def lp_digest(option):
    import reading
    import uc_Co

    inst = reading.reading("instances/uc_057.json")
    model, _ = uc_Co.uc(inst, option=option, nameins="uc_057", mode="Tight", scope="")
    out = Path(tempfile.mkdtemp()) / "model.lp"
    model.write(str(out), io_options={"symbolic_solver_labels": True})
    return hashlib.sha256(out.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def expected():
    return json.loads(DIGESTS.read_text())


@pytest.mark.parametrize("option", ["Milp", "LR"])
def test_emitted_model_is_unchanged(option, expected):
    assert lp_digest(option) == expected[option], (
        f"the {option} model uc_Co.uc() builds has changed. If that was intentional, "
        f"regenerate tests/data/model_lp_sha256_uc_057.json and re-run the experiments; "
        f"if not, the last edit to uc_Co.py moved the model."
    )


def test_export_is_deterministic():
    """Guards the pinning method itself: a non-reproducible export would make it useless."""
    assert lp_digest("Milp") == lp_digest("Milp")
