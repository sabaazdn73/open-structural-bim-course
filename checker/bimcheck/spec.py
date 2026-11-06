"""The project brief as data: the single source of truth for every number in the course.

TB-01 Training Building is fictional. All lengths are in metres; z is measured from
Level 0 (+0.000). The lessons, the brief drawings, the datasets, the reference solutions
and the checkers all read from this file, so they cannot drift apart.
"""

PROJECT = {
    "project_name": "TB-01 Training Building",
    "site_name": "TB-01 Site",
    "building_name": "TB-01",
    "latitude": 38.7369,        # decimal degrees (fictional plot in Lisbon)
    "longitude": -9.1427,
    "site_elevation": 90.0,     # metres above sea level at Level 0
    "true_north_deg": 12.0,     # true north is 12 degrees clockwise from project north (+Y)
}

STOREYS = [  # name, elevation of the storey (structural level, top of slab)
    ("Foundation", -1.200),
    ("Level 0", 0.000),
    ("Level 1", 3.600),
    ("Level 2", 7.200),
    ("Roof", 10.800),
]

GRID_X = {"A": 0.0, "B": 6.0, "C": 12.0, "D": 18.0}   # lettered axes: lines parallel to Y at these x
GRID_Y = {"1": 0.0, "2": 7.0, "3": 14.0}               # numbered axes: lines parallel to X at these y

SLAB_T = 0.25                      # Level 1 slab thickness
SLAB_TOP = 3.600
SLAB_SOFFIT = SLAB_TOP - SLAB_T    # 3.350: columns and walls stop here

COLUMN = {"size": 0.40, "z0": 0.0, "z1": SLAB_SOFFIT, "concrete": "C30/37", "exposure": "XC1"}

def column_marks():
    """Column marks and centres: C-A1 ... C-D3."""
    return {f"C-{gx}{gy}": (x, y) for gx, x in GRID_X.items() for gy, y in GRID_Y.items()}

# Core walls (the architect's model holds the same four walls, flagged load-bearing).
CORE = {"x0": 7.5, "y0": 9.0, "x1": 10.5, "y1": 12.0, "t": 0.25, "z0": 0.0, "z1": SLAB_SOFFIT,
        "concrete": "C30/37", "exposure": "XC1"}

def core_walls():
    """The four core walls as axis-aligned boxes (x0, y0, x1, y1)."""
    c, t = CORE, CORE["t"]
    return {
        "W-Core-S": (c["x0"], c["y0"], c["x1"], c["y0"] + t),
        "W-Core-N": (c["x0"], c["y1"] - t, c["x1"], c["y1"]),
        "W-Core-W": (c["x0"], c["y0"] + t, c["x0"] + t, c["y1"] - t),
        "W-Core-E": (c["x1"] - t, c["y0"] + t, c["x1"], c["y1"] - t),
    }

STAIR = {"x0": 13.0, "x1": 14.2, "y0": 1.0, "risers": 20, "riser": 0.18, "going": 0.28,
         "z0": 0.0, "z1": SLAB_TOP}
STAIR["y1"] = STAIR["y0"] + (STAIR["risers"] - 1) * STAIR["going"]   # 6.32

SLAB = {
    "x0": -0.2, "y0": -0.2, "x1": 18.2, "y1": 14.2, "z0": SLAB_SOFFIT, "z1": SLAB_TOP,
    "openings": {
        "core": (CORE["x0"] + CORE["t"], CORE["y0"] + CORE["t"], CORE["x1"] - CORE["t"], CORE["y1"] - CORE["t"]),
        "stair": (STAIR["x0"], STAIR["y0"], STAIR["x1"], 6.4),
    },
    "concrete": "C30/37", "exposure": "XC1",
}

def slab_volume():
    s = SLAB
    area = (s["x1"] - s["x0"]) * (s["y1"] - s["y0"])
    for x0, y0, x1, y1 in s["openings"].values():
        area -= (x1 - x0) * (y1 - y0)
    return area * SLAB_T

# Beams: downstand part only (the slab is not counted twice), 300 wide x 350 deep below the soffit,
# on every grid line, between column faces.
BEAM = {"b": 0.30, "h": 0.35, "z0": SLAB_SOFFIT - 0.35, "z1": SLAB_SOFFIT,
        "concrete": "C30/37", "exposure": "XC1"}

def beams():
    """Beam marks and boxes (x0, y0, x1, y1)."""
    out, hc, hb = {}, COLUMN["size"] / 2, BEAM["b"] / 2
    xs, ys = sorted(GRID_X.items(), key=lambda kv: kv[1]), sorted(GRID_Y.items(), key=lambda kv: kv[1])
    for gy, y in ys:
        for (ga, xa), (gb, xb) in zip(xs, xs[1:]):
            out[f"B-{gy}/{ga}{gb}"] = (xa + hc, y - hb, xb - hc, y + hb)
    for gx, x in xs:
        for (ga, ya), (gb, yb) in zip(ys, ys[1:]):
            out[f"B-{gx}/{ga}{gb}"] = (x - hb, ya + hc, x + hb, yb - hc)
    return out

FOOTING = {"size": 1.8, "t": 0.6, "z0": -1.2, "z1": -0.6, "concrete": "C25/30", "exposure": "XC2"}

PILE_CAP = {"cx": 9.0, "cy": 10.5, "size": 4.0, "t": 1.0, "z0": -1.6, "z1": -0.6,
            "concrete": "C25/30", "exposure": "XC2"}
PILES = {"d": 0.6, "length": 12.0, "offset": 1.2, "concrete": "C25/30", "exposure": "XC2"}

def pile_centres():
    c, o = PILE_CAP, PILES["offset"]
    return [(c["cx"] + sx * o, c["cy"] + sy * o) for sx in (-1, 1) for sy in (-1, 1)]

# Reinforcement exercise (3.4): column C-A1 and footing F-A1.
REBAR = {
    "steel": "A500",
    "column": {"element": "C-A1", "long_n": 8, "long_d": 0.016, "link_d": 0.008, "link_s": 0.150,
               "cover": 0.030},                       # nominal cover to the links
    "footing": {"element": "F-A1", "d": 0.016, "s": 0.150, "cover": 0.050},  # bottom mesh, both ways
}

GROUPS = {"Ground Floor Columns": "IfcColumn", "Level 1 Beams": "IfcBeam"}

TYPES = {"IfcColumn": "RC Column 400x400", "IfcBeam": "RC Beam 300x350 downstand",
         "IfcFooting": "Pad Footing 1800x1800x600"}

CUSTOM_PSET = "TB01_Structural"
FIRE = {"IfcColumn": "R90", "IfcBeam": "R60", "IfcSlab": "REI60", "IfcWall": "REI90"}
DESIGN_LIFE = 50

# Documentation (sections 5 and 6)
SHEET = {"number": "S-101", "title": "LEVEL 1 FRAMING PLAN", "scale": "1:100",
         "revisions": [("A", "First issue"), ("B", "Core walls revised")]}
DETAIL_TITLE = "TYPICAL COLUMN FOOTING DETAIL"

# Section 7
EXPORT = {"schema": "IFC4"}
