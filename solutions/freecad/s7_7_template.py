"""Exercise 7.7 in FreeCAD 1.1: a project library (template) with types and materials only.

  File > Open tb01.ifc (the native file of section 4), File > Save IFC File As... template.ifc
  select every placed element in the tree (columns, beams, walls, slab, stair, footings, pile cap,
  piles, bars) and press Delete; the types (Types group), materials and levels stay
  File > Save IFC File
"""
from fc_common import out
from s4_types import open_native, save_native

ELEMENTS = ("IfcColumn", "IfcBeam", "IfcWall", "IfcSlab", "IfcStair", "IfcStairFlight", "IfcFooting",
            "IfcPile", "IfcReinforcingBar", "IfcOpeningElement", "IfcBuildingElementProxy")


def build(source=None):
    doc = open_native(source or out("tb01_s4.ifc"), copy_to=out("template_work.ifc"))
    for o in [o for o in doc.Objects if getattr(o, "IfcClass", "") in ELEMENTS]:
        if o.Name in [x.Name for x in doc.Objects]:
            doc.removeObject(o.Name)        # Delete key: FreeCAD removes the element from the IFC file
    doc.recompute()
    return doc


if __name__ == "__main__":
    save_native(build(), "template.ifc")
