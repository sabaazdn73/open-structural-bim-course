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


# ---- checker changes for FreeCAD output: each relaxation still fails a wrong model -------------------

def test_storey_without_elevation_or_placement(tmp_path):
    """FreeCAD writes a level at +0.000 with neither Elevation nor ObjectPlacement: read as 0.0."""
    import ifcopenshell
    f = ifcopenshell.open(ref("tb01_s1.ifc"))
    for st in f.by_type("IfcBuildingStorey"):
        if st.Name == "Level 0":
            st.Elevation, st.ObjectPlacement = None, None
    good = tmp_path / "level0_bare.ifc"
    f.write(str(good))
    assert run("1.2", str(good)).passed
    for st in f.by_type("IfcBuildingStorey"):
        if st.Name == "Level 1":
            st.Elevation, st.ObjectPlacement = None, None
    bad = tmp_path / "level1_bare.ifc"
    f.write(str(bad))
    assert not run("1.2", str(bad)).passed


def test_stair_ending_one_riser_below_level(tmp_path):
    """A flight whose top tread is one riser below Level 1 passes only if it stores the full riser count."""
    import ifcopenshell
    import ifcopenshell.api
    f = ifcopenshell.open(ref("tb01_s3.ifc"))
    st = f.by_type("IfcStairFlight")[0]
    loc = st.ObjectPlacement.RelativePlacement.Location
    loc.Coordinates = (loc.Coordinates[0], loc.Coordinates[1], loc.Coordinates[2] - 0.18)
    good = tmp_path / "stair_low.ifc"
    f.write(str(good))
    assert run("3.1", str(good)).passed
    for rel in list(st.IsDefinedBy):
        if rel.RelatingPropertyDefinition.Name == "Pset_StairFlightCommon":
            ifcopenshell.api.run("pset.remove_pset", f, product=st, pset=rel.RelatingPropertyDefinition)
    bad = tmp_path / "stair_low_no_count.ifc"
    f.write(str(bad))
    assert not run("3.1", str(bad)).passed


def test_predefined_type_from_the_type_object(tmp_path):
    """An occurrence may leave PredefinedType empty and inherit it from its type."""
    import ifcopenshell
    import ifcopenshell.util.element as ue
    f = ifcopenshell.open(ref("tb01_s4.ifc"))
    pads = [e for e in f.by_type("IfcFooting") if e.Name.startswith("F-")]
    for e in pads:
        e.PredefinedType = None
    ue.get_type(pads[0]).PredefinedType = "PAD_FOOTING"
    good = tmp_path / "pad_from_type.ifc"
    f.write(str(good))
    assert run("3.2", str(good)).passed
    ue.get_type(pads[0]).PredefinedType = "STRIP_FOOTING"
    bad = tmp_path / "strip_from_type.ifc"
    f.write(str(bad))
    assert not run("3.2", str(bad)).passed


def test_svg_with_undeclared_prefix(tmp_path):
    """FreeCAD's 'Flattened SVG' writes freecad:... attributes without declaring the prefix."""
    src = open(os.path.join(FIX, "plan.svg"), encoding="utf-8").read()
    p = tmp_path / "plan_freecad.svg"
    p.write_text(src.replace("<text ", '<text freecad:skip="1" ', 1), encoding="utf-8")
    assert run("5.1", str(p)).passed
    q = tmp_path / "detail_freecad.svg"
    q.write_text(open(os.path.join(FIX, "detail.svg"), encoding="utf-8").read()
                 .replace("<text ", '<text freecad:skip="1" ', 1), encoding="utf-8")
    assert not run("5.1", str(q)).passed


def test_status_as_enumerated_value(tmp_path):
    import ifcopenshell
    f = ifcopenshell.open(ref("renovation_answer.ifc"))
    enum = f.create_entity("IfcPropertyEnumeration", Name="PEnum_ElementStatus",
                           EnumerationValues=[f.createIfcLabel(v) for v in ("NEW", "EXISTING", "DEMOLISH", "TEMPORARY")])
    for p in [p for p in f.by_type("IfcPropertySingleValue") if p.Name == "Status"]:
        val = p.NominalValue.wrappedValue
        new = f.create_entity("IfcPropertyEnumeratedValue", Name="Status", EnumerationValues=[f.createIfcLabel(val)],
                              EnumerationReference=enum)
        for ps in f.get_inverse(p):
            ps.HasProperties = [new if x == p else x for x in ps.HasProperties]
    out = tmp_path / "enum.ifc"
    f.write(str(out))
    assert run("7.1", str(out)).passed


def _frame_with_core(tmp_path, mitred, column_top=None):
    sys.path.insert(0, os.path.join(ROOT, "solutions", "bonsai_path"))
    from tb01 import build, run as api
    from bimcheck import spec
    m = build("s2")
    if column_top:
        for c in m.columns.values():
            c.Representation.Representations[0].Items[0].Depth = column_top
    if mitred:
        c, t = spec.CORE, spec.CORE["t"]
        for w in m.walls.values():
            api("root.remove_product", m.f, product=w)
        x0, y0, x1, y1 = c["x0"], c["y0"], c["x1"], c["y1"]
        outer = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        inner = [(x0 + t, y0 + t), (x1 - t, y0 + t), (x1 - t, y1 - t), (x0 + t, y1 - t)]
        for i in range(4):
            j = (i + 1) % 4
            pts = [outer[i], outer[j], inner[j], inner[i]]
            w = api("root.create_entity", m.f, ifc_class="IfcWall", name=f"W-Mitre-{i}")
            prof = m.f.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=m.f.create_entity(
                "IfcPolyline", Points=[m.f.createIfcCartesianPoint(p) for p in pts + [pts[0]]]))
            rep = api("geometry.add_profile_representation", m.f, context=m.body, profile=prof, depth=c["z1"],
                      cardinal_point=None)
            api("geometry.assign_representation", m.f, product=w, representation=rep)
            api("geometry.edit_object_placement", m.f, product=w)
            api("spatial.assign_container", m.f, relating_structure=m.storeys["Level 0"], products=[w])
    out = tmp_path / "frame.ifc"
    m.f.write(str(out))
    return str(out)


def test_mitred_core_corners_are_not_overlaps(tmp_path):
    res = run("2.5", _frame_with_core(tmp_path, mitred=True))
    assert res.items[0].ok, res.items[0].hint


def test_column_into_slab_is_an_overlap(tmp_path):
    assert not run("2.5", _frame_with_core(tmp_path, mitred=False, column_top=3.6)).items[0].ok


def test_true_north_wrong_direction_fails(tmp_path):
    import ifcopenshell
    f = ifcopenshell.open(ref("tb01_s1.ifc"))
    for ctx in f.by_type("IfcGeometricRepresentationContext"):
        if not ctx.is_a("IfcGeometricRepresentationSubContext") and ctx.TrueNorth is not None:
            x, y = ctx.TrueNorth.DirectionRatios[:2]
            ctx.TrueNorth = f.createIfcDirection((-x, y))
    out = tmp_path / "north.ifc"
    f.write(str(out))
    res = run("1.1", str(out))
    assert not res.passed and "counter-clockwise" in [i for i in res.items if not i.ok][0].hint
