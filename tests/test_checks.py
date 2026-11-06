"""Every check must pass on the reference answer and fail on a wrong or unfinished file.

Run:  python tools/build_datasets.py && python tools/build_brief.py && python -m pytest -q
"""
import csv
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "checker"))
from bimcheck.exercises import REGISTRY  # noqa: E402
from bimcheck.core import Model  # noqa: E402

REF = os.path.join(ROOT, "solutions", "reference")
DATA = os.path.join(ROOT, "datasets")
FIX = os.path.join(ROOT, "tests", "fixtures")


def ref(name):
    return os.path.join(REF, name)


def run(eid, *files):
    return REGISTRY[eid]["fn"](*files)


POSITIVE = {
    "1.1": [ref("tb01_s1.ifc")], "1.2": [ref("tb01_s1.ifc")], "1.3": [ref("tb01_s1.ifc")],
    "2.1": [ref("tb01_s2.ifc")], "2.2": [ref("tb01_s2.ifc"), os.path.join(DATA, "architect_model.ifc")],
    "2.3": [ref("tb01_s2.ifc")], "2.4": [ref("tb01_s2.ifc")], "2.5": [ref("tb01_s2.ifc")],
    "3.1": [ref("tb01_s3.ifc")], "3.2": [ref("tb01_s3.ifc")], "3.3": [ref("tb01_s3.ifc")],
    "3.4": [ref("tb01_s3.ifc")], "3.5": [ref("tb01_s3.ifc")], "3.6": [ref("tb01_s3.ifc")],
    "4.1": [ref("tb01_s4.ifc")], "4.2": [ref("tb01_s4.ifc")], "4.3": [ref("tb01_s4.ifc")],
    "5.1": [os.path.join(FIX, "plan.svg")], "5.2": [os.path.join(FIX, "section.svg")],
    "5.3": [os.path.join(FIX, "detail.svg")], "5.5": [ref("tb01_s2.ifc"), os.path.join(FIX, "plan.svg")],
    "6.1": [os.path.join(FIX, "sheet.svg")], "6.2": [os.path.join(FIX, "sheet.svg")],
    "7.1": [ref("renovation_answer.ifc")], "7.2": [ref("option_A.ifc"), ref("option_B.ifc")],
    "7.4": [ref("fixed_model.ifc")], "7.5": [ref("structure_with_openings.ifc"), os.path.join(DATA, "mep_model.ifc")],
    "7.6": [ref("purged_model.ifc")], "7.7": [ref("template.ifc")], "7.8": [ref("tb01_full.ifc")],
}

NEGATIVE = {
    "1.1": [os.path.join(DATA, "architect_model.ifc")],
    "1.3": [os.path.join(DATA, "mep_model.ifc")],
    "2.1": [ref("tb01_s1.ifc")], "2.2": [ref("tb01_s1.ifc")], "2.3": [ref("tb01_s1.ifc")], "2.4": [ref("tb01_s1.ifc")],
    "2.5": [ref("tb01_s1.ifc")], "3.1": [ref("tb01_s2.ifc")], "3.2": [ref("tb01_s2.ifc")], "3.3": [ref("tb01_s2.ifc")],
    "3.4": [ref("tb01_s2.ifc")], "3.5": [ref("tb01_s2.ifc")], "3.6": [ref("tb01_s2.ifc")],
    "4.1": [ref("tb01_s3.ifc")], "4.2": [ref("tb01_s3.ifc")], "4.3": [ref("tb01_s3.ifc")],
    "5.1": [os.path.join(FIX, "detail.svg")], "5.2": [os.path.join(FIX, "detail.svg")],
    "5.3": [os.path.join(FIX, "plan.svg")], "5.5": [ref("tb01_s2.ifc"), os.path.join(FIX, "detail.svg")],
    "6.1": [os.path.join(FIX, "plan.svg")], "6.2": [os.path.join(FIX, "plan.svg")],
    "7.1": [os.path.join(DATA, "renovation_model.ifc")], "7.2": [ref("option_A.ifc"), ref("option_A.ifc")],
    "7.4": [os.path.join(DATA, "unhealthy_model.ifc")], "7.5": [ref("tb01_s2.ifc"), os.path.join(DATA, "mep_model.ifc")],
    "7.6": [os.path.join(DATA, "bloated_model.ifc")], "7.7": [ref("tb01_s4.ifc")], "7.8": [ref("tb01_s4.ifc")],
}


@pytest.mark.parametrize("eid", sorted(POSITIVE))
def test_reference_passes(eid):
    res = run(eid, *POSITIVE[eid])
    assert res.passed, [(i.text, i.hint) for i in res.items if not i.ok]


@pytest.mark.parametrize("eid", sorted(NEGATIVE))
def test_wrong_file_fails(eid):
    res = run(eid, *NEGATIVE[eid])
    assert not res.passed


def _write_schedule(path, model_path, scale=1.0, drop=None):
    m = Model(model_path)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Element", "Class", "Volume (m3)"])
        for cls in ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting", "IfcPile"):
            if cls == drop:
                continue
            for e in m.elements(cls):
                w.writerow([e.Name, cls[3:], f"{m.volume(e) * scale:.4f}"])


def test_schedule(tmp_path):
    good, bad = tmp_path / "good.csv", tmp_path / "bad.csv"
    _write_schedule(good, ref("tb01_s3.ifc"))
    _write_schedule(bad, ref("tb01_s3.ifc"), drop="IfcBeam")
    assert run("5.4", str(good), ref("tb01_s3.ifc")).passed
    assert not run("5.4", str(bad), ref("tb01_s3.ifc")).passed


def test_git(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
    g("init", "-q")
    g("config", "user.name", "Test Learner")
    g("config", "user.email", "learner@example.com")
    assert not run("7.3", str(repo)).passed
    (repo / "tb01.ifc").write_bytes(open(ref("tb01_s1.ifc"), "rb").read())
    g("add", "tb01.ifc")
    g("commit", "-q", "-m", "Levels and grid for TB-01")
    (repo / "tb01.ifc").write_bytes(open(ref("tb01_s2.ifc"), "rb").read())
    g("commit", "-q", "-am", "Columns, core walls, slab and beams")
    assert run("7.3", str(repo)).passed


def test_levels_wrong_elevation(tmp_path):
    import ifcopenshell
    import ifcopenshell.util.placement as up  # noqa: F401
    f = ifcopenshell.open(ref("tb01_s1.ifc"))
    for st in f.by_type("IfcBuildingStorey"):
        if st.Name == "Level 1":
            st.Elevation = 3.65
            st.ObjectPlacement.RelativePlacement.Location.Coordinates = (0.0, 0.0, 3.65)
    out = tmp_path / "wrong_levels.ifc"
    f.write(str(out))
    assert not run("1.2", str(out)).passed


def test_every_exercise_is_tested():
    tested = set(POSITIVE) | {"5.4", "7.3"}
    assert tested == set(REGISTRY)
