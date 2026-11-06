"""Draw the TB-01 brief drawings (SVG) from the brief data, and a few example outputs for the tests.

Usage:  python tools/build_brief.py
Writes: brief/drawings/*.svg and tests/fixtures/*
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "checker"))
from bimcheck import spec  # noqa: E402

INK, GRID, CUT, NOTE = "#1d1d1b", "#c0392b", "#2b2b2b", "#555"
FONT = 'font-family="Helvetica, Arial, sans-serif"'


class SVG:
    def __init__(self, w, h, title):
        self.w, self.h, self.items = w, h, []
        self.items.append(f'<title>{title}</title>')

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, size=11, anchor="middle", color=INK, weight="normal"):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" '
                 f'font-weight="{weight}" {FONT}>{s}</text>')

    def line(self, x0, y0, x1, y1, color=INK, w=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{color}" stroke-width="{w}"{d}/>')

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def circle(self, x, y, r, color=INK):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="white" stroke="{color}" stroke-width="1"/>')

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = "\n".join(self.items)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                     f'viewBox="0 0 {self.w} {self.h}">\n<rect width="100%" height="100%" fill="white"/>\n{body}\n</svg>\n')
        return path


def dim(s, x0, y0, x1, y1, label, off=0, vertical=False):
    if vertical:
        s.line(x0 + off, y0, x0 + off, y1, NOTE, 0.8)
        for y in (y0, y1):
            s.line(x0 + off - 4, y + 4, x0 + off + 4, y - 4, NOTE, 0.8)
        s.add(f'<text x="{x0+off-6:.1f}" y="{(y0+y1)/2:.1f}" font-size="10" text-anchor="middle" fill="{NOTE}" {FONT} '
              f'transform="rotate(-90 {x0+off-6:.1f} {(y0+y1)/2:.1f})">{label}</text>')
    else:
        s.line(x0, y0 + off, x1, y0 + off, NOTE, 0.8)
        for x in (x0, x1):
            s.line(x - 4, y0 + off + 4, x + 4, y0 + off - 4, NOTE, 0.8)
        s.text((x0 + x1) / 2, y0 + off - 4, label, 10, color=NOTE)


def plan(s, ox, oy, k, with_tags=True, title=True):
    """Level 1 framing plan. ox, oy: page position of grid A1; k: px per metre; y up."""
    X = lambda x: ox + x * k   # noqa: E731
    Y = lambda y: oy - y * k   # noqa: E731
    xs, ys = spec.GRID_X, spec.GRID_Y
    # slab outline and openings
    sl = spec.SLAB
    s.rect(X(sl["x0"]), Y(sl["y1"]), (sl["x1"] - sl["x0"]) * k, (sl["y1"] - sl["y0"]) * k, stroke=INK, sw=1.2)
    for name, (x0, y0, x1, y1) in sl["openings"].items():
        s.rect(X(x0), Y(y1), (x1 - x0) * k, (y1 - y0) * k, stroke=INK, sw=0.8)
        s.line(X(x0), Y(y0), X(x1), Y(y1), INK, 0.6)
        s.line(X(x0), Y(y1), X(x1), Y(y0), INK, 0.6)
        s.text(X((x0 + x1) / 2), Y((y0 + y1) / 2) + 14, "OPENING" if name == "core" else "STAIR OPENING", 8, color=NOTE)
    # grids
    for tag, x in xs.items():
        s.line(X(x), Y(max(ys.values()) + 1.6), X(x), Y(min(ys.values()) - 1.6), GRID, 0.7, "12 4 2 4")
        s.circle(X(x), Y(max(ys.values()) + 2.2), 10, GRID)
        s.text(X(x), Y(max(ys.values()) + 2.2) + 4, tag, 11, color=GRID)
    for tag, y in ys.items():
        s.line(X(min(xs.values()) - 1.6), Y(y), X(max(xs.values()) + 1.6), Y(y), GRID, 0.7, "12 4 2 4")
        s.circle(X(min(xs.values()) - 2.2), Y(y), 10, GRID)
        s.text(X(min(xs.values()) - 2.2), Y(y) + 4, tag, 11, color=GRID)
    # beams (downstands, dashed), columns, core walls
    for mark, (x0, y0, x1, y1) in spec.beams().items():
        s.rect(X(x0), Y(y1), (x1 - x0) * k, (y1 - y0) * k, stroke=CUT, sw=0.8, dash="4 3")
    h = spec.COLUMN["size"] / 2
    for mark, (x, y) in spec.column_marks().items():
        s.rect(X(x - h), Y(y + h), 2 * h * k, 2 * h * k, fill="#9a9a9a", stroke=INK)
        if with_tags:
            s.text(X(x) + 16, Y(y) - 9, mark, 8, anchor="start")
    for name, (x0, y0, x1, y1) in spec.core_walls().items():
        s.rect(X(x0), Y(y1), (x1 - x0) * k, (y1 - y0) * k, fill="#9a9a9a", stroke=INK)
    # dimensions
    top = Y(max(ys.values())) - 2.9 * k
    xv = sorted(xs.values())
    for a, b in zip(xv, xv[1:]):
        dim(s, X(a), top, X(b), top, f"{int((b - a) * 1000)}")
    dim(s, X(xv[0]), top - 22, X(xv[-1]), top - 22, f"{int((xv[-1] - xv[0]) * 1000)}")
    left = X(min(xs.values())) - 3.0 * k
    yv = sorted(ys.values())
    for a, b in zip(yv, yv[1:]):
        dim(s, left, Y(a), left, Y(b), f"{int((b - a) * 1000)}", vertical=True)
    dim(s, left - 22, Y(yv[0]), left - 22, Y(yv[-1]), f"{int((yv[-1] - yv[0]) * 1000)}", vertical=True)
    if title:
        s.text(X(9), Y(-2.6), "LEVEL 1 FRAMING PLAN", 13, weight="bold")
        s.text(X(9), Y(-2.6) + 15, "Slab 250 mm, top +3.600. Beams 300 x 350 downstand (dashed). Columns 400 x 400.", 9, color=NOTE)


def section(s, ox, oy, k):
    """Section through grid 2, looking north."""
    X = lambda x: ox + x * k   # noqa: E731
    Z = lambda z: oy - z * k   # noqa: E731
    y2 = spec.GRID_Y["2"]
    for name, z in spec.STOREYS[:3] + [spec.STOREYS[2]]:
        pass
    for name, z in spec.STOREYS[:3]:
        s.line(X(-2.5), Z(z), X(20.5), Z(z), NOTE, 0.6, "6 3")
        s.text(X(20.7), Z(z) - 3, name, 10, anchor="start")
        s.text(X(20.7), Z(z) + 10, f"{z:+.3f}", 9, anchor="start", color=NOTE)
    sl = spec.SLAB
    s.rect(X(sl["x0"]), Z(sl["z1"]), (sl["x1"] - sl["x0"]) * k, spec.SLAB_T * k, fill="#bdbdbd")
    h = spec.COLUMN["size"] / 2
    f = spec.FOOTING
    for tag, x in spec.GRID_X.items():
        s.rect(X(x - h), Z(spec.COLUMN["z1"]), 2 * h * k, spec.COLUMN["z1"] * k, fill="#bdbdbd")
        s.rect(X(x - f["size"] / 2), Z(f["z1"]), f["size"] * k, f["t"] * k, fill="#d6d6d6")
        s.line(X(x), Z(4.6), X(x), Z(-1.6), GRID, 0.7, "12 4 2 4")
        s.circle(X(x), Z(5.2), 10, GRID)
        s.text(X(x), Z(5.2) + 4, tag, 11, color=GRID)
    for mark, (x0, y0, x1, y1) in spec.beams().items():
        if abs((y0 + y1) / 2 - y2) < 0.01:
            s.rect(X(x0), Z(spec.BEAM["z1"]), (x1 - x0) * k, spec.BEAM["h"] * k, fill="#bdbdbd")
    s.text(X(9), Z(-2.4), "SECTION 2-2 (THROUGH GRID 2)", 13, weight="bold")


def footing_detail(s, ox, oy, k):
    f, R = spec.FOOTING, spec.REBAR["footing"]
    X = lambda x: ox + x * k   # noqa: E731
    Z = lambda z: oy - z * k   # noqa: E731
    s.rect(X(-0.9), Z(f["z1"]), 1.8 * k, f["t"] * k, fill="#e6e6e6")
    s.rect(X(-0.2), Z(0.6), 0.4 * k, (0.6 - f["z1"]) * k, fill="#e6e6e6")
    n = int((f["size"] - 2 * R["cover"] - R["d"]) / R["s"]) + 1
    first = -0.9 + R["cover"] + R["d"] / 2
    zb = f["z0"] + R["cover"] + R["d"] / 2
    s.line(X(-0.9 + R["cover"]), Z(zb + R["d"]), X(0.9 - R["cover"]), Z(zb + R["d"]), INK, 2)
    for i in range(n):
        s.add(f'<circle cx="{X(first + i * R["s"]):.1f}" cy="{Z(zb):.1f}" r="2.6" fill="{INK}"/>')
    s.text(X(1.05), Z(-0.85), "C25/30, exposure XC2", 10, anchor="start")
    s.text(X(1.05), Z(-0.85) + 14, f"Bottom mesh Ø16 @ 150 each way, A500", 10, anchor="start")
    s.text(X(1.05), Z(-0.85) + 28, "50 mm bottom cover", 10, anchor="start")
    s.text(X(0), Z(-1.55), spec.DETAIL_TITLE, 12, weight="bold")


def write_brief_drawings():
    out = os.path.join(ROOT, "brief", "drawings")
    s = SVG(1100, 820, "TB-01 brief: Level 1 framing plan")
    plan(s, 180, 640, 36)
    s.save(os.path.join(out, "TB-01_brief_level1_framing_plan.svg"))
    s = SVG(1100, 520, "TB-01 brief: section through grid 2")
    section(s, 160, 330, 40)
    s.save(os.path.join(out, "TB-01_brief_section_grid2.svg"))
    s = SVG(900, 520, "TB-01 brief: foundation plan")
    k, ox, oy = 30, 140, 470
    X = lambda x: ox + x * k   # noqa: E731
    Y = lambda y: oy - y * k   # noqa: E731
    f, c = spec.FOOTING, spec.PILE_CAP
    for tag, x in spec.GRID_X.items():
        s.line(X(x), Y(15.6), X(x), Y(-1.6), GRID, 0.7, "12 4 2 4")
        s.circle(X(x), Y(16.2), 10, GRID)
        s.text(X(x), Y(16.2) + 4, tag, 11, color=GRID)
    for tag, y in spec.GRID_Y.items():
        s.line(X(-1.6), Y(y), X(19.6), Y(y), GRID, 0.7, "12 4 2 4")
        s.circle(X(-2.2), Y(y), 10, GRID)
        s.text(X(-2.2), Y(y) + 4, tag, 11, color=GRID)
    for mark, (x, y) in spec.column_marks().items():
        s.rect(X(x - 0.9), Y(y + 0.9), 1.8 * k, 1.8 * k, fill="#e6e6e6")
        s.text(X(x), Y(y) - 30, mark.replace("C-", "F-"), 8)
    s.rect(X(c["cx"] - 2), Y(c["cy"] + 2), 4 * k, 4 * k, fill="#e6e6e6")
    for (x, y) in spec.pile_centres():
        s.add(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{0.3*k:.1f}" fill="white" stroke="{INK}"/>')
    s.text(X(c["cx"]), Y(c["cy"]) + 4, "PC-1", 9)
    s.text(450, 30, "FOUNDATION PLAN: pads 1800 x 1800 x 600 (top -0.600); pile cap 4000 x 4000 x 1000 (top -0.600);"
                    " 4 piles Ø600, 12 m long", 10)
    s.save(os.path.join(out, "TB-01_brief_foundation_plan.svg"))
    return out


def write_fixtures():
    out = os.path.join(ROOT, "tests", "fixtures")
    s = SVG(1100, 820, "Level 1 framing plan")
    plan(s, 180, 640, 36)
    s.save(os.path.join(out, "plan.svg"))
    s = SVG(1100, 520, "Section")
    section(s, 160, 330, 40)
    s.save(os.path.join(out, "section.svg"))
    s = SVG(900, 520, "Detail")
    footing_detail(s, 300, 120, 160)
    s.save(os.path.join(out, "detail.svg"))
    # sheet: border, plan, title block, revisions
    s = SVG(1189, 841, "Sheet S-101")
    s.rect(20, 20, 1149, 801, sw=1.5)
    plan(s, 200, 640, 34)
    tb = 900
    s.rect(tb, 640, 269, 181)
    rows = [("PROJECT", spec.PROJECT["project_name"]), ("SHEET", spec.SHEET["number"]),
            ("TITLE", spec.SHEET["title"]), ("SCALE", spec.SHEET["scale"] + " @ A1"), ("REV", "B")]
    for i, (a, b) in enumerate(rows):
        s.text(tb + 8, 660 + i * 18, a, 8, anchor="start", color=NOTE)
        s.text(tb + 70, 660 + i * 18, b, 10, anchor="start")
    s.rect(tb, 520, 269, 110)
    s.text(tb + 8, 538, "REV   DATE         DESCRIPTION", 9, anchor="start", weight="bold")
    for i, ((rev, desc), date) in enumerate(zip(spec.SHEET["revisions"], ["2026-11-02", "2026-11-09"])):
        s.text(tb + 8, 556 + i * 16, f"{rev}     {date}   {desc}", 9, anchor="start")
    s.save(os.path.join(out, "sheet.svg"))
    return out


if __name__ == "__main__":
    print(write_brief_drawings())
    print(write_fixtures())
