#!/usr/bin/env python3
"""Repeatable export pipeline for the Brihadisvara Temple model.

The script drives the Blender generator, verifies that every expected file was
actually written, measures the exported geometry and writes an export manifest
with the metadata that a manufacturing hand-off needs (variant, units, bounding
dimensions, export timestamp, source project, validation status).

Usage
-----
    python3 src/scripts/export_models.py                # regenerate + manifest
    python3 src/scripts/export_models.py --manifest-only # only re-read files
    python3 src/scripts/export_models.py --no-render    # skip preview renders
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BLENDER_WRAPPER = SCRIPT_DIR / "blender.sh"
GENERATOR = SCRIPT_DIR / "generate_temple.py"

BLEND_DIR = PROJECT_ROOT / "src" / "models" / "blender"
STL_DIR = PROJECT_ROOT / "src" / "models" / "stl"
STEP_DIR = PROJECT_ROOT / "src" / "models" / "step"
PREVIEW_DIR = PROJECT_ROOT / "src" / "previews"
DOC_DIR = PROJECT_ROOT / "src" / "documentation"
MANIFEST = DOC_DIR / "export_manifest.json"

VARIANTS = {
    "exterior": {
        "scale_mm_per_m": 1.0,
        "scale_note": "1:1000 master model (1 mm of model = 1 m of building)",
        "blend": BLEND_DIR / "brihadisvara_exterior.blend",
        "stl": STL_DIR / "brihadisvara_exterior.stl",
    },
    "cutaway": {
        "scale_mm_per_m": 1000.0 / 320.0,
        "scale_note": "1:320 detail model with the southern half sectioned away",
        "blend": BLEND_DIR / "brihadisvara_cutaway.blend",
        "stl": STL_DIR / "brihadisvara_cutaway.stl",
    },
    "modular": {
        "scale_mm_per_m": 1.0,
        "scale_note": "1:1000 master model split into printable modules",
        "blend": BLEND_DIR / "brihadisvara_modular.blend",
        "stl": STL_DIR / "modules",
    },
}


def run_generator(variant: str, render: bool, samples: int, resolution: int) -> tuple[int, str]:
    command = [
        str(BLENDER_WRAPPER), "--background", "--python", str(GENERATOR), "--",
        "--variant", variant,
    ]
    if not render:
        command.append("--no-render")
    command += ["--samples", str(samples), "--resolution", str(resolution)]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    return completed.returncode, (completed.stdout + completed.stderr)[-4000:]


def stl_metrics(path: Path) -> dict:
    """Read a binary STL and return triangles plus the bounding box."""
    with path.open("rb") as handle:
        header = handle.read(84)
        count = struct.unpack("<I", header[80:84])[0]
        data = handle.read(50 * count)
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for index in range(count):
        values = struct.unpack("<12f", data[index * 50 : index * 50 + 48])
        for offset in (3, 6, 9):
            xs.append(values[offset])
            ys.append(values[offset + 1])
            zs.append(values[offset + 2])
    if not xs:
        return {"triangles": 0, "bounds_mm": None, "size_mm": None}
    mins = [min(xs), min(ys), min(zs)]
    maxs = [max(xs), max(ys), max(zs)]
    return {
        "triangles": count,
        "bounds_mm": [round(value, 3) for value in mins + maxs],
        "size_mm": [round(maxs[i] - mins[i], 3) for i in range(3)],
    }


def validation_status() -> dict[str, str]:
    path = DOC_DIR / "validation_results.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {report["name"]: report["status"] for report in payload.get("reports", [])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest-only", action="store_true", help="do not re-run Blender")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--resolution", type=int, default=1400)
    args = parser.parse_args(argv)

    for directory in (BLEND_DIR, STL_DIR, PREVIEW_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    if not args.manifest_only:
        for variant in VARIANTS:
            print(f"--- exporting variant {variant} ---")
            code, output = run_generator(variant, not args.no_render, args.samples, args.resolution)
            if code != 0:
                print(output, file=sys.stderr)
                print(f"error: generator failed for variant {variant}", file=sys.stderr)
                return code

    statuses = validation_status()
    manifest: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "units": "millimetres",
        "coordinate_system": "X = east-west, Y = north-south, Z = up, Z=0 at the base plate underside",
        "variants": {},
    }

    for variant, info in VARIANTS.items():
        entry: dict = {
            "scale_mm_per_metre": info["scale_mm_per_m"],
            "scale_note": info["scale_note"],
            "source_project": str(info["blend"].relative_to(PROJECT_ROOT)),
            "exports": [],
        }
        blend = info["blend"]
        if blend.exists():
            entry["blend"] = {
                "path": str(blend.relative_to(PROJECT_ROOT)),
                "bytes": blend.stat().st_size,
            }
        else:
            entry["blend_error"] = "missing"

        stl_paths = []
        if info["stl"].is_dir():
            stl_paths = sorted(info["stl"].glob("*.stl"))
        elif info["stl"].exists():
            stl_paths = [info["stl"]]

        for stl in stl_paths:
            metrics = stl_metrics(stl)
            record = {
                "path": str(stl.relative_to(PROJECT_ROOT)),
                "bytes": stl.stat().st_size,
                "triangles": metrics["triangles"],
                "size_mm": metrics["size_mm"],
                "bounds_mm": metrics["bounds_mm"],
                "validation": statuses.get(stl.name, "not validated"),
            }
            entry["exports"].append(record)
        manifest["variants"][variant] = entry

    step_files = sorted(STEP_DIR.glob("*.step"))
    manifest["step_exports"] = [
        {"path": str(path.relative_to(PROJECT_ROOT)), "bytes": path.stat().st_size}
        for path in step_files
    ]
    previews = sorted(PREVIEW_DIR.glob("*.png"))
    manifest["previews"] = [
        {"path": str(path.relative_to(PROJECT_ROOT)), "bytes": path.stat().st_size}
        for path in previews
    ]

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"export manifest written to {MANIFEST}")
    for variant, entry in manifest["variants"].items():
        print(f"  {variant}: {len(entry['exports'])} mesh export(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
