"""Build the data of the practice panel (web/) from the course sources.

The panel shows the same lessons, brief and checker as the repository: this script turns the lesson
text (tools/lessons_common.py, course/_steps/), the brief and the getting-started page into
web/data/course.json, packs the checker into web/data/bimcheck.json, and copies the datasets,
drawings and reference answers into web/files/.

Usage:  python tools/build_web.py        (needs: python -m pip install markdown-it-py ./checker)
"""
import json
import os
import posixpath
import re
import shutil
import sys

from markdown_it import MarkdownIt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "checker"))
from lessons_common import L, SECTIONS  # noqa: E402
from bimcheck.exercises import REGISTRY  # noqa: E402

WEB = os.path.join(ROOT, "web")
MD = MarkdownIt("commonmark", {"html": False}).enable("table")   # CommonMark, as GitHub renders the lessons
REPO = "https://github.com/sabaazdn73/open-structural-bim-course/blob/main/"
TREE = "https://github.com/sabaazdn73/open-structural-bim-course/tree/main/"

# Files the panel provides itself when an exercise needs a course file next to the student's own.
COURSE_INPUTS = {"architect_model.ifc": "files/architect_model.ifc", "mep_model.ifc": "files/mep_model.ifc"}

# What each input slot asks for, in words.
INPUT_LABELS = {
    "model.ifc": "Your model (.ifc)",
    "architect_model.ifc": "The architect's model (.ifc)",
    "plan.svg|pdf": "Your framing plan (.svg or .pdf)",
    "section.svg|pdf": "Your section (.svg or .pdf)",
    "detail.svg|pdf": "Your detail (.svg or .pdf)",
    "schedule.csv": "Your schedule (.csv)",
    "sheet.svg|pdf": "Your sheet (.svg or .pdf)",
    "renovation_model.ifc": "Your renovation model (.ifc)",
    "option_A.ifc": "Option A (.ifc)",
    "option_B.ifc": "Option B (.ifc)",
    "fixed_model.ifc": "Your fixed model (.ifc)",
    "structure.ifc": "Your structure with openings (.ifc)",
    "mep_model.ifc": "The MEP model (.ifc)",
    "purged_model.ifc": "Your purged model (.ifc)",
    "template.ifc": "Your template (.ifc)",
}

# Reference answers the panel can run a check on ("see a passing example"); the same files as tests/.
_R = "files/reference/"
REFERENCE = {e: [_R + "tb01_s1.ifc"] for e in ("1.1", "1.2", "1.3")}
REFERENCE.update({e: [_R + "tb01_s2.ifc"] for e in ("2.1", "2.3", "2.4", "2.5")})
REFERENCE.update({e: [_R + "tb01_s3.ifc"] for e in ("3.1", "3.2", "3.3", "3.4", "3.5", "3.6")})
REFERENCE.update({e: [_R + "tb01_s4.ifc"] for e in ("4.1", "4.2", "4.3")})
REFERENCE.update({
    "2.2": [_R + "tb01_s2.ifc", "files/architect_model.ifc"],
    "5.1": [_R + "plan.svg"], "5.2": [_R + "section.svg"], "5.3": [_R + "detail.svg"],
    "5.5": [_R + "tb01_s2.ifc", _R + "plan.svg"], "6.1": [_R + "sheet.svg"], "6.2": [_R + "sheet.svg"],
    "7.1": [_R + "renovation_answer.ifc"], "7.2": [_R + "option_A.ifc", _R + "option_B.ifc"],
    "7.4": [_R + "fixed_model.ifc"], "7.5": [_R + "structure_with_openings.ifc", "files/mep_model.ifc"],
    "7.6": [_R + "purged_model.ifc"], "7.7": [_R + "template.ifc"], "7.8": [_R + "tb01_full.ifc"],
})

DATASETS = [
    ("architect_model.ifc", "The architect's model of TB-01: walls to trace in exercise 2.2."),
    ("column_types.csv", "Column type catalogue for exercise 4.2."),
    ("renovation_model.ifc", "An existing building to phase in exercise 7.1."),
    ("unhealthy_model.ifc", "A model full of problems to fix in exercise 7.4."),
    ("mep_model.ifc", "Ducts and pipes to check for clashes in exercise 7.5."),
    ("bloated_model.ifc", "A model with unused data to purge in exercise 7.6."),
]


def key(eid):
    return [int(x) for x in eid.split(".")]


def md(text, src):
    """Markdown to HTML, with repository links made to work from the panel."""
    def link(m):
        label, target = m.group(1), m.group(2)
        if re.match(r"[a-z]+:", target) or target.startswith("#"):
            return m.group(0)
        path = posixpath.normpath(posixpath.join(posixpath.dirname(src), target))
        if path == "brief/README.md":
            return f"[{label}](#/brief)"
        if path.startswith("brief/drawings/") and path.endswith(".svg"):
            return f"[{label}](files/drawings/{posixpath.basename(path)})"
        if path.startswith("datasets/") and posixpath.basename(path) in dict(DATASETS):
            return f"[{label}](files/{posixpath.basename(path)})"
        if path.rstrip("/") == "datasets":
            return f"[{label}](#/files)"
        if path == "course/00_getting_started.md":
            return f"[{label}](#/start)"
        for eid, d in L.items():
            sec = SECTIONS[eid.split(".")[0]][0]
            if path == f"course/{sec}/{d['slug']}.md":
                return f"[{label}](#/ex/{eid})"
        base = TREE if target.endswith("/") else REPO
        return f"[{label}]({base}{path.rstrip('/')})"
    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    html = MD.render(text)
    # A dataset named in the steps (datasets/architect_model.ifc) links to its download in the panel.
    names = "|".join(re.escape(n) for n, _ in DATASETS)
    html = re.sub(rf"<code>datasets/({names})</code>", r'<a href="files/\1" download><code>datasets/\1</code></a>', html)
    html = re.sub(r'<a href="(files/[^"]+\.(?:ifc|csv))">', r'<a href="\1" download>', html)
    html = html.replace("<a href=\"http", "<a target=\"_blank\" rel=\"noopener\" href=\"http")
    # Code that spans lines must be a block, or a copied script loses its line breaks.
    for m in re.finditer(r"<code>(.*?)</code>", re.sub(r"<pre>.*?</pre>", "", html, flags=re.S), re.S):
        if "\n" in m.group(1):
            raise SystemExit(f"{src}: inline code spans lines (a code fence that did not render as a block)")
    return html


def inline(text):
    """One paragraph of lesson text, without its <p> wrapper."""
    html = md(text, "course/x.md").strip()
    if not (html.startswith("<p>") and html.endswith("</p>")) or html.count("<p>") != 1:
        raise SystemExit(f"expected one paragraph: {text[:60]}")
    return html[3:-4]


def steps(tool, eid):
    p = os.path.join(ROOT, "course", "_steps", tool, f"{eid}.md")
    if not os.path.exists(p):
        return ""
    return md(open(p, encoding="utf-8").read().strip(), f"course/_steps/{tool}/{eid}.md")


def inputs(eid):
    out = []
    for raw in REGISTRY[eid]["inputs"]:
        optional = raw.startswith("[")
        name = raw.strip("[]")
        if name == "repository_folder":
            out.append({"name": name, "kind": "folder", "label": "Your Git repository folder"})
            continue
        exts = [e for e in name.split(".")[-1].split("|")]
        out.append({"name": name, "kind": "file", "label": INPUT_LABELS.get(name, name),
                    "accept": ",".join("." + e for e in exts), "optional": optional,
                    "course_file": COURSE_INPUTS.get(name) if eid in ("2.2", "7.5") else None})
    return out


def section_md(path, heading):
    """One '## heading' section of a Markdown file."""
    text = open(path, encoding="utf-8").read()
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def build_course():
    ids = sorted(L, key=key)
    ex = {}
    for eid in ids:
        d = L[eid]
        ex[eid] = {
            "title": d["title"],
            "goal": inline(d["goal"]),
            "build": [inline(b) for b in d["build"]],
            "why": md(d["why"], "course/x.md"),
            "save": {"7.2": "option_A.ifc and option_B.ifc", "7.3": "a Git repository"}.get(eid, d["save"]),
            "check": d["check"],
            "inputs": inputs(eid),
            "reference": REFERENCE.get(eid),
            "steps": {"freecad": steps("freecad", eid), "bonsai": steps("bonsai", eid)},
        }
    gs = os.path.join(ROOT, "course", "00_getting_started.md")
    brief = open(os.path.join(ROOT, "brief", "README.md"), encoding="utf-8").read()
    return {
        "repo": "https://github.com/sabaazdn73/open-structural-bim-course",
        "sections": [{"id": s, "title": t, "exercises": [e for e in ids if e.split(".")[0] == s]}
                     for s, (_, t) in SECTIONS.items()],
        "exercises": ex,
        "need": md(section_md(gs, "What you need"), "course/00_getting_started.md"),
        "revit": md(section_md(gs, "If you know Revit"), "course/00_getting_started.md"),
        "brief": md(brief, "brief/README.md"),
        "datasets": [{"name": n, "about": a, "href": f"files/{n}"} for n, a in DATASETS],
    }


def build_checker():
    pkg = os.path.join(ROOT, "checker", "bimcheck")
    files = {}
    for dirpath, _, names in os.walk(pkg):
        if "__pycache__" in dirpath:
            continue
        for n in sorted(names):
            if n.endswith((".py", ".csv")):
                full = os.path.join(dirpath, n)
                files[os.path.relpath(full, pkg).replace(os.sep, "/")] = open(full, encoding="utf-8").read()
    return files


def copy_files():
    out = os.path.join(WEB, "files")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "drawings"))
    os.makedirs(os.path.join(out, "reference"))
    for n, _ in DATASETS:
        shutil.copy(os.path.join(ROOT, "datasets", n), os.path.join(out, n))
    for n in sorted(os.listdir(os.path.join(ROOT, "brief", "drawings"))):
        shutil.copy(os.path.join(ROOT, "brief", "drawings", n), os.path.join(out, "drawings", n))
    for n in sorted(os.listdir(os.path.join(ROOT, "solutions", "reference"))):
        if n.endswith(".ifc"):
            shutil.copy(os.path.join(ROOT, "solutions", "reference", n), os.path.join(out, "reference", n))
    for n in sorted(os.listdir(os.path.join(ROOT, "tests", "fixtures"))):
        if n.endswith(".svg"):
            shutil.copy(os.path.join(ROOT, "tests", "fixtures", n), os.path.join(out, "reference", n))


def main():
    os.makedirs(os.path.join(WEB, "data"), exist_ok=True)
    course = build_course()
    with open(os.path.join(WEB, "data", "course.json"), "w", encoding="utf-8") as fh:
        json.dump(course, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(WEB, "data", "bimcheck.json"), "w", encoding="utf-8") as fh:
        json.dump(build_checker(), fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    copy_files()
    print(f"web/data written: {len(course['exercises'])} exercises")


if __name__ == "__main__":
    main()
