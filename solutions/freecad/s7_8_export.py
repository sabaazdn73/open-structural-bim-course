"""Exercise 7.8 in FreeCAD 1.1: the issue file, IFC4, with base quantities.

FreeCAD's classic exporter can only write its own 'ElementQuantities' set (Manage > Manage IFC
Quantities, ticks), not the standard Qto_...BaseQuantities. In a native IFC document the same dialog
offers the Qto sets, but in 1.1.3 it fills them with 0 for native objects. So the lesson adds the
base quantities with this console snippet on the open native document (tb01.ifc of section 4),
then File > Save IFC File As... tb01_issue.ifc.
"""
from fc_common import out
from s4_types import open_native, save_native

SNIPPET = '''
import ifcopenshell.api, ifcopenshell.geom, ifcopenshell.util.shape as us
f = FreeCAD.ActiveDocument.Proxy.ifcfile
s = ifcopenshell.geom.settings()
for cls in ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting"):
    for e in f.by_type(cls):
        shape = ifcopenshell.geom.create_shape(s, e)      # keep the shape while it is read
        vol = us.get_volume(shape.geometry)
        q = ifcopenshell.api.run("pset.add_qto", f, product=e, name="Qto_" + cls[3:] + "BaseQuantities")
        ifcopenshell.api.run("pset.edit_qto", f, qto=q, properties={"NetVolume": vol})
FreeCAD.ActiveDocument.Modified = True
'''


def build(source=None):
    import FreeCAD
    doc = open_native(source or out("tb01_s4.ifc"), copy_to=out("issue_work.ifc"))
    assert doc is FreeCAD.ActiveDocument
    exec(SNIPPET, {"FreeCAD": FreeCAD})
    return doc


if __name__ == "__main__":
    save_native(build(), "tb01_issue.ifc")
