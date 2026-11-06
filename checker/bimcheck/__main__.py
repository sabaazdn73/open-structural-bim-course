"""Command line: python -m bimcheck <exercise> <files...>   |   python -m bimcheck list"""
import sys

from .exercises import REGISTRY

GREEN, RED, DIM, END = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    color = sys.stdout.isatty() and "--no-color" not in argv
    argv = [a for a in argv if a != "--no-color"]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "list":
        for eid, ex in sorted(REGISTRY.items(), key=lambda kv: [int(x) for x in kv[0].split(".")]):
            print(f"{eid:5} {ex['title']}   [{' '.join(ex['inputs'])}]")
        return 0
    eid, files = argv[0], argv[1:]
    if eid not in REGISTRY:
        print(f"Unknown exercise '{eid}'. Run: python -m bimcheck list")
        return 2
    ex = REGISTRY[eid]
    needed = [i for i in ex["inputs"] if not i.startswith("[")]
    if len(files) < len(needed):
        print(f"Exercise {eid} needs: {' '.join(ex['inputs'])}")
        return 2
    res = ex["fn"](*files)
    g, rd, d, e = (GREEN, RED, DIM, END) if color else ("", "", "", "")
    print(f"\nExercise {res.exercise}: {res.title}\n")
    for it in res.items:
        mark = f"{g}PASS{e}" if it.ok else f"{rd}FAIL{e}"
        print(f"  {mark}  {it.text}")
        if it.hint and not it.ok:
            print(f"        {d}{it.hint}{e}")
    ok, n = res.score()
    print(f"\n  {ok} of {n} checks passed." + ("  Exercise complete." if res.passed else ""))
    return 0 if res.passed else 1


if __name__ == "__main__":
    sys.exit(main())
