"""Section 1: project setup, levels and grids."""
import math

import numpy as np
import ifcopenshell.util.placement as up

from .. import spec
from ..core import Model, Result, norm, same, fmt, POS
from . import exercise


def _dms(v):
    if v is None:
        return None
    parts = list(v) + [0] * (4 - len(v))
    d, m, s, ms = parts[:4]
    sign = -1 if (d < 0 or m < 0 or s < 0 or ms < 0) else 1
    return sign * (abs(d) + abs(m) / 60 + (abs(s) + abs(ms) / 1e6) / 3600)


@exercise("1.1", "Project, site, building, units and location")
def ex_1_1(path):
    m, p = Model(path), spec.PROJECT
    r = Result("1.1", "Project, site, building, units and location")
    proj = m.by_type("IfcProject")
    r.check(proj and norm(proj[0].Name) == norm(p["project_name"]),
            f"Project name is '{p['project_name']}'", f"found: {proj[0].Name if proj else 'no IfcProject'}")
    sites = m.by_type("IfcSite")
    r.check(any(norm(s.Name) == norm(p["site_name"]) for s in sites),
            f"Site name is '{p['site_name']}'", f"found: {[s.Name for s in sites]}")
    blds = m.by_type("IfcBuilding")
    r.check(any(norm(b.Name) == norm(p["building_name"]) for b in blds),
            f"Building name is '{p['building_name']}'", f"found: {[b.Name for b in blds]}")
    lu = [u for u in m.by_type("IfcSIUnit") if u.UnitType == "LENGTHUNIT"]
    r.check(lu and lu[0].Name == "METRE", "Length unit is metres or millimetres (SI)",
            f"found: {[(u.Prefix, u.Name) for u in lu] or 'no SI length unit'}")
    site = sites[0] if sites else None
    lat = _dms(site.RefLatitude) if site else None
    lon = _dms(site.RefLongitude) if site else None
    r.check(lat is not None and abs(lat - p["latitude"]) <= 0.001, f"Site latitude {p['latitude']}",
            f"found: {fmt(lat) if lat is not None else 'not set'}")
    r.check(lon is not None and abs(lon - p["longitude"]) <= 0.001, f"Site longitude {p['longitude']}",
            f"found: {fmt(lon) if lon is not None else 'not set'}")
    elev = site.RefElevation * m.scale if site and site.RefElevation is not None else None
    r.check(elev is not None and abs(elev - p["site_elevation"]) <= 0.5,
            f"Site elevation {p['site_elevation']} m above sea level",
            f"found: {fmt(elev) if elev is not None else 'not set'}")
    angle = None
    for ctx in m.by_type("IfcGeometricRepresentationContext"):
        tn = getattr(ctx, "TrueNorth", None)
        if tn is not None:
            x, y = tn.DirectionRatios[0], tn.DirectionRatios[1]
            angle = math.degrees(math.atan2(x, y))
            break
    r.check(angle is not None and abs(abs(angle) - p["true_north_deg"]) <= 0.5,
            f"True north set {p['true_north_deg']} degrees from project north",
            f"found: {fmt(angle) + ' degrees' if angle is not None else 'no true north in the model'}")
    if angle is not None and abs(abs(angle) - p["true_north_deg"]) <= 0.5 and angle < 0:
        r.items[-1].hint = ("the angle is right; note that it is stored as counter-clockwise. The brief asks for true "
                            "north 12 degrees clockwise from project north (towards +X).")
    return r


@exercise("1.2", "Levels (building storeys)")
def ex_1_2(path):
    m = Model(path)
    r = Result("1.2", "Levels (building storeys)")
    found = {norm(n): (n, e) for n, e in m.storeys().items()}
    for name, elev in spec.STOREYS:
        hit = found.get(norm(name))
        r.check(hit is not None and same(hit[1], elev),
                f"Level '{name}' at {elev:+.3f}",
                "missing" if hit is None else f"found at {fmt(hit[1])}")
    extra = [n for k, (n, _) in found.items() if k not in {norm(s[0]) for s in spec.STOREYS}]
    r.check(not extra, "No extra levels", f"extra: {extra}")
    blds = m.by_type("IfcBuilding")
    inside = set()
    for b in blds:
        for rel in b.IsDecomposedBy or []:
            inside |= {o.id() for o in rel.RelatedObjects if o.is_a("IfcBuildingStorey")}
    r.check(m.by_type("IfcBuildingStorey") and all(s.id() in inside for s in m.by_type("IfcBuildingStorey")),
            "All levels belong to the building", "some levels are not inside the IfcBuilding")
    return r


def grid_axes(m):
    """World-coordinate line segments of every IfcGridAxis: {tag: [(p0, p1), ...]}."""
    out = {}
    for ax in m.by_type("IfcGridAxis"):
        grid = None
        for inv in ("PartOfU", "PartOfV", "PartOfW"):
            g = getattr(ax, inv, None)
            if g:
                grid = g[0]
                break
        M = np.eye(4)
        if grid is not None and grid.ObjectPlacement is not None:
            M = up.get_local_placement(grid.ObjectPlacement)
        pts = []
        curve = ax.AxisCurve
        if curve.is_a("IfcPolyline"):
            pts = [p.Coordinates for p in curve.Points]
        elif curve.is_a("IfcIndexedPolyCurve"):
            pts = list(curve.Points.CoordList)
        elif curve.is_a("IfcLine"):
            p0 = curve.Pnt.Coordinates
            d = curve.Dir.Orientation.DirectionRatios
            mag = curve.Dir.Magnitude
            pts = [p0, tuple(a + b * mag for a, b in zip(p0, d))]
        if len(pts) < 2:
            continue
        w = []
        for q in (pts[0], pts[-1]):
            q = list(q) + [0.0] * (3 - len(q))
            v = M @ np.array([q[0], q[1], q[2], 1.0])
            w.append(v[:3] * m.scale)
        out.setdefault(str(ax.AxisTag).strip(), []).append((w[0], w[1]))
    return out


@exercise("1.3", "Structural grid")
def ex_1_3(path):
    m = Model(path)
    r = Result("1.3", "Structural grid")
    axes = grid_axes(m)
    r.check(axes, "The model contains grid axes (IfcGridAxis)", "no grid axes found")
    ys, xs = list(spec.GRID_Y.values()), list(spec.GRID_X.values())
    for tag, x in spec.GRID_X.items():
        segs = axes.get(tag, [])
        ok = any(abs(p0[0] - x) <= POS and abs(p1[0] - x) <= POS and abs(p0[1] - p1[1]) >= (max(ys) - min(ys))
                 for p0, p1 in segs)
        r.check(ok, f"Axis {tag}: line parallel to Y at x = {x:.3f}, spanning grids 1 to 3",
                "missing" if not segs else f"found: {[(fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1])) for a, b in segs]}")
    for tag, y in spec.GRID_Y.items():
        segs = axes.get(tag, [])
        ok = any(abs(p0[1] - y) <= POS and abs(p1[1] - y) <= POS and abs(p0[0] - p1[0]) >= (max(xs) - min(xs))
                 for p0, p1 in segs)
        r.check(ok, f"Axis {tag}: line parallel to X at y = {y:.3f}, spanning grids A to D",
                "missing" if not segs else f"found: {[(fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1])) for a, b in segs]}")
    return r
