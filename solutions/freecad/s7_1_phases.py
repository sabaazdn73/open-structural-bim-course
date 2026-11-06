"""Exercise 7.1 in FreeCAD 1.1: phases (Status) on the renovation model, plus the new beam N-B1.

  File > Open datasets/renovation_model.ifc (native IFC, All individual IFC objects, Load the shape)
  Manage > Manage IFC Properties: Status in Pset_ColumnCommon / Pset_BeamCommon / Pset_SlabCommon
  3D/BIM > Beam (in a locked IFC document FreeCAD turns the new beam into IFC), drag it into Level 1
  File > Save IFC File As... renovation_model.ifc
"""
import os

from fc_common import V, DATASETS, out
from s4_types import open_native, save_native, set_native_property, add_to_native
import s2_structure

COMMON = {"IfcColumn": "Pset_ColumnCommon", "IfcBeam": "Pset_BeamCommon", "IfcSlab": "Pset_SlabCommon"}


def build():
    doc = open_native(os.path.join(DATASETS, "renovation_model.ifc"), copy_to=out("renovation_work.ifc"))
    els = [o for o in doc.Objects if getattr(o, "IfcClass", "") in COMMON]
    for o in els:
        status = {"E": "EXISTING", "D": "DEMOLISH"}.get(o.Label[:1])
        if status:
            set_native_property(o, COMMON[o.IfcClass], "Status", "IfcLabel", status)
    # the new beam: 300 x 600 on grid 1 between the column faces, top at the slab soffit
    level1 = [o for o in doc.Objects if getattr(o, "IfcClass", "") == "IfcBuildingStorey" and o.Label == "Level 1"][0]

    def new_beam():
        b = s2_structure.make_beam(V(200, 0, 3050), V(5800, 0, 3050), 300, 600)
        b.Label = "N-B1"
        return b

    new = add_to_native(doc, new_beam, level1)
    set_native_property(new, "Pset_BeamCommon", "Status", "IfcLabel", "NEW")
    doc.recompute()
    return doc


if __name__ == "__main__":
    save_native(build(), "renovation_model.ifc")
