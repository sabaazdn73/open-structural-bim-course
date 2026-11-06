# Open Structural BIM Course

A free, open-source course in structural BIM modelling, with automatic grading.

You model one small reinforced concrete building, **TB-01**, from the first level to the issued model: grids,
columns, walls, slab, beams, stair, footings, piles, reinforcement, types, custom data, drawings, sheets,
revisions, phases, design options, Git worksharing, model checks, clash detection and export. Every exercise has
step-by-step instructions for **two free programs, FreeCAD and Bonsai (Blender)**, and a checker that reads your
IFC file and tells you what is right and what is not.

The course follows the same outline as a typical commercial structural BIM course, so it is a free way to learn
the workflow and to practise for structural BIM roles. It uses IFC, the open standard, so what you learn carries
over to any BIM program.

## What is in this repository

| Folder | What it holds |
|---|---|
| [`course/`](course/README.md) | The 32 exercises in 7 sections, with steps for FreeCAD and Bonsai. Start with [Getting started](course/00_getting_started.md). |
| [`brief/`](brief/README.md) | The project brief and drawings of TB-01: every dimension you need. |
| [`datasets/`](datasets/) | Starting files: the architect's model, an MEP model, a renovation model, a model full of problems, a bloated model, a type catalogue. |
| [`checker/`](checker/) | `bimcheck`, the automatic grader (Python, reads IFC, SVG, PDF and CSV). |
| [`solutions/`](solutions/) | Reference answers: a scripted model built with the IfcOpenShell API (the same API Bonsai uses) and FreeCAD scripts. Try the exercise first. |
| [`tools/`](tools/) | Scripts that generate the brief, the datasets, the reference answers and the lessons from one data file. |
| [`tests/`](tests/) | Tests: every check passes on the reference answer and fails on a wrong file. |

## The sections

1. **Project setup**: project, site and location, levels, grid.
2. **Structural elements**: columns, core walls traced from the architect's model, slab with openings, beams, clean joints.
3. **Stair, foundations, reinforcement, materials and groups.**
4. **Types, a type catalogue and custom properties.**
5. **Views, details, schedules and tags.**
6. **Sheets and revisions.**
7. **Project management**: phases, design options, Git worksharing, model health, clash detection, purge, templates, export.

## Quick start

```
git clone https://github.com/sabaazdn73/open-structural-bim-course.git
cd open-structural-bim-course
python -m pip install ./checker
python -m bimcheck list
```

Then open [course/00_getting_started.md](course/00_getting_started.md).

## How the checking works

The checker does not care which program made your file. It reads the IFC data and the geometry itself
(positions, sizes, volumes, levels, properties, materials, types) and compares them with the brief. All the
numbers live in one file, [`checker/bimcheck/spec.py`](checker/bimcheck/spec.py), which also generates the brief,
so the brief and the checks cannot disagree.

```
$ python -m bimcheck 2.1 tb01.ifc

Exercise 2.1: Columns

  PASS  12 columns between Level 0 and Level 1
  PASS  One column at every grid intersection
  FAIL  Columns run from +0.000 to the slab soffit +3.350
        C-A1 0.000 to 3.600; C-A2 0.000 to 3.600 ...
```

## Status and honesty notes

- The checker and the reference answers are tested automatically (see `tests/`).
- The FreeCAD steps were written against FreeCAD 1.1.3 and the Bonsai steps against the Bonsai 0.8 source code.
  Some steps were run by script rather than clicked through in the interface; each lesson says so where it matters.
  If a step does not match what you see, please open an issue.
- Where a program has no tool for something (for example, Bonsai has no reinforcement tool yet), the lesson
  gives a short tested script instead and says so.
- The concrete and exposure classes in the brief are reasonable teaching values, not a design.

## Licence

- Code (checker, tools, scripts): [MIT](LICENSE).
- Course text, brief, drawings and datasets: [CC BY 4.0](LICENSE-CONTENT.md).

This course is independent. It is not affiliated with or endorsed by Autodesk, the FreeCAD project or the Bonsai
project. Revit and Navisworks are trademarks of Autodesk, Inc. No Autodesk material is included.

## Author

Saba Azadegan, structural engineer (MSc). Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).
