"""Exercise 7.5 in FreeCAD 1.1: clashes with the MEP model, resolved with openings.

  3D/BIM > Generic 3D Tools > External Reference: datasets/mep_model.ifc (kept outside the building)
  Python console: list the clashes (FreeCAD 1.1 has no clash tool; Shape.common does the test)
  3D/BIM > Generic 3D Tools > Box for each opening, sized from the duct + 25 mm clearance
  select the box, then the beam or wall, Modify > Remove Component   (exported as IfcOpeningElement)
  File > Export > structure.ifc
"""
import os

import FreeCAD
import Arch

from fc_common import V, spec, mm, DATASETS, export_ifc
import s7_2_options

CLEAR = 25.0 + 5.0          # 25 mm clearance asked by the brief, plus 5 mm so the check is not on the edge


def find_clashes(ref, elements, grow=0.0):
    """Console check: every duct solid of the reference against every element (volume in litres)."""
    out = []
    for i, duct in enumerate(ref.Shape.Solids):
        probe = duct
        if grow:
            bb = duct.BoundBox
            import Part
            probe = Part.makeBox(bb.XLength + 2 * grow, bb.YLength + 2 * grow, bb.ZLength + 2 * grow,
                                 V(bb.XMin - grow, bb.YMin - grow, bb.ZMin - grow))
        for e in elements:
            v = probe.common(e.Shape).Volume
            if v > 1.0:                       # mm3
                out.append((i, e, v / 1e6))
    return out


def build():
    m = s7_2_options.concrete_frame()
    doc = m["doc"]
    ref = Arch.makeReference(os.path.join(DATASETS, "mep_model.ifc"), name="MEP model")
    doc.recompute()
    elements = list(m["beams"].values()) + list(m["walls"].values()) + list(m["columns"].values()) + [m["slab"]]
    hard = find_clashes(ref, elements)
    print("clashes before:", [(f"duct {i}", e.Label, round(v, 1)) for i, e, v in hard])
    for i, host, _ in hard:
        d = ref.Shape.Solids[i].BoundBox
        hb = host.Shape.BoundBox
        box = doc.addObject("Part::Box", "Box")
        if d.XLength > d.YLength:           # duct along X: the opening goes through the host in X
            x0, x1 = hb.XMin - 50, hb.XMax + 50
            y0, y1 = d.YMin - CLEAR, d.YMax + CLEAR
        else:                               # duct along Y
            x0, x1 = d.XMin - CLEAR, d.XMax + CLEAR
            y0, y1 = hb.YMin - 50, hb.YMax + 50
        box.Length, box.Width, box.Height = x1 - x0, y1 - y0, d.ZLength + 2 * CLEAR
        box.Placement.Base = V(x0, y0, d.ZMin - CLEAR)
        box.Label = f"Opening {host.Label}"
        doc.recompute()
        Arch.removeComponents([box], host)
    doc.recompute()
    print("clashes after:", len(find_clashes(ref, elements)), "within 25 mm:", len(find_clashes(ref, elements, 25.0)))
    return m


if __name__ == "__main__":
    m = build()
    export_ifc([m["project"]], "structure.ifc")
