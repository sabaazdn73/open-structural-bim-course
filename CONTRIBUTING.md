# Contributing

Thank you for helping. The most useful contributions are:

1. **Corrections to the steps.** If a menu, button or property is named differently in your version of FreeCAD or
   Bonsai, open an issue or a pull request with the version number and what you see.
2. **Screenshots** for the steps (PNG, cropped to the relevant panel, placed in `course/img/`).
3. **Steps for other programs** that export IFC (for example other open-source BIM tools).
4. **New exercises**, with a check in `checker/bimcheck/exercises/` and tests in `tests/`.

## How the repository is built

- All project numbers live in `checker/bimcheck/spec.py`.
- `python tools/build_brief.py` writes the brief, its drawings and the test fixtures.
- `python tools/build_datasets.py` writes the datasets and the reference answers.
- `python tools/build_lessons.py` writes the lessons from `tools/lessons_common.py` (the common part) and
  `course/_steps/freecad/` and `course/_steps/bonsai/` (the steps for each program). Edit those sources, not the
  generated files in `course/0*`.
- `python -m pytest -q tests` must stay green: every check passes on the reference answer and fails on a wrong file.

Write plainly: short sentences, numbered steps, exact names of menus and buttons.
