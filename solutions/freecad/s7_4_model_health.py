"""Exercise 7.4 in FreeCAD 1.1: find and fix the four problems of datasets/unhealthy_model.ifc.

  File > Open unhealthy_model.ifc (native IFC; tick 'Preload materials' in the import dialog)
  Python console: a short health check (BIM > Manage > Preflight Checks reads only classic
                  FreeCAD objects, not native IFC ones)
  Fix:  select the duplicate column and press Delete
        drag the loose beam onto Level 1 in the tree
        Manage > Material: give the slab Concrete C30/37
        rename the wall without a name (F2 in the tree) to W-Core-E
  File > Save IFC File As... fixed_model.ifc
"""
import os

import FreeCAD

from fc_common import DATASETS, out
from s4_types import open_native, save_native, ifcfile

STRUCTURAL = ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting", "IfcPile", "IfcStair", "IfcStairFlight")


def health_check(doc):
    """The console check given in the lesson: prints every problem it finds."""
    import ifcopenshell.util.element as ue
    import ifcopenshell.util.placement as up
    f = ifcfile(doc)
    seen, problems = {}, []
    for e in [e for c in STRUCTURAL for e in f.by_type(c)]:
        key = (e.is_a(), tuple(round(v, 3) for v in up.get_local_placement(e.ObjectPlacement)[:3, 3]))
        if key in seen:
            problems.append(f"duplicate: {e.Name} #{e.id()} = #{seen[key].id()}")
        seen[key] = e
        if not ue.get_container(e):
            problems.append(f"no level: {e.Name} #{e.id()}")
        if not ue.get_material(e):
            problems.append(f"no material: {e.Name} #{e.id()}")
        if not (e.Name or "").strip():
            problems.append(f"no name: {e.is_a()} #{e.id()}")
    for p in problems:
        print(p)
    return problems


def obj_of(doc, element):
    from nativeifc import ifc_tools
    return ifc_tools.get_object(element, doc)


def fix(doc):
    from nativeifc import ifc_tools, ifc_materials
    import ifcopenshell.util.element as ue
    f = ifcfile(doc)
    ifc_materials.load_materials(doc)                       # 'Preload materials' at import does the same
    storeys = {s.Label: s for s in doc.Objects if getattr(s, "IfcClass", "") == "IfcBuildingStorey"}
    mats = {m.Label: m for m in doc.Objects if getattr(m, "IfcClass", "") == "IfcMaterial"}
    for line in health_check(doc):
        kind, rest = line.split(": ", 1)
        step = int(rest.split("#")[1].split()[0])
        e = f.by_id(step)
        cls = e.is_a()
        o = obj_of(doc, e)
        if kind == "duplicate":
            doc.removeObject(o.Name)                         # Delete key; FreeCAD removes the IFC element
            print("duplicate removed from the IFC file:", step not in [x.id() for x in f.by_type(cls)])
        elif kind == "no level":
            level = "Level 1" if cls in ("IfcBeam", "IfcSlab") else "Level 0"
            ifc_tools.aggregate(o, storeys[level])          # drag and drop onto the level
        elif kind == "no material":
            ifc_materials.set_material(mats["Concrete C30/37"], o)
        elif kind == "no name":
            o.Label = "W-Core-E"                            # rename in the tree; FreeCAD writes IfcRoot.Name
    doc.recompute()


def build():
    doc = open_native(os.path.join(DATASETS, "unhealthy_model.ifc"), copy_to=out("unhealthy_work.ifc"))
    print("before:")
    fix(doc)
    print("after:")
    left = health_check(doc)
    print("problems left:", len(left))
    return doc


if __name__ == "__main__":
    save_native(build(), "fixed_model.ifc")
