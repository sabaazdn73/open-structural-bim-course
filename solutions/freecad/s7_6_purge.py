"""Exercise 7.6 in FreeCAD 1.1: purge unused types, materials, profiles and empty groups.

FreeCAD 1.1 has no purge command, and unused types, materials, profiles and empty groups of a
native IFC file are not shown in the tree (only what the elements use is loaded). The lesson uses
this console snippet on the open native document, then File > Save IFC File As... purged_model.ifc.
"""
import os

from fc_common import DATASETS, out
from s4_types import open_native, save_native, ifcfile

SNIPPET = '''
import ifcopenshell.api, ifcopenshell.util.element as ue
f = FreeCAD.ActiveDocument.Proxy.ifcfile
keep = [r.split(",")[0] for r in open(CSV).read().splitlines()[1:]]
for t in f.by_type("IfcElementType"):
    if not ue.get_types(t) and t.Name not in keep:
        print("type", t.Name); ifcopenshell.api.run("root.remove_product", f, product=t)
for m in f.by_type("IfcMaterial"):
    if f.get_total_inverses(m) == 0:
        print("material", m.Name); ifcopenshell.api.run("material.remove_material", f, material=m)
for p in f.by_type("IfcProfileDef"):
    if f.get_total_inverses(p) == 0:
        print("profile", p.ProfileName); f.remove(p)
for g in f.by_type("IfcGroup"):
    if not any(r.RelatedObjects for r in g.IsGroupedBy):
        print("group", g.Name); ifcopenshell.api.run("group.remove_group", f, group=g)
FreeCAD.ActiveDocument.Modified = True
'''


def purge(doc):
    import FreeCAD
    g = {"FreeCAD": FreeCAD, "CSV": os.path.join(DATASETS, "column_types.csv")}
    assert doc is FreeCAD.ActiveDocument
    exec(SNIPPET, g)


def build():
    doc = open_native(os.path.join(DATASETS, "bloated_model.ifc"), copy_to=out("bloated_work.ifc"))
    purge(doc)
    return doc


if __name__ == "__main__":
    save_native(build(), "purged_model.ifc")
