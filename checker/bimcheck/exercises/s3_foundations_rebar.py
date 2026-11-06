"""Section 3: stair, footings, piles, reinforcement, materials, groups."""
import math

from .. import spec
from ..core import Model, Result, norm, same, fmt, match_by_position, has_material, plan_center, predefined_type
from . import exercise
from .s2_structure import _in_storey


@exercise("3.1", "Stair from Level 0 to Level 1")
def ex_3_1(path):
    m = Model(path)
    r = Result("3.1", "Stair from Level 0 to Level 1")
    st = spec.STAIR
    parts = [e for e in m.by_type("IfcStair") + m.by_type("IfcStairFlight") if m.bbox(e) is not None]
    r.check(parts, "The model contains a stair (IfcStair or IfcStairFlight)", "none found")
    if not parts:
        return r
    bbs = [m.bbox(e) for e in parts]
    x0, y0, z0 = min(b[0] for b in bbs), min(b[1] for b in bbs), min(b[2] for b in bbs)
    x1, y1, z1 = max(b[3] for b in bbs), max(b[4] for b in bbs), max(b[5] for b in bbs)
    r.check(abs(x0 - st["x0"]) <= 0.05 and abs(x1 - st["x1"]) <= 0.05,
            f"Stair width {st['x1']-st['x0']:.2f} m between x {st['x0']} and {st['x1']}", f"found x {fmt(x0)} to {fmt(x1)}")
    r.check(abs(y0 - st["y0"]) <= 0.05 and st["y1"] - 0.15 <= y1 <= 6.4 + 0.01,
            f"Stair starts at y {st['y0']} and lands inside the slab opening (y up to 6.4)", f"found y {fmt(y0)} to {fmt(y1)}")
    n = h = None
    for e in parts:
        n = n or m.find_prop(e, "NumberOfRiser") or m.find_prop(e, "NumberOfRisers")
        h = h or m.find_prop(e, "RiserHeight")
    top_ok = abs(z1 - st["z1"]) <= 0.03
    if not top_ok and n is not None and int(n) == st["risers"]:
        # Some programs (FreeCAD's Stairs tool) end the flight at its last tread: the last riser is the
        # slab edge. Accepted only when the model says it has the full riser count.
        top_ok = abs(z1 - (st["z1"] - (st["z1"] - st["z0"]) / int(n))) <= 0.03
    r.check(top_ok, f"Stair rises to Level 1 ({st['z1']:+.3f})", f"top found at {fmt(z1)}")
    r.check(z0 >= -0.30 and z0 <= 0.05, "Stair starts at Level 0", f"bottom found at {fmt(z0)}")
    if n is not None:
        r.check(int(n) == st["risers"], f"{st['risers']} risers", f"found {n}")
    if h is not None:
        r.check(abs(float(h) * (m.scale if float(h) > 1 else 1) - st["riser"]) <= 0.005,
                f"Riser height {int(st['riser']*1000)} mm", f"found {h}")
    if n is None and h is None:
        r.check(True, "Riser count not stored in the model (optional); the rise was checked from the geometry")
    r.check(any(_in_storey(m, e, "Level 0") for e in parts), "Stair belongs to Level 0", "")
    return r


@exercise("3.2", "Pad footings")
def ex_3_2(path):
    m = Model(path)
    r = Result("3.2", "Pad footings")
    f = spec.FOOTING
    pads = [e for e in m.elements("IfcFooting") if m.bbox(e) is not None
            and abs((m.bbox(e)[3] - m.bbox(e)[0]) - f["size"]) < 0.3]
    marks = {k.replace("C-", "F-"): v for k, v in spec.column_marks().items()}
    r.check(len(pads) == len(marks), f"{len(marks)} pad footings", f"found {len(pads)}")
    found = match_by_position(m, pads, marks)
    missing = [k for k, v in found.items() if v is None]
    r.check(not missing, "A footing centred under every column", f"missing: {missing}")
    bad, bad_type, bad_name = [], [], []
    for mark, el in found.items():
        if el is None:
            continue
        bb = m.bbox(el)
        if not (same(bb[3] - bb[0], f["size"]) and same(bb[4] - bb[1], f["size"]) and same(bb[2], f["z0"]) and same(bb[5], f["z1"])):
            bad.append(f"{mark}: {fmt(bb[3]-bb[0])}x{fmt(bb[4]-bb[1])}, z {fmt(bb[2])} to {fmt(bb[5])}")
        if predefined_type(el) != "PAD_FOOTING":
            bad_type.append(mark)
        if norm(el.Name) != norm(mark):
            bad_name.append(f"{mark} named '{el.Name}'")
    r.check(not bad, f"Footings {f['size']} x {f['size']} x {f['t']} m, top at {f['z1']:+.3f}", "; ".join(bad[:4]))
    r.check(not bad_type, "Footing type is PAD_FOOTING", f"not set on: {bad_type[:6]}")
    r.check(not bad_name, "Footings are named F-A1 ... F-D3", "; ".join(bad_name[:6]))
    r.check(all(_in_storey(m, e, "Foundation") for e in found.values() if e is not None),
            "Footings belong to the Foundation level", "")
    return r


@exercise("3.3", "Pile cap and piles under the core")
def ex_3_3(path):
    m = Model(path)
    r = Result("3.3", "Pile cap and piles under the core")
    c, p = spec.PILE_CAP, spec.PILES
    caps = [e for e in m.elements("IfcFooting") if m.bbox(e) is not None
            and abs((m.bbox(e)[3] - m.bbox(e)[0]) - c["size"]) < 0.3]
    r.check(len(caps) == 1, "One pile cap", f"found {len(caps)}")
    if caps:
        bb = m.bbox(caps[0])
        h = c["size"] / 2
        ok = all(abs(a - t) <= 0.02 for a, t in zip(bb, (c["cx"] - h, c["cy"] - h, c["z0"], c["cx"] + h, c["cy"] + h, c["z1"])))
        r.check(ok, f"Pile cap {c['size']} x {c['size']} x {c['t']} m centred on the core, top at {c['z1']:+.3f}",
                f"found x {fmt(bb[0])}-{fmt(bb[3])}, y {fmt(bb[1])}-{fmt(bb[4])}, z {fmt(bb[2])}-{fmt(bb[5])}")
        r.check(predefined_type(caps[0]) == "PILE_CAP", "Pile cap type is PILE_CAP",
                f"found {predefined_type(caps[0])}")
    piles = [e for e in m.elements("IfcPile") if m.bbox(e) is not None]
    r.check(len(piles) == 4, "Four piles (IfcPile)", f"found {len(piles)}")
    targets = {f"P{i+1}": xy for i, xy in enumerate(spec.pile_centres())}
    found = match_by_position(m, piles, targets)
    r.check(all(found.values()), f"Piles at {p['offset']} m each way from the core centre",
            f"missing at: {[targets[k] for k, v in found.items() if v is None]}")
    bad = []
    for k, el in found.items():
        if el is None:
            continue
        bb = m.bbox(el)
        if not (same(bb[3] - bb[0], p["d"]) and same(bb[5], c["z0"]) and same(bb[5] - bb[2], p["length"], 0.02)):
            bad.append(f"{k}: diameter {fmt(bb[3]-bb[0])}, top {fmt(bb[5])}, length {fmt(bb[5]-bb[2])}")
    r.check(not bad, f"Piles {int(p['d']*1000)} mm diameter, {p['length']:.0f} m long, from the underside of the cap",
            "; ".join(bad))
    r.check(all(_in_storey(m, e, "Foundation") for e in piles + caps), "Pile cap and piles belong to the Foundation level", "")
    return r


def _host_bars(m, host_bb, bars):
    """All bar pieces whose centre lies inside the host's plan outline (and within its height + 1 m)."""
    out = []
    for b in bars:
        for bb in m.components(b):
            cx, cy = plan_center(bb)
            cz = (bb[2] + bb[5]) / 2
            if host_bb[0] - 0.01 <= cx <= host_bb[3] + 0.01 and host_bb[1] - 0.01 <= cy <= host_bb[4] + 0.01 \
                    and host_bb[2] - 1.0 <= cz <= host_bb[5] + 1.0:
                out.append(bb)
    return out


@exercise("3.4", "Reinforcement: column C-A1 and footing F-A1")
def ex_3_4(path):
    m = Model(path)
    r = Result("3.4", "Reinforcement: column C-A1 and footing F-A1")
    R = spec.REBAR
    bars = m.by_type("IfcReinforcingBar")
    r.check(bars, "The model contains reinforcing bars (IfcReinforcingBar)", "none found")
    if not bars:
        return r
    cols = match_by_position(m, [e for e in m.elements("IfcColumn") if m.bbox(e) is not None and m.bbox(e)[2] < 1],
                             {"C-A1": spec.column_marks()["C-A1"]})
    col = cols["C-A1"]
    rc = R["column"]
    if r.check(col is not None, "Column C-A1 found", "missing"):
        cb = m.bbox(col)
        pieces = _host_bars(m, cb, bars)
        longs = [b for b in pieces if (b[5] - b[2]) > 2.0 and max(b[3] - b[0], b[4] - b[1]) < 0.05]
        links = [b for b in pieces if (b[5] - b[2]) < 0.06 and min(b[3] - b[0], b[4] - b[1]) > 0.2]
        r.check(len(longs) == rc["long_n"], f"{rc['long_n']} vertical bars in C-A1", f"found {len(longs)}")
        if longs:
            d = sum(max(b[3] - b[0], b[4] - b[1]) for b in longs) / len(longs)
            r.check(abs(d - rc["long_d"]) <= 0.0015, f"Vertical bars Ø{int(rc['long_d']*1000)}", f"found Ø{d*1000:.1f}")
            want = rc["cover"] + rc["link_d"]
            gaps = [min(b[0] - cb[0], cb[3] - b[3], b[1] - cb[1], cb[4] - b[4]) for b in longs]
            r.check(all(abs(g - want) <= 0.004 for g in gaps),
                    f"Vertical bars {want*1000:.0f} mm from the column faces ({int(rc['cover']*1000)} cover + Ø{int(rc['link_d']*1000)} link)",
                    f"found {[round(g*1000) for g in gaps]} mm")
        span = (cb[5] - cb[2]) - 2 * 0.05
        n_expect = int(span / rc["link_s"]) + 1
        r.check(abs(len(links) - n_expect) <= 2, f"About {n_expect} links at {int(rc['link_s']*1000)} mm centres",
                f"found {len(links)}")
        if links:
            gaps = [min(b[0] - cb[0], cb[3] - b[3], b[1] - cb[1], cb[4] - b[4]) for b in links]
            r.check(all(abs(g - rc["cover"]) <= 0.004 for g in gaps), f"Links at {int(rc['cover']*1000)} mm cover",
                    f"found {sorted(set(round(g*1000) for g in gaps))} mm")
    foots = match_by_position(m, [e for e in m.elements("IfcFooting") if m.bbox(e) is not None],
                              {"F-A1": spec.column_marks()["C-A1"]})
    ft = foots["F-A1"]
    rf = R["footing"]
    if r.check(ft is not None, "Footing F-A1 found", "missing"):
        fb = m.bbox(ft)
        pieces = [b for b in _host_bars(m, fb, bars) if b[2] < fb[5] and b[5] > fb[2] and b[5] - b[2] < 0.05]
        xb = [b for b in pieces if (b[3] - b[0]) > 1.2]
        yb = [b for b in pieces if (b[4] - b[1]) > 1.2]
        n_expect = int((spec.FOOTING["size"] - 2 * rf["cover"] - rf["d"]) / rf["s"]) + 1
        r.check(abs(len(xb) - n_expect) <= 1 and abs(len(yb) - n_expect) <= 1,
                f"Bottom mesh: about {n_expect} bars each way at {int(rf['s']*1000)} mm",
                f"found {len(xb)} along X and {len(yb)} along Y")
        if pieces:
            d = sum(b[5] - b[2] for b in pieces) / len(pieces)
            r.check(abs(d - rf["d"]) <= 0.0015, f"Mesh bars Ø{int(rf['d']*1000)}", f"found Ø{d*1000:.1f}")
            low = min(b[2] for b in pieces) - fb[2]
            r.check(abs(low - rf["cover"]) <= 0.004, f"Bottom cover {int(rf['cover']*1000)} mm",
                    f"found {low*1000:.0f} mm")
    mats = [b for b in bars if not has_material(m.materials(b), R["steel"])]
    r.check(not mats, f"Bars have the material {R['steel']}", f"{len(mats)} bar object(s) without it")
    return r


def _concrete_targets():
    return {"IfcColumn": spec.COLUMN, "IfcBeam": spec.BEAM, "IfcSlab": spec.SLAB, "IfcWall": spec.CORE,
            "IfcPile": spec.PILES}


@exercise("3.5", "Materials and concrete data")
def ex_3_5(path):
    m = Model(path)
    r = Result("3.5", "Materials and concrete data")
    groups = dict(_concrete_targets())
    for cls, data in groups.items():
        els = [e for e in m.elements(cls) if m.bbox(e) is not None]
        _check_concrete(m, r, cls, els, data)
    feet = [e for e in m.elements("IfcFooting") if m.bbox(e) is not None]
    _check_concrete(m, r, "IfcFooting", feet, spec.FOOTING)
    return r


def _check_concrete(m, r, cls, els, data):
    if not els:
        r.check(False, f"{cls[3:]}s present", "none found")
        return
    no_mat = [e.Name for e in els if not has_material(m.materials(e), data["concrete"])]
    r.check(not no_mat, f"{cls[3:]}s: material {data['concrete']}", f"{len(no_mat)} without it, e.g. {no_mat[:3]}")
    bad = []
    for e in els:
        ps = m.psets(e).get("Pset_ConcreteElementGeneral", {})
        if norm(ps.get("StrengthClass")) != norm(data["concrete"]) or norm(ps.get("ExposureClass")) != norm(data["exposure"]):
            bad.append(e.Name)
    r.check(not bad, f"{cls[3:]}s: Pset_ConcreteElementGeneral StrengthClass {data['concrete']}, ExposureClass {data['exposure']}",
            f"{len(bad)} missing or wrong, e.g. {bad[:3]}")


@exercise("3.6", "Selection groups")
def ex_3_6(path):
    m = Model(path)
    r = Result("3.6", "Selection groups")
    groups = {norm(g.Name): g for g in m.by_type("IfcGroup") if not g.is_a("IfcSystem") or g.is_a() == "IfcGroup"}
    for name, cls in spec.GROUPS.items():
        g = groups.get(norm(name))
        if not r.check(g is not None, f"Group '{name}' exists", f"groups found: {[x.Name for x in groups.values()]}"):
            continue
        members = set()
        for rel in g.IsGroupedBy or []:
            members |= {o.id() for o in rel.RelatedObjects}
        if cls == "IfcColumn":
            want = {e.id() for e in m.elements("IfcColumn") if m.bbox(e) is not None and m.bbox(e)[2] < 1}
        else:
            want = {e.id() for e in m.elements(cls)}
        r.check(want and members == want, f"'{name}' holds exactly the {len(want)} {cls[3:].lower()}s",
                f"{len(members & want)} of {len(want)} in the group, {len(members - want)} other element(s)")
    return r
