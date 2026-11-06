"""Section 5: drawings (plan, section, detail), schedules, tags.

Drawings are checked from the exported file (SVG or PDF): the checker reads the text in it.
Export text as text, not as outlines, or the checker cannot read it.
"""
import csv
import re
import xml.etree.ElementTree as ET

from .. import spec
from ..core import Model, Result, norm
from . import exercise


def _parse_svg(path):
    """Parse an SVG file. Some exporters (FreeCAD's 'Flattened SVG') use attribute prefixes such as
    freecad:skip without declaring them; declare the missing prefixes so the file can be read."""
    try:
        return ET.parse(path)
    except ET.ParseError:
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        m = re.search(r"<svg\b[^>]*>", src)
        if not m:
            raise
        declared = set(re.findall(r"xmlns:([A-Za-z_][\w.-]*)=", src))
        used = set(re.findall(r"[\s<]([A-Za-z_][\w.-]*):[A-Za-z_][\w.-]*\s*=", src)) - {"xml", "xmlns"}
        extra = "".join(f' xmlns:{p}="urn:undeclared:{p}"' for p in sorted(used - declared))
        src = src[:m.end() - 1] + extra + src[m.end() - 1:]
        return ET.ElementTree(ET.fromstring(src.encode("utf-8")))


def read_text(path):
    """All text in an SVG or PDF drawing, as one string with tokens separated by spaces."""
    p = path.lower()
    if p.endswith(".svg"):
        tree = _parse_svg(path)
        parts = []
        for el in tree.iter():
            tag = el.tag.split("}")[-1]
            if tag in ("text", "tspan", "textPath", "title"):
                if el.text:
                    parts.append(el.text)
                if el.tail and tag == "tspan":
                    parts.append(el.tail)
        return " ".join(parts)
    if p.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit("Reading PDF needs pypdf: python -m pip install pypdf (or export SVG instead)")
        return " ".join((pg.extract_text() or "") for pg in PdfReader(path).pages)
    raise SystemExit("Give an .svg or .pdf drawing")


def tokens(text):
    return set(re.findall(r"[A-Za-z0-9\-\+\./:]+", text))


def has_number(text, metres):
    """True if the text shows a length in mm (6000, 6 000) or in metres (6.00, 6,00, 6.000)."""
    mm = int(round(metres * 1000))
    pats = [rf"(?<![\d.,]){mm}(?![\d])", rf"(?<![\d.,]){mm // 1000}[  ]{mm % 1000:03d}(?![\d])",
            rf"(?<![\d]){metres:.2f}".replace(".", "[.,]"), rf"(?<![\d]){metres:.3f}".replace(".", "[.,]")]
    return any(re.search(p, text) for p in pats)


def _drawing_result(eid, title, path):
    r = Result(eid, title)
    text = read_text(path)
    r.check(text.strip(), "The drawing contains readable text", "no text found: export text as text, not as paths")
    return r, text


@exercise("5.1", "Level 1 framing plan with grids and dimensions", inputs=("plan.svg|pdf",))
def ex_5_1(path):
    r, text = _drawing_result("5.1", "Level 1 framing plan with grids and dimensions", path)
    tk = tokens(text)
    for tag in list(spec.GRID_X) + list(spec.GRID_Y):
        r.check(tag in tk, f"Grid bubble '{tag}' shown", "not found")
    r.check(len(re.findall(r"(?<![\d.,])6[  ]?000(?!\d)|(?<!\d)6[.,]00", text)) >= 3,
            "Bay dimensions along X shown (3 x 6000)", "fewer than three '6000' dimensions found")
    r.check(len(re.findall(r"(?<![\d.,])7[  ]?000(?!\d)|(?<!\d)7[.,]00", text)) >= 2,
            "Bay dimensions along Y shown (2 x 7000)", "fewer than two '7000' dimensions found")
    r.check(re.search(r"18[  ]?000|18[.,]00", text) and re.search(r"14[  ]?000|14[.,]00", text),
            "Overall dimensions shown (18000 and 14000)", "not found")
    return r


@exercise("5.2", "Section through grid 2", inputs=("section.svg|pdf",))
def ex_5_2(path):
    r, text = _drawing_result("5.2", "Section through grid 2", path)
    low = norm(text)
    for name, elev in spec.STOREYS[:3]:
        r.check(norm(name) in low, f"Level name '{name}' shown", "not found")
    r.check(re.search(r"\+?3[.,]600|\+?3[.,]60\b|3600", text), "Level 1 elevation shown (+3.600)", "not found")
    r.check(re.search(r"-1[.,]200|-1[.,]20\b|-1200", text), "Foundation level shown (-1.200)", "not found")
    tk = tokens(text)
    r.check(all(t in tk for t in spec.GRID_X), "Grid bubbles A to D shown", "not all found")
    return r


@exercise("5.3", "Detail callout with annotation", inputs=("detail.svg|pdf",))
def ex_5_3(path):
    r, text = _drawing_result("5.3", "Detail callout with annotation", path)
    r.check(norm(spec.DETAIL_TITLE) in norm(text), f"Detail title '{spec.DETAIL_TITLE}'", "not found")
    r.check(re.search(r"C\s*25\s*/\s*30", text), "Concrete class of the footing noted (C25/30)", "not found")
    r.check("A500" in text.replace(" ", ""), "Steel grade noted (A500)", "not found")
    r.check(re.search(r"(Ø|ø|T|#)?\s*16\s*@\s*150", text), "Bottom mesh noted (Ø16 @ 150)", "not found")
    r.check(re.search(r"\b50\b", text) and re.search(r"cover", text, re.I), "Cover noted (50 mm cover)", "not found")
    return r


def _class_of(row_text):
    t = row_text.lower()
    for cls in ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting", "IfcPile"):   # an IFC class name wins
        if cls.lower() in t.replace(" ", ""):
            return cls
    for key, cls in (("column", "IfcColumn"), ("beam", "IfcBeam"), ("slab", "IfcSlab"), ("wall", "IfcWall"),
                     ("footing", "IfcFooting"), ("pile cap", "IfcFooting"), ("foundation", "IfcFooting"),
                     ("pile", "IfcPile")):
        if key in t:
            return cls
    return None


def _num(s):
    s = str(s).strip().replace(" ", "").replace(" ", "")
    s = re.sub(r"(m3|m³|mm3|mm³)$", "", s)
    if re.fullmatch(r"-?\d+,\d+", s):
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def read_schedule(path):
    """Concrete volume per class from a CSV schedule (one row per element or per class)."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(fh, dialect))
    if not rows:
        return {}
    header = [h.lower() for h in rows[0]]
    vcol = next((i for i, h in enumerate(header) if "vol" in h), None)
    totals = {}
    for row in rows[1:] if vcol is not None else rows:
        cls = _class_of(" ".join(row))
        if not cls:
            continue
        vals = [_num(c) for c in row]
        v = vals[vcol] if vcol is not None and vcol < len(vals) else next((x for x in reversed(vals) if x is not None), None)
        if v is None:
            continue
        totals[cls] = totals.get(cls, 0.0) + v
    if totals and max(totals.values()) > 1e6:     # the schedule is in mm3
        totals = {k: v / 1e9 for k, v in totals.items()}
    return totals


@exercise("5.4", "Concrete quantity schedule (CSV)", inputs=("schedule.csv", "model.ifc"))
def ex_5_4(schedule, model):
    m = Model(model)
    r = Result("5.4", "Concrete quantity schedule (CSV)")
    got = read_schedule(schedule)
    r.check(got, "The schedule lists elements with a volume column", "no rows with a class and a volume were found")
    for cls in ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting", "IfcPile"):
        want = sum(m.volume(e) for e in m.elements(cls) if m.bbox(e) is not None)
        if want == 0:
            continue
        v = got.get(cls)
        r.check(v is not None and abs(v - want) <= 0.02 * want + 0.01,
                f"{cls[3:]}s: {want:.2f} m3 (from the model)", f"schedule says {v:.2f} m3" if v is not None else "missing")
    return r


@exercise("5.5", "Element marks and tags", inputs=("model.ifc", "plan.svg|pdf"))
def ex_5_5(model, plan):
    m = Model(model)
    r = Result("5.5", "Element marks and tags")
    cols = [e for e in m.elements("IfcColumn") if m.bbox(e) is not None and m.bbox(e)[2] < 1]
    marks = set(spec.column_marks())
    names = {norm(e.Name) for e in cols}
    r.check({norm(k) for k in marks} <= names, "Every column carries its mark (C-A1 ... C-D3) as its name",
            f"missing: {sorted(k for k in marks if norm(k) not in names)[:6]}")
    text = read_text(plan)
    shown = {k for k in marks if norm(k) in norm(text) or k.replace("-", "") in text.replace("-", "")}
    r.check(len(shown) == len(marks), "All 12 column tags shown on the plan",
            f"{len(shown)} shown; missing {sorted(marks - shown)[:6]}")
    return r
