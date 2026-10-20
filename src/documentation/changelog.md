# Changelog

All notable changes to the Brihadisvara Temple 3-D model project.

## 2026-10-20 — project bootstrap and first complete model

### Added
* `chore:` project structure, `.gitignore`, environment audit
  (`src/documentation/environment_audit.md`) covering the audited toolchain:
  Blender 5.2 LTS and FreeCAD 1.1.4 obtained as user-level Flatpak
  installations, Python 3.14, Pillow, optional trimesh.
* `assets:` 44 attributed reference photographs from Wikimedia Commons with
  `image_manifest.json` (source page, author, licence, dimensions, SHA-256,
  status) and `sources.md`.
* `feat:` repeatable reference pipeline — `download_references.py`
  (API client, signature checks, decode verification, retries, duplicate
  avoidance, resume) and `inspect_references.py` (per-image technical analysis
  plus contact sheets).
* `docs:` architecture analysis, model dimensions, historical assumptions,
  project plan, toolchain decision, print settings, assembly guide.
* `feat:` parametric Blender generator (`generate_temple.py`,
  `temple_params.py`, `temple_geom.py`, `temple_build.py`) producing the
  exterior master model, the 1:320 sectioned cut-away model and the modular
  print set, with named collections, four cameras, EEVEE previews and STL
  export.
* `feat:` FreeCAD engineering components (`src/scripts/cad/generate_cad.py`):
  spreadsheet-driven foundation plates, alignment pin/socket, roof
  spigot/socket, wall key and fit-test coupon, exported as STEP.
* `build:` export pipeline (`export_models.py`) and mesh validation
  (`validate_meshes.py`) with a generated `validation_report.md`.
* `tests:` 39 unit and integration tests under `tests/`.

### Notable engineering decisions
* Master scale 1:1000 (1 mm of model = 1 m of building) for the complete
  240.79 × 121.92 m compound; the cut-away core uses the same parametric
  source at 1:320 so the interior is legible and printable.
* Detail amplification to a 0.9 mm printable minimum instead of dropping
  sub-millimetre ornament.
* Geometry is built from explicit vertex/face lists (no booleans in the
  source), so the exports are deterministic and reproducible.
* The section cut of the cut-away model is the only boolean in the pipeline.

### Known limitations
* The host filesystem refuses one file name (`src/scripts/generate_cad.py`);
  the CAD script therefore lives in `src/scripts/cad/generate_cad.py`. The
  stale entry is invisible to Git and to the build scripts.
* The interior is a plausible connected arrangement (cella, ambulatory
  passage, antrala, two mandapas, Nandi hall) based on the published
  sequence; it is not a measured reconstruction of the interior.
* No slicer is installed on the build host, so no slice files or print-time
  estimates are provided.
* The 81 *karana* figures of the *aditala* wall and the Chola frescoes are
  not modelled.
