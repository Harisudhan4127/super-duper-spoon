#!/usr/bin/env python3
"""Generate the parametric FreeCAD engineering components of the model.

The ornamental geometry of the temple lives in Blender (it is a mesh, not a
solid).  The parts that benefit from exact, parametric dimensions are produced
here with the FreeCAD kernel:

* the two foundation plates of the modular print set,
* the alignment pins and sockets that join the modules,
* the spigot / socket interface used by the removable roof section,
* a wall-to-wall key,
* a small fit-test coupon that verifies the chosen joint clearance.

Everything is driven by a FreeCAD spreadsheet, so changing a value in the
spreadsheet and recomputing updates every part and the exported STEP files.

The script is executed with FreeCAD's console binary:

    src/scripts/freecad.sh src/scripts/cad/generate_cad.py

Units: millimetres, identical to the Blender/STL coordinate system.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
if str(PROJECT_ROOT / "src" / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "scripts"))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

from temple_params import PARAMS, plan_positions  # noqa: E402

FCSTD_DIR = PROJECT_ROOT / "src" / "models" / "freecad"
STEP_DIR = PROJECT_ROOT / "src" / "models" / "step"
DOC_DIR = PROJECT_ROOT / "src" / "documentation"

#: Master scale of the printable master model (model millimetres per metre).
SCALE = 1.0

#: Joint clearance per side, in millimetres (calibrated FDM assumption).
CLEARANCE = 0.30

#: Nominal dowel / pin diameter in millimetres.
PIN_DIAMETER = 2.00


def mm(metres: float) -> float:
    """Real metres -> model millimetres (master scale)."""
    return metres * SCALE


def build_parameters(document) -> object:
    """Create the driving spreadsheet with named aliases."""
    sheet = document.addObject("Spreadsheet::Sheet", "Parameters")
    rows = [
        ("Model scale (mm per metre)", SCALE, "scale"),
        ("Foundation plate thickness", 1.6, "plate_thickness"),
        ("Foundation west length", mm(plan_positions(PARAMS)["nandi_x1"] + 2.0
                                      - (plan_positions(PARAMS)["complex_x0"] - 1.0)), "plate_west_length"),
        ("Foundation east length", mm((plan_positions(PARAMS)["complex_x1"] + 1.0)
                                      - (plan_positions(PARAMS)["nandi_x1"] + 2.0)), "plate_east_length"),
        ("Compound width", mm(PARAMS.complex_width_y + 2.0), "plate_width"),
        ("Pin diameter", PIN_DIAMETER, "pin_diameter"),
        ("Pin length", 6.0, "pin_length"),
        ("Socket diameter", PIN_DIAMETER + 2 * CLEARANCE, "socket_diameter"),
        ("Socket depth", 4.0, "socket_depth"),
        ("Roof spigot diameter", 6.0, "spigot_diameter"),
        ("Roof spigot height", 3.0, "spigot_height"),
        ("Roof socket depth", 3.0 + CLEARANCE, "spigot_socket_depth"),
        ("Wall key width", 4.0, "key_width"),
        ("Wall key thickness", 2.0 + 2 * CLEARANCE, "key_thickness"),
        ("Wall key length", 8.0, "key_length"),
        ("Clearance per side", CLEARANCE, "clearance"),
    ]
    sheet.set("A1", "Parameter")
    sheet.set("B1", "Value")
    sheet.set("C1", "Alias")
    for index, (label, value, alias) in enumerate(rows, start=2):
        sheet.set(f"A{index}", label)
        sheet.set(f"B{index}", str(value))
        sheet.set(f"C{index}", alias)
        sheet.setAlias(f"B{index}", alias)
    document.recompute()
    return sheet


def box(name: str, length: float, width: float, height: float, document, placement=None):
    obj = document.addObject("Part::Box", name)
    obj.Length = length
    obj.Width = width
    obj.Height = height
    if placement is not None:
        obj.Placement = placement
    return obj


def cut_cylinder(target, document, radius: float, height: float, x: float, y: float, z: float):
    """Subtract a vertical cylinder (a socket) from ``target``."""
    tool = document.addObject("Part::Cylinder", f"{target.Name}_socketTool")
    tool.Radius = radius
    tool.Height = height
    tool.Placement = App.Placement(App.Vector(x, y, z), App.Rotation())
    boolean = document.addObject("Part::Cut", f"{target.Name}_cut")
    boolean.Base = target
    boolean.Tool = tool
    document.recompute()
    return boolean


def build_foundation_plates(document, sheet) -> list:
    """Two base plates with the sockets that accept the module dowels."""
    parts = []
    plate_t = sheet.get("plate_thickness")
    width = sheet.get("plate_width")
    west_len = sheet.get("plate_west_length")
    east_len = sheet.get("plate_east_length")
    socket_r = sheet.get("socket_diameter") / 2.0
    socket_depth = sheet.get("socket_depth")

    for name, length, x_offset in (
        ("Foundation_Plate_West", west_len, 0.0),
        ("Foundation_Plate_East", east_len, west_len),
    ):
        plate = box(name, length, width, plate_t, document,
                    App.Placement(App.Vector(x_offset, -width / 2.0, 0), App.Rotation()))
        # four dowel sockets near the corners
        for index, (sx, sy) in enumerate((
            (0.10, 0.10), (0.90, 0.10), (0.10, 0.90), (0.90, 0.90),
        )):
            cut_cylinder(plate, document, socket_r, socket_depth + 0.1,
                         x_offset + length * sx, -width / 2.0 + width * sy, plate_t - socket_depth)
        document.recompute()
        parts.append(plate)
    return parts


def build_alignment_pin(document, sheet):
    """A chamfered dowel that joins two modules."""
    diameter = sheet.get("pin_diameter")
    length = sheet.get("pin_length")
    pin = document.addObject("Part::Cylinder", "Alignment_Pin")
    pin.Radius = diameter / 2.0
    pin.Height = length
    pin.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    chamfer = document.addObject("Part::Cylinder", "Alignment_Pin_chamfer")
    chamfer.Radius = diameter / 2.0 - 0.3
    chamfer.Height = 0.6
    chamfer.Placement = App.Placement(App.Vector(0, 0, length - 0.6), App.Rotation())
    boolean = document.addObject("Part::Cut", "Alignment_Pin_cut")
    boolean.Base = pin
    boolean.Tool = chamfer
    document.recompute()
    return boolean


def build_alignment_socket(document, sheet):
    """A sleeve that receives the alignment pin."""
    diameter = sheet.get("socket_diameter")
    length = sheet.get("pin_length") + 1.0
    outer = document.addObject("Part::Cylinder", "Alignment_Socket")
    outer.Radius = diameter / 2.0 + 1.2
    outer.Height = length
    inner = document.addObject("Part::Cylinder", "Alignment_Socket_bore")
    inner.Radius = diameter / 2.0
    inner.Height = length + 1.0
    inner.Placement = App.Placement(App.Vector(0, 0, -0.5), App.Rotation())
    boolean = document.addObject("Part::Cut", "Alignment_Socket_cut")
    boolean.Base = outer
    boolean.Tool = inner
    document.recompute()
    return boolean


def build_roof_interface(document, sheet):
    """Spigot and socket used by the removable roof section of the cut-away model."""
    spigot_d = sheet.get("spigot_diameter")
    spigot_h = sheet.get("spigot_height")
    spigot = document.addObject("Part::Cylinder", "Roof_Spigot")
    spigot.Radius = spigot_d / 2.0
    spigot.Height = spigot_h
    spigot.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

    socket_depth = sheet.get("spigot_socket_depth")
    socket = document.addObject("Part::Cylinder", "Roof_Socket")
    socket.Radius = spigot_d / 2.0 + sheet.get("clearance")
    socket.Height = socket_depth
    socket.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    bore = document.addObject("Part::Cylinder", "Roof_Socket_bore")
    bore.Radius = spigot_d / 2.0
    bore.Height = socket_depth + 0.5
    bore.Placement = App.Placement(App.Vector(0, 0, -0.25), App.Rotation())
    socket_cut = document.addObject("Part::Cut", "Roof_Socket_cut")
    socket_cut.Base = socket
    socket_cut.Tool = bore
    document.recompute()
    return [spigot, socket_cut]


def build_wall_key(document, sheet):
    """A flat key that keys the wall modules to each other."""
    width = sheet.get("key_width")
    thickness = sheet.get("key_thickness")
    length = sheet.get("key_length")
    key = box("Wall_Key", length, width, thickness, document)
    return key


def build_fit_coupon(document, sheet):
    """A small coupon that lets the printed joint clearance be checked first."""
    block = box("Fit_Test_Block", 20.0, 20.0, 6.0, document)
    pin_d = sheet.get("pin_diameter")
    block = cut_cylinder(block, document, pin_d / 2.0 + 0.1, 4.0, 6.0, 10.0, 0.0)
    document.recompute()
    pin = document.addObject("Part::Cylinder", "Fit_Test_Pin")
    pin.Radius = pin_d / 2.0
    pin.Height = 6.0
    pin.Placement = App.Placement(App.Vector(6.0, 10.0, 0.0), App.Rotation())
    document.recompute()
    return [block, pin]


def export_step(objects, path: Path) -> str:
    import Import

    path.parent.mkdir(parents=True, exist_ok=True)
    Import.export(objects, str(path))
    return str(path.relative_to(PROJECT_ROOT))


def main() -> int:
    log_lines = []

    def log(message: str) -> None:
        log_lines.append(message)
        try:
            print(message)
        except Exception:  # pragma: no cover - FreeCAD console may swallow stdout
            pass

    try:
        summary = _build(log)
    except Exception:  # pragma: no cover - surfaced through the log file
        import traceback

        log("EXCEPTION:\n" + traceback.format_exc())
        (DOC_DIR / "cad_generation_log.txt").write_text("\n".join(log_lines), encoding="utf-8")
        raise
    (DOC_DIR / "cad_generation_log.txt").write_text("\n".join(log_lines), encoding="utf-8")
    return 1 if summary.get("invalid_solids") else 0


def _build(log) -> int:
    FCSTD_DIR.mkdir(parents=True, exist_ok=True)
    STEP_DIR.mkdir(parents=True, exist_ok=True)

    document = App.newDocument("brihadisvara_engineering")
    sheet = build_parameters(document)

    exported = []
    groups = {
        "Foundation_Plates": build_foundation_plates(document, sheet),
        "Alignment_Hardware": [build_alignment_pin(document, sheet), build_alignment_socket(document, sheet)],
        "Roof_Interface": build_roof_interface(document, sheet),
        "Wall_Key": [build_wall_key(document, sheet)],
        "Fit_Test_Coupon": build_fit_coupon(document, sheet),
    }

    for name, objects in groups.items():
        for obj in objects:
            obj.Label = f"{name}_{obj.Name}"
        path = STEP_DIR / f"{name.lower()}.step"
        export_step(objects, path)
        exported.append(str(path.relative_to(PROJECT_ROOT)))

    # a single combined STEP file with every engineering component
    all_objects = [obj for objects in groups.values() for obj in objects]
    combined = STEP_DIR / "brihadisvara_engineering_all.step"
    export_step(all_objects, combined)
    exported.append(str(combined.relative_to(PROJECT_ROOT)))

    document.recompute()
    fcstd_path = FCSTD_DIR / "brihadisvara_engineering.FCStd"
    document.saveAs(str(fcstd_path))

    invalid = []
    for obj in document.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is not None and hasattr(shape, "isValid") and not shape.isValid():
            invalid.append(obj.Name)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "freecad_version": ".".join(App.Version()[:3]),
        "document": str(fcstd_path.relative_to(PROJECT_ROOT)),
        "step_exports": exported,
        "objects": len(document.Objects),
        "invalid_solids": invalid,
        "parameters": {
            "scale_mm_per_metre": SCALE,
            "clearance_per_side_mm": CLEARANCE,
            "pin_diameter_mm": PIN_DIAMETER,
        },
    }
    (DOC_DIR / "cad_generation_log.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    log(json.dumps(summary, indent=2))
    return summary


# FreeCADCmd executes this file with a module name that is not
# "__main__", so the build is started explicitly.
_RESULT = main()
