# Project Plan — Brihadisvara Temple Architectural Model

## 1. Objective

Deliver a historically informed, architecturally coherent, **manufacturable**
3-D model of the Brihadisvara Temple (Peruvudaiyar Kovil), Thanjavur, together
with the assets required to inspect, print and reproduce it:

* an editable Blender project of the complete exterior complex,
* a sectioned (cut-away) model that exposes the connected interior,
* a modular print set that fits a 250 mm FDM build volume,
* parametric FreeCAD engineering components (STEP),
* validated STL files, rendered previews, an automated pipeline and tests.

The model is an **architectural interpretation**, not a survey reconstruction.
Every dimension is either cited or explicitly flagged as an interpretation.

## 2. Milestones and status

| # | Milestone | Deliverables | Status |
|---|---|---|---|
| 0 | Environment audit | `src/documentation/environment_audit.md` | done |
| 1 | Project structure | `.gitignore`, `src/` tree, README | done |
| 2 | Reference acquisition | `src/references/images/*`, `image_manifest.json`, `sources.md` | done (44 images) |
| 3 | Architecture & dimension plan | `architecture_analysis.md`, `model_dimensions.md`, `historical_assumptions.md` | done |
| 4 | Toolchain decision | `toolchain_decision.md` | done |
| 5 | Exterior model | `brihadisvara_exterior.blend` / `.stl` / 4 previews | done |
| 6 | Connected interior + cut-away | `brihadisvara_cutaway.blend` / `.stl` / 4 previews | done |
| 7 | Modular print set | `src/models/stl/modules/*.stl` (7 modules) | done |
| 8 | FreeCAD engineering parts | `brihadisvara_engineering.FCStd`, 6 STEP files | done |
| 9 | Export pipeline | `export_models.py`, `export_manifest.json` | done |
| 10 | Mesh validation | `validate_meshes.py`, `validation_report.md` | done |
| 11 | Preview review | 8 preview renders | done |
| 12 | Tests | `tests/` (39 tests) | done |
| 13 | Documentation | this file and the rest of `src/documentation/` | done |

## 3. Key architectural decisions

1. **Two scales, one geometry.** The complete complex is modelled at 1:1000
   (1 mm of model = 1 m of building) so that the historically correct
   proportions of the 240.79 m × 121.92 m compound are preserved. The
   cut-away core model uses the same parametric source at 1:320 so that the
   interior (pillars, cella, linga, Nandi) is large enough to read and to
   print. Both share the same origin and axis convention.
2. **Coordinate system.** X = east–west (the long axis of the complex),
   Y = north–south, Z = up, Z = 0 at the underside of the base plate. The
   origin is the centre of the sanctum.
3. **Detail amplification.** Features that would be thinner than the
   printer's nozzle at the master scale (cornice projections, pilaster
   depths, kuta motifs) are amplified to a printable minimum instead of being
   dropped, which is standard architectural-model practice.
4. **No booleans in the source geometry.** The model is built from explicit
   vertex/face lists, so it is deterministic and reproducible. The only
   boolean in the pipeline is the section cut applied to the cut-away variant.
5. **Blender for form, FreeCAD for fit.** Ornament and massing are meshes;
   anything that needs a controlled tolerance (base plates, dowels, spigots,
   keys) is a FreeCAD solid with a real clearance.

## 4. Risks and mitigations

| Risk | Mitigation |
|---|---|
| The complete complex does not fit a small printer | modular print set; every module ≤ 142 mm |
| 1:1000 makes the ornament sub-printable | detail amplification + 1:320 detail model |
| Reference photographs are not measured drawings | every dimension is cited or marked as an interpretation |
| Blender/FreeCAD not installed on a fresh machine | `blender.sh` / `freecad.sh` wrappers document the flatpak route |
| The host filesystem rejects a file name | documented in `environment_audit.md`; the CAD script lives in `src/scripts/cad/` |

## 5. Out of scope

* Photogrammetric or laser-scanned reconstruction.
* The Chola frescoes, the brass Nataraja and the 13th-century mural programme
  (represented geometrically only as the wall surfaces that carry them).
* Structural analysis, load paths and material specification of the original
  building.
* Slice files (no slicer is installed on the build host).
