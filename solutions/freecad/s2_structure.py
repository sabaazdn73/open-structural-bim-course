"""Section 2 in FreeCAD 1.1: columns, core walls, slab with openings, beams (exercises 2.1 to 2.5).

GUI command -> call made here:
  3D/BIM > Column ............................ Arch.makeStructure(length, width, height), Placement.Base
  3D/BIM > Generic 3D Tools > External Reference  Arch.makeReference(architect_model.ifc)
  3D/BIM > Wall .............................. Arch.makeWall(line, width, height, align="Center")
  Manage > Manage IFC Properties ............. IfcProperties: Pset_WallCommon.LoadBearing = True
  2D Drafting > Rectangle + 3D/BIM > Slab .... Arch.makeStructure(rectangle, height), IfcType "Slab", Normal -Z
  3D/BIM > Generic 3D Tools > Box ............ Part::Box (the opening volumes)
  Modify > Remove Component .................. Arch.removeComponents(boxes, slab)
  3D/BIM > Beam .............................. Arch.makeStructure(length, width, height) placed along two points
"""
import os

import FreeCAD
import Arch
import ArchStructure
import Draft

from fc_common import V, spec, mm, DATASETS, export_ifc, set_ifc_property
import s1_project


def add_columns(m):
    c = spec.COLUMN
    m["columns"] = {}
    for mark, (x, y) in spec.column_marks().items():
        col = Arch.makeStructure(length=mm(c["size"]), width=mm(c["size"]), height=mm(c["z1"] - c["z0"]))
        col.Placement.Base = V(mm(x), mm(y), mm(c["z0"]))     # the column is centred on its base point
        col.Label = mark
        m["levels"]["Level 0"].addObject(col)
        m["columns"][mark] = col


def architect_load_bearing_walls(path):
    """The boxes of the architect's load-bearing walls, read from the IFC file (what you snap to)."""
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element as ue
    f = ifcopenshell.open(path)
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    boxes = []
    for w in f.by_type("IfcWall"):
        if ue.get_psets(w).get("Pset_WallCommon", {}).get("LoadBearing") is True:
            shape = ifcopenshell.geom.create_shape(s, w)      # keep the shape alive while reading it
            v = list(shape.geometry.verts)
            xs, ys, zs = v[0::3], v[1::3], v[2::3]
            boxes.append((min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))
    return boxes


def add_core_walls(m):
    doc = m["doc"]
    path = os.path.join(DATASETS, "architect_model.ifc")
    ref = Arch.makeReference(path, name="Architect model")     # kept outside the building: not exported
    doc.recompute()
    m["reference"] = ref
    m["walls"] = {}
    for i, (x0, y0, z0, x1, y1, z1) in enumerate(architect_load_bearing_walls(path), 1):
        # trace the centre line of the architect's wall, 250 mm wide, Align = Center
        cx, cy = (spec.CORE["x0"] + spec.CORE["x1"]) / 2, (spec.CORE["y0"] + spec.CORE["y1"]) / 2
        if (x1 - x0) >= (y1 - y0):
            p0, p1 = V(mm(x0), mm((y0 + y1) / 2), 0), V(mm(x1), mm((y0 + y1) / 2), 0)
            side = "S" if (y0 + y1) / 2 < cy else "N"
        else:
            p0, p1 = V(mm((x0 + x1) / 2), mm(y0), 0), V(mm((x0 + x1) / 2), mm(y1), 0)
            side = "W" if (x0 + x1) / 2 < cx else "E"
        line = Draft.make_line(p0, p1)
        wall = Arch.makeWall(line, width=mm(spec.CORE["t"]), height=mm(spec.CORE["z1"] - spec.CORE["z0"]),
                             align="Center")
        wall.Label = f"W-Core-{side}"
        wall.PredefinedType = "SOLIDWALL"                       # the default is MOVABLE
        set_ifc_property(wall, "Pset_WallCommon", "LoadBearing", "IfcBoolean", "True")
        m["levels"]["Level 0"].addObject(wall)
        m["walls"][wall.Label] = wall
    ref.Visibility = False


def add_slab(m):
    doc, s = m["doc"], spec.SLAB
    rect = Draft.make_rectangle(mm(s["x1"] - s["x0"]), mm(s["y1"] - s["y0"]),
                                placement=FreeCAD.Placement(V(mm(s["x0"]), mm(s["y0"]), mm(s["z1"])),
                                                            FreeCAD.Rotation()), face=True)
    slab = Arch.makeStructure(rect, height=mm(spec.SLAB_T))     # what 3D/BIM > Slab does ...
    slab.IfcType = "Slab"
    slab.Normal = V(0, 0, -1)                                    # ... extruded downwards from the top
    slab.Label = "S-L1"
    boxes = []
    for name, (x0, y0, x1, y1) in s["openings"].items():
        b = doc.addObject("Part::Box", "Box")
        b.Label = f"Opening {name}"
        b.Length, b.Width, b.Height = mm(x1 - x0), mm(y1 - y0), mm(spec.SLAB_T) + 200
        b.Placement.Base = V(mm(x0), mm(y0), mm(s["z0"]) - 100)
        boxes.append(b)
    doc.recompute()
    Arch.removeComponents(boxes, slab)                           # Modify > Remove Component
    m["levels"]["Level 1"].addObject(slab)
    m["slab"] = slab


def make_beam(p0, p1, width, depth):
    """3D/BIM > Beam: two points on the beam axis (at mid-depth), Width and Height in the task panel."""
    b = Arch.makeStructure(length=(p1 - p0).Length, width=width, height=depth)
    b.Placement = ArchStructure.placeAlongEdge(p0, p1, True)
    return b


def add_beams(m, override=None):
    bm = spec.BEAM
    m["beams"] = {}
    for mark, (x0, y0, x1, y1) in spec.beams().items():
        z0, z1, w = bm["z0"], bm["z1"], bm["b"]
        if override and mark in override:
            x0, y0, x1, y1, z0, z1 = override[mark]
            w = min(x1 - x0, y1 - y0)
        zc = mm((z0 + z1) / 2)
        if (x1 - x0) >= (y1 - y0):
            p0, p1 = V(mm(x0), mm((y0 + y1) / 2), zc), V(mm(x1), mm((y0 + y1) / 2), zc)
        else:
            p0, p1 = V(mm((x0 + x1) / 2), mm(y0), zc), V(mm((x0 + x1) / 2), mm(y1), zc)
        b = make_beam(p0, p1, mm(w), mm(z1 - z0))
        b.Label = mark
        m["levels"]["Level 1"].addObject(b)
        m["beams"][mark] = b


def build(override=None):
    m = s1_project.build()
    add_columns(m)
    add_core_walls(m)
    add_slab(m)
    add_beams(m, override)
    m["doc"].recompute()
    return m


if __name__ == "__main__":
    m = build()
    export_ifc([m["project"]], "tb01_s2.ifc")
