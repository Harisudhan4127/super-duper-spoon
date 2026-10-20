# Toolchain Decision

Recorded before the modelling pipeline was implemented, as required by the
project's own execution order.

## 1. Candidates and the actual environment

| Tool | Availability on the build host | Decision |
|---|---|---|
| Blender | not installed system-wide; obtainable as a user-level Flatpak (5.2 LTS) | **adopted** — primary modelling tool |
| FreeCAD | not installed system-wide; obtainable as a user-level Flatpak (1.1.4) | **adopted** — parametric engineering parts |
| `bpy` as a PyPI module | not published for the host's CPython 3.12/3.14 | rejected (impossible) |
| OpenSCAD | not installed | rejected (weak for complex ornament, and not needed) |
| MeshLab / admesh / OpenMesh | not installed | rejected (Blender's mesh API is sufficient) |
| PrusaSlicer / Cura | not installed | out of scope — no printer profile exists on the host |
| ImageMagick | not installed | replaced by Pillow for reference-image inspection |
| NumPy / trimesh | not present in the system interpreter | optional, used only as a secondary validator inside a project venv |

## 2. Division of labour

**Blender owns the form.** Massing, the 13-storey tapering vimana, the
mouldings, the pillar rhythms, the Nandi, the gopurams, the enclosure walls
and the prakara are all built procedurally from explicit vertex/face lists
(`src/scripts/temple_geom.py`, `src/scripts/temple_build.py`). Blender also
renders the previews and exports the STL.

**FreeCAD owns the fit.** Base plates with dowel sockets, the alignment
pin/socket pair, the roof spigot and socket, the wall key and the fit-test
coupon are real solids driven by a FreeCAD spreadsheet, exported as STEP.
They are the parts that need exact tolerances and that a slicer must see as
dimensioned engineering components.

**The two are not assumed to be linked.** There is no live Blender → FreeCAD
parametric link, and there is not one in reality. The interchange is explicit
and one-way:

```
temple_params.py  (single source of truth, real metres)
        ├── Blender  →  mesh geometry  →  .blend  →  .stl  →  slicer
        └── FreeCAD  →  solid geometry →  .FCStd →  .step  →  slicer
```

Both branches read the *same* parameter file, so the two models agree on
every dimension; the FreeCAD parts are dimensioned in the same millimetre
coordinate frame as the Blender exports.

## 3. Why not one tool for everything

* Modelling the ornament in FreeCAD would mean hundreds of scripted
  primitives and a far slower iteration loop; modelling it in Blender with
  explicit meshes is deterministic, fast and gives the dense *kuta*/*sala*
  rhythm that defines a Dravidian tower.
* Modelling the dowels and the base plates in Blender would mean hand-tuned
  clearances expressed as mesh offsets — exactly the kind of thing a
  parametric CAD kernel should own.

## 4. Reproducibility

* Every script resolves its paths from `__file__`, so it runs from any working
  directory.
* No random numbers, no time-dependent geometry: the same command always
  produces the same mesh (only the timestamps in the manifests differ).
* The Blender STL exporter runs with `global_scale = 1.0` and
  `use_scene_unit = False`, so the exported coordinates are millimetres and
  the scale can never be silently changed.
* `src/scripts/export_models.py` re-runs the whole pipeline and writes
  `export_manifest.json` with the measured size of every exported file, so a
  scale change would be visible immediately.
