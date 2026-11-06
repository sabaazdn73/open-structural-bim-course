"""Section 2: columns, core walls, slab, beams, and clean joints."""
import itertools

from .. import spec
from ..core import Model, Result, norm, same, fmt, match_by_position, raster_area, plan_center, TOL
from . import exercise


def _in_storey(m, el, name):
    c = m.container(el)
    return c is not None and norm(c.Name) == norm(name)


def check_columns(m, r):
    cols = m.elements("IfcColumn")
    marks = spec.column_marks()
    ground = [c for c in cols if m.bbox(c) is not None and m.bbox(c)[2] < 1.0]
    r.check(len(ground) == len(marks), f"{len(marks)} columns between Level 0 and Level 1",
            f"found {len(ground)}")
    found = match_by_position(m, ground, marks)
    missing = [k for k, v in found.items() if v is None]
    r.check(not missing, "One column at every grid intersection", f"missing at: {missing}")
    s, c = spec.COLUMN["size"], spec.COLUMN
    bad_size, bad_z, bad_name, bad_storey = [], [], [], []
    for mark, el in found.items():
        if el is None:
            continue
        bb = m.bbox(el)
        if not (same(bb[3] - bb[0], s) and same(bb[4] - bb[1], s)):
            bad_size.append(f"{mark} {fmt(bb[3]-bb[0])}x{fmt(bb[4]-bb[1])}")
        if not (same(bb[2], c["z0"]) and same(bb[5], c["z1"])):
            bad_z.append(f"{mark} {fmt(bb[2])} to {fmt(bb[5])}")
        if norm(el.Name) != norm(mark):
            bad_name.append(f"{mark} named '{el.Name}'")
        if not _in_storey(m, el, "Level 0"):
            bad_storey.append(mark)
    more = lambda xs: "; ".join(xs[:3]) + (f" ... ({len(xs)} columns)" if len(xs) > 3 else "")  # noqa: E731
    r.check(not bad_size, f"Columns are {int(s*1000)} x {int(s*1000)} mm", more(bad_size))
    r.check(not bad_z, f"Columns run from {c['z0']:+.3f} to the slab soffit {c['z1']:+.3f}", more(bad_z))
    r.check(not bad_name, "Columns are named by grid (C-A1 ... C-D3)", "; ".join(bad_name[:6]))
    r.check(not bad_storey, "Columns belong to Level 0", f"not in Level 0: {bad_storey}")
    return found


@exercise("2.1", "Columns")
def ex_2_1(path):
    m = Model(path)
    r = Result("2.1", "Columns")
    check_columns(m, r)
    return r


def wall_boxes(m):
    out = []
    for w in m.elements("IfcWall"):
        bb = m.bbox(w)
        if bb is not None:
            out.append((w, bb))
    return out


@exercise("2.2", "Core walls traced from the architect's model", inputs=("model.ifc", "[architect_model.ifc]"))
def ex_2_2(path, architect=None):
    m = Model(path)
    r = Result("2.2", "Core walls traced from the architect's model")
    c = spec.CORE
    walls = wall_boxes(m)
    r.check(walls, "The model contains walls (IfcWall)", "no walls found")
    if not walls:
        return r
    target = list(spec.core_walls().values())
    if architect:
        a = Model(architect)
        lb = [w for w in a.elements("IfcWall") if a.find_prop(w, "LoadBearing") in (True, "True", "TRUE")]
        target = [tuple(a.bbox(w)[[0, 1, 3, 4]]) for w in lb if a.bbox(w) is not None]
        r.check(len(lb) == 4, "Architect's model read: 4 load-bearing walls", f"found {len(lb)}")
    plan = [(bb[0], bb[1], bb[3], bb[4]) for _, bb in walls]
    want_area, got_area = raster_area(target), raster_area(plan)
    r.check(abs(got_area - want_area) <= 0.03 * want_area,
            f"Wall footprint matches the core: {want_area:.2f} m2", f"your walls cover {got_area:.2f} m2")
    xs0, ys0 = min(p[0] for p in plan), min(p[1] for p in plan)
    xs1, ys1 = max(p[2] for p in plan), max(p[3] for p in plan)
    ok = all(abs(a - b) <= 0.02 for a, b in zip((xs0, ys0, xs1, ys1), (c["x0"], c["y0"], c["x1"], c["y1"])))
    r.check(ok, f"Core outline x {c['x0']} to {c['x1']}, y {c['y0']} to {c['y1']}",
            f"found x {fmt(xs0)} to {fmt(xs1)}, y {fmt(ys0)} to {fmt(ys1)}")
    thin = [min(bb[3] - bb[0], bb[4] - bb[1]) for _, bb in walls]
    r.check(all(same(t, c["t"]) for t in thin), f"Walls are {int(c['t']*1000)} mm thick",
            f"thicknesses: {[fmt(t) for t in thin]}")
    r.check(all(same(bb[2], c["z0"]) and same(bb[5], c["z1"]) for _, bb in walls),
            f"Walls run from {c['z0']:+.3f} to the slab soffit {c['z1']:+.3f}",
            f"found: {[(fmt(bb[2]), fmt(bb[5])) for _, bb in walls]}")
    lb_ok = [w for w, _ in walls if m.find_prop(w, "LoadBearing") in (True, "True", "TRUE", 1)]
    r.check(len(lb_ok) == len(walls), "Every core wall is marked load-bearing (LoadBearing = True)",
            f"{len(walls) - len(lb_ok)} wall(s) without LoadBearing = True")
    r.check(all(_in_storey(m, w, "Level 0") for w, _ in walls), "Walls belong to Level 0", "")
    return r


def check_slab(m, r):
    s = spec.SLAB
    slabs = [e for e in m.elements("IfcSlab") if m.bbox(e) is not None and 3.0 < m.bbox(e)[5] < 4.0]
    r.check(len(slabs) == 1, "One slab at Level 1", f"found {len(slabs)}")
    if not slabs:
        return None
    sl = slabs[0]
    bb = m.bbox(sl)
    ok = all(abs(a - b) <= 0.02 for a, b in zip(bb, (s["x0"], s["y0"], s["z0"], s["x1"], s["y1"], s["z1"])))
    r.check(ok, f"Slab edges at the outer column faces (x {s['x0']} to {s['x1']}, y {s['y0']} to {s['y1']}), "
                f"top {s['z1']:+.3f}, soffit {s['z0']:+.3f}",
            f"found x {fmt(bb[0])} to {fmt(bb[3])}, y {fmt(bb[1])} to {fmt(bb[4])}, z {fmt(bb[2])} to {fmt(bb[5])}")
    want, got = spec.slab_volume(), m.volume(sl)
    full = (s["x1"] - s["x0"]) * (s["y1"] - s["y0"]) * spec.SLAB_T
    r.check(abs(got - want) <= 0.01 * want,
            f"Slab volume {want:.2f} m3, with the core and stair openings cut",
            f"found {got:.2f} m3" + (" (the openings are missing)" if abs(got - full) < 0.01 * full else ""))
    r.check(_in_storey(m, sl, "Level 1"), "Slab belongs to Level 1",
            f"in: {m.container(sl).Name if m.container(sl) else 'no level'}")
    return sl


@exercise("2.3", "Level 1 slab with openings")
def ex_2_3(path):
    m = Model(path)
    r = Result("2.3", "Level 1 slab with openings")
    check_slab(m, r)
    return r


def check_beams(m, r):
    b = spec.BEAM
    want = spec.beams()
    beams = [e for e in m.elements("IfcBeam") if m.bbox(e) is not None]
    r.check(len(beams) == len(want), f"{len(want)} beams at Level 1", f"found {len(beams)}")
    centres = {k: ((x0 + x1) / 2, (y0 + y1) / 2) for k, (x0, y0, x1, y1) in want.items()}
    found = match_by_position(m, beams, centres, tol=0.05)
    missing = [k for k, v in found.items() if v is None]
    r.check(not missing, "A beam on every grid line between columns", f"missing: {missing}")
    bad_box, bad_name, bad_storey = [], [], []
    for mark, el in found.items():
        if el is None:
            continue
        bb = m.bbox(el)
        x0, y0, x1, y1 = want[mark]
        if not all(abs(a - t) <= TOL for a, t in zip(bb, (x0, y0, b["z0"], x1, y1, b["z1"]))):
            bad_box.append(f"{mark}: x {fmt(bb[0])}-{fmt(bb[3])} y {fmt(bb[1])}-{fmt(bb[4])} z {fmt(bb[2])}-{fmt(bb[5])}")
        if norm(el.Name) != norm(mark):
            bad_name.append(f"{mark} named '{el.Name}'")
        if not _in_storey(m, el, "Level 1"):
            bad_storey.append(mark)
    r.check(not bad_box, f"Beams are {int(b['b']*1000)} wide x {int(b['h']*1000)} deep below the soffit "
                         f"({b['z0']:+.3f} to {b['z1']:+.3f}) and stop at the column faces", "; ".join(bad_box[:4]))
    r.check(not bad_name, "Beams are named by grid line and bay (B-1/AB ...)", "; ".join(bad_name[:6]))
    r.check(not bad_storey, "Beams belong to Level 1", f"not in Level 1: {bad_storey[:6]}")
    return found


@exercise("2.4", "Level 1 beams")
def ex_2_4(path):
    m = Model(path)
    r = Result("2.4", "Level 1 beams")
    check_beams(m, r)
    return r


def _overlap(a, b):
    dx = min(a[3], b[3]) - max(a[0], b[0])
    dy = min(a[4], b[4]) - max(a[1], b[1])
    dz = min(a[5], b[5]) - max(a[2], b[2])
    return dx * dy * dz if dx > 0 and dy > 0 and dz > 0 else 0.0


def _mesh_overlap(m, a, b, ba, bb, n=10):
    """Approximate overlap volume of two solids: sample the intersection of their boxes."""
    import numpy as np
    from .s7_management import _points_in_mesh
    lo = np.maximum(ba[:3], bb[:3])
    hi = np.minimum(ba[3:], bb[3:])
    axes = [np.linspace(lo[i], hi[i], n + 2)[1:-1] for i in range(3)]
    pts = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3) + np.array([1e-4, 2.3e-4, 3.1e-4])
    va, fa = m.mesh(a)
    vb, fb = m.mesh(b)
    inside = _points_in_mesh(pts, va, fa) & _points_in_mesh(pts, vb, fb)
    return inside.mean() * float(np.prod(hi - lo))


def frame_volumes():
    c, b, w = spec.COLUMN, spec.BEAM, spec.CORE
    col = len(spec.column_marks()) * c["size"] ** 2 * (c["z1"] - c["z0"])
    beam = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in spec.beams().values()) * b["h"]
    wall = raster_area(list(spec.core_walls().values())) * (w["z1"] - w["z0"])
    return {"IfcColumn": col, "IfcBeam": beam, "IfcWall": wall, "IfcSlab": spec.slab_volume()}


@exercise("2.5", "Clean joints: no element counted twice")
def ex_2_5(path):
    m = Model(path)
    r = Result("2.5", "Clean joints: no element counted twice")
    classes = ["IfcColumn", "IfcBeam", "IfcWall", "IfcSlab"]
    els = [(e, m.bbox(e)) for cl in classes for e in m.elements(cl) if m.bbox(e) is not None]
    els = [(e, bb) for e, bb in els if bb[2] > -0.5 and bb[5] < 4.0]
    clashes = []
    for (a, ba), (b, bb) in itertools.combinations(els, 2):
        ov = _overlap(ba, bb)
        if ov > 0.001:   # the boxes overlap; measure the real overlap (mitred corners overlap only as boxes)
            ov = _mesh_overlap(m, a, b, ba, bb)
        if ov > 0.001:
            clashes.append(f"{a.Name} / {b.Name}: {ov*1000:.0f} litres")
    r.check(not clashes, "No two elements overlap (beams stop at column faces, columns and walls stop at the soffit)",
            "; ".join(clashes[:6]) + (f" ... and {len(clashes)-6} more" if len(clashes) > 6 else ""))
    want = frame_volumes()
    for cl in classes:
        got = sum(m.volume(e) for e, bb in els if e.is_a(cl))
        r.check(abs(got - want[cl]) <= 0.01 * want[cl] + 0.01,
                f"Concrete volume of {cl[3:].lower()}s {want[cl]:.2f} m3", f"found {got:.2f} m3")
    total = sum(want.values())
    got = sum(m.volume(e) for e, _ in els)
    r.check(abs(got - total) <= 0.01 * total, f"Total frame concrete {total:.2f} m3", f"found {got:.2f} m3")
    return r
