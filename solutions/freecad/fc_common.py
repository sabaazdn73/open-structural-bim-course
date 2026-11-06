"""Shared helpers for the FreeCAD solution scripts of the TB-01 course.

Each script builds the TB-01 model the way a learner does it in the FreeCAD 1.1 BIM workbench:
it calls the same Arch / Draft functions that the toolbar commands call, sets the same
properties a learner sets in the property editor, and exports with FreeCAD's own IFC
exporter (File > Export > Industry Foundation Classes).

FreeCAD works in millimetres internally, so every length below is in mm.

Run the scripts inside FreeCAD, with the GUI up (grid bubble letters come from the view
provider of the axes, and exercise 1.1 fills in the real Setup Project dialog). A window is not
needed for the IFC files; the drawings need a working 3D view, so on a server use xvfb-run:

    QT_QPA_PLATFORM=offscreen freecad solutions/freecad/run_all.py      (all IFC exercises)
    xvfb-run freecad solutions/freecad/s5_drawings.py                    (sections 5 and 6)
    python solutions/freecad/check_all.py                                (the checker on every file)

Output goes to $FC_OUT (default /tmp/fc_out). Tested with FreeCAD 1.1.3 (AppImage, Linux).
"""
import os
import sys

import FreeCAD
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "checker"))
from bimcheck import spec  # noqa: E402  (the numbers of the brief)

OUT = os.environ.get("FC_OUT", "/tmp/fc_out")
DATASETS = os.path.join(ROOT, "datasets")
GUI = bool(FreeCAD.GuiUp)


def mm(metres):
    return round(metres * 1000.0, 6)


def out(name):
    os.makedirs(OUT, exist_ok=True)
    return os.path.join(OUT, name)


def find(doc, label):
    """The object with this label (as you would pick it in the tree)."""
    hits = doc.getObjectsByLabel(label)
    if not hits:
        raise KeyError(label)
    return hits[0]


def set_ifc_property(obj, pset, name, ifc_type, value):
    """What Manage > Manage IFC Properties writes into an object's IfcProperties map."""
    props = dict(obj.IfcProperties)
    props[f"{name};;{pset}"] = f"{ifc_type};;{value}"
    obj.IfcProperties = props


def export_preferences(groups=False):
    """Edit > Preferences > Import-Export > IFC Export.

    The defaults of FreeCAD 1.1 are kept, except (for exercise 3.6 onwards) the box
    'Export FreeCAD Groups' is ticked and 'Export nested groups as assemblies' is cleared,
    so that the selection groups inside the levels are written as IfcGroup.
    """
    from draftutils import params
    params.set_param_arch("ifcExportModel", 0)            # Export type: Standard model
    params.set_param_arch("IfcExportStdGroups", bool(groups))
    params.set_param_arch("IfcGroupsAsAssemblies", not groups)
    params.set_param_arch("IfcAddDefaultBuilding", True)


def export_ifc(objects, filename, groups=False):
    """File > Export > Industry Foundation Classes (*.ifc), with the selected objects."""
    from importers import exportIFC
    export_preferences(groups)
    path = out(filename)
    exportIFC.export(objects, path)
    print("exported", path)
    return path


def save_fcstd(doc, filename):
    path = out(filename)
    doc.saveAs(path)
    return path
