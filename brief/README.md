# TB-01 Training Building: the project brief

This is the building you model through the whole course. It is fictional. Every number below comes from
[`checker/bimcheck/spec.py`](../checker/bimcheck/spec.py), the same file the checker reads, so the brief and the
checks always agree. Lengths are in metres; levels are measured from Level 0 (+0.000).

Drawings: [Level 1 framing plan](drawings/TB-01_brief_level1_framing_plan.svg), [section through grid 2](drawings/TB-01_brief_section_grid2.svg), [foundation plan](drawings/TB-01_brief_foundation_plan.svg).

## Project and site

| Item | Value |
|---|---|
| Project name | TB-01 Training Building |
| Site name | TB-01 Site |
| Building name | TB-01 |
| Latitude, longitude | 38.7369, -9.1427 (a fictional plot in Lisbon) |
| Elevation of Level 0 above sea level | 90.0 m |
| True north | 12 degrees clockwise from project north (+Y) |
| Units | metres (or millimetres) |

## Levels

| Level | Elevation |
|---|---|
| Foundation | -1.200 |
| Level 0 | +0.000 |
| Level 1 | +3.600 |
| Level 2 | +7.200 |
| Roof | +10.800 |

Structural levels are at the top of the structural slab. The Foundation level is the underside of the pad footings.

## Grid

| Axis | Position | Direction |
|---|---|---|
| A | x = 0.000 | parallel to Y |
| B | x = 6.000 | parallel to Y |
| C | x = 12.000 | parallel to Y |
| D | x = 18.000 | parallel to Y |
| 1 | y = 0.000 | parallel to X |
| 2 | y = 7.000 | parallel to X |
| 3 | y = 14.000 | parallel to X |

Grid lines extend 2 m past the outer grids.

## Ground floor structure (Level 0 to Level 1)

- **Columns**: 400 x 400 mm at all 12 grid intersections, named by grid (C-A1 ... C-D3), from +0.000 up to the slab soffit +3.350. Concrete C30/37, exposure XC1.
- **Core walls**: four load-bearing walls, 250 mm thick, forming a core from x 7.5 to 10.5 and y 9.0 to 12.0 (outside faces), from +0.000 to +3.350. The architect's model ([`datasets/architect_model.ifc`](../datasets/architect_model.ifc)) holds the same walls; trace them from it.
- **Level 1 slab**: 250 mm, top +3.600, edges at the outer column faces (x -0.2 to 18.2, y -0.2 to 14.2). Two openings: the core (x 7.75 to 10.25, y 9.25 to 11.75) and the stair (x 13.0 to 14.2, y 1.0 to 6.4). Volume 63.06 m3.
- **Beams**: on every grid line, between column faces, 300 wide x 350 deep below the soffit (+3.000 to +3.350). Model only the downstand: the slab above is not counted twice. Names: B-1/AB means the beam on grid 1 between grids A and B. 17 beams.
- **Stair**: one straight flight, 1.2 m wide between x 13.0 and 14.2, starting at y 1.0 and rising in +Y: 20 risers of 180 mm, treads 280 mm, The last riser is at y 6.32; the slab opening ends at y 6.40, and the 80 mm between them is the top step onto the slab (a short top tread in Bonsai; in FreeCAD the slab edge closes it). Concrete C30/37.

## Foundations

- **Pad footings**: 1.8 x 1.8 x 0.6 m under every column, top -0.600, named F-A1 ... F-D3. Concrete C25/30, exposure XC2.
- **Pile cap** PC-1: 4.0 x 4.0 x 1.0 m centred on the core (x 9.0, y 10.5), top -0.600.
- **Piles**: four, 600 mm diameter, 12 m long, 1.2 m each way from the core centre, from the underside of the cap. Concrete C25/30.

Not modelled in this course: the column stubs and core walls between the foundations (-0.600) and Level 0, the ground slab, and starter bars and laps. That is why columns and walls start at +0.000.

## Reinforcement (exercise 3.4)

- Steel grade A500 (A500 NR, the Portuguese designation of a 500 MPa ribbed bar; B500B or B500C in EN 1992-1-1 and EN 10080 terms).
- **Column C-A1**: 8 vertical bars Ø16 (four corners and four mid-sides), links Ø8 at 150 mm, 30 mm nominal cover to the links.
- **Footing F-A1**: bottom mesh Ø16 at 150 mm each way, centred in the footing (12 bars each way, from -825 to +825 mm about the footing centre), 50 mm cover (the footing is cast on blinding; concrete cast directly against soil needs at least 75 mm).

## Data

| Element | Concrete | Exposure | Fire resistance | Type name |
|---|---|---|---|---|
| Columns | C30/37 | XC1 | R90 | RC Column 400x400 |
| Beams | C30/37 | XC1 | R60 | RC Beam 300x350 downstand |
| Slab | C30/37 | XC1 | REI60 | |
| Core walls | C30/37 | XC1 | REI90 | |
| Pad footings | C25/30 | XC2 | | Pad Footing 1800x1800x600 |
| Pile cap and piles | C25/30 | XC2 | | |
| Stair | C30/37 | XC1 | | |

Custom property set **TB01_Structural**: FireResistance (above) and DesignWorkingLife = 50.

## Drawings to produce (sections 5 and 6)

- Sheet **S-101**, title **LEVEL 1 FRAMING PLAN**, scale 1:100.
- Revisions: A First issue; B Core walls revised.
- Detail title: **TYPICAL COLUMN FOOTING DETAIL**.

The concrete classes and exposure classes follow EN 206 and Eurocode 2 notation. They are a reasonable choice for a teaching model, not a design: a real project sets them from its own exposure and the National Annex.
