# Model Dimensions

All design values live in `src/scripts/temple_params.py` as **real-world
metres**; the model scale is applied at build time. This document explains
where each value comes from and how the printed sizes follow from it.

## 1. Coordinate system and units

| Axis | Direction | Notes |
|---|---|---|
| `X` | east–west | the long axis of the complex (240.79 m); the temple faces **+X** (east) |
| `Y` | north–south | the short axis of the complex (121.92 m) |
| `Z` | up | `Z = 0` is the underside of the base plate (the printing bed contact) |

* Origin `(0, 0, 0)` = the centre of the sanctum (garbhagriha), which is also
  the centre of the vimana and of the main axis.
* Model space is **millimetres**. In Blender, one Blender unit = 1 mm
  (`scene.unit_settings.scale_length = 0.001`, length unit millimetres) and
  STL export runs with `global_scale = 1.0`, `use_scene_unit = False`, so the
  STL coordinates are true millimetres. FreeCAD works natively in mm.
* The prompt's shorthand "X = width, Y = length" is applied to the *core
  building* (north–south width along Y, east–west length along X). Because
  the whole compound is wider east–west than north–south, the compound's long
  dimension necessarily runs along X.

## 2. Scale strategy

| Variant | Scale | Model mm per real metre | Why |
|---|---|---|---|
| Exterior (master) | 1:1000 | 1.0 | keeps the historic proportions of the 240.79 × 121.92 m compound; 1 mm of model = 1 m of building, so every real-world metre-sized feature is a printable millimetre |
| Cut-away core | 1:320 | 3.125 | the interior (0.6 m pillars, 2 m doorways, the 5.94 m Nandi) becomes large enough to read and to print |
| FreeCAD engineering parts | 1:1000 | 1.0 | the parts mate with the master model |

Both Blender variants are generated from the **same** parametric source, so
the cut-away model is provably the same building as the exterior model.

## 3. Principal dimensions (real metres → master model millimetres)

| Element | Real | Model @1:1000 | Source |
|---|---|---|---|
| Compound, east–west | 240.79 m | 240.79 mm | Balasubrahmanyam via Wikipedia |
| Compound, north–south | 121.92 m | 121.92 mm | Balasubrahmanyam via Wikipedia |
| Overall temple height (finial tip) | 65.83 m | 65.83 mm | Wikipedia infobox |
| Vimana base (aditala) | 30.18 m square | 30.18 mm | Balasubrahmanyam via Wikipedia |
| Tapering storeys | 13 | 13 | Wikipedia |
| Storey height | 2.87 m (derived) | 2.87 mm | derived so the total equals 65.83 m |
| Griva block | 7.77 m square | 7.77 mm | Wikipedia |
| Corner Nandi | 1.98 × 1.68 m | 1.98 × 1.68 mm | Wikipedia |
| Finial (stupi) | 3.81 m | 3.81 mm | Wikipedia |
| Inner gopuram height | 30.0 m | 30.0 mm | Wikipedia |
| Gopuram storeys | 5 | 5 | Wikipedia (five-storey gopuram) |
| Nandi bull | 5.94 × 2.59 × 3.65 m | 5.94 × 2.59 × 3.65 mm | Wikipedia (3.65 / 5.94 / 2.59 m, 25 t) |
| Linga | 8.70 m high | 8.70 mm | Wikipedia |
| Prakara circumambulation | ~450 m | ~450 mm perimeter | Balasubrahmanyam via Wikipedia |
| Cella (garbhagriha) | 6.4 m square | 6.4 mm | interpretation (see below) |
| Sanctuary block height | 12.5 m | 12.5 mm | interpretation |
| Maha-mandapa | 17.8 × 15.0 m | 17.8 × 15.0 mm | interpretation, sized from the six-pillar rule |
| Mukha-mandapa | 11.1 × 11.2 m | 11.1 × 11.2 mm | interpretation, square plan per source |
| Nandi mandapa | 12.0 × 11.0 m | 12.0 × 11.0 mm | interpretation, must contain the 5.94 m bull |
| Platform (3 courses) | 1.9 m | 1.9 mm | interpretation of the moulded plinth |
| Compound wall | 3.5 m high, 1.2 m thick | 3.5 / 1.2 mm | interpretation of the enclosure wall |

## 4. Axial plan (real metres, origin at the sanctum)

| Element | X from | X to |
|---|---|---|
| West enclosure wall | −45.00 | −44.80 (1.2 m thick) |
| Vimana base (aditala) | −15.09 | +15.09 |
| Cella (garbhagriha) | −3.20 | +3.20 |
| Ambulatory passage, outer wall | −5.70 | +5.70 |
| Antrala (vestibule) | +5.70 | +8.30 |
| Maha-mandapa | +8.30 | +26.10 |
| Mukha-mandapa | +26.10 | +37.20 |
| Nandi mandapa | +40.70 | +52.70 |
| Nandi bull (centre) | +48.53 | +54.47 (5.94 m long) |
| Inner gopuram (Rajarajan tiruvasal) | +97.00 | +103.00 |
| Outer gopuram (Keralantakan tiruvasal) | +174.00 | +180.00 |
| East enclosure wall | +195.79 | inward by 1.2 m |

The temple block therefore occupies the western part of the compound and the
courtyard the eastern part, which matches the published description of the
inner gopuram leading into the courtyard with the main temple at its far end.

## 5. Printed sizes actually produced

| File | Size (mm) | Triangles |
|---|---|---|
| `brihadisvara_exterior.stl` | 242.79 × 123.92 × 67.04 | 15 834 |
| `brihadisvara_cutaway.stl` | 227.47 × 51.22 × 205.75 | 7 355 |
| `brihadisvara_cutaway_roof.stl` (lift-off roof) | 140.94 × 24.53 × 11.56 | 190 |
| `MOD_01_Foundation_West.stl` | 101.00 × 123.92 × 1.60 | 24 |
| `MOD_02_Foundation_East.stl` | 141.79 × 123.92 × 1.60 | 24 |
| `MOD_03_Temple_Block.stl` | 72.79 × 32.78 × 65.84 | 9 934 |
| `MOD_04_Gopurams.stl` | 88.50 × 14.00 × 31.20 | 1 400 |
| `MOD_05_Compound_Wall.stl` | 240.79 × 121.92 × 3.50 | 60 |
| `MOD_06_Prakara.stl` | 174.23 × 80.80 × 4.80 | 4 176 |
| `MOD_07_Courtyard_Shrines.stl` | 8.00 × 35.50 × 9.00 | 240 |

Sizes are measured from the exported STL files by `src/scripts/validate_meshes.py`
and are reproduced in `src/documentation/validation_report.md`.

## 6. Relation to the target dimensions in the brief

The brief suggested a complete assembled model of roughly 220–250 mm long,
170–200 mm wide and 200–250 mm high. The project delivers two complementary
models rather than forcing one box to hit all three numbers, because the
historic proportions cannot satisfy them simultaneously:

| Target | Master model (1:1000) | Core model (1:320) | Comment |
|---|---|---|---|
| Length 220–250 mm | **242.8 mm** ✔ | **227.5 mm** ✔ | both inside the target |
| Width 170–200 mm | 123.9 mm ✘ | 51.2 mm ✘ (94 mm for the full core) | the compound is only 121.92 m wide against 240.79 m long; widening it would falsify the plan |
| Height 200–250 mm | 67.0 mm ✘ | **205.8 mm** ✔ | the vimana is 65.83 m against a 240.79 m compound; the height target is only reachable by modelling the core at a larger scale |

The core model therefore delivers the requested *height* while the master
model delivers the requested *length*, and both are faithful to the same
parametric source.

## 7. Detail amplification

At 1:1000 a real 0.3 m cornice would be 0.3 mm — thinner than a 0.4 mm
nozzle. Rather than dropping those features, the builder amplifies them to a
printable minimum of **0.9 mm** (cornices, pilaster depths) and **1.0 mm**
(motif widths), and the amplification is applied in a single place
(`TempleBuilder.amp`). The rule is: *no modelled detail is thinner than the
printable minimum, and no detail is invented that is not visible in the
reference photographs*.
