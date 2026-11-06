"""Sections 5 and 6 in FreeCAD 1.1: plan, section, detail, schedule, tags, sheet and revisions.

The drawings are made with BIM 2D drawings and Draft annotations, and written with
File > Export > 'Flattened SVG (*.svg)'. That exporter writes every text, dimension, label and grid
bubble as SVG <text>, which is what the checker reads.

  Annotation > Section Plane ............ Arch.makeSectionPlane(objects), Placement
  Annotation > Create 2D Views > 2D Drawing (with the section plane selected)
                                          Arch.make2DDrawing() + Draft.make_shape2dview(section)
  Annotation > Horizontal / Vertical Dimension   Draft.make_linear_dimension(p1, p2, p3)
  Annotation > Label (Label type 'Label')        Draft.make_label(..., target_object, "Label")
  Annotation > Text ..................... Draft.make_text([...], placement)
  Manage > Schedule ..................... Arch.makeSchedule(), Operation / Value / Unit / Filter
                                          columns, Export button (CSV)
  File > Export > Flattened SVG (*.svg) . importSVG.export(objects, path)

Needs the GUI with a working 3D view (the exporter measures texts in the 3D view): run it in a
normal FreeCAD window, or under xvfb-run on a server. With QT_QPA_PLATFORM=offscreen the SVG export
stops with "AttributeError: getViewer".
"""
import FreeCAD
import Arch
import Draft

from fc_common import V, spec, mm, out
import s3_foundations_rebar

Z_PLAN = 3200.0          # plan cut, between the beam soffit (3000) and the slab soffit (3350)


SCALE = 100              # 1:100: set it in the Draft annotation scale box of the status bar


def at_scale(objs):
    """Annotations drawn at 1:100 (status bar annotation scale 1:100 before drawing them)."""
    if FreeCAD.GuiUp:
        for o in objs:
            vp = o.ViewObject.PropertiesList
            if "ScaleMultiplier" in vp:
                o.ViewObject.ScaleMultiplier = SCALE
            if "FontSize" in vp:                    # the SVG exporter writes FontSize as it is
                o.ViewObject.FontSize = 2.5 * SCALE
            if "ArrowSizeStart" in vp:
                o.ViewObject.ArrowSizeStart = 1.0 * SCALE
            elif "ArrowSize" in vp:
                o.ViewObject.ArrowSize = 1.0 * SCALE
    return objs


def text(lines, x, y, z=0.0):
    t = Draft.make_text(lines, placement=FreeCAD.Placement(V(x, y, z), FreeCAD.Rotation()))
    at_scale([t])
    return t


def two_d_drawing(section, name):
    """Annotation > Create 2D Views > 2D Drawing, with the section plane selected."""
    drawing = Arch.make2DDrawing(name=name)
    viewed = Draft.make_shape2dview(section)
    viewed.Label = "Viewed lines"
    viewed.InPlace = False
    drawing.addObject(viewed)
    cut = Draft.make_shape2dview(section)
    cut.Label = "Cut lines"
    cut.InPlace = False
    cut.ProjectionMode = "Cutfaces"
    drawing.addObject(cut)
    return drawing


def plan(m):
    """5.1 and 5.5: the Level 1 framing plan with grid, dimensions and column tags (in plan, z = 3200)."""
    doc = m["doc"]
    sp = Arch.makeSectionPlane([m["levels"]["Level 0"], m["levels"]["Level 1"]])
    sp.Label = "Section Level 1 plan"
    sp.Placement = FreeCAD.Placement(V(9000, 7000, Z_PLAN), FreeCAD.Rotation())
    doc.recompute()
    drawing = two_d_drawing(sp, "Level 1 framing plan")
    xs = [mm(v) for v in spec.GRID_X.values()]
    ys = [mm(v) for v in spec.GRID_Y.values()]
    annos = []
    for a, b in zip(xs, xs[1:]):                                       # bays along X
        annos.append(Draft.make_linear_dimension(V(a, -2500, 0), V(b, -2500, 0), V((a + b) / 2, -3000, 0)))
    annos.append(Draft.make_linear_dimension(V(xs[0], -3500, 0), V(xs[-1], -3500, 0), V(9000, -4000, 0)))
    for a, b in zip(ys, ys[1:]):                                       # bays along Y
        annos.append(Draft.make_linear_dimension(V(-2500, a, 0), V(-2500, b, 0), V(-3000, (a + b) / 2, 0)))
    annos.append(Draft.make_linear_dimension(V(-3500, ys[0], 0), V(-3500, ys[-1], 0), V(-4000, 7000, 0)))
    for mark, col in m["columns"].items():                            # 5.5: tags read the column Label
        p = col.Placement.Base
        annos.append(Draft.make_label(V(p.x + 200, p.y + 200, 0), V(p.x + 900, p.y + 900, 0),
                                      target_object=col, label_type="Label"))
    annos.append(text(["LEVEL 1 FRAMING PLAN 1:100"], 0, -5500))
    at_scale(annos)
    if FreeCAD.GuiUp:
        for ax in m["grid"].Axes:
            ax.ViewObject.FontSize = 350
            ax.ViewObject.BubbleSize = 800
    for a in annos:
        drawing.addObject(a)
    doc.recompute()
    return drawing, list(m["grid"].Axes)


def section(m):
    """5.2: section along grid 2, looking north, with level lines and names."""
    doc = m["doc"]
    y2 = mm(spec.GRID_Y["2"])
    objs = [m["levels"][n] for n in ("Foundation", "Level 0", "Level 1")]
    sp = Arch.makeSectionPlane(objs)
    sp.Label = "Section grid 2"
    # the plane stands up on grid 2; its normal points south, so it looks north
    sp.Placement = FreeCAD.Placement(V(9000, y2, 1000), FreeCAD.Rotation(V(1, 0, 0), 90))
    doc.recompute()
    drawing = two_d_drawing(sp, "Section grid 2")
    doc.recompute()
    bb = drawing.Group[0].Shape.BoundBox                # where FreeCAD laid the section out
    annos = []
    for name, z in spec.STOREYS[:3]:
        # the 2D view keeps the section's own x and z: put the level lines at those heights
        yz = bb.YMin + (mm(z) - mm(spec.FOOTING["z0"])) if bb.isValid() else mm(z)
        annos.append(Draft.make_line(V(bb.XMin - 1500, yz, 0), V(bb.XMax + 500, yz, 0)))
        annos.append(text([f"{name} {z:+.3f}"], bb.XMin - 4500, yz + 100))
    for tag, x in spec.GRID_X.items():                                 # grid bubbles above the section
        annos.append(text([tag], bb.XMin + (mm(x) - mm(spec.SLAB["x0"])) - 100, bb.YMax + 800))
    annos.append(text(["SECTION ON GRID 2, LOOKING NORTH 1:100"], bb.XMin, bb.YMin - 1500))
    for a in annos:
        drawing.addObject(a)
    doc.recompute()
    return drawing


def detail(m):
    """5.3: footing F-A1 with the column above, larger scale, notes."""
    doc = m["doc"]
    sp = Arch.makeSectionPlane([m["footings"]["F-A1"], m["columns"]["C-A1"]] + m["rebars"])
    sp.Label = "Detail F-A1"
    sp.Placement = FreeCAD.Placement(V(0, 0, -600), FreeCAD.Rotation(V(1, 0, 0), 90))
    sp.ViewObject.DisplayLength = 3000
    sp.ViewObject.DisplayHeight = 3000
    doc.recompute()
    drawing = two_d_drawing(sp, "Detail F-A1")
    doc.recompute()
    bb = drawing.Group[0].Shape.BoundBox
    x0, y0 = (bb.XMax + 400, bb.YMin) if bb.isValid() else (1500, -1200)
    notes = [text(["TYPICAL COLUMN FOOTING DETAIL"], x0 - 2600, y0 - 700),
             text(["Concrete C25/30, exposure XC2"], x0, y0 + 900),
             text(["Steel A500"], x0, y0 + 650),
             text(["Bottom mesh Ø16 @ 150 each way"], x0, y0 + 400),
             text(["50 mm cover"], x0, y0 + 150)]
    for n in notes:
        drawing.addObject(n)
    doc.recompute()
    return drawing


def sheet(m, plan_drawing, axes):
    """6.1 and 6.2: a sheet frame, title block and revision table drawn around the plan."""
    w, h, x0, y0 = 42000.0, 29700.0, -6000.0, -9000.0          # A3 at 1:100, in model millimetres
    frame = [Draft.make_rectangle(w, h, placement=FreeCAD.Placement(V(x0, y0, 0), FreeCAD.Rotation())),
             Draft.make_rectangle(17000, 5000, placement=FreeCAD.Placement(V(x0 + w - 17000, y0, 0), FreeCAD.Rotation()))]
    tx, ty = x0 + w - 16500, y0 + 4000
    block = [text(["TB-01 Training Building"], tx, ty),
             text(["LEVEL 1 FRAMING PLAN"], tx, ty - 900),
             text(["Sheet S-101"], tx, ty - 1800),
             text(["Scale 1:100"], tx + 7000, ty - 1800),
             text(["Rev  Description          Date"], tx, ty - 2700),
             text(["A    First issue          2026-10-15"], tx, ty - 3300),
             text(["B    Core walls revised   2026-11-06"], tx, ty - 3900)]
    return frame + block


def schedule(m):
    """5.4: Manage > Schedule, one line per class, Value Shape.Volume in m^3, then Export (CSV)."""
    sch = Arch.makeSchedule()
    rows = [("Columns", "IfcType:Column"), ("Beams", "IfcType:Beam"), ("Slab", "IfcType:Slab"),
            ("Walls", "IfcType:Wall"), ("Footings and caps", "IfcType:Footing"), ("Piles", "IfcType:Pile")]
    sch.Operation = [r[0] for r in rows]
    sch.Value = ["Shape.Volume"] * len(rows)
    sch.Unit = ["m^3"] * len(rows)
    sch.Objects = [m["building"].Name] * len(rows)       # 'Objects' column: the building
    sch.Filter = [r[1] for r in rows]
    m["doc"].recompute()
    sch.Proxy.execute(sch)
    path = out("schedule.csv")
    from ArchSchedule import ArchScheduleTaskPanel
    panel = ArchScheduleTaskPanel(sch)
    panel.exportCSV(path, delimiter=",")
    return path


def export_svg(objs, filename):
    """File > Export > Flattened SVG (*.svg), with these objects selected (3D view active)."""
    import importSVG
    if FreeCAD.GuiUp:
        import FreeCADGui
        from PySide import QtWidgets
        QtWidgets.QApplication.processEvents()
        if FreeCADGui.ActiveDocument is None:
            raise RuntimeError("Flattened SVG export needs an active 3D view: run this script on its own "
                               "in a FreeCAD window (or under xvfb-run), not after other scripts")
    path = out(filename)
    importSVG.export(objs, path)
    print("exported", path)
    return path


def flat(drawing):
    return [o for o in drawing.Group]


if __name__ == "__main__":
    m = s3_foundations_rebar.build()
    pl, axes = plan(m)
    export_svg(flat(pl) + axes, "plan.svg")
    export_svg(flat(section(m)), "section.svg")
    export_svg(flat(detail(m)), "detail.svg")
    export_svg(flat(pl) + axes + sheet(m, pl, axes), "sheet.svg")
    print("schedule", schedule(m))
