"""Run the course checker on every file written by run_all.py (normal Python with ifcopenshell, not FreeCAD).

    python solutions/freecad/check_all.py [folder]      (default: $FC_OUT or /tmp/fc_out)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "checker"))
from bimcheck.exercises import REGISTRY  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FC_OUT", "/tmp/fc_out")
DATA = os.path.join(ROOT, "datasets")


def o(name):
    return os.path.join(OUT, name)


# exercise: files. Each exercise is checked on the file of its own section, as a learner hands it in.
RUNS = {
    "1.1": [o("tb01_s1.ifc")], "1.2": [o("tb01_s1.ifc")], "1.3": [o("tb01_s1.ifc")],
    "2.1": [o("tb01_s2.ifc")], "2.2": [o("tb01_s2.ifc"), os.path.join(DATA, "architect_model.ifc")],
    "2.3": [o("tb01_s2.ifc")], "2.4": [o("tb01_s2.ifc")], "2.5": [o("tb01_s2.ifc")],
    "3.1": [o("tb01_s3.ifc")], "3.2": [o("tb01_s3.ifc")], "3.3": [o("tb01_s3.ifc")],
    "3.4": [o("tb01_s3.ifc")], "3.5": [o("tb01_s3.ifc")], "3.6": [o("tb01_s3.ifc")],
    "4.1": [o("tb01_s4.ifc")], "4.2": [o("tb01_s4.ifc")], "4.3": [o("tb01_s4.ifc")],
    "5.1": [o("plan.svg")], "5.2": [o("section.svg")], "5.3": [o("detail.svg")],
    "5.4": [o("schedule.csv"), o("tb01_s4.ifc")], "5.5": [o("tb01_s4.ifc"), o("plan.svg")],
    "6.1": [o("sheet.svg")], "6.2": [o("sheet.svg")],
    "7.1": [o("renovation_model.ifc")], "7.2": [o("option_A.ifc"), o("option_B.ifc")],
    "7.3": [o("tb01_repo")], "7.4": [o("fixed_model.ifc")],
    "7.5": [o("structure.ifc"), os.path.join(DATA, "mep_model.ifc")],
    "7.6": [o("purged_model.ifc")], "7.7": [o("template.ifc")], "7.8": [o("tb01_issue.ifc")],
}
# the later files must still pass the earlier exercises (the model is cumulative)
LATER = {"tb01_s4.ifc": ["1.1", "1.2", "1.3", "2.1", "2.3", "2.4", "2.5", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6"],
         "tb01_issue.ifc": ["4.1", "4.2", "4.3", "3.6"]}


def main():
    bad = 0
    for eid in sorted(RUNS, key=lambda e: [int(x) for x in e.split(".")]):
        files = RUNS[eid]
        if not all(os.path.exists(f) for f in files):
            print(f"{eid:5} MISSING  {[os.path.basename(f) for f in files if not os.path.exists(f)]}")
            bad += 1
            continue
        res = REGISTRY[eid]["fn"](*files)
        ok, n = res.score()
        print(f"{eid:5} {'PASS' if res.passed else 'FAIL'}  {ok}/{n}  {os.path.basename(files[0])}")
        for it in res.items:
            if not it.ok:
                print(f"        FAIL {it.text}: {it.hint}")
        bad += not res.passed
    for fname, eids in LATER.items():
        if os.path.exists(o(fname)):
            for eid in eids:
                files = [o(fname)] + RUNS[eid][1:]
                res = REGISTRY[eid]["fn"](*files)
                if not res.passed:
                    print(f"{eid:5} FAIL on {fname}: {[i.text for i in res.items if not i.ok]}")
                    bad += 1
    print("all passed" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
