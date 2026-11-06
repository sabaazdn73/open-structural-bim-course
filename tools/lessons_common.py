"""The tool-independent part of every lesson: goal, what to build, why it matters, how to check.

tools/build_lessons.py combines this with the FreeCAD and Bonsai steps in course/_steps/ into course/**.md.
"""

SECTIONS = {
    "1": ("01_project_setup", "Project setup: project, levels and grid"),
    "2": ("02_structural_elements", "Structural elements: columns, walls, slab, beams"),
    "3": ("03_foundations_reinforcement", "Stair, foundations, reinforcement, materials and groups"),
    "4": ("04_types_and_properties", "Types, a type catalogue and custom properties"),
    "5": ("05_views_and_schedules", "Views, details, schedules and tags"),
    "6": ("06_sheets_and_revisions", "Sheets and revisions"),
    "7": ("07_project_management", "Phases, options, worksharing, model health, clashes and export"),
}

L = {}

L["1.1"] = dict(
    slug="1.1_project_and_site", title="Project, site, building, units and location",
    goal="Start the TB-01 model: name the project, the site and the building, use metric units, and place the "
         "site on the map with its true north.",
    build=["Project name **TB-01 Training Building**, site **TB-01 Site**, building **TB-01**.",
           "Units: metres (or millimetres).",
           "Site latitude **38.7369**, longitude **-9.1427**, elevation of Level 0 **90.0 m** above sea level.",
           "True north **12 degrees clockwise** from project north (the +Y axis of the model)."],
    why="Every other model on the project (architecture, MEP, survey) must land in the same place. Names, units "
        "and location are the first thing a coordinator checks when two models do not line up, and the first thing "
        "a permit portal reads. Project north is the drawing's 'up'; true north is the real one, and the angle "
        "between them drives orientation, sun studies and the setting out on site.",
    check="python -m bimcheck 1.1 tb01.ifc", save="tb01.ifc")

L["1.2"] = dict(
    slug="1.2_levels", title="Levels (building storeys)",
    goal="Create the five levels of TB-01 at their structural elevations.",
    build=["Foundation **-1.200**, Level 0 **+0.000**, Level 1 **+3.600**, Level 2 **+7.200**, Roof **+10.800**.",
           "Use exactly these names; they are how the checker (and your colleagues) find the levels.",
           "All levels belong to the building TB-01."],
    why="In IFC a level is an *IfcBuildingStorey*: every element is placed in one, and schedules, drawings and "
        "quantities are organised by it. Structural levels are usually at the top of the structural slab, which "
        "is a few centimetres below the architect's finished floor level; agree which one you model before you start.",
    check="python -m bimcheck 1.2 tb01.ifc", save="tb01.ifc")

L["1.3"] = dict(
    slug="1.3_grid", title="Structural grid",
    goal="Draw the structural grid that every element will be set out from.",
    build=["Lettered axes A, B, C, D parallel to Y at x = 0, 6, 12, 18 m.",
           "Numbered axes 1, 2, 3 parallel to X at y = 0, 7, 14 m.",
           "Each axis must run across the whole building (A to D lines from below grid 1 to beyond grid 3, and so on). "
           "The brief extends them 2 m past the outer grids."],
    why="The grid is the contract between all disciplines: drawings, site setting out and coordination meetings "
        "all refer to 'B/2', not to coordinates. In IFC it is an *IfcGrid* with *IfcGridAxis* objects, each with a "
        "tag (A, 1...) that other programs can read.",
    check="python -m bimcheck 1.3 tb01.ifc", save="tb01.ifc")

L["2.1"] = dict(
    slug="2.1_columns", title="Columns",
    goal="Place the twelve ground floor columns.",
    build=["400 x 400 mm columns at all 12 grid intersections.",
           "From Level 0 (+0.000) up to the underside of the Level 1 slab (+3.350), not to +3.600: the slab is "
           "modelled on its own and nothing is counted twice.",
           "Name each column by its grid position: C-A1, C-A2, ... C-D3.",
           "Place the columns in Level 0."],
    why="Columns at grid intersections are the simplest structural element, but they teach the three habits every "
        "model needs: exact setting out from the grid, a clear top and bottom, and a mark that matches the drawings. "
        "Stopping the column at the slab soffit keeps the concrete quantities right (exercise 2.5).",
    check="python -m bimcheck 2.1 tb01.ifc", save="tb01.ifc")

L["2.2"] = dict(
    slug="2.2_core_walls", title="Core walls traced from the architect's model",
    goal="Link the architect's model and model the structural core walls exactly where the architect placed "
         "their load-bearing walls.",
    build=["Open or link `datasets/architect_model.ifc` as a reference. It holds four load-bearing core walls "
           "(A-Core-1 to 4) and two partitions that are not yours to model.",
           "Model four 250 mm walls on the architect's core walls: outside faces x 7.5 to 10.5, y 9.0 to 12.0.",
           "From +0.000 to the slab soffit +3.350, in Level 0.",
           "Mark them load-bearing (`Pset_WallCommon.LoadBearing = True`)."],
    why="On a real project you never type the architect's coordinates in again: you link their model and trace "
        "(or copy and monitor) the elements that are structural. Linking also shows you at once when the architect "
        "moves a wall. Partitions stay in the architect's model.",
    check="python -m bimcheck 2.2 tb01.ifc datasets/architect_model.ifc", save="tb01.ifc")

L["2.3"] = dict(
    slug="2.3_slab", title="Level 1 slab with openings",
    goal="Model the 250 mm Level 1 slab with the core and stair openings.",
    build=["Top of slab +3.600, soffit +3.350.",
           "Edges at the outer column faces: x -0.2 to 18.2, y -0.2 to 14.2.",
           "Core opening x 7.75 to 10.25, y 9.25 to 11.75; stair opening x 13.0 to 14.2, y 1.0 to 6.4.",
           "Place the slab in Level 1. Expected volume: 63.06 m3."],
    why="Openings must be real openings (voids) in the slab, not holes drawn on top of it, or the quantities and "
        "every downstream check will be wrong. The checker compares the slab's volume with the brief.",
    check="python -m bimcheck 2.3 tb01.ifc", save="tb01.ifc")

L["2.4"] = dict(
    slug="2.4_beams", title="Level 1 beams",
    goal="Model the 17 downstand beams of Level 1.",
    build=["One beam on every grid line between two columns: 9 along X (grids 1, 2, 3) and 8 along Y (grids A to D).",
           "300 mm wide, 350 mm deep below the slab soffit (+3.000 to +3.350).",
           "Each beam stops at the column faces (clear spans: 5.6 m along X, 6.6 m along Y).",
           "Name them by grid line and bay: B-1/AB is the beam on grid 1 between A and B. Place them in Level 1."],
    why="The full beam is 600 mm deep (350 downstand + 250 slab). Modelling only the downstand is a common "
        "convention that keeps the concrete volumes honest. Stopping beams at the column faces does the same at "
        "the joints.",
    check="python -m bimcheck 2.4 tb01.ifc", save="tb01.ifc")

L["2.5"] = dict(
    slug="2.5_clean_joints", title="Clean joints: no element counted twice",
    goal="Check that no two elements overlap, and that the concrete volumes of the frame match the brief.",
    build=["Fix any overlap between columns, beams, walls and the slab (for example a column running into the slab "
           "or a beam running into a column).",
           "Expected volumes: columns 6.43 m3, beams 10.84 m3, walls 9.21 m3, slab 63.06 m3; total 89.54 m3."],
    why="Revit handles this with 'join geometry' and structural connections. In open tools you get the same result "
        "by modelling each element to its true extent. Overlaps are not just untidy: they double count concrete in "
        "quantities and make clash reports noisy.",
    check="python -m bimcheck 2.5 tb01.ifc", save="tb01.ifc")

L["3.1"] = dict(
    slug="3.1_stair", title="Stair from Level 0 to Level 1",
    goal="Model a straight concrete stair through the stair opening.",
    build=["Width 1.2 m between x 13.0 and 14.2; first riser at y 1.0; climbs in +Y.",
           "20 risers of 180 mm (total rise 3.600), treads of 280 mm, arriving at Level 1 inside the opening (y up to 6.4).",
           "Place it in Level 0. If your program can store the number of risers and the riser height, do it."],
    why="Stairs are where architecture and structure meet: the structural engineer owns the flight and its supports, "
        "the architect owns the going and the headroom. A stair modelled with the right riser count is also checked "
        "against building rules (riser height, going) by code-checking tools.",
    check="python -m bimcheck 3.1 tb01.ifc", save="tb01.ifc")

L["3.2"] = dict(
    slug="3.2_pad_footings", title="Pad footings",
    goal="Place a pad footing under every column.",
    build=["1.8 x 1.8 x 0.6 m, centred under each column, top at -0.600, bottom at -1.200.",
           "Footing type PAD_FOOTING, named F-A1 ... F-D3, in the Foundation level.",
           "The short column stubs between the footings and Level 0 are not part of this course."],
    why="Foundations are their own discipline in the model: their level, their concrete (C25/30 here) and their "
        "quantities are reported separately.",
    check="python -m bimcheck 3.2 tb01.ifc", save="tb01.ifc")

L["3.3"] = dict(
    slug="3.3_piles", title="Pile cap and piles under the core",
    goal="Support the core on a pile cap and four piles.",
    build=["Pile cap PC-1: 4.0 x 4.0 x 1.0 m centred at x 9.0, y 10.5, top -0.600; footing type PILE_CAP.",
           "Four piles (IfcPile), 600 mm diameter, 12 m long, at 1.2 m each way from the core centre, from the "
           "underside of the cap (-1.600) down to -13.600.",
           "Everything in the Foundation level."],
    why="Piles and caps show how IFC separates element classes (IfcPile, IfcFooting) and predefined types "
        "(PILE_CAP, PAD_FOOTING). Getting the class right is what lets a contractor's software pick up the piles "
        "for the piling subcontract.",
    check="python -m bimcheck 3.3 tb01.ifc", save="tb01.ifc")

L["3.4"] = dict(
    slug="3.4_reinforcement", title="Reinforcement: column C-A1 and footing F-A1",
    goal="Reinforce one column and one footing with real bars.",
    build=["Steel A500.",
           "Column C-A1: 8 vertical Ø16 bars (corners and mid-sides) over the column height; Ø8 links at 150 mm "
           "from 50 mm above Level 0; 30 mm nominal cover to the links (so the vertical bars are 38 mm from the faces).",
           "Footing F-A1: bottom mesh Ø16 at 150 mm both ways (12 bars each way), 50 mm cover."],
    why="Reinforcement is where BIM pays off for a concrete engineer: bar schedules, bending shapes and clash "
        "checks between bars and inserts come straight from the model. It is also the part of the model that the "
        "site checks most carefully before a pour.",
    check="python -m bimcheck 3.4 tb01.ifc", save="tb01.ifc")

L["3.5"] = dict(
    slug="3.5_materials", title="Materials and concrete data",
    goal="Give every element its material and its concrete data.",
    build=["Columns, beams, slab and core walls: material **Concrete C30/37**.",
           "Pad footings, the pile cap and the piles: **Concrete C25/30**.",
           "On every concrete element, `Pset_ConcreteElementGeneral`: StrengthClass (C30/37 or C25/30) and "
           "ExposureClass (XC1 above ground, XC2 for footings, cap and piles)."],
    why="The material drives the quantities by concrete class and the colours in views; the property set is what "
        "a reviewer or an automatic check reads (see the model-checking notes in this repository). A model "
        "without this data looks finished but cannot be checked.",
    check="python -m bimcheck 3.5 tb01.ifc", save="tb01.ifc")

L["3.6"] = dict(
    slug="3.6_groups", title="Selection groups",
    goal="Save two selection groups you will reuse.",
    build=["Group **Ground Floor Columns** with exactly the 12 columns.",
           "Group **Level 1 Beams** with exactly the 17 beams."],
    why="Groups (IfcGroup) are saved selections that travel with the model: another engineer can open the IFC "
        "and select the same set. They are the open equivalent of Revit's selection sets.",
    check="python -m bimcheck 3.6 tb01.ifc", save="tb01.ifc")

L["4.1"] = dict(
    slug="4.1_types", title="Types for columns, beams and footings",
    goal="Define element types and make every occurrence use one.",
    build=["IfcColumnType **RC Column 400x400** used by all 12 columns.",
           "IfcBeamType **RC Beam 300x350 downstand** used by all 17 beams.",
           "IfcFootingType **Pad Footing 1800x1800x600** used by all 12 pad footings."],
    why="Types are IFC's version of Revit families and types: change the type once and every occurrence follows, "
        "and schedules can count by type. A model where every column is its own one-off object is hard to edit "
        "and hard to schedule.",
    check="python -m bimcheck 4.1 tb01.ifc", save="tb01.ifc")

L["4.2"] = dict(
    slug="4.2_type_catalogue", title="Column type catalogue from a CSV file",
    goal="Create column types from a catalogue file, the open equivalent of a Revit type catalogue.",
    build=["Read `datasets/column_types.csv` (Name, Width_mm, Depth_mm).",
           "Create one IfcColumnType per row with that name. Store Width and Depth as type properties.",
           "RC Column 400x400 is the type you made in 4.1: reuse it, do not duplicate it."],
    why="Offices keep their standard sections in catalogues so every project uses the same names and sizes. "
        "Loading types from a file is faster and less error-prone than typing them, and it is the kind of task "
        "you will automate with a script.",
    check="python -m bimcheck 4.2 tb01.ifc", save="tb01.ifc")

L["4.3"] = dict(
    slug="4.3_custom_properties", title="Custom property set TB01_Structural",
    goal="Add project-specific data with a custom property set (the open equivalent of shared parameters).",
    build=["Property set **TB01_Structural** on every column, beam, slab and core wall.",
           "FireResistance: columns **R90**, beams **R60**, slab **REI60**, walls **REI90**.",
           "DesignWorkingLife: **50** on all of them."],
    why="Standard property sets (Pset_...) cover the common data; everything else a project needs goes into "
        "custom sets with an agreed name. The name is the contract: a typo means the data is invisible to "
        "whoever reads the model next.",
    check="python -m bimcheck 4.3 tb01.ifc", save="tb01.ifc")

L["5.1"] = dict(
    slug="5.1_framing_plan", title="Level 1 framing plan with grids and dimensions",
    goal="Produce the Level 1 framing plan from the model and export it as SVG (or PDF).",
    build=["A plan view of Level 1 showing the grid with its bubbles (A to D, 1 to 3), columns, beams and the slab openings.",
           "Dimension the bays (6000 x 3 along X, 7000 x 2 along Y) and the overall sizes (18000 and 14000).",
           "Export as SVG (best) or PDF with text kept as text."],
    why="The drawing is still the legal document on most projects. A plan cut from the model stays right when the "
        "model changes; a plan drawn by hand does not.",
    check="python -m bimcheck 5.1 plan.svg", save="plan.svg")

L["5.2"] = dict(
    slug="5.2_section", title="Section through grid 2",
    goal="Cut a section through grid 2 and annotate the levels.",
    build=["Section along grid 2 looking north, showing columns, beams, the slab and the footings.",
           "Level lines with names and elevations: Foundation -1.200, Level 0 +0.000, Level 1 +3.600.",
           "Grid bubbles A to D. Export as SVG or PDF."],
    why="Sections show what plans hide: levels, depths and how elements stack. Level tags read their values from "
        "the model, so they update when a level moves.",
    check="python -m bimcheck 5.2 section.svg", save="section.svg")

L["5.3"] = dict(
    slug="5.3_detail", title="Detail callout with annotation",
    goal="Make a detail of footing F-A1 with notes.",
    build=["A callout (enlarged view) of footing F-A1 with the column above.",
           "Title **TYPICAL COLUMN FOOTING DETAIL**.",
           "Notes: concrete **C25/30**, steel **A500**, bottom mesh **Ø16 @ 150** each way, **50 mm cover**.",
           "Export as SVG or PDF."],
    why="Details are where 2D annotation adds what the model does not show well. Keep notes short and tied to the "
        "model's data so they do not contradict it.",
    check="python -m bimcheck 5.3 detail.svg", save="detail.svg")

L["5.4"] = dict(
    slug="5.4_schedule", title="Concrete quantity schedule (CSV)",
    goal="Schedule the concrete volume of every element and export it to CSV.",
    build=["One row per element (or per class) with the element class and its volume in m3.",
           "Columns, beams, slab, walls, footings (pad and cap), piles.",
           "Export as CSV. The checker compares your totals with the volumes in your model (2% tolerance)."],
    why="This is the quantity takeoff an estimator does by hand from drawings, done in minutes from the model. "
        "It only works if the model is clean (exercise 2.5) and every element has its class right.",
    check="python -m bimcheck 5.4 schedule.csv tb01.ifc", save="schedule.csv")

L["5.5"] = dict(
    slug="5.5_tags", title="Element marks and tags",
    goal="Tag every column with its mark on the framing plan.",
    build=["Every column is named by its mark (C-A1 ... C-D3) in the model (done in 2.1).",
           "Add a tag on the Level 1 framing plan for each of the 12 columns, reading the mark from the model.",
           "Export the plan again."],
    why="A tag reads the model; a text label does not. When a column is renamed, the tag follows.",
    check="python -m bimcheck 5.5 tb01.ifc plan.svg", save="plan.svg")

L["6.1"] = dict(
    slug="6.1_sheet", title="Sheet S-101 with a title block",
    goal="Place the framing plan on a sheet with a title block.",
    build=["Sheet number **S-101**, title **LEVEL 1 FRAMING PLAN**, scale **1:100**, project **TB-01 Training Building**.",
           "Place the Level 1 framing plan on it.",
           "Export as SVG or PDF."],
    why="Sheets are what leaves the office. A title block filled from the model's data (project, sheet number, "
        "scale) avoids the classic error of an issue with last week's sheet number.",
    check="python -m bimcheck 6.1 sheet.svg", save="sheet.svg")

L["6.2"] = dict(
    slug="6.2_revisions", title="Revisions on the sheet",
    goal="Record two revisions on sheet S-101.",
    build=["Revision **A**, 'First issue', with a date.",
           "Revision **B**, 'Core walls revised', with a date.",
           "Show them in a revision table on the sheet and export it again."],
    why="Revisions are the audit trail of a design. Contractors build from the latest revision; a missing or "
        "wrong revision is one of the most common causes of building from an old drawing.",
    check="python -m bimcheck 6.2 sheet.svg", save="sheet.svg")

L["7.1"] = dict(
    slug="7.1_phases", title="Phases: existing, demolish, new",
    goal="Mark what exists, what is demolished and what is new in a renovation model.",
    build=["Open `datasets/renovation_model.ifc`: an existing one-bay frame.",
           "Elements named E-... : Status **EXISTING**. Beam D-1/AB: Status **DEMOLISH**.",
           "Add a new beam **N-B1** in place of D-1/AB: 300 x 600, x 0.2 to 5.8 on grid 1, +2.750 to +3.350, "
           "Status **NEW**.",
           "Save as renovation_model.ifc (your copy)."],
    why="Most structural work is on existing buildings. IFC records phases with the Status property "
        "(NEW, EXISTING, DEMOLISH, TEMPORARY) in each element's common property set, which drawings and "
        "quantities can filter by.",
    check="python -m bimcheck 7.1 renovation_model.ifc", save="renovation_model.ifc")

L["7.2"] = dict(
    slug="7.2_design_options", title="Design options: compare two versions",
    goal="Save two design options and compare them.",
    build=["Option A: your TB-01 model as it is (sections 1 and 2).",
           "Option B: the same model with beam **B-2/BC** changed to 400 wide x 500 deep, still hung from the slab "
           "soffit (+2.850 to +3.350).",
           "Save them as option_A.ifc and option_B.ifc, then compare them with your program's IFC diff tool."],
    why="Revit keeps options inside one file; in open BIM you keep each option as its own file (or Git branch) and "
        "compare them. The comparison is the deliverable: exactly what changed, and nothing else.",
    check="python -m bimcheck 7.2 option_A.ifc option_B.ifc", save="option_A.ifc, option_B.ifc")

L["7.3"] = dict(
    slug="7.3_worksharing", title="Worksharing with Git",
    goal="Put the model under version control so a team can work on it.",
    build=["Create a Git repository for your TB-01 work.",
           "Commit the IFC model at least twice, with messages that say what changed (for example "
           "'Levels and grid' and 'Columns, walls, slab and beams').",
           "Commit the IFC file itself, not only the FreeCAD or Blender file."],
    why="Revit worksharing locks parts of a central model. In open BIM the IFC file is text, so Git can store every "
        "version, show who changed what, and merge work from two people. Bonsai has Git built in; with FreeCAD "
        "you use Git directly.",
    check="python -m bimcheck 7.3 path/to/your/repository", save="a Git repository")

L["7.4"] = dict(
    slug="7.4_model_health", title="Model health: fix the warnings",
    goal="Find and fix the problems in a model that looks fine.",
    build=["Open `datasets/unhealthy_model.ifc`.",
           "It has four problems: a duplicate column, an element that belongs to no level, an element without a "
           "material, and an element without a name. Find them with your program's checking tools and fix them.",
           "Save as fixed_model.ifc."],
    why="Revit lists these as warnings. Open tools let you run the same checks (and your own, written as IDS "
        "rules or scripts). A model with silent duplicates doubles concrete in the quantities and confuses "
        "everyone downstream.",
    check="python -m bimcheck 7.4 fixed_model.ifc", save="fixed_model.ifc")

L["7.5"] = dict(
    slug="7.5_clash_detection", title="Clash detection with the MEP model",
    goal="Find the clashes between your structure and the MEP model, and resolve them with openings.",
    build=["Run a clash check between your TB-01 model (sections 1 and 2) and `datasets/mep_model.ifc`.",
           "Duct D-1 (300 x 150) crosses three beams on grid A-B; duct D-2 (300 x 150) crosses two core walls.",
           "Resolve each clash with an opening in the beam or wall, at least 25 mm clear of the duct on every side. "
           "Do not move the ducts: the MEP model is not yours.",
           "Keep openings local: each beam keeps at least 90% of its volume.",
           "Save as structure.ifc."],
    why="Clash detection is what Navisworks is used for, and it is the daily work of BIM coordinators "
        "(and, for example, of the BIM teams that model supports and anchors for MEP). Any opening in a beam "
        "must be agreed with the structural engineer; this exercise sizes them, a real project also checks them.",
    check="python -m bimcheck 7.5 structure.ifc datasets/mep_model.ifc", save="structure.ifc")

L["7.6"] = dict(
    slug="7.6_purge", title="Purge unused data",
    goal="Clean a model of everything it does not use.",
    build=["Open `datasets/bloated_model.ifc`.",
           "Remove unused types, materials and profiles, and empty groups. Keep the column types of the project "
           "catalogue (4.2).",
           "Save as purged_model.ifc."],
    why="Old types, test materials and empty groups pile up in every project. They make files bigger and, worse, "
        "end up in schedules and type lists that others rely on.",
    check="python -m bimcheck 7.6 purged_model.ifc", save="purged_model.ifc")

L["7.7"] = dict(
    slug="7.7_template", title="Project library (template)",
    goal="Save a template that the next project can start from.",
    build=["A file with the three types of 4.1 and the materials Concrete C30/37, Concrete C25/30 and A500.",
           "No placed elements (no columns, beams...): only definitions. Levels may be included.",
           "Save as template.ifc."],
    why="Revit transfers project standards between files; open BIM keeps them in a library file that every new "
        "project starts from or loads types from. It is how an office keeps its standards consistent.",
    check="python -m bimcheck 7.7 template.ifc", save="template.ifc")

L["7.8"] = dict(
    slug="7.8_export", title="Export for issue: IFC4, levels, base quantities",
    goal="Export the finished TB-01 model for issue, with base quantities.",
    build=["Schema IFC4, SI units.",
           "Every element in a level.",
           "Base quantities (Qto_...BaseQuantities with the volume) on every column, beam, slab, wall and footing, "
           "matching the geometry.",
           "Save as tb01_issue.ifc."],
    why="The issued IFC is what the client, the contractor and the checker receive. Export settings decide "
        "whether quantities, properties and the spatial structure arrive intact.",
    check="python -m bimcheck 7.8 tb01_issue.ifc", save="tb01_issue.ifc")
