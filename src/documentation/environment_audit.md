# Environment Audit

Audit date: 2026-10-20
Audited by: project automation (Phase Zero)
Host: Linux workstation, repo on removable volume
`/run/media/harisudhan/Data/Git file/super-duper-spoon`

## 1. Repository state at audit time

| Item | Value |
|---|---|
| Branch | `main` |
| Remotes | `origin -> https://github.com/Harisudhan4127/super-duper-spoon.git` |
| Commits | 1 (`face797 Initial commit`) |
| Pre-existing tracked files | `README.md` (single line: `# super-duper-spoon`) — preserved, not rewritten in place of user content |
| Working tree | clean except empty untracked `src/`, `tests/` directories created before the audit |
| Free disk | ~56 GB available on `/run/media/harisudhan/Data` |

The user's original `README.md` was kept and extended (not deleted); its first line is
unchanged.

## 2. Tool discovery (actual executable probing, not package names)

| Tool | Status | Path / version |
|---|---|---|
| `python3` | present | `/usr/bin/python3` → Python 3.14.4 |
| `python3.12` | present | `/usr/bin/python3.12` (used for the auxiliary venv) |
| `git` | present | system git |
| `curl` | present | `/usr/bin/curl` |
| `wget` | present | `/usr/bin/wget` |
| `pip` | present | pip for 3.14 |
| `flatpak` | present | `/usr/bin/flatpak` (used to obtain Blender/FreeCAD without elevated permissions) |
| `snap` | present | `/usr/bin/snap` (Blender is **not** available as a snap here) |
| `blender` (system) | **absent** | not in PATH, not in `/usr/lib/blender`, not in `/opt` |
| `bpy` (pip module) | **unavailable** | `pip index versions bpy` → "No matching distribution found" for both CPython 3.12 and 3.14 (no wheels published for those interpreters) |
| `freecad` / `FreeCAD` / `freecadcmd` | **absent** from PATH | provided through flatpak (see below) |
| `openscad` | absent | — |
| `meshlab` / `admesh` | absent | — |
| `prusa-slicer` / `slicer` | absent | — |
| ImageMagick (`convert`/`identify`) | absent | Pillow used instead |
| `numpy` | **absent** in system Python 3.14 | installed into the project venv (`.venv`) |
| `Pillow` | present | 12.1.1 (system) — used for reference-image inspection |
| `trimesh` | absent | installed into the project venv (optional, secondary validator) |

## 3. Blender

Blender is not installed system-wide and could not be installed from PyPI. The
non-elevated, reproducible route used is **Flatpak (user installation)**:

```
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y --user flathub org.blender.Blender
flatpak override --user --filesystem=/media --filesystem=/run/media org.blender.Blender
```

Verified capability:

```
flatpak run --command=blender org.blender.Blender --version
  → Blender 5.2.0 LTS (build date 2026-07-14)

flatpak run --command=blender org.blender.Blender --background --python-expr "import bpy; print(bpy.app.version_string)"
  → BPYVER 5.2.0 LTS
```

* Background (`--background`) execution works.
* The `bpy` Python API is fully available (mesh, operators, exporters, renderers).
* The flatpak sandbox starts with CWD `/app/blender`; the project tree is reachable
  through the explicit `--filesystem=/media --filesystem=/run/media` override.
  A write test (`open(...,'w')`) inside the repository succeeded, so scripts may
  read and write project files when invoked with absolute paths.
* Everything therefore uses **absolute paths derived from `__file__`**, never from
  the process CWD.

A convenience wrapper is provided at `src/scripts/blender.sh` so all commands in the
documentation can be written as `src/scripts/blender.sh --background --python ...`.

## 4. FreeCAD

FreeCAD is likewise obtained as a user-level flatpak (`org.freecad.FreeCAD`),
executed in console mode:

```
flatpak run --command=FreeCADCmd org.freecad.FreeCAD -c script.py
```

Verified capability:

```
flatpak run --command=FreeCADCmd org.freecad.FreeCAD -c "import FreeCAD; print(FreeCAD.Version())"
  → ['1', '1', '4', '45039 (Git)', 'https://github.com/FreeCAD/FreeCAD.git',
     '2026/09/28 13:46:34', '(HEAD detached at 1.1.4)', '4fd3bf320d9566...']

flatpak run --command=FreeCADCmd org.freecad.FreeCAD <script.py>
  → runs the script, builds the document, writes the .FCStd and the STEP files
  → a new document with a Part::Box recomputes to Volume = 1000.0 and
    Shape.isValid() = True
```

* Console (script) mode works; no GUI is required.
* `Part` primitives, booleans, a `Spreadsheet::Sheet` with aliases and the
  `Import` (STEP) exporter are all available.
* The same filesystem override is required as for Blender, otherwise the
  sandbox cannot see the repository.

## 5. Rendering

* Cycles (CPU) is used for all architectural previews because it renders reliably in
  background mode on a headless host; EEVEE Next requires a GPU/GL context that is
  not guaranteed inside the flatpak sandbox. Preview renders use low sample counts
  (documented in `src/documentation/print_settings.md`).
* No GPU is assumed anywhere in the pipeline.

## 6. Mesh validation

Primary validation runs **inside Blender** using `bpy.types.Mesh` /
`bmesh` operators (degenerate faces, non-manifold edges, loose parts, normals,
bounding box, base flatness). Secondary, optional validation uses `trimesh`
inside the project venv for independent STL re-reading and self-intersection
reporting. Both are optional/secondary to the Blender-side checks, so the pipeline
never depends on a network-installed package being present.

## 7. Slicing / printer

No slicer and no printer profile exists on this machine or in the repository.
Therefore the print profile in `src/documentation/print_settings.md` is written as a
**documented, configurable assumption set** (generic FDM, 0.4 mm nozzle) and no
printer-specific compatibility is claimed.

## 8. Missing tools and chosen alternatives

| Missing | Alternative used | Consequence |
|---|---|---|
| system Blender | Blender 5.2 LTS via flatpak | all modelling runs through `bpy` in background mode |
| system FreeCAD | FreeCAD via flatpak console | parametric STEP parts are produced with the real CAD kernel |
| `bpy` pip wheel | flatpak Blender | none — same API, executed as a subprocess |
| ImageMagick | Pillow (already installed) | reference images are inspected for size/format/entropy |
| numpy (system) | `.venv` in repo (git-ignored) | validation helpers only; not required for core pipeline |
| slicer | none available | slicing is out of scope; print orientation/clearance guidance is documented instead |
| trimesh | optional in `.venv` | secondary checks degrade gracefully when absent |

### 4.1 One host filesystem limitation

The repository lives on a removable exFAT-style volume. During the session a
file entry became unreadable (`stat` returns `EINVAL`); the name
`src/scripts/generate_cad.py` can neither be written, read nor removed, and
Git refuses to `add` it. The FreeCAD generator was therefore written to
`src/scripts/cad/generate_cad.py`, which is functionally equivalent. The
stale entry stays invisible to `git status` and to every script in the
repository, but `git add -A` fails on it — stage files explicitly instead.

## 9. Documentation and network

* Network access to `en.wikipedia.org`, `commons.wikimedia.org`,
  `upload.wikimedia.org` and `download.blender.org` is available and was verified
  before the reference pipeline was written.
* No authentication, CAPTCHA or paywall is bypassed anywhere in this project.
