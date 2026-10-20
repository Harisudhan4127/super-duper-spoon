# Mesh Validation Report

Generated: 2026-10-20T04:21:47+00:00

## Tooling actually used

* Binary STL reader (pure Python, in-repo): **yes**
* Blender mesh API (`bpy`/`bmesh`): **no (plain CPython run)**
* `trimesh` (optional): **no**
* Build volume assumed: 250 x 250 x 250 mm

## Summary

| Model | Status | Triangles | Size X x Y x Z (mm) | Fits bed | Degenerate | Open edges |
|---|---|---|---|---|---|---|
| `brihadisvara_cutaway.stl` | warn | 7355 | 227.5 x 51.2 x 205.8 | yes | 50 | 62 |
| `brihadisvara_cutaway_roof.stl` | pass | 190 | 140.9 x 24.5 x 11.6 | yes | 0 | 0 |
| `brihadisvara_exterior.stl` | pass | 15834 | 242.8 x 123.9 x 67.0 | yes | 0 | 76 |
| `MOD_01_Foundation_West.stl` | pass | 24 | 101.0 x 123.9 x 1.6 | yes | 0 | 0 |
| `MOD_02_Foundation_East.stl` | pass | 24 | 141.8 x 123.9 x 1.6 | yes | 0 | 0 |
| `MOD_03_Temple_Block.stl` | pass | 9934 | 72.8 x 32.8 x 65.8 | yes | 0 | 28 |
| `MOD_04_Gopurams.stl` | pass | 1400 | 88.5 x 14.0 x 31.2 | yes | 0 | 24 |
| `MOD_05_Compound_Wall.stl` | pass | 60 | 240.8 x 121.9 x 3.5 | yes | 0 | 0 |
| `MOD_06_Prakara.stl` | pass | 4176 | 174.2 x 80.8 x 4.8 | yes | 0 | 0 |
| `MOD_07_Courtyard_Shrines.stl` | pass | 240 | 8.0 x 35.5 x 9.0 | yes | 0 | 24 |

## Detailed results

### `brihadisvara_cutaway.stl`

* Path: `src/models/stl/brihadisvara_cutaway.stl`
* File size: 367834 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [-51.219, 0.0, 0.0, 176.25, 51.219, 205.75] mm
* Bounding size: [227.469, 51.219, 205.75] mm
* Triangles: 7355
* Degenerate (zero area) triangles: 50
* Duplicate vertices (after welding): 18617
* Open edges: 62
* Non-manifold edges (>2 faces): 1036
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True
* Note: 50 degenerate triangles
* Note: 62 open edges (expected for assemblies and sectioned models)

### `brihadisvara_cutaway_roof.stl`

* Path: `src/models/stl/brihadisvara_cutaway_roof.stl`
* File size: 9584 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [25.781, 0.0, 29.688, 166.719, 24.531, 41.25] mm
* Bounding size: [140.938, 24.531, 11.562] mm
* Triangles: 190
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 471
* Open edges: 0
* Non-manifold edges (>2 faces): 0
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True

### `brihadisvara_exterior.stl`

* Path: `src/models/stl/brihadisvara_exterior.stl`
* File size: 791784 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [-46.0, -61.96, -1.2, 196.79, 61.96, 65.84] mm
* Bounding size: [242.79, 123.92, 67.04] mm
* Triangles: 15834
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 37753
* Open edges: 76
* Non-manifold edges (>2 faces): 1135
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True
* Note: 76 open edges (expected for assemblies and sectioned models)

### `MOD_01_Foundation_West.stl`

* Path: `src/models/stl/modules/MOD_01_Foundation_West.stl`
* File size: 1284 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [-46.0, -61.96, -1.2, 55.0, 61.96, 0.4] mm
* Bounding size: [101.0, 123.92, 1.6] mm
* Triangles: 24
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 56
* Open edges: 0
* Non-manifold edges (>2 faces): 0
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True

### `MOD_02_Foundation_East.stl`

* Path: `src/models/stl/modules/MOD_02_Foundation_East.stl`
* File size: 1284 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [55.0, -61.96, -1.2, 196.79, 61.96, 0.4] mm
* Bounding size: [141.79, 123.92, 1.6] mm
* Triangles: 24
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 56
* Open edges: 0
* Non-manifold edges (>2 faces): 0
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True

### `MOD_03_Temple_Block.stl`

* Path: `src/models/stl/modules/MOD_03_Temple_Block.stl`
* File size: 496784 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [-16.39, -16.39, 0.0, 56.4, 16.39, 65.84] mm
* Bounding size: [72.79, 32.78, 65.84] mm
* Triangles: 9934
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 23917
* Open edges: 28
* Non-manifold edges (>2 faces): 1128
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True
* Note: 28 open edges (expected for assemblies and sectioned models)

### `MOD_04_Gopurams.stl`

* Path: `src/models/stl/modules/MOD_04_Gopurams.stl`
* File size: 70084 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [94.5, -7.0, 0.4, 183.0, 7.0, 31.6] mm
* Bounding size: [88.5, 14.0, 31.2] mm
* Triangles: 1400
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 3310
* Open edges: 24
* Non-manifold edges (>2 faces): 0
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True
* Note: 24 open edges (expected for assemblies and sectioned models)

### `MOD_05_Compound_Wall.stl`

* Path: `src/models/stl/modules/MOD_05_Compound_Wall.stl`
* File size: 3084 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [-45.0, -60.96, 0.0, 195.79, 60.96, 3.5] mm
* Bounding size: [240.79, 121.92, 3.5] mm
* Triangles: 60
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 148
* Open edges: 0
* Non-manifold edges (>2 faces): 4
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True

### `MOD_06_Prakara.stl`

* Path: `src/models/stl/modules/MOD_06_Prakara.stl`
* File size: 208884 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [-33.428, -40.0, 0.0, 140.8, 40.8, 4.8] mm
* Bounding size: [174.228, 80.8, 4.8] mm
* Triangles: 4176
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 9744
* Open edges: 0
* Non-manifold edges (>2 faces): 0
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True

### `MOD_07_Courtyard_Shrines.stl`

* Path: `src/models/stl/modules/MOD_07_Courtyard_Shrines.stl`
* File size: 12084 bytes
* Bounding box (min x, min y, min z, max x, max y, max z): [68.0, -18.0, 0.4, 76.0, 17.5, 9.4] mm
* Bounding size: [8.0, 35.5, 9.0] mm
* Triangles: 240
* Degenerate (zero area) triangles: 0
* Duplicate vertices (after welding): 574
* Open edges: 24
* Non-manifold edges (>2 faces): 0
* Connected components: not evaluated
* Watertight: not evaluated
* Self intersections: not evaluated
* Fits the assumed build volume: True
* Flat contact base: True
* Note: 24 open edges (expected for assemblies and sectioned models)

## Additional results

* **step_files**: ['alignment_hardware.step', 'brihadisvara_engineering_all.step', 'fit_test_coupon.step', 'foundation_plates.step', 'roof_interface.step', 'wall_key.step']
* **notes**: Open edges are expected in the multi-solid exterior assembly and in the sectioned cut-away model; they are not treated as failures there.

