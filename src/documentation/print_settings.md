# Print Settings

> **No printer is known to this project.** Nothing below is a claim of
> compatibility with a specific machine. The values are a documented,
> configurable assumption set for a generic FDM printer and must be calibrated
> against the printer that will actually produce the parts.

## 1. Assumed printer and material

| Parameter | Assumption | Why |
|---|---|---|
| Technology | FDM (also usable for resin) | the geometry is solid, closed and undercut-free at the chosen scale |
| Build volume | 250 × 250 × 250 mm | the most common "large" desktop FDM bed; the modular set also fits a 200 mm bed |
| Nozzle | 0.4 mm | the reference for wall thicknesses, layer height and support rules |
| Layer height | 0.20 mm | 0.4 mm nozzle, 50 % of the nozzle diameter |
| Material | PLA (easiest) or PETG (tougher) | a 240 mm long part in PLA warps easily; PETG is the safer choice for the master model |
| Infill | 15 % for walls and plates, 20 % for the temple block | the temple block is the only part with long unsupported spans |
| Cooling | 100 % after layer 3 | the model has no fine features that need slow cooling, but the courtyard floor does |
| Supports | tree/organic supports only where noted | see §5 |

## 2. Thickness rules used while modelling

| Feature class | Minimum | Where it comes from |
|---|---|---|
| Main structural walls (compound wall, hall walls, cella walls) | 1.2 mm modelled (2.4 mm = 6 perimeters recommended) | 3 × 0.4 mm extrusion width; the model walls are 1.0–1.4 m real, i.e. 1.0–1.4 mm at 1:1000 |
| Base plate | 1.2 mm (three layers of 0.4 mm) | flat, stable contact surface |
| Decorative features (cornices, pilasters, *kuta* motifs) | 0.9–1.0 mm | 2–2.5 extrusion widths, the smallest feature the builder will emit (detail amplification) |
| Plinth steps | 0.5 mm rise (2.5 layers) | 0.8/0.6/0.5 m real steps at 1:1000 |
| Pillars (prakara columns) | 0.6 mm ⌀ | 1.5 extrusion widths — the weakest feature in the model, see §5 |
| Finial, Nandi horns, small motifs | 0.8 mm | detail amplification minimum |

The builder enforces these by amplifying any modelled feature that would fall
below the minimum (`TempleBuilder.amp`), so the exported mesh contains no
sub-millimetre detail.

## 3. Joints and clearances

| Joint | Type | Clearance per side | Notes |
|---|---|---|---|
| Foundation west ↔ east plate | butt joint + 2 mm dowels | 0.30 mm | the joint lies in the open courtyard at x = +61.5 m real |
| Temple block ↔ foundation | locating spigot + socket | 0.30 mm | `Roof_Spigot` / `Roof_Socket` in the FreeCAD model |
| Wall ↔ wall modules | flat key 4 × 2.8 × 8 mm | 0.30 mm | `Wall_Key` |
| Alignment dowels | ⌀2.0 mm pin into a ⌀2.6 mm socket | 0.30 mm | `Alignment_Pin` / `Alignment_Socket` |
| Removable roof (cut-away model) | ⌀6.0 mm spigot | 0.30 mm | `Roof_Interface` |
| Fit-test coupon | same dowel geometry as the real joint | 0.30 mm | `Fit_Test_Coupon` — print this first |

**Calibration note.** 0.30 mm per side is a starting value for a well-tuned
FDM machine. Measure one printed coupon, adjust the clearance in
`src/scripts/cad/generate_cad.py` (`CLEARANCE`), re-export the STEP files and
reprint. Never apply one clearance value to every joint: a large flat butt
joint may need 0.2 mm, while a cylindrical dowel in a hole typically needs
0.25–0.35 mm because of the shrinkage of the hole.

## 4. Module sizes and build-volume fit

| Module | Size (mm) | Fits 250 mm bed | Fits 200 mm bed |
|---|---|---|---|
| MOD_01 Foundation West | 101.0 × 123.9 × 1.6 | yes | yes |
| MOD_02 Foundation East | 141.8 × 123.9 × 1.6 | yes | yes |
| MOD_03 Temple Block | 72.8 × 32.8 × 65.8 | yes | yes |
| MOD_04 Gopurams | 88.5 × 14.0 × 31.2 | yes | yes |
| MOD_05 Compound Wall | 240.8 × 121.9 × 3.5 | yes (bed edge to edge) | no — split at the courtyard gate or print as four straight runs |
| MOD_06 Prakara | 174.2 × 80.8 × 4.8 | yes | no — print as four straight arms |
| MOD_07 Courtyard Shrines | 8.0 × 35.5 × 9.0 | yes | yes |
| Exterior (single file) | 242.8 × 123.9 × 67.0 | yes | no |
| Cut-away core | 227.5 × 51.2 × 205.8 | yes | no (height) |

## 5. Orientation, overhangs and supports

| Part | Recommended orientation | Overhangs | Support |
|---|---|---|---|
| MOD_01/02 foundation plates | flat on the bed (as modelled) | none | none |
| MOD_03 temple block | **upside down**: the vimana tip on the bed | the plinth steps and the hall cornices become the top surfaces; the tower's cornices then overhang by ≤ 0.9 mm, well within a 45° limit | none or light tree supports for the hall roofs |
| MOD_04 gopurams | base down | the stepped storeys are self-supporting (each step is set back) | tree support for the crowning *sikhara* |
| MOD_05 compound wall | flat on the bed | none | none |
| MOD_06 prakara | flat on the bed | the colonnade columns are vertical, the roof is flat | none; the 0.6 mm columns are the fragile feature |
| MOD_07 shrines | base down | the domed *sikhara* overhangs at ~60° | light support |
| Nandi bull | on its pedestal, legs down | the muzzle overhangs ~1 mm | none |
| Cut-away core | as the temple block, but print the sectioned half with the cut face on the bed if the section is not wanted | — | — |

**Fragile features to watch.** The prakara columns (0.6 mm ⌀) and the Nandi
horns (0.8 mm) are the two places where the model is closest to the limit of
the process. If they break, increase the minimum detail from 0.9 mm to 1.2 mm
in `temple_params.MIN_PRINTABLE_DETAIL_MM` and regenerate.

**Warp.** The 240 mm master model is long and flat; print it in PLA only with
a brim and a closed chamber, or in PETG. The two foundation plates should be
printed with a brim, as they are the largest single-layer area.

## 6. Resin printing

The same geometry is valid for SLA/MSLA:

* tilt the model so the base plate is on the build plate, or print the
  temple block tilted 30–45° with supports for the tower;
* 0.05 mm layers reproduce the amplified details exactly;
* wash and cure fully — the 0.9 mm features trap resin;
* the sectioned cut-away model is a single piece with one flat cut face and
  is the easiest part to print in resin.

## 7. Print order

1. `FITTEST_Coupon` (`src/models/stl/hardware/FITTEST_Coupon.stl`, 20 × 20 × 6 mm
   with a ⌀2.2 mm hole and a loose ⌀2.0 mm dowel) — check the clearance, then
   set the final clearance and re-export the STEP and STL hardware.
2. `MOD_01` and `MOD_02` — the foundation plates (flat, no supports).
3. `MOD_06` — the prakara (flat).
4. `MOD_05` — the compound wall (flat).
5. `MOD_07` — the courtyard shrines.
6. `MOD_04` — the gopurams.
7. `MOD_03` — the temple block (the largest and slowest part).
8. The cut-away core model, if the interior is to be printed as well.
