"""Section 4 in FreeCAD 1.1: types, a type catalogue and a custom property set (exercises 4.1 to 4.3).

FreeCAD's classic IFC exporter (File > Export) writes no element types at all, so from this section
on the model is opened as a native IFC document (File > Open tb01.ifc) and edited in place:

  File > Open (IFC Import Options: All individual IFC objects, Load the shape, Locked)
                     nativeifc.ifc_import.insert(path, doc, strategy=2, shapemode=0, singledoc=True)
  right-click an element > Convert to Type (keep the original object)
                     nativeifc.ifc_types.convert_to_type(obj, keep_object=True)
  property editor: Label of the type, Type of every other element
                     obj.Type = type_object  (FreeCAD writes IfcRelDefinesByType)
  Python console:    the catalogue (4.2) and one clean-up line (see remove_types_from_groups)
  Manage > Manage IFC Properties (TB01_Structural)
                     what the dialog does for native objects: addProperty + ifc_psets.edit_pset
  File > Save IFC File As...   nativeifc.ifc_tools.save_ifc(doc, path)
"""
import csv
import os
import shutil

import FreeCAD

from fc_common import spec, out, ROOT

PARAMS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/NativeIFC")


def open_native(path, copy_to=None):
    """File > Open an .ifc file: FreeCAD 1.1 opens it as a native IFC document."""
    from nativeifc import ifc_import
    if copy_to:
        shutil.copy(path, copy_to)
        path = copy_to
    name = os.path.splitext(os.path.basename(path))[0].replace("-", "_")
    doc = FreeCAD.newDocument(name)
    ifc_import.insert(path, doc.Name, strategy=2, shapemode=0, silent=True, singledoc=True)
    doc.recompute()
    return doc


def ifcfile(doc):
    from nativeifc import ifc_tools
    return ifc_tools.get_ifcfile(doc)


def save_native(doc, filename):
    """File > Save IFC File As..."""
    from nativeifc import ifc_tools
    path = out(filename)
    ifc_tools.save_ifc(doc, path)
    print("saved", path)
    return path


def add_to_native(doc, make, parent):
    """Make a new BIM object in a locked IFC document and put it under parent (a level).

    In the GUI, FreeCAD converts every new object to IFC a moment after the tool has finished
    (nativeifc.ifc_observer) and you then drag it onto the level. A script runs too fast for that
    timer, so the observer is paused while the object is built and the conversion is called directly."""
    from nativeifc import ifc_observer, ifc_tools
    ifc_observer.remove_observer()
    try:
        obj = make()
        doc.recompute()
    finally:
        ifc_observer.add_observer()
    new = ifc_tools.aggregate(obj, parent)
    doc.recompute()
    return new


def by_class(doc, ifc_class):
    return [o for o in doc.Objects if getattr(o, "IfcClass", "") == ifc_class]


def make_types(doc):
    """4.1: Convert to Type on one element of each kind, then point the others to that type."""
    from nativeifc import ifc_types
    PARAMS.SetBool("ConvertTypeAskAgain", False)     # the dialog: 'Keep the original object' ticked
    PARAMS.SetBool("ConvertTypeKeepOriginal", True)
    pads = [o for o in by_class(doc, "IfcFooting") if o.Label.startswith("F-")]
    groups = {"IfcColumn": ("C-A1", by_class(doc, "IfcColumn")),
              "IfcBeam": ("B-1/AB", by_class(doc, "IfcBeam")),
              "IfcFooting": ("F-A1", pads)}
    types = {}
    for cls, (first, members) in groups.items():
        src = [o for o in members if o.Label == first][0]
        ifc_types.convert_to_type(src, keep_object=True)
        doc.recompute()
        t = src.Type
        t.Label = spec.TYPES[cls]                        # rename the new type in the tree
        for o in members:
            if o is not src:
                o.Type = t                               # property editor: Type
        types[cls] = t
    doc.recompute()
    remove_types_from_groups(doc)
    return types


def remove_types_from_groups(doc):
    """Convert to Type copies the element with its relationships, so the new type also lands in the
    selection groups of exercise 3.6. One line in the Python console takes types out of groups."""
    f = ifcfile(doc)
    for rel in f.by_type("IfcRelAssignsToGroup"):
        rel.RelatedObjects = [o for o in rel.RelatedObjects if not o.is_a("IfcTypeObject")]
    doc.Modified = True


def load_catalogue(doc, csv_path=None):
    """4.2: the catalogue, in the Python console, with the IfcOpenShell API that ships with FreeCAD."""
    from nativeifc import ifc_tools
    f = ifcfile(doc)
    csv_path = csv_path or os.path.join(ROOT, "datasets", "column_types.csv")
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    existing = {t.Name: t for t in f.by_type("IfcColumnType")}
    for row in rows:
        t = existing.get(row["Name"]) or ifc_tools.api_run("root.create_entity", f, ifc_class="IfcColumnType",
                                                           name=row["Name"])
        pset = ifc_tools.api_run("pset.add_pset", f, product=t, name="TB01_TypeData")
        ifc_tools.api_run("pset.edit_pset", f, pset=pset,
                          properties={"Width": float(row["Width_mm"]), "Depth": float(row["Depth_mm"])})
    doc.Modified = True
    return rows


def set_native_property(obj, pset, name, ptype, value):
    """What Manage > Manage IFC Properties does for a native IFC object when you press OK: it adds a
    FreeCAD property in a group named after the property set and writes it to the IFC file."""
    from nativeifc import ifc_psets
    if name not in obj.PropertiesList:
        obj.addProperty(ifc_psets.get_freecad_type(ptype), name, pset, ptype + ":" + name)
        ifc_psets.edit_pset(obj, name, force=True)
    setattr(obj, name, value)


def add_custom_pset(doc):
    """4.3: Manage IFC Properties > Add property set > New 'TB01_Structural', two properties."""
    for cls, fire in spec.FIRE.items():
        els = by_class(doc, cls)
        if cls == "IfcColumn":
            els = [o for o in els if o.Label.startswith("C-")]
        for o in els:
            set_native_property(o, spec.CUSTOM_PSET, "FireResistance", "IfcLabel", fire)
            set_native_property(o, spec.CUSTOM_PSET, "DesignWorkingLife", "IfcInteger", spec.DESIGN_LIFE)
    doc.recompute()


def build(source=None):
    source = source or out("tb01_s3.ifc")
    doc = open_native(source, copy_to=out("tb01_s4_work.ifc"))
    make_types(doc)
    load_catalogue(doc)
    add_custom_pset(doc)
    return doc


if __name__ == "__main__":
    doc = build()
    save_native(doc, "tb01_s4.ifc")
