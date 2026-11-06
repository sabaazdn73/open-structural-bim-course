"""Shared helpers for the exercise checks.

The checks read what is in the IFC file and look at the geometry itself (bounding boxes,
volumes, positions), not at how a particular program wrote it. That way the same check
works for a model made in FreeCAD, in Bonsai or in any other program that exports IFC.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as ue
import ifcopenshell.util.placement as up
import ifcopenshell.util.unit as uu

TOL = 0.010   # 10 mm for sizes and levels
POS = 0.030   # 30 mm for positions


# ---------------------------------------------------------------- results
@dataclass
class Item:
    ok: bool
    text: str
    hint: str = ""


@dataclass
class Result:
    exercise: str
    title: str
    items: list = field(default_factory=list)

    def check(self, ok, text, hint=""):
        self.items.append(Item(bool(ok), text, hint))
        return bool(ok)

    @property
    def passed(self):
        return bool(self.items) and all(i.ok for i in self.items)

    def score(self):
        return sum(i.ok for i in self.items), len(self.items)


# ---------------------------------------------------------------- loading
class Model:
    """An IFC file with cached geometry, in metres."""

    def __init__(self, path):
        self.path = path
        self.f = ifcopenshell.open(path)
        self.scale = uu.calculate_unit_scale(self.f)   # file length unit -> metres
        self._geom = None

    def by_type(self, t):
        try:
            return self.f.by_type(t)
        except RuntimeError:          # entity not in this schema
            return []

    # geometry -----------------------------------------------------------
    def _load_geometry(self):
        self._geom = {}
        s = ifcopenshell.geom.settings()
        s.set("use-world-coords", True)
        prods = [p for p in self.by_type("IfcProduct") if getattr(p, "Representation", None)
                 and not p.is_a("IfcOpeningElement") and not p.is_a("IfcSpatialStructureElement")
                 and not p.is_a("IfcGrid") and not p.is_a("IfcAnnotation")]
        for p in prods:
            try:
                sh = ifcopenshell.geom.create_shape(s, p)
            except Exception:
                continue
            v = np.array(sh.geometry.verts, float).reshape(-1, 3)
            fcs = np.array(sh.geometry.faces, int).reshape(-1, 3)
            if len(v) and len(fcs):
                self._geom[p.id()] = (v, fcs)

    def mesh(self, el):
        if self._geom is None:
            self._load_geometry()
        return self._geom.get(el.id())

    def bbox(self, el):
        m = self.mesh(el)
        if m is None:
            return None
        v = m[0]
        return np.concatenate([v.min(0), v.max(0)])   # x0 y0 z0 x1 y1 z1

    def volume(self, el):
        m = self.mesh(el)
        if m is None:
            return 0.0
        v, f = m
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        return abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)

    def components(self, el):
        """Split an element's mesh into connected pieces (for example, one rebar object with many bars)."""
        m = self.mesh(el)
        if m is None:
            return []
        v, f = m
        # merge coincident vertices first
        key = np.round(v, 5)
        _, inv = np.unique(key, axis=0, return_inverse=True)
        inv = inv.reshape(-1)
        parent = list(range(inv.max() + 1))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for tri in inv[f]:
            a, b, c = (find(int(x)) for x in tri)
            parent[b] = a
            parent[find(c)] = a
        groups = {}
        for vi, ui in enumerate(inv):
            groups.setdefault(find(int(ui)), []).append(vi)
        boxes = []
        for idx in groups.values():
            pts = v[idx]
            boxes.append(np.concatenate([pts.min(0), pts.max(0)]))
        return boxes

    # data ---------------------------------------------------------------
    def elements(self, ifc_class):
        return [e for e in self.by_type(ifc_class) if not (ifc_class == "IfcSlab" and e.is_a() != "IfcSlab")]

    def psets(self, el):
        return ue.get_psets(el)

    def prop(self, el, pset, name):
        return self.psets(el).get(pset, {}).get(name)

    def find_prop(self, el, name):
        """Value of a property in any property set (first match)."""
        for ps in self.psets(el).values():
            if name in ps:
                return ps[name]
        return None

    def container(self, el):
        c = ue.get_container(el)
        if c is None:  # elements inside an assembly or aggregate: walk up
            parent = ue.get_aggregate(el)
            while parent is not None and c is None:
                c = ue.get_container(parent)
                parent = ue.get_aggregate(parent)
        return c

    def materials(self, el):
        names = []
        try:
            for m in ue.get_materials(el, should_inherit=True):
                if getattr(m, "Name", None):
                    names.append(m.Name)
                if m.is_a("IfcMaterialLayer") or m.is_a("IfcMaterialProfile") or m.is_a("IfcMaterialConstituent"):
                    if m.Material is not None and m.Material.Name:
                        names.append(m.Material.Name)
        except Exception:
            pass
        mat = ue.get_material(el, should_inherit=True)
        if mat is not None:
            for attr in ("Name", "LayerSetName"):
                if getattr(mat, attr, None):
                    names.append(getattr(mat, attr))
        return names

    def storey_elevation(self, st):
        if st.Elevation is not None:
            return float(st.Elevation) * self.scale
        if st.ObjectPlacement is not None:
            return float(up.get_local_placement(st.ObjectPlacement)[2][3]) * self.scale
        return None

    def storeys(self):
        return {s.Name: self.storey_elevation(s) for s in self.by_type("IfcBuildingStorey")}


# ---------------------------------------------------------------- small helpers
def norm(s):
    return re.sub(r"[\s_\-]+", "", str(s or "")).lower()


def same(a, b, tol=TOL):
    return a is not None and b is not None and abs(a - b) <= tol


def fmt(x):
    return f"{x:.3f}" if isinstance(x, (int, float)) else str(x)


def box_close(bb, target, tol=POS, dims=6):
    """bb and target as x0 y0 z0 x1 y1 z1 (target entries may be None to skip)."""
    return all(t is None or abs(b - t) <= tol for b, t in zip(bb[:dims], target[:dims]))


def plan_center(bb):
    return ((bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2)


def match_by_position(model, elements, targets, tol=POS):
    """targets: {mark: (x, y)}. Returns {mark: element or None} by nearest plan centre."""
    out, used = {}, set()
    centres = {e.id(): plan_center(model.bbox(e)) for e in elements if model.bbox(e) is not None}
    for mark, (x, y) in targets.items():
        best, bd = None, tol
        for e in elements:
            if e.id() in used or e.id() not in centres:
                continue
            cx, cy = centres[e.id()]
            d = math.hypot(cx - x, cy - y)
            if d <= bd:
                best, bd = e, d
        out[mark] = best
        if best is not None:
            used.add(best.id())
    return out


def has_material(names, wanted):
    w = norm(wanted)
    return any(w in norm(n) for n in names)


def raster_area(boxes, step=0.01):
    """Union area of axis-aligned plan rectangles (x0, y0, x1, y1), on a 1 cm grid."""
    if not boxes:
        return 0.0
    b = np.array(boxes)
    x0, y0 = b[:, 0].min(), b[:, 1].min()
    nx = int(math.ceil((b[:, 2].max() - x0) / step)) + 1
    ny = int(math.ceil((b[:, 3].max() - y0) / step)) + 1
    grid = np.zeros((nx, ny), bool)
    for bx0, by0, bx1, by1 in boxes:
        i0, i1 = int(round((bx0 - x0) / step)), int(round((bx1 - x0) / step))
        j0, j1 = int(round((by0 - y0) / step)), int(round((by1 - y0) / step))
        grid[i0:i1, j0:j1] = True
    return grid.sum() * step * step
