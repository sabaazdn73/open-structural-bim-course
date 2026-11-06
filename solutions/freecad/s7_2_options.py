"""Exercise 7.2 in FreeCAD 1.1: two design options as two IFC files.

  Option A: the section 2 model (with its concrete materials), File > Export > option_A.ifc
  File > Save a Copy as option_B.FCStd, open it, select B-2/BC and in the property editor set
  Width 400, Height 500 and Placement > Position > z 3100 (the beam axis is at mid-depth), then
  File > Export > option_B.ifc. Utils > IFC Diff compares the two open documents.
"""
from fc_common import spec, mm, export_ifc
import s2_structure


def concrete_frame():
    m = s2_structure.build()
    # materials as in exercise 3.5, frame only (the options are about sections 1 and 2)
    import Arch
    mat = Arch.makeMaterial(name="Concrete C30/37")
    for e in list(m["columns"].values()) + list(m["beams"].values()) + list(m["walls"].values()) + [m["slab"]]:
        e.Material = mat
    m["doc"].recompute()
    return m


def option_b(m):
    b = m["beams"]["B-2/BC"]
    b.Width = 400
    b.Height = 500
    z0 = spec.SLAB_SOFFIT - 0.5
    b.Placement.Base.z = mm((z0 + spec.SLAB_SOFFIT) / 2)      # still hung from the soffit
    m["doc"].recompute()


if __name__ == "__main__":
    m = concrete_frame()
    export_ifc([m["project"]], "option_A.ifc")
    option_b(m)
    export_ifc([m["project"]], "option_B.ifc")
