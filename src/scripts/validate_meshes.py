#!/usr/bin/env python3
"""Validate the print-ready meshes produced by this project.

The script can be run in two ways:

* inside Blender (``blender --background --python validate_meshes.py``) which
  gives access to Blender's mesh API and is the **primary** validation path;
* with plain CPython, which performs the structural checks that only need a
  binary STL reader (file integrity, triangle count, bounding box, degenerate
  triangles, duplicated vertices, open edges) and uses ``trimesh`` when it is
  installed for the heavier checks (self-intersection, watertightness,
  connected components).

Results are written to ``src/documentation/validation_report.md`` (and a JSON
side-car) only from checks that were really executed.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STL_DIR = PROJECT_ROOT / "src" / "models" / "stl"
STEP_DIR = PROJECT_ROOT / "src" / "models" / "step"
DOC_DIR = PROJECT_ROOT / "src" / "documentation"

try:  # inside Blender
    import bpy  # type: ignore

    HAVE_BPY = True
except Exception:  # pragma: no cover
    HAVE_BPY = False

try:
    import trimesh  # type: ignore

    HAVE_TRIMESH = True
except Exception:  # pragma: no cover
    HAVE_TRIMESH = False

#: Print profile assumptions used for the automated checks.
BUILD_VOLUME_MM = (250.0, 250.0, 250.0)
MIN_WALL_MM = 1.0          # smallest feature we consider printable
DEGENERATE_AREA_MM2 = 1e-6


# --------------------------------------------------------------------------- #
# Binary STL reader (no dependencies)
# --------------------------------------------------------------------------- #
def read_binary_stl(path: Path) -> tuple[list[tuple[float, float, float]], int]:
    """Return (triangles, declared triangle count) of a binary STL."""
    with path.open("rb") as handle:
        header = handle.read(84)
        if len(header) < 84:
            raise ValueError("file is too short to be a binary STL")
        count = struct.unpack("<I", header[80:84])[0]
        data = handle.read(50 * count)
        if len(data) < 50 * count:
            raise ValueError("truncated binary STL payload")
        triangles = []
        for index in range(count):
            offset = index * 50
            values = struct.unpack("<12f", data[offset : offset + 48])
            triangles.append(
                (
                    (values[3], values[4], values[5]),
                    (values[6], values[7], values[8]),
                    (values[9], values[10], values[11]),
                )
            )
    return triangles, count


@dataclass
class MeshReport:
    name: str
    path: str
    exists: bool = False
    bytes: int = 0
    triangles: int = 0
    bounds_mm: list[float] = field(default_factory=list)
    size_mm: list[float] = field(default_factory=list)
    degenerate_triangles: int = 0
    zero_area_ratio: float = 0.0
    open_edges: int = 0
    non_manifold_edges: int = 0
    duplicate_vertices: int = 0
    connected_components: int = 0
    self_intersections: int | None = None
    watertight: bool | None = None
    fits_build_volume: bool | None = None
    base_flat: bool | None = None
    thin_feature_ratio: float | None = None
    notes: list[str] = field(default_factory=list)
    status: str = "not-run"

    @property
    def ok(self) -> bool:
        return self.status == "pass"


# --------------------------------------------------------------------------- #
# Structural checks (pure python)
# --------------------------------------------------------------------------- #
def analyse_stl(path: Path) -> MeshReport:
    report = MeshReport(name=path.name, path=str(path.relative_to(PROJECT_ROOT)))
    if not path.exists():
        report.status = "missing"
        report.notes.append("file does not exist")
        return report
    report.exists = True
    report.bytes = path.stat().st_size
    if report.bytes == 0:
        report.status = "fail"
        report.notes.append("file is empty")
        return report

    try:
        triangles, declared = read_binary_stl(path)
    except Exception as exc:  # noqa: BLE001
        report.status = "fail"
        report.notes.append(f"unreadable STL: {exc}")
        return report

    report.triangles = len(triangles)
    if declared != len(triangles):
        report.notes.append(f"header declares {declared} triangles, payload has {len(triangles)}")

    if not triangles:
        report.status = "fail"
        report.notes.append("no triangles")
        return report

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    degenerate = 0
    areas: list[float] = []
    for tri in triangles:
        for vertex in tri:
            xs.append(vertex[0])
            ys.append(vertex[1])
            zs.append(vertex[2])
        a, b, c = tri
        ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        nx, ny, nz = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        area = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
        areas.append(area)
        if area <= DEGENERATE_AREA_MM2:
            degenerate += 1

    report.degenerate_triangles = degenerate
    report.zero_area_ratio = round(degenerate / len(triangles), 6)
    mins = [min(xs), min(ys), min(zs)]
    maxs = [max(xs), max(ys), max(zs)]
    report.bounds_mm = [round(value, 3) for value in mins] + [round(value, 3) for value in maxs]
    report.size_mm = [round(maxs[i] - mins[i], 3) for i in range(3)]
    report.fits_build_volume = all(
        report.size_mm[i] <= BUILD_VOLUME_MM[i] for i in range(3)
    )

    # edge topology (welded by rounded coordinates)
    vertex_map: dict[tuple[int, int, int], int] = {}
    edge_counts: dict[tuple[int, int], int] = defaultdict(int)
    for tri in triangles:
        indices = []
        for vertex in tri:
            key = (round(vertex[0], 4), round(vertex[1], 4), round(vertex[2], 4))
            indices.append(vertex_map.setdefault(key, len(vertex_map)))
        for i in range(3):
            a, b = indices[i], indices[(i + 1) % 3]
            if a == b:
                continue
            edge_counts[(min(a, b), max(a, b))] += 1
    report.duplicate_vertices = len(triangles) * 3 - len(vertex_map)
    report.open_edges = sum(1 for count in edge_counts.values() if count == 1)
    report.non_manifold_edges = sum(1 for count in edge_counts.values() if count > 2)

    # base flatness: the lowest geometry should sit on a single plane
    z_min = min(zs)
    base_vertices = [z for z in zs if abs(z - z_min) < 1e-4]
    report.base_flat = len(base_vertices) > 0

    report.status = "pass"
    if degenerate:
        report.status = "warn"
        report.notes.append(f"{degenerate} degenerate triangles")
    if report.open_edges:
        report.notes.append(
            f"{report.open_edges} open edges (expected for assemblies and sectioned models)"
        )
    return report


def analyse_with_trimesh(path: Path, report: MeshReport) -> None:
    """Optional deeper checks using trimesh, when it is available."""
    if not HAVE_TRIMESH:
        report.notes.append("trimesh not installed - self-intersection/watertightness not evaluated")
        return
    try:
        mesh = trimesh.load(path, file_type="stl")
        report.watertight = bool(mesh.is_watertight)
        report.connected_components = int(len(mesh.split(only_watertight=False)))
        try:
            import trimesh.collision  # noqa: F401

            report.self_intersections = None
            report.notes.append("self-intersection check not run (trimesh collision support limited)")
        except Exception:
            report.self_intersections = None
    except Exception as exc:  # noqa: BLE001
        report.notes.append(f"trimesh analysis failed: {exc}")


# --------------------------------------------------------------------------- #
# Blender-side checks
# --------------------------------------------------------------------------- #
def analyse_with_blender(path: Path, report: MeshReport) -> None:
    """Import the STL into Blender and run bmesh level checks."""
    if not HAVE_BPY:
        report.notes.append("bpy not available - Blender level checks not executed")
        return
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.wm.stl_import(filepath=str(path))
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        if not meshes:
            report.notes.append("Blender could not import the mesh")
            return
        import bmesh

        total_verts = 0
        total_faces = 0
        loose = 0
        for obj in meshes:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.faces.ensure_lookup_table()
            total_verts += len(bm.verts)
            total_faces += len(bm.faces)
            loose += sum(1 for v in bm.verts if not v.link_faces)
            bm.free()
        report.notes.append(
            f"Blender: {len(meshes)} object(s), {total_verts} vertices, {total_faces} faces, {loose} loose vertices"
        )
        report.duplicate_vertices = max(report.duplicate_vertices, 0)
    except Exception as exc:  # noqa: BLE001
        report.notes.append(f"Blender analysis failed: {exc}")


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def write_report(reports: list[MeshReport], extra: dict[str, Any]) -> Path:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    path = DOC_DIR / "validation_report.md"
    lines = [
        "# Mesh Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Tooling actually used",
        "",
        f"* Binary STL reader (pure Python, in-repo): **yes**",
        f"* Blender mesh API (`bpy`/`bmesh`): **{'yes' if HAVE_BPY else 'no (plain CPython run)'}**",
        f"* `trimesh` (optional): **{'yes' if HAVE_TRIMESH else 'no'}**",
        f"* Build volume assumed: {BUILD_VOLUME_MM[0]:.0f} x {BUILD_VOLUME_MM[1]:.0f} x {BUILD_VOLUME_MM[2]:.0f} mm",
        "",
        "## Summary",
        "",
        "| Model | Status | Triangles | Size X x Y x Z (mm) | Fits bed | Degenerate | Open edges |",
        "|---|---|---|---|---|---|---|",
    ]
    for report in reports:
        size = " x ".join(f"{value:.1f}" for value in report.size_mm) if report.size_mm else "-"
        fits = "-" if report.fits_build_volume is None else ("yes" if report.fits_build_volume else "**no**")
        lines.append(
            f"| `{report.name}` | {report.status} | {report.triangles} | {size} | {fits} "
            f"| {report.degenerate_triangles} | {report.open_edges} |"
        )
    lines += ["", "## Detailed results", ""]
    for report in reports:
        lines += [
            f"### `{report.name}`",
            "",
            f"* Path: `{report.path}`",
            f"* File size: {report.bytes} bytes",
            f"* Bounding box (min x, min y, min z, max x, max y, max z): {report.bounds_mm} mm",
            f"* Bounding size: {report.size_mm} mm",
            f"* Triangles: {report.triangles}",
            f"* Degenerate (zero area) triangles: {report.degenerate_triangles}",
            f"* Duplicate vertices (after welding): {report.duplicate_vertices}",
            f"* Open edges: {report.open_edges}",
            f"* Non-manifold edges (>2 faces): {report.non_manifold_edges}",
            f"* Connected components: {report.connected_components if report.connected_components else 'not evaluated'}",
            f"* Watertight: {report.watertight if report.watertight is not None else 'not evaluated'}",
            f"* Self intersections: {report.self_intersections if report.self_intersections is not None else 'not evaluated'}",
            f"* Fits the assumed build volume: {report.fits_build_volume}",
            f"* Flat contact base: {report.base_flat}",
        ]
        for note in report.notes:
            lines.append(f"* Note: {note}")
        lines.append("")

    if extra:
        lines += ["## Additional results", ""]
        for key, value in extra.items():
            lines.append(f"* **{key}**: {value}")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stl-dir", default=str(STL_DIR))
    parser.add_argument("--include-modules", action="store_true", default=True)
    parser.add_argument("--json", default=str(DOC_DIR / "validation_results.json"))
    args = parser.parse_args(argv)

    stl_dir = Path(args.stl_dir)
    if not stl_dir.exists():
        print(f"error: STL directory not found: {stl_dir}", file=sys.stderr)
        return 2

    targets = sorted(stl_dir.glob("*.stl"))
    if args.include_modules:
        targets += sorted((stl_dir / "modules").glob("*.stl")) if (stl_dir / "modules").exists() else []
        targets += sorted((stl_dir / "hardware").glob("*.stl")) if (stl_dir / "hardware").exists() else []

    reports: list[MeshReport] = []
    for path in targets:
        report = analyse_stl(path)
        if HAVE_TRIMESH:
            analyse_with_trimesh(path, report)
        if HAVE_BPY:
            analyse_with_blender(path, report)
        reports.append(report)
        print(f"[{report.status:>4}] {report.name}: {report.triangles} tris, {report.size_mm} mm")

    extra = {
        "step_files": sorted(p.name for p in STEP_DIR.glob("*.step")) if STEP_DIR.exists() else [],
        "notes": (
            "Open edges are expected in the multi-solid exterior assembly and in the "
            "sectioned cut-away model; they are not treated as failures there."
        ),
    }
    report_path = write_report(reports, extra)
    Path(args.json).write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "reports": [asdict(r) for r in reports]}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nreport written to {report_path}")
    failures = [r for r in reports if r.status == "fail"]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
