"""Section 6: sheets, title block and revisions."""
import re

from .. import spec
from ..core import Result, norm
from . import exercise
from .s5_documentation import read_text


@exercise("6.1", "Sheet S-101 with a title block", inputs=("sheet.svg|pdf",))
def ex_6_1(path):
    r = Result("6.1", "Sheet S-101 with a title block")
    text = read_text(path)
    low = norm(text)
    S = spec.SHEET
    r.check(norm(S["number"]) in low, f"Sheet number {S['number']}", "not found")
    r.check(norm(S["title"]) in low, f"Sheet title '{S['title']}'", "not found")
    r.check(re.search(r"1\s*:\s*100\b", text), f"Scale {S['scale']}", "not found")
    r.check(norm(spec.PROJECT["project_name"]) in low or "tb01" in low, "Project name in the title block", "not found")
    tk = set(re.findall(r"[A-Za-z0-9\-]+", text))
    r.check(all(t in tk for t in list(spec.GRID_X) + list(spec.GRID_Y)), "The framing plan is placed on the sheet (grid bubbles visible)",
            "grid labels not found on the sheet")
    return r


@exercise("6.2", "Revisions on the sheet", inputs=("sheet.svg|pdf",))
def ex_6_2(path):
    r = Result("6.2", "Revisions on the sheet")
    text = read_text(path)
    low = norm(text)
    r.check(re.search(r"\brev", text, re.I), "A revision table or revision field is shown", "no 'Rev' text found")
    for rev, desc in spec.SHEET["revisions"]:
        r.check(norm(desc) in low, f"Revision {rev}: '{desc}'", "not found")
    r.check(re.search(r"\b20\d\d[-/.]\d{1,2}[-/.]\d{1,2}\b|\b\d{1,2}[-/.]\d{1,2}[-/.]20\d\d\b", text),
            "Revision dates shown", "no date found")
    return r
