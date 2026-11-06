"""Section 4: types, a type catalogue, and custom properties."""
import csv
import os

import ifcopenshell.util.element as ue

from .. import spec
from ..core import Model, Result, norm, same, fmt
from . import exercise

DATASETS = os.path.join(os.path.dirname(__file__), "..", "data")


def _occurrences(m, cls):
    els = [e for e in m.elements(cls) if m.bbox(e) is not None]
    if cls == "IfcFooting":
        els = [e for e in els if abs((m.bbox(e)[3] - m.bbox(e)[0]) - spec.FOOTING["size"]) < 0.3]
    if cls == "IfcColumn":
        els = [e for e in els if m.bbox(e)[2] < 1]
    return els


@exercise("4.1", "Types for columns, beams and footings")
def ex_4_1(path):
    m = Model(path)
    r = Result("4.1", "Types for columns, beams and footings")
    for cls, tname in spec.TYPES.items():
        types = [t for t in m.by_type(cls + "Type") if norm(t.Name) == norm(tname)]
        if not r.check(types, f"{cls}Type '{tname}' exists",
                       f"types found: {[t.Name for t in m.by_type(cls + 'Type')]}"):
            continue
        occ = _occurrences(m, cls)
        typed = [e for e in occ if ue.get_type(e) is not None and norm(ue.get_type(e).Name) == norm(tname)]
        r.check(occ and len(typed) == len(occ), f"All {len(occ)} {cls[3:].lower()}s use '{tname}'",
                f"{len(typed)} of {len(occ)} do")
    return r


def read_catalogue(path=None):
    path = path or os.path.join(DATASETS, "column_types.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        return [row for row in csv.DictReader(fh)]


@exercise("4.2", "Column type catalogue from a CSV file")
def ex_4_2(path):
    m = Model(path)
    r = Result("4.2", "Column type catalogue from a CSV file")
    rows = read_catalogue()
    types = {norm(t.Name): t for t in m.by_type("IfcColumnType")}
    for row in rows:
        t = types.get(norm(row["Name"]))
        if not r.check(t is not None, f"Column type '{row['Name']}' exists", "missing"):
            continue
        w, d = float(row["Width_mm"]) / 1000, float(row["Depth_mm"]) / 1000
        occ = [e for e in m.elements("IfcColumn") if ue.get_type(e) == t and m.bbox(e) is not None]
        if occ:
            bad = [e.Name for e in occ if not (
                (same(m.bbox(e)[3] - m.bbox(e)[0], w) and same(m.bbox(e)[4] - m.bbox(e)[1], d)) or
                (same(m.bbox(e)[3] - m.bbox(e)[0], d) and same(m.bbox(e)[4] - m.bbox(e)[1], w)))]
            r.check(not bad, f"Columns of '{row['Name']}' are {row['Width_mm']} x {row['Depth_mm']} mm",
                    f"wrong size: {bad[:4]}")
        props = {}
        for ps in ue.get_psets(t).values():
            props.update(ps)
        has_dims = any(k.lower() in ("width", "width_mm", "b") for k in props) and any(
            k.lower() in ("depth", "depth_mm", "h") for k in props)
        if not occ:
            r.check(has_dims, f"'{row['Name']}' stores its width and depth as type properties (no column uses it yet)",
                    "add Width and Depth to the type's property set, or place one column of this type")
    return r


@exercise("4.3", "Custom property set TB01_Structural")
def ex_4_3(path):
    m = Model(path)
    r = Result("4.3", f"Custom property set {spec.CUSTOM_PSET}")
    for cls, fire in spec.FIRE.items():
        els = [e for e in m.elements(cls) if m.bbox(e) is not None]
        if cls == "IfcColumn":
            els = [e for e in els if m.bbox(e)[2] < 1]
        if not r.check(els, f"{cls[3:]}s present", "none found"):
            continue
        bad_fire, bad_life = [], []
        for e in els:
            ps = m.psets(e).get(spec.CUSTOM_PSET, {})
            if norm(ps.get("FireResistance")) != norm(fire):
                bad_fire.append(e.Name)
            try:
                life = int(float(ps.get("DesignWorkingLife")))
            except (TypeError, ValueError):
                life = None
            if life != spec.DESIGN_LIFE:
                bad_life.append(e.Name)
        r.check(not bad_fire, f"{cls[3:]}s: {spec.CUSTOM_PSET}.FireResistance = {fire}",
                f"{len(bad_fire)} missing or wrong, e.g. {bad_fire[:3]}")
        r.check(not bad_life, f"{cls[3:]}s: {spec.CUSTOM_PSET}.DesignWorkingLife = {spec.DESIGN_LIFE}",
                f"{len(bad_life)} missing or wrong, e.g. {bad_life[:3]}")
    return r
