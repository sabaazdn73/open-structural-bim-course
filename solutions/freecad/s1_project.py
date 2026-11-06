"""Section 1 in FreeCAD 1.1: project, site, building, levels and grid (exercises 1.1 to 1.3).

What the learner does in the GUI, and the call each step makes:
  Manage > Setup Project ............ the real dialog is filled in and accepted (GUI), which calls
                                      Arch.makeSite / makeBuilding / makeFloor / makeAxis / makeAxisSystem
  property editor ................... Label, Latitude, Longitude, Elevation, Declination, Placement
  Python console (no button in 1.1) . Arch.makeProject(...) names the IfcProject
  Annotation > Axis System .......... Arch.makeAxisSystem([axes])
  File > Export > IFC ............... importers.exportIFC.export([project], "tb01.ifc")
"""
import FreeCAD
import Arch
import Draft

from fc_common import V, spec, mm, GUI, export_ifc


def setup_project_dialog():
    """Manage > Setup Project, filled in as in the lesson (exercise 1.1), and OK pressed."""
    from bimcommands import BimProjectManager
    p = spec.PROJECT
    pm = BimProjectManager.BIM_ProjectManager()
    pm.Activated()
    f = pm.form
    f.groupNewProject.setChecked(True)
    f.radioNative1.setChecked(True)                    # Create a new document without IFC support
    f.projectName.setText(p["project_name"])
    f.groupSite.setChecked(True)
    f.siteName.setText(p["site_name"])
    f.siteLatitude.setValue(p["latitude"])
    f.siteLongitude.setValue(p["longitude"])
    f.siteElevation.setText(f"{p['site_elevation']:g} m")
    f.groupBuilding.setChecked(True)
    f.buildingName.setText(p["building_name"])
    f.countVAxes.setValue(len(spec.GRID_X))
    f.distVAxes.setText("6000 mm")
    f.countHAxes.setValue(len(spec.GRID_Y))
    f.distHAxes.setText("7000 mm")
    f.countLevels.setValue(4)
    f.levelHeight.setText("3600 mm")
    f.addHumanFigure.setChecked(False)
    pm.accept()
    doc = FreeCAD.ActiveDocument
    site = doc.getObjectsByLabel(p["site_name"])[0]
    building = doc.getObjectsByLabel(p["building_name"])[0]
    return doc, site, building


def build(doc=None):
    p = spec.PROJECT
    xs, ys = list(spec.GRID_X.values()), list(spec.GRID_Y.values())
    ext = 2000.0                                       # 2 m past the outer grids
    if GUI and doc is None:
        # 1.1: Manage > Setup Project makes the site, the building, four levels and two sets of axes
        doc, site, building = setup_project_dialog()
        site.Declination = -p["true_north_deg"]        # step 9: -12 deg = 12 deg clockwise
        levels = {lv.Label: lv for lv in building.Group if getattr(lv, "IfcType", "") == "Building Storey"}
        # 1.2: rename Level 3, add Foundation with 3D/BIM > Level
        levels["Level 3"].Label = "Roof"
        levels["Roof"] = levels.pop("Level 3")
        lv = Arch.makeFloor()
        lv.Label = "Foundation"
        lv.Placement.Base.z = mm(spec.STOREYS[0][1])
        building.addObject(lv)
        levels["Foundation"] = lv
        # 1.3: the axes made by the dialog get their tags, lengths and positions
        letters = doc.getObjectsByLabel("Vertical Axes")[0]
        numbers = doc.getObjectsByLabel("Horizontal Axes")[0]
        letters.ViewObject.NumberingStyle = "A,B,C"
        letters.Length = mm(max(ys) - min(ys)) + 2 * ext
        letters.Placement.Base.y = mm(min(ys)) - ext
        letters.Label = "Grid A-D"
        numbers.ViewObject.NumberingStyle = "1,2,3"
        numbers.Length = mm(max(xs) - min(xs)) + 2 * ext
        numbers.Placement.Base.x = mm(max(xs)) + ext
        numbers.Label = "Grid 1-3"
        grid = [o for o in doc.Objects if Draft.getType(o) == "AxisSystem"][0]
    else:
        # the same model through the API (FreeCADCmd, or a document passed in)
        doc = doc or FreeCAD.newDocument("tb01")
        site = Arch.makeSite()
        site.Label = p["site_name"]
        site.Latitude = p["latitude"]
        site.Longitude = p["longitude"]
        site.Elevation = mm(p["site_elevation"])
        site.Declination = -p["true_north_deg"]
        building = Arch.makeBuilding()
        building.Label = p["building_name"]
        site.Group = [building]
        levels = {}
        for name, z in spec.STOREYS:
            lv = Arch.makeFloor()
            lv.Label = name
            lv.Placement.Base.z = mm(z)
            building.addObject(lv)
            levels[name] = lv
        letters = Arch.makeAxis(num=len(xs), size=mm(xs[1] - xs[0]), name="Grid A-D")
        letters.Length = mm(max(ys) - min(ys)) + 2 * ext
        letters.Placement.Base = V(mm(xs[0]), mm(min(ys)) - ext, 0)
        numbers = Arch.makeAxis(num=len(ys), size=mm(ys[1] - ys[0]), name="Grid 1-3")
        numbers.Length = mm(max(xs) - min(xs)) + 2 * ext
        numbers.Placement = FreeCAD.Placement(V(mm(max(xs)) + ext, mm(ys[0]), 0),
                                              FreeCAD.Rotation(V(0, 0, 1), 90))
        if GUI:
            letters.ViewObject.NumberingStyle = "A,B,C"
            numbers.ViewObject.NumberingStyle = "1,2,3"
        else:
            print("WARNING: no GUI, the grid axes are exported with the tags 0, 1, 2 ... "
                  "(run with the GUI, offscreen is fine)")
        grid = Arch.makeAxisSystem([numbers, letters], name="Axes")
        building.addObject(grid)

    # 1.1 the IFC project name: FreeCAD 1.1 has no button for the classic project object,
    # one line in the Python console (View > Panels > Python Console) makes it.
    project = Arch.makeProject([site], name=p["project_name"])
    doc.recompute()
    return dict(doc=doc, project=project, site=site, building=building, levels=levels, grid=grid)


if __name__ == "__main__":
    m = build()
    export_ifc([m["project"]], "tb01_s1.ifc")
