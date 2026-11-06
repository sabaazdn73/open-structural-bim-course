"""Section 3 in FreeCAD 1.1: stair, footings, piles, reinforcement, materials, groups (exercises 3.1 to 3.6).

GUI command -> call made here:
  3D/BIM > Stairs ............................ Arch.makeStairs(length, width, height, steps)
  3D/BIM > Column (as a footing) ............. Arch.makeStructure(...), IfcType "Footing", PredefinedType
  2D Drafting > Circle + 3D/BIM > Column ..... Arch.makeStructure(circle, height), IfcType "Pile"
  2D Drafting > Wire / Rectangle + 3D/BIM > Custom Rebar
                                               Arch.makeRebar(host, wire), then Diameter, Amount,
                                               Direction, Distance, OffsetStart, OffsetEnd, Rounding
  Manage > Material .......................... Arch.makeMaterial(name), obj.Material = material
  Manage > Manage IFC Properties ............. IfcProperties: Pset_ConcreteElementGeneral, Pset_StairCommon
  right-click a level > Add group ............ App::DocumentObjectGroup inside the level
  Edit > Preferences > Import-Export > IFC Export: 'Export FreeCAD Groups' on,
                                               'Export nested groups as assemblies' off
"""
import FreeCAD
import Arch
import Draft

from fc_common import V, spec, mm, export_ifc, set_ifc_property
import s2_structure


def add_stair(m):
    st = spec.STAIR
    n = st["risers"]
    stair = Arch.makeStairs(length=mm((n - 1) * st["going"]), width=mm(st["x1"] - st["x0"]),
                            height=mm(st["z1"] - st["z0"]), steps=n)
    # the flight is drawn along +X with its width to the right (Align = Left): turn it 90 degrees
    stair.Placement = FreeCAD.Placement(V(mm(st["x0"]), mm(st["y0"]), mm(st["z0"])),
                                        FreeCAD.Rotation(V(0, 0, 1), 90))
    stair.Label = "ST-1"
    set_ifc_property(stair, "Pset_StairCommon", "NumberOfRiser", "IfcCountMeasure", str(n))
    set_ifc_property(stair, "Pset_StairCommon", "NumberOfTreads", "IfcCountMeasure", str(n - 1))
    m["levels"]["Level 0"].addObject(stair)
    m["stair"] = stair


def add_footings(m):
    f = spec.FOOTING
    m["footings"] = {}
    for mark, (x, y) in spec.column_marks().items():
        ft = Arch.makeStructure(length=mm(f["size"]), width=mm(f["size"]), height=mm(f["t"]))
        ft.IfcType = "Footing"
        ft.PredefinedType = "PAD_FOOTING"
        ft.Placement.Base = V(mm(x), mm(y), mm(f["z0"]))
        ft.Label = mark.replace("C-", "F-")
        m["levels"]["Foundation"].addObject(ft)
        m["footings"][ft.Label] = ft


def add_piles(m):
    c, p = spec.PILE_CAP, spec.PILES
    cap = Arch.makeStructure(length=mm(c["size"]), width=mm(c["size"]), height=mm(c["t"]))
    cap.IfcType = "Footing"
    cap.PredefinedType = "PILE_CAP"
    cap.Placement.Base = V(mm(c["cx"]), mm(c["cy"]), mm(c["z0"]))
    cap.Label = "PC-1"
    m["levels"]["Foundation"].addObject(cap)
    m["pile_cap"] = cap
    m["piles"] = []
    doc = m["doc"]
    for i, (x, y) in enumerate(spec.pile_centres(), 1):
        # Part > Primitives > Cylinder, then select it and 3D/BIM > Column. (A structure extruded from
        # a Draft circle cannot be exported as IfcPile in FreeCAD 1.1.3: the exporter stops with
        # "Cannot create polygon because less than two vertices are given".)
        cyl = doc.addObject("Part::Cylinder", "Cylinder")
        cyl.Radius, cyl.Height = mm(p["d"] / 2), mm(p["length"])
        cyl.Placement.Base = V(mm(x), mm(y), mm(c["z0"] - p["length"]))
        doc.recompute()
        pile = Arch.makeStructure(cyl)
        pile.IfcType = "Pile"
        pile.PredefinedType = "BORED"
        pile.Label = f"P-{i}"
        m["levels"]["Foundation"].addObject(pile)
        m["piles"].append(pile)


def custom_rebar(host, wire, diameter, amount, direction, distance, rounding=0.0, label="Rebar", kind="MAIN"):
    """3D/BIM > Custom Rebar with the host and the wire selected, then the property editor."""
    bar = Arch.makeRebar(host, wire, diameter=diameter, amount=amount, offset=0)
    bar.Direction = direction
    bar.Distance = distance
    bar.OffsetStart = 0
    bar.OffsetEnd = 0
    bar.Rounding = rounding
    bar.Label = label
    bar.PredefinedType = kind                                   # IFC Attributes; the default is ANCHORING
    return bar


def add_rebar(m):
    doc, R = m["doc"], spec.REBAR
    rc, rf = R["column"], R["footing"]
    col, ft = m["columns"]["C-A1"], m["footings"]["F-A1"]
    x, y = (mm(v) for v in spec.column_marks()["C-A1"])
    h = mm(spec.COLUMN["size"] / 2)
    top = mm(spec.COLUMN["z1"])
    off = h - mm(rc["cover"] + rc["link_d"] + rc["long_d"] / 2)     # bar centre to column centre
    bars = []
    # vertical bars: three Custom Rebars spread along X (3 on each Y face, 2 at mid-sides)
    for label, yy, n in (("C-A1 vertical south", y - off, 3), ("C-A1 vertical north", y + off, 3),
                         ("C-A1 vertical mid", y, 2)):
        wire = Draft.make_wire([V(x - off, yy, 0), V(x - off, yy, top)])
        bars.append(custom_rebar(col, wire, mm(rc["long_d"]), n, V(1, 0, 0), 2 * off, label=label))
    # links: a closed rectangle (Make Face off) on the link centre line, repeated upwards
    lo = h - mm(rc["cover"] + rc["link_d"] / 2)
    n_links = int((spec.COLUMN["z1"] - 0.10) / rc["link_s"]) + 1
    rect = Draft.make_rectangle(2 * lo, 2 * lo, placement=FreeCAD.Placement(V(x - lo, y - lo, 50),
                                                                            FreeCAD.Rotation()), face=False)
    bars.append(custom_rebar(col, rect, mm(rc["link_d"]), n_links, V(0, 0, 1),
                             (n_links - 1) * mm(rc["link_s"]), rounding=2, label="C-A1 links",
                             kind="LIGATURE"))
    # footing F-A1: bottom mesh, one Custom Rebar each way
    f = spec.FOOTING
    hf = mm(f["size"] / 2)
    n = int((f["size"] - 2 * rf["cover"] - rf["d"]) / rf["s"]) + 1
    first = -hf + mm(rf["cover"] + rf["d"] / 2)
    z1 = mm(f["z0"] + rf["cover"] + rf["d"] / 2)
    z2 = z1 + mm(rf["d"])
    cv = mm(rf["cover"])
    wx = Draft.make_wire([V(x - hf + cv, y + first, z1), V(x + hf - cv, y + first, z1)])
    bars.append(custom_rebar(ft, wx, mm(rf["d"]), n, V(0, 1, 0), (n - 1) * mm(rf["s"]), label="F-A1 bottom X"))
    wy = Draft.make_wire([V(x + first, y - hf + cv, z2), V(x + first, y + hf - cv, z2)])
    bars.append(custom_rebar(ft, wy, mm(rf["d"]), n, V(1, 0, 0), (n - 1) * mm(rf["s"]), label="F-A1 bottom Y"))
    doc.recompute()
    for b in bars[:4]:
        m["levels"]["Level 0"].addObject(b)
    for b in bars[4:]:
        m["levels"]["Foundation"].addObject(b)
    m["rebars"] = bars


def add_materials(m):
    mats = {}

    def mat(name):
        if name not in mats:
            mats[name] = Arch.makeMaterial(name=name)
        return mats[name]

    def concrete(obj, data):
        obj.Material = mat(f"Concrete {data['concrete']}")
        set_ifc_property(obj, "Pset_ConcreteElementGeneral", "StrengthClass", "IfcLabel", data["concrete"])
        set_ifc_property(obj, "Pset_ConcreteElementGeneral", "ExposureClass", "IfcLabel", data["exposure"])

    for e in m["columns"].values():
        concrete(e, spec.COLUMN)
    for e in m["beams"].values():
        concrete(e, spec.BEAM)
    for e in m["walls"].values():
        concrete(e, spec.CORE)
    concrete(m["slab"], spec.SLAB)
    concrete(m["stair"], spec.SLAB)
    for e in list(m["footings"].values()) + [m["pile_cap"]]:
        concrete(e, spec.FOOTING)
    for e in m["piles"]:
        concrete(e, spec.PILES)
    for b in m.get("rebars", []):
        b.Material = mat(spec.REBAR["steel"])
    m["materials"] = mats


def add_groups(m):
    doc = m["doc"]
    for (name, cls), level, members in (
            (("Ground Floor Columns", "IfcColumn"), "Level 0", m["columns"].values()),
            (("Level 1 Beams", "IfcBeam"), "Level 1", m["beams"].values())):
        g = doc.addObject("App::DocumentObjectGroup", "Group")
        g.Label = name
        m["levels"][level].addObject(g)
        for e in members:
            g.addObject(e)                      # drag the elements into the group in the tree


def build():
    m = s2_structure.build()
    add_stair(m)
    add_footings(m)
    add_piles(m)
    add_rebar(m)
    add_materials(m)
    add_groups(m)
    m["doc"].recompute()
    return m


if __name__ == "__main__":
    m = build()
    export_ifc([m["project"]], "tb01_s3.ifc", groups=True)
