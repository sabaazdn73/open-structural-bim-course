"""Build the course datasets (the files learners start from) and the reference answers used by the tests.

Usage:  python tools/build_datasets.py
Writes: datasets/*.ifc, datasets/column_types.csv, solutions/reference/*.ifc
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "solutions", "bonsai_path"))
sys.path.insert(0, os.path.join(ROOT, "checker"))

import ifcopenshell.api as api  # noqa: E402
from tb01 import TB01, build, run  # noqa: E402
from bimcheck import spec  # noqa: E402

DATA = os.path.join(ROOT, "datasets")
REF = os.path.join(ROOT, "solutions", "reference")


def architect_model():
    m = TB01(name="TB-01 Architecture")
    m.add_storeys()
    m.add_grid()
    c = spec.CORE
    for i, (name, (x0, y0, x1, y1)) in enumerate(spec.core_walls().items(), 1):
        w = m.box("IfcWall", f"A-Core-{i}", "Level 0", x0, y0, c["z0"], x1, y1, c["z1"], predefined="SOLIDWALL")
        ps = run("pset.add_pset", m.f, product=w, name="Pset_WallCommon")
        run("pset.edit_pset", m.f, pset=ps, properties={"LoadBearing": True, "IsExternal": False})
    for i, (x0, y0, x1, y1) in enumerate([(1.0, 3.45, 5.0, 3.55), (14.5, 8.95, 17.5, 9.05)], 1):
        w = m.box("IfcWall", f"A-Partition-{i}", "Level 0", x0, y0, 0.0, x1, y1, spec.SLAB_SOFFIT, predefined="PARTITIONING")
        ps = run("pset.add_pset", m.f, product=w, name="Pset_WallCommon")
        run("pset.edit_pset", m.f, pset=ps, properties={"LoadBearing": False, "IsExternal": False})
    return m


MEP_DUCTS = {  # name: box x0 y0 z0 x1 y1 z1 (300 x 150 rectangular ducts)
    "D-1 Supply": (2.85, -1.0, 3.10, 3.15, 15.0, 3.25),
    "D-2 Extract": (6.5, 10.35, 2.60, 11.5, 10.65, 2.75),
}


def mep_model():
    m = TB01(name="TB-01 MEP")
    m.add_storeys()
    for name, (x0, y0, z0, x1, y1, z1) in MEP_DUCTS.items():
        m.box("IfcDuctSegment", name, "Level 0", x0, y0, z0, x1, y1, z1, predefined="RIGIDSEGMENT")
    return m


def renovation_model(with_answer=False):
    m = TB01(name="TB-01 Renovation (existing frame)")
    m.add_storeys()
    h = spec.COLUMN["size"] / 2
    pts = {"E-A1": (0, 0), "E-B1": (6, 0), "E-A2": (0, 7), "E-B2": (6, 7)}
    els = {}
    for name, (x, y) in pts.items():
        els[name] = m.box("IfcColumn", name, "Level 0", x - h, y - h, 0, x + h, y + h, spec.SLAB_SOFFIT)
    b = spec.BEAM
    els["E-2/AB"] = m.beam("E-2/AB", 0.2, 6.85, 5.8, 7.15, b["z0"], b["z1"])
    els["E-A/12"] = m.beam("E-A/12", -0.15, 0.2, 0.15, 6.8, b["z0"], b["z1"])
    els["E-B/12"] = m.beam("E-B/12", 5.85, 0.2, 6.15, 6.8, b["z0"], b["z1"])
    els["D-1/AB"] = m.beam("D-1/AB", 0.2, -0.15, 5.8, 0.15, b["z0"], b["z1"])
    els["E-S1"] = m.box("IfcSlab", "E-S1", "Level 1", -0.2, -0.2, spec.SLAB_SOFFIT, 6.2, 7.2, spec.SLAB_TOP)
    for e in els.values():
        m.concrete(e, "C25/30", "XC1")
    if with_answer:
        n = m.beam("N-B1", 0.2, -0.15, 5.8, 0.15, 2.75, spec.SLAB_SOFFIT)
        m.concrete(n, "C30/37", "XC1")
        els["N-B1"] = n
        for name, e in els.items():
            status = {"E": "EXISTING", "D": "DEMOLISH", "N": "NEW"}[name[0]]
            ps = run("pset.add_pset", m.f, product=e, name=f"Pset_{e.is_a()[3:]}Common")
            run("pset.edit_pset", m.f, pset=ps, properties={"Status": status})
    return m


def frame_with_data():
    """Sections 2 + materials: the base for several section 7 files."""
    m = build("s2")
    for e in m.columns.values():
        m.concrete(e, "C30/37", "XC1")
    for e in m.beams.values():
        m.concrete(e, "C30/37", "XC1")
    for e in m.walls.values():
        m.concrete(e, "C30/37", "XC1")
    m.concrete(m.slab, "C30/37", "XC1")
    return m


def unhealthy_model():
    m = frame_with_data()
    x, y = spec.column_marks()["C-B2"]
    h = spec.COLUMN["size"] / 2
    dup = m.box("IfcColumn", "C-B2", "Level 0", x - h, y - h, 0, x + h, y + h, spec.SLAB_SOFFIT)
    m.concrete(dup, "C30/37", "XC1")
    loose = m.beams["B-2/CD"]
    run("spatial.unassign_container", m.f, products=[loose])
    run("material.unassign_material", m.f, products=[m.slab])
    m.walls["W-Core-E"].Name = ""
    return m


def structure_with_openings():
    m = frame_with_data()
    pad = 0.025 + 0.005
    hosts = {"D-1 Supply": ["B-1/AB", "B-2/AB", "B-3/AB"], "D-2 Extract": ["W-Core-W", "W-Core-E"]}
    for duct, names in hosts.items():
        x0, y0, z0, x1, y1, z1 = MEP_DUCTS[duct]
        for n in names:
            host = m.beams.get(n) or m.walls.get(n)
            if n.startswith("B-"):
                yy = [v for v in spec.beams()[n][1::2]]
                m.opening(host, x0 - pad, yy[0] - 0.05, z0 - pad, x1 + pad, yy[1] + 0.05, z1 + pad, name=f"Opening {duct}")
            else:
                wx = spec.core_walls()[n]
                m.opening(host, wx[0] - 0.05, y0 - pad, z0 - pad, wx[2] + 0.05, y1 + pad, z1 + pad, name=f"Opening {duct}")
    return m


def bloated_model(purged=False):
    m = build("s4")
    if purged:
        return m
    run("root.create_entity", m.f, ifc_class="IfcColumnType", name="Old Column 250x250")
    run("root.create_entity", m.f, ifc_class="IfcBeamType", name="Temp Beam")
    m.material("Concrete C20/25 (old)", "concrete")
    m.material("Steel S235", "steel")
    m.f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName="Unused 200x200", XDim=0.2, YDim=0.2)
    run("group.add_group", m.f, name="Temp selection")
    return m


def template():
    m = TB01(name="TB-01 Structural Template")
    m.add_storeys()
    for cls, name in spec.TYPES.items():
        run("root.create_entity", m.f, ifc_class=cls + "Type", name=name)
    for name, cat in (("Concrete C30/37", "concrete"), ("Concrete C25/30", "concrete"), (spec.REBAR["steel"], "steel")):
        m.material(name, cat)
    return m


def option_b():
    m = frame_with_data()
    return m


def main():
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(REF, exist_ok=True)
    shutil.copy(os.path.join(ROOT, "checker", "bimcheck", "data", "column_types.csv"), DATA)
    architect_model().write(os.path.join(DATA, "architect_model.ifc"))
    mep_model().write(os.path.join(DATA, "mep_model.ifc"))
    renovation_model().write(os.path.join(DATA, "renovation_model.ifc"))
    unhealthy_model().write(os.path.join(DATA, "unhealthy_model.ifc"))
    bloated_model().write(os.path.join(DATA, "bloated_model.ifc"))
    for st in ("s1", "s2", "s3", "s4", "full"):
        build(st).write(os.path.join(REF, f"tb01_{st}.ifc"))
    renovation_model(with_answer=True).write(os.path.join(REF, "renovation_answer.ifc"))
    frame_with_data().write(os.path.join(REF, "fixed_model.ifc"))
    structure_with_openings().write(os.path.join(REF, "structure_with_openings.ifc"))
    bloated_model(purged=True).write(os.path.join(REF, "purged_model.ifc"))
    template().write(os.path.join(REF, "template.ifc"))
    frame_with_data().write(os.path.join(REF, "option_A.ifc"))
    b = spec.BEAM
    x0, y0, x1, y1 = spec.beams()["B-2/BC"]
    ob = build("s2")
    # rebuild option B with one beam changed
    from tb01 import TB01 as _T  # noqa: F401
    m = TB01()
    m.set_location()
    m.add_storeys()
    m.add_grid()
    m.add_columns()
    m.add_core_walls()
    m.add_slab()
    m.add_beams(override={"B-2/BC": (x0, 6.8, x1, 7.2, spec.SLAB_SOFFIT - 0.5, spec.SLAB_SOFFIT)})
    for e in list(m.columns.values()) + list(m.beams.values()) + list(m.walls.values()) + [m.slab]:
        m.concrete(e, "C30/37", "XC1")
    m.write(os.path.join(REF, "option_B.ifc"))
    print("datasets:", sorted(os.listdir(DATA)))
    print("reference:", sorted(os.listdir(REF)))


if __name__ == "__main__":
    main()
