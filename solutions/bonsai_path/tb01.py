"""Reference model of TB-01, built with the IfcOpenShell API.

Bonsai (BlenderBIM) uses this same API underneath its buttons, so every function here is
also a script you can paste into Bonsai's Python console. The reference solutions for the
checker tests are built from these functions.

Run:  python solutions/bonsai_path/tb01.py out_folder
"""
import math
import os
import sys

import numpy as np
import ifcopenshell
import ifcopenshell.api as api

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "checker"))
from bimcheck import spec  # noqa: E402

run = api.run


def dms(dd):
    """Decimal degrees -> IFC compound angle (degrees, minutes, seconds, millionths of a second)."""
    sign = -1 if dd < 0 else 1
    total = round(abs(dd) * 3600 * 1e6)
    d, rem = divmod(total, 3600 * 10**6)
    mi, rem = divmod(rem, 60 * 10**6)
    se, mu = divmod(rem, 10**6)
    return tuple(sign * int(v) for v in (d, mi, se, mu))


# ------------------------------------------------------------------ basics
class TB01:
    def __init__(self, name=None):
        self.f = run("project.create_file", version="IFC4")
        p = spec.PROJECT
        self.project = run("root.create_entity", self.f, ifc_class="IfcProject", name=name or p["project_name"])
        units = [run("unit.add_si_unit", self.f, unit_type=t) for t in ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT")]
        units.append(run("unit.add_si_unit", self.f, unit_type="PLANEANGLEUNIT"))
        run("unit.assign_unit", self.f, units=units)
        model = run("context.add_context", self.f, context_type="Model")
        self.body = run("context.add_context", self.f, context_type="Model", context_identifier="Body",
                        target_view="MODEL_VIEW", parent=model)
        self.model_ctx = model
        self.site = run("root.create_entity", self.f, ifc_class="IfcSite", name=p["site_name"])
        self.building = run("root.create_entity", self.f, ifc_class="IfcBuilding", name=p["building_name"])
        run("aggregate.assign_object", self.f, relating_object=self.project, products=[self.site])
        run("aggregate.assign_object", self.f, relating_object=self.site, products=[self.building])
        self.storeys, self.materials = {}, {}

    def write(self, path):
        self.f.write(path)
        return path

    # location ------------------------------------------------------------
    def set_location(self):
        p = spec.PROJECT
        self.site.RefLatitude = dms(p["latitude"])
        self.site.RefLongitude = dms(p["longitude"])
        self.site.RefElevation = p["site_elevation"]
        a = math.radians(p["true_north_deg"])
        self.model_ctx.TrueNorth = self.f.createIfcDirection((math.sin(a), math.cos(a)))

    # levels and grid -----------------------------------------------------
    def add_storeys(self):
        for name, z in spec.STOREYS:
            s = run("root.create_entity", self.f, ifc_class="IfcBuildingStorey", name=name)
            run("aggregate.assign_object", self.f, relating_object=self.building, products=[s])
            M = np.eye(4)
            M[2, 3] = z
            run("geometry.edit_object_placement", self.f, product=s, matrix=M, is_si=True)
            s.Elevation = z
            self.storeys[name] = s

    def add_grid(self):
        grid = run("root.create_entity", self.f, ifc_class="IfcGrid", name="Structural Grid")
        run("geometry.edit_object_placement", self.f, product=grid, matrix=np.eye(4), is_si=True)
        run("spatial.assign_container", self.f, relating_structure=self.storeys["Level 0"], products=[grid])
        ys, xs = spec.GRID_Y.values(), spec.GRID_X.values()
        for tag, x in spec.GRID_X.items():
            ax = run("grid.create_grid_axis", self.f, axis_tag=tag, uvw_axes="UAxes", grid=grid)
            run("grid.create_axis_curve", self.f, p1=np.array([x, min(ys) - 2.0, 0.0]),
                p2=np.array([x, max(ys) + 2.0, 0.0]), grid_axis=ax)
        for tag, y in spec.GRID_Y.items():
            ax = run("grid.create_grid_axis", self.f, axis_tag=tag, uvw_axes="VAxes", grid=grid)
            run("grid.create_axis_curve", self.f, p1=np.array([min(xs) - 2.0, y, 0.0]),
                p2=np.array([max(xs) + 2.0, y, 0.0]), grid_axis=ax)
        return grid

    # generic boxes -----------------------------------------------------------
    @staticmethod
    def placement(origin, z_dir=(0, 0, 1), x_dir=(1, 0, 0)):
        z = np.array(z_dir, float)
        z /= np.linalg.norm(z)
        x = np.array(x_dir, float)
        x -= z * x.dot(z)
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        M = np.eye(4)
        M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, origin
        return M

    def box(self, ifc_class, name, storey, x0, y0, z0, x1, y1, z1, predefined=None):
        """An axis-aligned box element, extruded upwards."""
        e = run("root.create_entity", self.f, ifc_class=ifc_class, name=name, predefined_type=predefined)
        prof = self.f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=x1 - x0, YDim=y1 - y0)
        rep = run("geometry.add_profile_representation", self.f, context=self.body, profile=prof, depth=z1 - z0)
        run("geometry.assign_representation", self.f, product=e, representation=rep)
        run("geometry.edit_object_placement", self.f, product=e,
            matrix=self.placement(((x0 + x1) / 2, (y0 + y1) / 2, z0)), is_si=True)
        run("spatial.assign_container", self.f, relating_structure=self.storeys[storey], products=[e])
        return e

    def beam(self, name, x0, y0, x1, y1, z0, z1, storey="Level 1"):
        """A beam extruded along its axis (as Bonsai's Beam Tool does)."""
        e = run("root.create_entity", self.f, ifc_class="IfcBeam", name=name, predefined_type="BEAM")
        along_x = (x1 - x0) >= (y1 - y0)
        width = (y1 - y0) if along_x else (x1 - x0)
        prof = self.f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=width, YDim=z1 - z0)
        length = (x1 - x0) if along_x else (y1 - y0)
        rep = run("geometry.add_profile_representation", self.f, context=self.body, profile=prof, depth=length)
        run("geometry.assign_representation", self.f, product=e, representation=rep)
        d = (1, 0, 0) if along_x else (0, 1, 0)
        o = (x0, (y0 + y1) / 2, (z0 + z1) / 2) if along_x else ((x0 + x1) / 2, y0, (z0 + z1) / 2)
        run("geometry.edit_object_placement", self.f, product=e,
            matrix=self.placement(o, z_dir=d, x_dir=(-d[1], d[0], 0)), is_si=True)
        run("spatial.assign_container", self.f, relating_structure=self.storeys[storey], products=[e])
        return e

    def opening(self, host, x0, y0, z0, x1, y1, z1, name="Opening"):
        o = run("root.create_entity", self.f, ifc_class="IfcOpeningElement", name=name)
        prof = self.f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", XDim=x1 - x0, YDim=y1 - y0)
        rep = run("geometry.add_profile_representation", self.f, context=self.body, profile=prof, depth=z1 - z0)
        run("geometry.assign_representation", self.f, product=o, representation=rep)
        run("geometry.edit_object_placement", self.f, product=o,
            matrix=self.placement(((x0 + x1) / 2, (y0 + y1) / 2, z0)), is_si=True)
        run("feature.add_feature", self.f, feature=o, element=host)
        return o

    # section 2 ---------------------------------------------------------------
    def add_columns(self):
        h, c = spec.COLUMN["size"] / 2, spec.COLUMN
        self.columns = {}
        for mark, (x, y) in spec.column_marks().items():
            self.columns[mark] = self.box("IfcColumn", mark, "Level 0", x - h, y - h, c["z0"], x + h, y + h, c["z1"],
                                          predefined="COLUMN")

    def add_core_walls(self):
        c = spec.CORE
        self.walls = {}
        for name, (x0, y0, x1, y1) in spec.core_walls().items():
            w = self.box("IfcWall", name, "Level 0", x0, y0, c["z0"], x1, y1, c["z1"], predefined="SOLIDWALL")
            pset = run("pset.add_pset", self.f, product=w, name="Pset_WallCommon")
            run("pset.edit_pset", self.f, pset=pset, properties={"LoadBearing": True, "IsExternal": False})
            self.walls[name] = w

    def add_slab(self):
        s = spec.SLAB
        self.slab = self.box("IfcSlab", "S-L1", "Level 1", s["x0"], s["y0"], s["z0"], s["x1"], s["y1"], s["z1"],
                             predefined="FLOOR")
        for name, (x0, y0, x1, y1) in s["openings"].items():
            self.opening(self.slab, x0, y0, s["z0"] - 0.05, x1, y1, s["z1"] + 0.05, name=f"Opening {name}")

    def add_beams(self, override=None):
        b = spec.BEAM
        self.beams = {}
        for mark, (x0, y0, x1, y1) in spec.beams().items():
            z0, z1 = b["z0"], b["z1"]
            if override and mark in override:
                x0, y0, x1, y1, z0, z1 = override[mark]
            self.beams[mark] = self.beam(mark, x0, y0, x1, y1, z0, z1)

    # section 3 ---------------------------------------------------------------
    def add_stair(self):
        st = spec.STAIR
        n, rh, g = st["risers"], st["riser"], st["going"]
        pts = [(0.0, 0.0)]
        for i in range(n):
            pts.append((i * g, (i + 1) * rh))
            if i < n - 1:
                pts.append(((i + 1) * g, (i + 1) * rh))
        top_y = (n - 1) * g + 0.08   # short top tread up to the slab edge at y = 6.40
        pts += [(top_y, n * rh), (top_y, n * rh - 0.30), (0.45, 0.0)]
        prof = self.f.create_entity(
            "IfcArbitraryClosedProfileDef", ProfileType="AREA",
            OuterCurve=self.f.create_entity("IfcPolyline", Points=[self.f.createIfcCartesianPoint(p) for p in pts + [pts[0]]]))
        stair = run("root.create_entity", self.f, ifc_class="IfcStairFlight", name="ST-1", predefined_type="STRAIGHT")
        rep = run("geometry.add_profile_representation", self.f, context=self.body, profile=prof,
                  depth=st["x1"] - st["x0"], cardinal_point=None)
        run("geometry.assign_representation", self.f, product=stair, representation=rep)
        # local x = +Y (going), local y = +Z (rise), extrusion = +X (width)
        run("geometry.edit_object_placement", self.f, product=stair,
            matrix=self.placement((st["x0"], st["y0"], st["z0"]), z_dir=(1, 0, 0), x_dir=(0, 1, 0)), is_si=True)
        run("spatial.assign_container", self.f, relating_structure=self.storeys["Level 0"], products=[stair])
        pset = run("pset.add_pset", self.f, product=stair, name="Pset_StairFlightCommon")
        run("pset.edit_pset", self.f, pset=pset, properties={"NumberOfRiser": n, "NumberOfTreads": n - 1,
                                                             "RiserHeight": rh, "TreadLength": g})
        self.stair = stair

    def add_footings(self):
        f, h = spec.FOOTING, spec.FOOTING["size"] / 2
        self.footings = {}
        for mark, (x, y) in spec.column_marks().items():
            fm = mark.replace("C-", "F-")
            self.footings[fm] = self.box("IfcFooting", fm, "Foundation", x - h, y - h, f["z0"], x + h, y + h, f["z1"],
                                         predefined="PAD_FOOTING")

    def add_piles(self):
        c, p = spec.PILE_CAP, spec.PILES
        h = c["size"] / 2
        self.pile_cap = self.box("IfcFooting", "PC-1", "Foundation", c["cx"] - h, c["cy"] - h, c["z0"],
                                 c["cx"] + h, c["cy"] + h, c["z1"], predefined="PILE_CAP")
        self.piles = []
        for i, (x, y) in enumerate(spec.pile_centres(), 1):
            e = run("root.create_entity", self.f, ifc_class="IfcPile", name=f"P-{i}", predefined_type="BORED")
            prof = self.f.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=p["d"] / 2)
            rep = run("geometry.add_profile_representation", self.f, context=self.body, profile=prof, depth=p["length"])
            run("geometry.assign_representation", self.f, product=e, representation=rep)
            run("geometry.edit_object_placement", self.f, product=e,
                matrix=self.placement((x, y, c["z0"] - p["length"])), is_si=True)
            run("spatial.assign_container", self.f, relating_structure=self.storeys["Foundation"], products=[e])
            self.piles.append(e)

    def material(self, name, category):
        if name not in self.materials:
            self.materials[name] = run("material.add_material", self.f, name=name, category=category)
        return self.materials[name]

    def rebar(self, name, points, d, storey, closed=False):
        bar = run("root.create_entity", self.f, ifc_class="IfcReinforcingBar", name=name,
                  predefined_type="LIGATURE" if closed else "MAIN")
        pts = [self.f.createIfcCartesianPoint(tuple(float(c) for c in p)) for p in points]
        if closed:  # a link: stop just short of the start (a closed polyline does not sweep reliably)
            p0, p1 = np.array(points[0], float), np.array(points[-1], float)
            pts.append(self.f.createIfcCartesianPoint(tuple(float(c) for c in (p0 + (p1 - p0) * 0.85))))
        solid = self.f.create_entity("IfcSweptDiskSolid", Directrix=self.f.create_entity("IfcPolyline", Points=pts),
                                     Radius=d / 2)
        rep = self.f.create_entity("IfcShapeRepresentation", ContextOfItems=self.body, RepresentationIdentifier="Body",
                                   RepresentationType="AdvancedSweptSolid", Items=[solid])
        run("geometry.assign_representation", self.f, product=bar, representation=rep)
        run("geometry.edit_object_placement", self.f, product=bar, matrix=np.eye(4), is_si=True)
        run("spatial.assign_container", self.f, relating_structure=self.storeys[storey], products=[bar])
        bar.NominalDiameter = d
        run("material.assign_material", self.f, products=[bar], material=self.material(spec.REBAR["steel"], "steel"))
        return bar

    def add_rebar(self):
        R = spec.REBAR
        rc = R["column"]
        x, y = spec.column_marks()["C-A1"]
        h = spec.COLUMN["size"] / 2
        off = h - rc["cover"] - rc["link_d"] - rc["long_d"] / 2
        self.bars = []
        for i, (sx, sy) in enumerate([(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)], 1):
            self.bars.append(self.rebar(f"C-A1 V{i}", [(x + sx * off, y + sy * off, 0.0),
                                                        (x + sx * off, y + sy * off, spec.COLUMN["z1"])],
                                        rc["long_d"], "Level 0"))
        lo = h - rc["cover"] - rc["link_d"] / 2
        n = int((spec.COLUMN["z1"] - 0.10) / rc["link_s"]) + 1
        for k in range(n):
            z = 0.05 + k * rc["link_s"]
            self.bars.append(self.rebar(f"C-A1 L{k+1}", [(x - lo, y - lo, z), (x + lo, y - lo, z), (x + lo, y + lo, z),
                                                         (x - lo, y + lo, z)], rc["link_d"], "Level 0", closed=True))
        rf, f = R["footing"], spec.FOOTING
        hf = f["size"] / 2
        n = int((f["size"] - 2 * rf["cover"] - rf["d"]) / rf["s"]) + 1
        z1 = f["z0"] + rf["cover"] + rf["d"] / 2
        z2 = z1 + rf["d"]
        first = -hf + rf["cover"] + rf["d"] / 2
        for k in range(n):
            t = first + k * rf["s"]
            self.bars.append(self.rebar(f"F-A1 X{k+1}", [(x - hf + rf["cover"], y + t, z1), (x + hf - rf["cover"], y + t, z1)],
                                        rf["d"], "Foundation"))
            self.bars.append(self.rebar(f"F-A1 Y{k+1}", [(x + t, y - hf + rf["cover"], z2), (x + t, y + hf - rf["cover"], z2)],
                                        rf["d"], "Foundation"))

    def concrete(self, el, cls, exposure):
        run("material.assign_material", self.f, products=[el], material=self.material(f"Concrete {cls}", "concrete"))
        pset = run("pset.add_pset", self.f, product=el, name="Pset_ConcreteElementGeneral")
        run("pset.edit_pset", self.f, pset=pset, properties={"StrengthClass": cls, "ExposureClass": exposure})

    def add_concrete_data(self):
        for e in self.columns.values():
            self.concrete(e, spec.COLUMN["concrete"], spec.COLUMN["exposure"])
        for e in self.beams.values():
            self.concrete(e, spec.BEAM["concrete"], spec.BEAM["exposure"])
        for e in self.walls.values():
            self.concrete(e, spec.CORE["concrete"], spec.CORE["exposure"])
        self.concrete(self.slab, spec.SLAB["concrete"], spec.SLAB["exposure"])
        for e in list(self.footings.values()) + [self.pile_cap]:
            self.concrete(e, spec.FOOTING["concrete"], spec.FOOTING["exposure"])
        for e in self.piles:
            self.concrete(e, spec.PILES["concrete"], spec.PILES["exposure"])
        self.concrete(self.stair, "C30/37", "XC1")

    def add_groups(self):
        g1 = run("group.add_group", self.f, name="Ground Floor Columns")
        run("group.assign_group", self.f, products=list(self.columns.values()), group=g1)
        g2 = run("group.add_group", self.f, name="Level 1 Beams")
        run("group.assign_group", self.f, products=list(self.beams.values()), group=g2)

    # section 4 ---------------------------------------------------------------
    def add_types(self):
        self.types = {}
        for cls, name in spec.TYPES.items():
            t = run("root.create_entity", self.f, ifc_class=cls + "Type", name=name)
            self.types[cls] = t
        run("type.assign_type", self.f, related_objects=list(self.columns.values()), relating_type=self.types["IfcColumn"],
            should_map_representations=False)
        run("type.assign_type", self.f, related_objects=list(self.beams.values()), relating_type=self.types["IfcBeam"],
            should_map_representations=False)
        run("type.assign_type", self.f, related_objects=list(self.footings.values()), relating_type=self.types["IfcFooting"],
            should_map_representations=False)

    def add_catalogue(self, csv_rows):
        for row in csv_rows:
            t = self.types["IfcColumn"] if row["Name"] == spec.TYPES["IfcColumn"] else \
                run("root.create_entity", self.f, ifc_class="IfcColumnType", name=row["Name"])
            pset = run("pset.add_pset", self.f, product=t, name="TB01_TypeData")
            run("pset.edit_pset", self.f, pset=pset, properties={"Width": float(row["Width_mm"]), "Depth": float(row["Depth_mm"])})

    def add_custom_pset(self):
        groups = {"IfcColumn": self.columns.values(), "IfcBeam": self.beams.values(), "IfcSlab": [self.slab],
                  "IfcWall": self.walls.values()}
        for cls, els in groups.items():
            for e in els:
                pset = run("pset.add_pset", self.f, product=e, name=spec.CUSTOM_PSET)
                run("pset.edit_pset", self.f, pset=pset, properties={"FireResistance": spec.FIRE[cls],
                                                                     "DesignWorkingLife": spec.DESIGN_LIFE})

    # section 7 ---------------------------------------------------------------
    def add_quantities(self):
        import ifcopenshell.geom
        s = ifcopenshell.geom.settings()
        s.set("use-world-coords", True)
        names = {"IfcColumn": "Qto_ColumnBaseQuantities", "IfcBeam": "Qto_BeamBaseQuantities",
                 "IfcSlab": "Qto_SlabBaseQuantities", "IfcWall": "Qto_WallBaseQuantities",
                 "IfcFooting": "Qto_FootingBaseQuantities"}
        for cls, qname in names.items():
            for e in self.f.by_type(cls):
                sh = ifcopenshell.geom.create_shape(s, e)
                v = np.array(sh.geometry.verts).reshape(-1, 3)
                fc = np.array(sh.geometry.faces).reshape(-1, 3)
                a, b, c = v[fc[:, 0]], v[fc[:, 1]], v[fc[:, 2]]
                vol = abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6)
                q = run("pset.add_qto", self.f, product=e, name=qname)
                run("pset.edit_qto", self.f, qto=q, properties={"NetVolume": vol})


def build(stage="full"):
    """Build TB-01 up to a stage: s1, s2, s3, s4 or full."""
    import csv
    m = TB01()
    m.set_location()
    m.add_storeys()
    m.add_grid()
    if stage == "s1":
        return m
    m.add_columns()
    m.add_core_walls()
    m.add_slab()
    m.add_beams()
    if stage == "s2":
        return m
    m.add_stair()
    m.add_footings()
    m.add_piles()
    m.add_rebar()
    m.add_concrete_data()
    m.add_groups()
    if stage == "s3":
        return m
    m.add_types()
    with open(os.path.join(HERE, "..", "..", "checker", "bimcheck", "data", "column_types.csv"), encoding="utf-8") as fh:
        m.add_catalogue(list(csv.DictReader(fh)))
    m.add_custom_pset()
    if stage == "s4":
        return m
    m.add_quantities()
    return m


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    for st in ("s1", "s2", "s3", "s4", "full"):
        print(build(st).write(os.path.join(out, f"tb01_{st}.ifc")))
