"""Characterization tests for util.py.

These pin down what the helpers do *today*, so the refactor can be shown not to move them.
Where current behaviour is a bug, the test says so explicitly rather than asserting the
behaviour we wish it had.
"""
import numpy as np
import pytest

import util


class TestIgap:
    """Integrality gap, as reported in stat.csv."""

    def test_zero_when_bounds_meet(self):
        assert util.igap(571490.65504, 571490.65504) == pytest.approx(0.0)

    def test_matches_published_hard3_gap(self):
        # The golden uc_057 row records g_hard3 = 0.00823746. It is computed from the *unrounded*
        # bounds (stat.csv rounds z to 1 decimal only for display), so feed the real ones.
        z_lp, z_hard3 = 566783.0234356394, 571490.65504
        assert round(util.igap(z_lp, z_hard3), 8) == 0.00823746

    def test_is_symmetric_in_magnitude_only(self):
        assert util.igap(10.0, 20.0) == pytest.approx(0.5)
        assert util.igap(20.0, 10.0) == pytest.approx(1.0)

    def test_survives_zero_upper_bound(self):
        # The 1e-10 term in the denominator is what keeps this from dividing by zero.
        assert util.igap(0.0, 0.0) == pytest.approx(0.0)
        assert np.isfinite(util.igap(1.0, 0.0))


class TestGetLetter:
    """Suffix used to label local-branching / kernel-search iterations."""

    def test_single_letters(self):
        assert util.getLetter(0) == "_a"
        assert util.getLetter(25) == "_z"

    def test_rolls_over_to_two_letters(self):
        assert util.getLetter(26) == "_aa"
        assert util.getLetter(27) == "_ab"
        assert util.getLetter(52) == "_ba"

    def test_labels_are_unique_over_the_used_range(self):
        labels = [util.getLetter(i) for i in range(200)]
        assert len(set(labels)) == len(labels)


class TestTrunc:
    def test_truncates_rather_than_rounds(self):
        assert util.trunc(np.array([1.99]), decs=1)[0] == pytest.approx(1.9)

    def test_default_is_one_decimal(self):
        assert util.trunc(np.array([2.349]))[0] == pytest.approx(2.3)


class TestSolutionRoundTrip:
    """saveSolution/loadSolution is the recovery path main.py takes on a re-run."""

    def test_round_trip_preserves_every_field(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Every one of these lists holds (generator, period) index pairs.
        SB, NO_SB, LOWER = [(0, 1), (2, 3), (4, 5)], [(6, 7), (8, 9)], [(1, 1)]
        V, W, DELTA = [(0, 0), (1, 2)], [(3, 4)], [(5, 6), (7, 8), (2, 2)]

        util.saveSolution(0.5, 566783.0, 1.2, 571490.7, SB, NO_SB, LOWER, V, W, DELTA,
                          "Hard3", "uc_057")
        got = util.loadSolution("Hard3", "uc_057")
        t_lp, z_lp, t_, z_, sb, no_sb, lower, v, w, delta = got

        assert (t_lp, z_lp, t_, z_) == (0.5, 566783.0, 1.2, 571490.7)
        assert [tuple(x) for x in sb] == SB
        assert [tuple(x) for x in no_sb] == NO_SB
        assert [tuple(x) for x in lower] == LOWER
        assert [tuple(x) for x in v] == V
        assert [tuple(x) for x in w] == W
        assert [tuple(x) for x in delta] == DELTA

    def test_writes_the_two_files_main_py_probes_for(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pair = [(0, 0)]
        util.saveSolution(0.0, 0.0, 0.0, 0.0, pair, pair, pair, pair, pair, pair, "Hard3", "uc_057")
        assert (tmp_path / "solHard3_a_uc_057.csv").exists()
        assert (tmp_path / "solHard3_b_uc_057.csv").exists()


class TestDeleteTabu:
    """delete_tabu drops cuts whose 4th field is 0."""

    def test_removes_a_single_flagged_cut(self):
        cuts = [["a", "b", "c", 1], ["a", "b", "c", 0], ["a", "b", "c", 2]]
        assert util.delete_tabu(cuts) == [["a", "b", "c", 1], ["a", "b", "c", 2]]

    def test_removes_adjacent_flagged_cuts(self):
        """Regression: the old pop-while-iterating left one of two adjacent tabu cuts alive."""
        cuts = [["a", "b", "c", 0], ["a", "b", "c", 0], ["a", "b", "c", 1]]
        assert util.delete_tabu(cuts) == [["a", "b", "c", 1]]

    def test_removes_every_flagged_cut(self):
        assert util.delete_tabu([["a", "b", "c", 0]] * 5) == []

    def test_keeps_order_of_survivors(self):
        cuts = [["a", "b", "c", 1], ["a", "b", "c", 0], ["a", "b", "c", 0], ["a", "b", "c", 2]]
        assert [c[3] for c in util.delete_tabu(cuts)] == [1, 2]

    def test_does_not_mutate_the_caller_list(self):
        cuts = [["a", "b", "c", 0], ["a", "b", "c", 1]]
        util.delete_tabu(cuts)
        assert len(cuts) == 2


class TestConfigEnv:
    def test_reads_the_repo_config(self):
        values = util.config_env("config.con")
        assert len(values) == 31, "main.py unpacks exactly 31 values from config_env()"
        assert values[0] == "yalma"
        assert values[1] == "instances/"


class TestReadingInstances:
    """reading.reading() is the single entry point for instance data."""

    def test_uc_057_shape(self):
        import reading
        inst = reading.reading("instances/uc_057.json")
        assert len(inst[0]) == 8, "8 generators"
        assert len(inst[1]) == 24, "24 periods"

    def test_uc_059_loads(self):
        """Regression: uc_059 declares 121 demands for 120 periods and used to raise
        IndexError on the reserves list, making a README-documented instance unusable."""
        import reading
        inst = reading.reading("instances/uc_059.json")
        assert len(inst[0]) == 8
        assert len(inst[1]) == 120

    def test_demand_series_are_truncated_to_the_horizon(self):
        import reading
        inst = reading.reading("instances/uc_059.json")
        periods, De = inst[1], inst[8]
        assert len(De) == len(periods) == 120

    def test_parsing_does_not_mutate_the_json(self):
        """The old code aliased md['demand'] and appended to it while iterating."""
        import json, reading
        raw = json.load(open("instances/uc_057.json"))
        before = len(raw["demand"])
        reading.reading("instances/uc_057.json")
        assert len(json.load(open("instances/uc_057.json"))["demand"]) == before


class TestInstanceCatalogue:
    """Guards against broken instance files reaching the batch runs."""

    def test_no_instance_file_is_empty(self):
        """uc_011.json was committed as 0 bytes and crashed reading() with a JSON error."""
        from pathlib import Path
        empty = [p.name for p in sorted(Path("instances").glob("*.json")) if p.stat().st_size == 0]
        assert not empty, f"empty instance files: {empty}"

    def test_every_instance_is_valid_json(self):
        import json
        from pathlib import Path
        broken = []
        for p in sorted(Path("instances").glob("*.json")):
            try:
                json.loads(p.read_text())
            except Exception as err:
                broken.append(f"{p.name}: {type(err).__name__}")
        assert not broken, f"malformed instances: {broken}"

    def test_demand_and_reserves_cover_the_horizon(self):
        """uc_059 declares 121 demands for 120 periods; reading() must not walk off reserves."""
        import json
        from pathlib import Path
        short = []
        for p in sorted(Path("instances").glob("*.json")):
            md = json.loads(p.read_text())
            t = int(md["time_periods"])
            if len(md["demand"]) < t or len(md["reserves"]) < t:
                short.append(f"{p.name}: T={t} demand={len(md['demand'])} reserves={len(md['reserves'])}")
        assert not short, f"series shorter than the horizon: {short}"


class TestInstanceContract:
    """uc_Co.uc() indexes the reading() result positionally, so its width is load-bearing."""

    def test_instance_is_a_47_element_positional_list(self):
        import reading
        inst = reading.reading("instances/uc_057.json")
        assert len(inst) == 47, (
            "uc_Co.uc() reads instance[0]..instance[46]; changing this width silently "
            "breaks the model. The index map is documented in reading.reading's docstring."
        )

    def test_docstring_documents_every_index(self):
        import re, reading
        documented = {int(n) for n in re.findall(r"^\s*\[\s*(\d+)\]", reading.reading.__doc__, re.M)}
        assert documented == set(range(47)), f"undocumented indices: {sorted(set(range(47)) - documented)}"


class TestModelConstraints:
    """Guards against constraints silently vanishing from the MILP."""

    def test_registered_constraints_are_stable(self):
        """uc_Co.uc() must keep emitting the same constraint components.

        eq.(54)-(56) are the full start-up cost chain. (56) was unregistered until 2026-08-25
        (its registration sat inside the rule, after the return), so published objectives
        excluded start-up costs; it is now required to be present.
        """
        import reading, uc_Co
        from pyomo.environ import Constraint

        inst = reading.reading("instances/uc_057.json")
        model, _ = uc_Co.uc(inst, option="Milp", nameins="uc_057", mode="Tight")
        names = {c.name for c in model.component_objects(Constraint)}

        assert "Start_up_cost54" in names
        assert "Start_up_cost55" in names
        assert "Start_up_cost56" in names, (
            "eq.(56) vanished again — start-up costs would silently drop out of the objective"
        )

    def test_startcost4_fixes_initial_delta_for_cold_units(self):
        """(Startcost4): a unit offline TD_0 hours before the horizon cannot claim a hotter
        start-up type than TD_0 allows. Vacuous on the shipped dataset (every unit starts
        online, TD_0=0) but load-bearing for any extension with cold initial conditions."""
        import copy, json, reading, uc_Co
        from pathlib import Path

        md = json.loads(Path("instances/uc_057.json").read_text())
        gen = list(md["thermal_generators"])[2]
        md["thermal_generators"][gen].update(unit_on_t0=0, time_down_t0=4, power_output_t0=0)
        tmp = Path("instances") / ".uc_057_cold_tmp.json"
        try:
            tmp.write_text(json.dumps(md))
            inst = reading.reading(str(tmp))
            model, _ = uc_Co.uc(inst, option="Milp", nameins="syn", mode="Tight")
            fixed = [i for i in model.delta if model.delta[i].fixed]
            assert fixed, "no delta was fixed for a unit with TD_0=4"
            assert all(model.delta[i].value == 0 for i in fixed)
        finally:
            tmp.unlink(missing_ok=True)
