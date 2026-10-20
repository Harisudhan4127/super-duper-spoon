#!/usr/bin/env python3
"""Inspect the downloaded reference images.

Produces, for every file in ``src/references/images``:

* technical facts (pixel size, aspect ratio, byte size, mean luminance, contrast,
  a crude sharpness/edge-density measure, dominant hue) used to flag blank or
  unusable frames;
* a set of contact sheets (montages) so that the whole reference set can be
  reviewed visually in a few images instead of dozens.

The script never modifies the source images.  It writes
``src/references/reference_analysis.json`` and ``src/references/contact_sheet_*.png``.

Usage
-----
    python3 src/scripts/inspect_references.py [--columns 4] [--rows 3] [--cell 320]
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageOps
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"Pillow is required for reference inspection: {exc}")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
REF_DIR = PROJECT_ROOT / "src" / "references"
IMAGE_DIR = REF_DIR / "images"
ANALYSIS_PATH = REF_DIR / "reference_analysis.json"
SHEET_DIR = REF_DIR / "sheets"


def analyse(path: Path) -> dict:
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        mode = image.mode
        grey = image.convert("L")
        small = grey.resize((160, 160))
        pixels = list(small.getdata())
        mean = statistics.fmean(pixels)
        stdev = statistics.pstdev(pixels)

        # edge density (crude sharpness indicator)
        edges = 0
        for index in range(160 * 160):
            if index % 160 == 0:
                continue
            if abs(pixels[index] - pixels[index - 1]) > 24:
                edges += 1
        edge_density = edges / (160 * 160)

        hsv = image.convert("HSV").resize((80, 80))
        hues = [h for h, s, v in hsv.getdata() if s > 40 and v > 40]
        dominant_hue = round(statistics.fmean(hues), 1) if hues else None

    return {
        "filename": path.name,
        "width_px": width,
        "height_px": height,
        "aspect_ratio": round(width / height, 3),
        "bytes": path.stat().st_size,
        "mode": mode,
        "mean_luminance": round(mean, 2),
        "contrast_stdev": round(stdev, 2),
        "edge_density": round(edge_density, 4),
        "dominant_hue_deg": dominant_hue,
        "orientation": "portrait" if height > width else ("square" if height == width else "landscape"),
        "usable": mean > 12 and stdev > 12 and edge_density > 0.005,
    }


def build_sheets(reports: list[dict], columns: int, rows: int, cell: int) -> list[str]:
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    per_sheet = columns * rows
    outputs: list[str] = []
    ordered = sorted(reports, key=lambda r: r["filename"])
    for sheet_index in range(math.ceil(len(ordered) / per_sheet)):
        chunk = ordered[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        sheet = Image.new("RGB", (columns * cell, rows * (cell + 22)), (24, 24, 28))
        draw = ImageDraw.Draw(sheet)
        for index, report in enumerate(chunk):
            source = IMAGE_DIR / report["filename"]
            with Image.open(source) as image:
                thumb = ImageOps.fit(image.convert("RGB"), (cell - 8, cell - 8))
            x = (index % columns) * cell + 4
            y = (index // columns) * (cell + 22) + 4
            sheet.paste(thumb, (x, y))
            label = report["filename"].replace(".jpg", "")
            draw.text((x, y + cell - 2), label[:44], fill=(220, 220, 220))
        out_path = SHEET_DIR / f"contact_sheet_{sheet_index + 1:02d}.png"
        sheet.save(out_path)
        outputs.append(str(out_path.relative_to(PROJECT_ROOT)))
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cell", type=int, default=320)
    args = parser.parse_args(argv)

    if not IMAGE_DIR.exists():
        raise SystemExit(f"reference image directory not found: {IMAGE_DIR}")

    files = sorted(p for p in IMAGE_DIR.glob("*.jpg") if p.is_file())
    if not files:
        raise SystemExit("no reference images to inspect")

    reports = [analyse(path) for path in files]
    sheets = build_sheets(reports, args.columns, args.rows, args.cell)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "image_count": len(reports),
        "contact_sheets": sheets,
        "images": reports,
    }
    ANALYSIS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    unusable = [r["filename"] for r in reports if not r["usable"]]
    print(f"analysed {len(reports)} reference images")
    print(f"contact sheets: {len(sheets)} -> {SHEET_DIR}")
    if unusable:
        print(f"flagged as low-information: {len(unusable)}")
        for name in unusable:
            print(f"  - {name}")
    print(f"analysis written to {ANALYSIS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
