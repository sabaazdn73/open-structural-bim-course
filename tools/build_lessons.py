"""Assemble the lessons: common text (tools/lessons_common.py) + FreeCAD and Bonsai steps (course/_steps/).

Usage:  python tools/build_lessons.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from lessons_common import L, SECTIONS  # noqa: E402

STEPS = os.path.join(ROOT, "course", "_steps")


def key(eid):
    return [int(x) for x in eid.split(".")]


def steps(tool, eid):
    p = os.path.join(STEPS, tool, f"{eid}.md")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    return "_Steps for this program are not written yet. Contributions are welcome (see CONTRIBUTING.md)._"


def lesson_path(eid):
    sec = SECTIONS[eid.split(".")[0]][0]
    return os.path.join("course", sec, L[eid]["slug"] + ".md")


def main():
    ids = sorted(L, key=key)
    for i, eid in enumerate(ids):
        d = L[eid]
        prev_ = ids[i - 1] if i else None
        next_ = ids[i + 1] if i + 1 < len(ids) else None
        rel = lambda e: os.path.relpath(lesson_path(e), os.path.dirname(lesson_path(eid)))  # noqa: E731
        nav = []
        if prev_:
            nav.append(f"[← {prev_} {L[prev_]['title']}]({rel(prev_)})")
        nav.append("[Course index](../README.md)")
        if next_:
            nav.append(f"[{next_} {L[next_]['title']} →]({rel(next_)})")
        md = [f"# Exercise {eid}: {d['title']}", "", f"**Goal.** {d['goal']}", "", "## What you build", ""]
        md += [f"- {b}" for b in d["build"]]
        md += ["", "All numbers come from the [project brief](../../brief/README.md) and its "
                   "[drawings](../../brief/drawings/).", "",
               "## In FreeCAD", "", steps("freecad", eid), "",
               "## In Bonsai", "", steps("bonsai", eid), "",
               "## Check your work", "",
               f"Save or export your work as `{d['save']}`, then run:", "", "```", d["check"], "```", "",
               "Every line should say PASS. A FAIL line tells you what was expected and what was found.", "",
               "## Why this matters", "", d["why"], "", "---", "", " · ".join(nav), ""]
        out = os.path.join(ROOT, lesson_path(eid))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(md))
    idx = ["# Course index", "",
           "Work through the exercises in order: each one builds on the model from the one before. "
           "Start with [Getting started](00_getting_started.md).", ""]
    for s, (folder, title) in SECTIONS.items():
        idx += [f"## {s}. {title}", ""]
        for eid in [e for e in ids if e.split(".")[0] == s]:
            idx.append(f"- [{eid} {L[eid]['title']}]({os.path.relpath(lesson_path(eid), 'course')})")
        idx.append("")
    with open(os.path.join(ROOT, "course", "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(idx))
    print(f"{len(ids)} lessons written")


if __name__ == "__main__":
    main()
