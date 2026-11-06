"""Section 7: phases, design options, worksharing, model health, clashes, purge, templates, export."""
import os
import subprocess

import numpy as np
import ifcopenshell.util.element as ue

from .. import spec
from ..core import Model, Result, norm, fmt, plan_center
from . import exercise

STRUCTURAL = ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting", "IfcPile", "IfcStair", "IfcStairFlight")


def _status(m, e):
    v = m.find_prop(e, "Status")
    return str(v).upper() if v is not None else None


@exercise("7.1", "Phases: existing, demolish, new", inputs=("renovation_model.ifc",))
def ex_7_1(path):
    m = Model(path)
    r = Result("7.1", "Phases: existing, demolish, new")
    els = [e for cl in STRUCTURAL for e in m.elements(cl) if e.Name]
    for prefix, status in (("E-", "EXISTING"), ("D-", "DEMOLISH")):
        group = [e for e in els if e.Name.upper().startswith(prefix)]
        bad = [e.Name for e in group if _status(m, e) != status]
        r.check(group and not bad, f"Elements named {prefix}... have Status = {status}",
                f"{len(bad)} of {len(group)} wrong: {bad[:4]}" if group else "no such elements found")
    new = [e for e in els if e.Name.upper().startswith("N-")]
    r.check(new, "The new beam N-B1 is modelled", "no element named N-... found")
    for e in new:
        bb = m.bbox(e)
        r.check(_status(m, e) == "NEW", f"{e.Name} has Status = NEW", f"found {_status(m, e)}")
        ok = bb is not None and abs(bb[0] - 0.2) <= 0.03 and abs(bb[3] - 5.8) <= 0.03 and abs(bb[1] + 0.15) <= 0.03 \
            and abs(bb[4] - 0.15) <= 0.03 and abs(bb[2] - 2.75) <= 0.03 and abs(bb[5] - 3.35) <= 0.03
        r.check(ok, f"{e.Name} is 300 x 600 between columns E-A1 and E-B1 (x 0.2 to 5.8, z +2.750 to +3.350)",
                f"found {[fmt(v) for v in bb] if bb is not None else 'no geometry'}")
    return r


def _boxes(m):
    out = []
    for cl in STRUCTURAL:
        for e in m.elements(cl):
            bb = m.bbox(e)
            if bb is not None:
                out.append((e, tuple(np.round(bb, 2))))
    return out


@exercise("7.2", "Design options: compare two versions", inputs=("option_A.ifc", "option_B.ifc"))
def ex_7_2(a_path, b_path):
    a, b = Model(a_path), Model(b_path)
    r = Result("7.2", "Design options: compare two versions")
    ba, bb = _boxes(a), _boxes(b)
    only_a = [e for e, x in ba if x not in {y for _, y in bb}]
    only_b = [e for e, x in bb if x not in {y for _, y in ba}]
    r.check(len(only_a) == 1 and len(only_b) == 1, "Exactly one element differs between the options",
            f"{len(only_a)} element(s) only in A, {len(only_b)} only in B")
    if only_a and only_b:
        ea, eb = only_a[0], only_b[0]
        r.check(norm(ea.Name) == norm("B-2/BC") or norm(eb.Name) == norm("B-2/BC"), "The changed element is beam B-2/BC",
                f"found {ea.Name} / {eb.Name}")
        x = a.bbox(ea)
        y = b.bbox(eb)
        r.check(abs((x[4] - x[1]) - 0.30) <= 0.01 and abs((x[5] - x[2]) - 0.35) <= 0.01,
                "Option A keeps B-2/BC at 300 x 350", f"found {fmt(x[4]-x[1])} x {fmt(x[5]-x[2])}")
        r.check(abs((y[4] - y[1]) - 0.40) <= 0.01 and abs((y[5] - y[2]) - 0.50) <= 0.01 and abs(y[5] - spec.SLAB_SOFFIT) <= 0.01,
                "Option B makes B-2/BC 400 x 500, still hung from the soffit", f"found {fmt(y[4]-y[1])} x {fmt(y[5]-y[2])}, top {fmt(y[5])}")
    return r


@exercise("7.3", "Worksharing with Git", inputs=("repository_folder",))
def ex_7_3(repo):
    r = Result("7.3", "Worksharing with Git")

    def git(*args):
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)

    ok = git("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
    if not r.check(ok, "The folder is a Git repository", "run 'git init' or use Bonsai's Git panel"):
        return r
    log = git("log", "--format=%H|%an|%s", "--", "*.ifc").stdout.strip().splitlines()
    r.check(len(log) >= 2, "At least two commits change the IFC model", f"found {len(log)}")
    r.check(all(l.split("|")[1].strip() for l in log), "Every commit has an author", "")
    r.check(all(len(l.split("|", 2)[2].strip()) >= 10 for l in log), "Commit messages describe the change (10+ characters)",
            f"messages: {[l.split('|', 2)[2] for l in log[:4]]}")
    if len(log) >= 2:
        first, last = log[-1].split("|")[0], log[0].split("|")[0]
        diff = git("diff", "--stat", first, last, "--", "*.ifc").stdout.strip()
        r.check(diff, "The model changed between the first and the last commit", "no difference found")
    tracked = git("ls-files", "*.ifc").stdout.split()
    r.check(tracked, "The IFC model is tracked (not just FreeCAD or Blender files)", "no .ifc file tracked")
    return r


@exercise("7.4", "Model health: fix the warnings", inputs=("fixed_model.ifc",))
def ex_7_4(path):
    m = Model(path)
    r = Result("7.4", "Model health: fix the warnings")
    els = [e for cl in STRUCTURAL for e in m.elements(cl) if m.bbox(e) is not None]
    seen, dups = {}, []
    for e in els:
        key = (e.is_a(), tuple(np.round(m.bbox(e), 2)))
        if key in seen:
            dups.append(f"{e.Name} = {seen[key].Name}")
        seen[key] = e
    r.check(not dups, "No duplicate elements in the same place", "; ".join(dups[:5]))
    loose = [e.Name or e.GlobalId for e in els if m.container(e) is None]
    r.check(not loose, "Every element belongs to a level", f"not in a level: {loose[:5]}")
    nomat = [e.Name or e.GlobalId for e in els if not m.materials(e)]
    r.check(not nomat, "Every element has a material", f"no material: {nomat[:5]}")
    noname = [e.GlobalId for e in els if not (e.Name or "").strip()]
    r.check(not noname, "Every element has a name (mark)", f"{len(noname)} without a name")
    r.check(len(els) >= 20, "The model still holds the frame (nothing important deleted)", f"only {len(els)} elements left")
    return r


def _points_in_mesh(pts, v, f):
    """Ray parity test (+X ray) for many points against one closed mesh."""
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    e1, e2 = b - a, c - a
    d = np.array([1.0, 0.0, 0.0])
    h = np.cross(np.broadcast_to(d, e2.shape), e2)
    det = np.einsum("ij,ij->i", e1, h)
    good = np.abs(det) > 1e-12
    inside = np.zeros(len(pts), bool)
    for k, p in enumerate(pts):
        s = p - a
        u = np.einsum("ij,ij->i", s, h) / np.where(good, det, 1)
        q = np.cross(s, e1)
        vv = (q @ d) / np.where(good, det, 1)
        t = np.einsum("ij,ij->i", e2, q) / np.where(good, det, 1)
        hit = good & (u >= 0) & (vv >= 0) & (u + vv <= 1) & (t > 1e-9)
        inside[k] = hit.sum() % 2 == 1
    return inside


def _sample(box, n=6):
    xs = np.linspace(box[0], box[3], n)
    ys = np.linspace(box[1], box[4], n)
    zs = np.linspace(box[2], box[5], n)
    g = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1).reshape(-1, 3)
    return g + np.array([1e-4, 2.3e-4, 3.1e-4])   # avoid hitting edges exactly


def _inter(a, b, grow=0.0):
    lo = np.maximum(a[:3] - grow, b[:3])
    hi = np.minimum(a[3:] + grow, b[3:])
    return np.concatenate([lo, hi]) if np.all(hi > lo) else None


@exercise("7.5", "Clash detection with the MEP model", inputs=("structure.ifc", "mep_model.ifc"))
def ex_7_5(struct_path, mep_path):
    s, mp = Model(struct_path), Model(mep_path)
    r = Result("7.5", "Clash detection with the MEP model")
    mep = [e for e in mp.by_type("IfcFlowSegment") + mp.by_type("IfcDuctSegment") + mp.by_type("IfcPipeSegment")
           if mp.bbox(e) is not None]
    mep = list({e.id(): e for e in mep}.values())
    r.check(mep, "MEP model read", "no duct or pipe segments found in the MEP file")
    els = [e for cl in ("IfcBeam", "IfcWall", "IfcColumn", "IfcSlab") for e in s.elements(cl) if s.bbox(e) is not None]
    hard, soft = [], []
    for d in mep:
        db = mp.bbox(d)
        for e in els:
            eb = s.bbox(e)
            box = _inter(db, eb)
            if box is not None:
                v, f = s.mesh(e)
                if _points_in_mesh(_sample(box), v, f).any():
                    hard.append(f"{d.Name} x {e.Name}")
                    continue
            box = _inter(db, eb, grow=0.025)
            if box is not None:
                v, f = s.mesh(e)
                if _points_in_mesh(_sample(box), v, f).any():
                    soft.append(f"{d.Name} x {e.Name}")
    r.check(not hard, "No hard clashes: every duct passes through an opening", "; ".join(hard[:6]))
    r.check(not soft, "At least 25 mm clearance around every duct", "; ".join(soft[:6]))
    beams = {e.Name: e for e in s.elements("IfcBeam")}
    full = spec.BEAM["b"] * spec.BEAM["h"]
    weak = []
    for name, (x0, y0, x1, y1) in spec.beams().items():
        e = beams.get(name)
        if e is None:
            continue
        length = max(x1 - x0, y1 - y0)
        if s.volume(e) < 0.9 * full * length:
            weak.append(name)
    r.check(not weak, "Openings are local (each beam keeps at least 90% of its volume)", f"too much removed from: {weak}")
    openings = s.by_type("IfcOpeningElement")
    r.check(openings, "Openings are modelled as IFC openings (IfcOpeningElement)", "no openings found")
    return r


@exercise("7.6", "Purge unused data", inputs=("purged_model.ifc",))
def ex_7_6(path):
    m = Model(path)
    r = Result("7.6", "Purge unused data")
    from .s4_types import read_catalogue
    keep = {norm(row["Name"]) for row in read_catalogue()}
    unused_types = [t.Name for t in m.by_type("IfcElementType") if not ue.get_types(t) and norm(t.Name) not in keep]
    r.check(not unused_types, "No unused types (the column types of the project catalogue may stay)",
            f"unused: {unused_types[:6]}")
    unused_mats = [x.Name for x in m.by_type("IfcMaterial") if m.f.get_total_inverses(x) == 0]
    r.check(not unused_mats, "No unused materials", f"unused: {unused_mats[:6]}")
    unused_prof = [p.ProfileName or p.is_a() for p in m.by_type("IfcProfileDef") if m.f.get_total_inverses(p) == 0]
    r.check(not unused_prof, "No unused profiles", f"unused: {unused_prof[:6]}")
    empty_groups = [g.Name for g in m.by_type("IfcGroup") if not any(rel.RelatedObjects for rel in (g.IsGroupedBy or []))]
    r.check(not empty_groups, "No empty groups", f"empty: {empty_groups}")
    r.check(len(m.elements("IfcColumn")) >= 12, "The used elements are still there", "columns were deleted")
    return r


@exercise("7.7", "Project library (template)", inputs=("template.ifc",))
def ex_7_7(path):
    m = Model(path)
    r = Result("7.7", "Project library (template)")
    for cls, tname in spec.TYPES.items():
        r.check(any(norm(t.Name) == norm(tname) for t in m.by_type(cls + "Type")), f"Type '{tname}'", "missing")
    mats = {norm(x.Name) for x in m.by_type("IfcMaterial")}
    for mat in ("C30/37", "C25/30", spec.REBAR["steel"]):
        r.check(any(norm(mat) in x for x in mats), f"Material {mat}", "missing")
    occ = [e for e in m.by_type("IfcElement") if not e.is_a("IfcOpeningElement")]
    r.check(not occ, "No placed elements (a template holds definitions only)", f"{len(occ)} placed element(s)")
    names = {norm(s.Name) for s in m.by_type("IfcBuildingStorey")}
    r.check(all(norm(n) in names for n, _ in spec.STOREYS) or not names, "Levels, if included, follow the brief", "")
    return r


@exercise("7.8", "Export for issue: IFC4, levels, base quantities", inputs=("model.ifc",))
def ex_7_8(path):
    m = Model(path)
    r = Result("7.8", "Export for issue: IFC4, levels, base quantities")
    r.check(m.f.schema in ("IFC4", "IFC4X3", "IFC4X3_ADD2"), "Schema IFC4 (or IFC4.3)", f"found {m.f.schema}")
    lu = [u for u in m.by_type("IfcSIUnit") if u.UnitType == "LENGTHUNIT"]
    r.check(lu and lu[0].Name == "METRE", "SI length unit", "")
    els = [e for cl in STRUCTURAL for e in m.elements(cl) if m.bbox(e) is not None]
    r.check(len(els) >= 40, "The full TB-01 model is in the file", f"only {len(els)} elements")
    loose = [e.Name for e in els if m.container(e) is None]
    r.check(not loose, "Every element belongs to a level", f"{len(loose)} without a level")
    bad = []
    for e in [x for x in els if x.is_a() in ("IfcColumn", "IfcBeam", "IfcSlab", "IfcWall", "IfcFooting")]:
        q = None
        for name, ps in m.psets(e).items():
            if name.startswith("Qto_") and name.endswith("BaseQuantities"):
                q = ps.get("NetVolume") or ps.get("GrossVolume")
        if q is None or abs(float(q) * (m.scale ** 3 if float(q) > 1e5 else 1) - m.volume(e)) > 0.02 * m.volume(e) + 0.001:
            bad.append(e.Name)
    r.check(not bad, "Base quantities (Qto_...BaseQuantities volume) on every concrete element, matching the geometry",
            f"{len(bad)} missing or wrong, e.g. {bad[:4]}")
    return r
