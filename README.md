# super-duper-spoon

**Brihadisvara Temple (Peruvudaiyar Kovil), Thanjavur — professional architectural 3-D model and 3-D-printing pipeline.**

A parametric, historically informed, **manufacturable** model of the 11th-century
Chola temple, built with Blender, validated as print-ready STL, and supported
by parametric FreeCAD engineering components (STEP), an automated export and
validation pipeline, and a test suite.

The model is an *architectural interpretation*: every dimension is either
cited to a published source or explicitly flagged as an interpretation in
[`src/documentation/historical_assumptions.md`](src/documentation/historical_assumptions.md).

---

## 1. What is in the box

| Deliverable | Path |
|---|---|
| Exterior master model (1:1000) | `src/models/blender/brihadisvara_exterior.blend`, `src/models/stl/brihadisvara_exterior.stl` |
| Cut-away core model (1:320) with the connected interior | `src/models/blender/brihadisvara_cutaway.blend`, `src/models/stl/brihadisvara_cutaway.stl` |
| Lift-off roof section of the cut-away model | `src/models/stl/brihadisvara_cutaway_roof.stl` |
| Modular print set (7 parts) | `src/models/stl/modules/` |
| 3MF assembly of the modular set | `src/models/3mf/brihadisvara_modular.3mf` |
| FreeCAD engineering project | `src/models/freecad/brihadisvara_engineering.FCStd` |
| STEP engineering components | `src/models/step/*.step` |
| Printable hardware and fit-test coupon | `src/models/stl/hardware/` |
| Rendered previews (8 views) | `src/previews/` |
| Reference photographs + attribution | `src/references/images/`, `image_manifest.json`, `sources.md` |
| Documentation | `src/documentation/` |
| Tests | `tests/` |

Measured sizes of the exported meshes:

| Model | Size (mm) | Triangles |
|---|---|---|
| Exterior (whole compound) | 242.8 × 123.9 × 67.0 | 15 894 |
| Cut-away core (sanctum → Nandi hall) | 227.5 × 51.2 × 205.8 | 7 425 |
| Foundation west / east plate | 101.0 × 123.9 × 1.6 / 141.8 × 123.9 × 1.6 | 24 / 24 |
| Temple block | 72.8 × 32.8 × 65.8 | 9 994 |
| Gopurams | 88.5 × 14.0 × 31.2 | 1 400 |
| Compound wall | 240.8 × 121.9 × 3.5 | 60 |
| Prakara | 174.2 × 80.8 × 4.8 | 4 176 |

## 2. Software requirements

| Tool | Version used | Required? |
|---|---|---|
| Python | 3.12+ (3.14 used) | yes, for the scripts and tests |
| Blender | 5.2 LTS | yes, for modelling, export and rendering |
| FreeCAD | 1.1.4 | yes, for the parametric STEP components |
| Pillow | 12+ | for reference-image inspection |
| trimesh | optional | secondary mesh validation only |

If Blender and FreeCAD are not installed system-wide, the project uses
**user-level Flatpak** installations (no elevated privileges):

```bash
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y --user flathub org.blender.Blender org.freecad.FreeCAD
flatpak override --user --filesystem=/media --filesystem=/run/media org.blender.Blender
flatpak override --user --filesystem=/media --filesystem=/run/media org.freecad.FreeCAD
```

## 3. Repository structure

```
super-duper-spoon/
├── README.md
├── .gitignore
├── src/
│   ├── references/          # downloaded images, manifest, sources, analysis
│   ├── scripts/             # generation, export, validation, report
│   │   └── cad/             # FreeCAD engineering generator
│   ├── models/
│   │   ├── blender/         # .blend source projects
│   │   ├── freecad/         # .FCStd engineering project
│   │   ├── stl/             # print-ready meshes (+ modules/)
│   │   ├── step/            # STEP engineering components
│   │   └── 3mf/             # 3MF assembly of the modular set
│   ├── previews/            # rendered architectural views
│   ├── documentation/       # analysis, dimensions, print settings, reports
│   └── tests/               # reserved
└── tests/                   # unit and integration tests
```

## 4. Reference image workflow

```bash
python3 src/scripts/download_references.py --limit 45   # download + manifest
python3 src/scripts/inspect_references.py               # analyse + contact sheets
```

The downloader queries the public Wikimedia Commons API, verifies the byte
signature *and* the decodability of every file, refuses HTML error pages,
never overwrites an existing file, retries with back-off and records the
author, licence, source page, dimensions and SHA-256 of every image in
`src/references/image_manifest.json`. `sources.md` is the human-readable
attribution list.

## 5. Model generation workflow

```bash
# everything (exterior + cut-away + modular), with previews
src/scripts/blender.sh --background --python src/scripts/generate_temple.py -- --variant all

# a single variant, no rendering
src/scripts/blender.sh --background --python src/scripts/generate_temple.py -- --variant exterior --no-render
```

The generator is fully parametric: every dimension lives in
`src/scripts/temple_params.py` in **real-world metres**, and the model scale
(1 mm of model = 1 m of building) is applied at build time, so the same source
produces both the 1:1000 master model and the 1:320 detail model. The Blender
scene is organised into the named collections `00_REFERENCE` … `09_PRINT_ASSEMBLY`
and carries four cameras (front elevation, three-quarter, side elevation,
aerial).

## 6. FreeCAD workflow

```bash
src/scripts/freecad.sh src/scripts/cad/generate_cad.py
```

Produces `src/models/freecad/brihadisvara_engineering.FCStd` (spreadsheet-driven,
recomputable) and six STEP files: the foundation plates, the alignment
pin/socket, the roof spigot/socket, the wall key, the fit-test coupon and a
combined file. Every solid is checked for validity before export.

## 7. Export and validation

```bash
python3 src/scripts/export_models.py        # regenerate everything + manifest
python3 src/scripts/validate_meshes.py      # mesh checks + validation report
python3 src/scripts/build_report.py         # project report from the artefacts
```

`export_manifest.json` records, for every exported file, the variant, the
scale, the units, the measured bounding dimensions, the triangle count, the
timestamp and the validation status. `validation_report.md` lists the checks
that were actually executed (file integrity, bounding box, degenerate
triangles, duplicate vertices, open edges, non-manifold edges, connected
components, build-volume fit, base flatness) and states which tools ran.

## 8. Printing

Read [`src/documentation/print_settings.md`](src/documentation/print_settings.md)
before slicing. In short: 0.4 mm nozzle, 0.20 mm layers, PLA/PETG, 2.4 mm
minimum structural wall, 1.2 mm minimum detail, 0.30 mm joint clearance per
side, and the orientation table for every part. **Print the fit-test coupon
first** and calibrate the clearance on the actual printer.

Assembly order and part list: [`src/documentation/assembly_guide.md`](src/documentation/assembly_guide.md).

## 9. Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite covers the parameter set, the mesh helpers, the plan geometry, the
presence and scale of the generated assets, the reference manifest and the
documentation. Tests that need an artefact which has not been generated yet
skip instead of failing.

## 10. Known limitations

* The model is an architectural interpretation, not a measured survey.
* The interior arrangement (cella, ambulatory passage, antrala, mandapas,
  Nandi hall) follows the published sequence but the individual interior
  dimensions are interpretations.
* The 81 *karana* dance figures of the *aditala* wall and the Chola frescoes
  are not modelled.
* No slicer is installed on the build host, so no slice files or print-time
  estimates are provided.
* The compound's width (121.92 m) is historically fixed; it is *not* inflated
  to meet the width target in the brief. See
  [`src/documentation/model_dimensions.md`](src/documentation/model_dimensions.md) §6.
* `src/scripts/generate_cad.py` could not be created on this filesystem (the
  name is blocked by a stale entry); the FreeCAD generator lives at
  `src/scripts/cad/generate_cad.py` instead.

## 11. Attribution

Reference photographs are the property of their authors and are redistributed
under the licences recorded in `src/references/sources.md` and
`src/references/image_manifest.json`. The architectural sources are listed in
[`src/documentation/architecture_analysis.md`](src/documentation/architecture_analysis.md).
