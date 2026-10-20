# Assembly Guide

Two assemblies are documented: the **modular exterior** (master scale 1:1000)
and the **cut-away core** (1:320). Both use the same parts language.

## 1. Parts list

### Modular exterior (`src/models/stl/modules/`)

| Part | File | Print orientation | Notes |
|---|---|---|---|
| Foundation, west half | `MOD_01_Foundation_West.stl` | flat | 101 × 124 × 1.6 mm; the courtyard skin is modelled on top |
| Foundation, east half | `MOD_02_Foundation_East.stl` | flat | 142 × 124 × 1.6 mm; mates with the west half at x = +61.5 m real |
| Temple block | `MOD_03_Temple_Block.stl` | vimana tip on the bed | plinth, cella, antrala, both mandapas, Nandi hall, Nandi, the whole vimana and the steps |
| Gopurams | `MOD_04_Gopurams.stl` | bases down | inner (Rajarajan tiruvasal) and outer (Keralantakan tiruvasal) gateway towers |
| Compound wall | `MOD_05_Compound_Wall.stl` | flat | with the eastern gateway opening |
| Prakara | `MOD_06_Prakara.stl` | flat | the pillared veranda that frames the courtyard |
| Courtyard shrines | `MOD_07_Courtyard_Shrines.stl` | bases down | Amman and Murugan shrines |

### Engineering hardware (`src/models/step/`)

| Part | STEP file | Function |
|---|---|---|
| Foundation plates | `foundation_plates.step` | dimensioned base plates with dowel sockets |
| Alignment pin / socket | `alignment_hardware.step` | ⌀2.0 mm dowel and its ⌀2.6 mm sleeve |
| Roof spigot / socket | `roof_interface.step` | ⌀6.0 mm spigot for the removable roof |
| Wall key | `wall_key.step` | 4 × 2.8 × 8 mm flat key |
| Fit-test coupon | `fit_test_coupon.step`, `src/models/stl/hardware/FITTEST_Coupon.stl` | 20 × 20 × 6 mm block with a dowel hole and a loose dowel |
| Printable hardware | `src/models/stl/hardware/*.stl` | the alignment pin/socket, the roof spigot/socket and the wall key, ready to slice |
| Combined | `brihadisvara_engineering_all.step` | every engineering part in one file |

## 2. Assembly sequence — modular exterior

1. **Dry fit the foundation.** Put `MOD_01` and `MOD_02` on the bed and
   push them together along the joint at x = +61.5 m real. The joint face is
   flat; a 0.2 mm gap is normal for FDM. If the joint rocks, scrape or sand
   one face — do not use glue to hide a bad fit.
2. **Install the dowels.** Print two `Alignment_Pin` parts and press them
   into the sockets in `MOD_01` (or drill the sockets if the plate is
   printed without them). The pins locate the two halves so that the seam
   cannot open.
3. **Add the compound wall** (`MOD_05`) to the perimeter of the foundation.
   It is a single flat ring; glue or pin it to the plates at the corners.
4. **Add the prakara** (`MOD_06`) inside the wall. Its four arms meet at the
   corners; the wall keys (`Wall_Key`) can be used to lock the arms together
   before the wall is bonded on.
5. **Add the courtyard shrines** (`MOD_07`) at the positions marked in
   `src/documentation/model_dimensions.md` §4 — 72 m east of the sanctum and
   14 m north/south of the axis.
6. **Add the gopurams** (`MOD_04`). The outer gateway drops into the
   opening in the east wall; the inner gateway stands on the courtyard floor
   at x = +100 m real.
7. **Add the temple block** (`MOD_03`) in the west half of the courtyard.
   It carries its own stepped plinth, which should rest on the courtyard
   skin; use the `Roof_Spigot`/`Roof_Socket` pair to lock it if the fit is
   loose.
8. **Fit the steps** — the stair flight at the east face of the Nandi hall
   is part of the temple block and is printed with it.

## 3. Assembly sequence — cut-away core (1:320)

1. Print the cut-away model as a single part (the section face is flat and
   can be placed against the bed or against a build plate).
2. If the roof is printed separately, locate it with the ⌀6 mm spigot in the
   centre of the sanctuary block; the roof is a push-fit, not a glued joint.
3. Stand the model with the section face facing the viewer: the cella, the
   ambulatory passage, the antrala, the two mandapas and the Nandi hall are
   all open to view.

## 4. Handling and display

* The master model is 243 mm long and weighs little; it is a display model.
  Keep it out of direct sunlight (PLA) and off hot car dashboards.
* The base plate is the datum. When the model is displayed, the *kuttu
  vannam* (courtyard) is the lowest architectural surface and the compound
  wall rises from the plate edge.
* The vimana tip is the most fragile point; when transporting the model, lay
  it on its back on a flat surface.

## 5. Re-printing a single part

Every part is regenerated from the same source:

```bash
src/scripts/blender.sh --background --python src/scripts/generate_temple.py -- --variant modular
```

If only the geometry is needed (no preview renders), add `--no-render`.
The STEP engineering parts are regenerated with:

```bash
src/scripts/freecad.sh src/scripts/cad/generate_cad.py
```
