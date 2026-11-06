# Getting started

## What you need

Everything in this course is free and open source.

| Tool | What it is | Get it |
|---|---|---|
| **FreeCAD 1.1** | A parametric 3D modeller. Its BIM workbench models buildings and exports IFC. | [freecad.org](https://www.freecad.org/downloads.php) (Windows, macOS, Linux) |
| **Blender + Bonsai** | Blender is a 3D program; Bonsai is the add-on that turns it into a native IFC (BIM) authoring tool. | [bonsaibim.org](https://bonsaibim.org) (install the Blender version that the current Bonsai release supports) |
| **Python 3.9 or newer** | Runs the checker that grades your exercises. | [python.org](https://www.python.org/downloads/) |
| **Git** (section 7) | Version control for exercise 7.3. | [git-scm.com](https://git-scm.com/downloads) |

You can follow the course in FreeCAD, in Bonsai, or in both: every exercise has steps for each.

## Get the course files

```
git clone https://github.com/sabaazdn73/open-structural-bim-course.git
cd open-structural-bim-course
```

Or download the repository as a ZIP from GitHub and unzip it.

## Install the checker

```
python -m pip install ./checker
python -m bimcheck list
```

The second command lists all 32 exercises. To grade an exercise, give it the exercise number and your file:

```
python -m bimcheck 2.1 tb01.ifc
```

For drawings exported as PDF (sections 5 and 6), also install `pypdf`: `python -m pip install pypdf`. SVG needs nothing extra.

## How the course works

1. Read the [project brief](../brief/README.md) and look at its [drawings](../brief/drawings/). You will model this building, TB-01, a small two-bay reinforced concrete frame with a core.
2. Do the exercises in order. Each one builds on your model from the one before; most of them save to the same file, `tb01.ifc`.
3. After each exercise, run the checker. It reads your IFC file (or your exported drawing) and tells you, line by line, what is right and what is not.
4. Section 7 gives you some separate starting files in [`datasets/`](../datasets/).

**FreeCAD users:** keep your work in a FreeCAD file (`tb01.FCStd`) and export it to `tb01.ifc` each time you want to check it.
**Bonsai users:** Bonsai works directly in IFC, so your saved file is already `tb01.ifc`.

## If you know Revit

The course follows the order of a typical Revit structure course, with the open equivalents:

| In Revit | In this course (IFC) |
|---|---|
| Level | Building storey (IfcBuildingStorey) |
| Grid | Grid and grid axes (IfcGrid, IfcGridAxis) |
| Link, copy/monitor | Linking or referencing another IFC model and tracing from it |
| Shared coordinates, survey point | Site latitude/longitude, true north, georeferencing |
| Family and type | Type objects (IfcColumnType, IfcBeamType...) |
| Type catalogue | Types created from a CSV file |
| Shared or project parameters | Custom property sets |
| Selection sets | Groups (IfcGroup) |
| Join geometry, structural connections | Modelling each element to its true extent, no overlaps |
| Schedules | Schedules and quantity take-off, exported to CSV |
| Phases | The Status property: NEW, EXISTING, DEMOLISH |
| Design options | Separate option files compared with an IFC diff |
| Worksharing | Git version control of the IFC file |
| Warnings | Model checks (and IDS rules) |
| Interference check, Navisworks clash detection | IFC clash detection |
| Purge unused | Purging unused types, materials, profiles and groups |
| Transfer project standards | A project library or template file |

Revit is a trademark of Autodesk, Inc. This course is independent and contains no Autodesk material.
