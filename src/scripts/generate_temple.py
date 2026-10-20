#!/usr/bin/env python3
"""Generate the Brihadisvara Temple model in Blender.

The script is executed *inside* Blender:

    src/scripts/blender.sh --background --python src/scripts/generate_temple.py -- --variant all

Variants
--------
``exterior``  the complete complex (compound, prakara, gopurams, halls, vimana)
              at the master scale of 1:1000 (1 mm of model = 1 m of building).
``cutaway``   the temple core at 1:320 with the southern half of the walls and
              roofs removed by a boolean section cut, so the connected interior
              (cella, ambulatory, antrala, mandapas, Nandi mandapa) is visible.
``modular``   the exterior split into printable modules.

Outputs
-------
``src/models/blender/brihadisvara_<variant>.blend``
``src/models/stl/brihadisvara_<variant>.stl`` (+ modular parts)
``src/previews/brihadisvara_<variant>_*.png``
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy  # noqa: E402  (only available inside Blender)
from mathutils import Vector  # noqa: E402

import temple_build as tb  # noqa: E402
from temple_params import (  # noqa: E402
    CUTAWAY_SCALE,
    MASTER_SCALE,
    PARAMS,
    plan_positions,
)

BLEND_DIR = PROJECT_ROOT / "src" / "models" / "blender"
STL_DIR = PROJECT_ROOT / "src" / "models" / "stl"
PREVIEW_DIR = PROJECT_ROOT / "src" / "previews"

COLLECTIONS = [
    "00_REFERENCE",
    "01_FOUNDATION",
    "02_PLINTH",
    "03_MAIN_VIMANA",
    "04_MAIN_HALLS",
    "05_ENTRANCE_GOPURAM",
    "06_COURTYARD_WALLS",
    "07_NANDI_PAVILION",
    "08_ARCHITECTURAL_DETAILS",
    "09_PRINT_ASSEMBLY",
]


# --------------------------------------------------------------------------- #
# Scene helpers
# --------------------------------------------------------------------------- #
def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def setup_scene_units() -> None:
    """Model space is millimetres: 1 Blender unit = 1 mm.

    ``scale_length = 0.001`` makes Blender's metric system display the
    geometry in millimetres, while the raw coordinates stay millimetres so
    that STL export (with ``use_scene_unit=False``) writes true millimetres.
    """
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"


def make_collections() -> dict[str, bpy.types.Collection]:
    scene = bpy.context.scene
    collections = {}
    for name in COLLECTIONS:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
        collections[name] = collection
    return collections


def stone_material(name: str = "TempleStone") -> bpy.types.Material:
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        principled = nodes.get("Principled BSDF")
        if principled is not None:
            principled.inputs["Base Color"].default_value = (0.62, 0.55, 0.44, 1.0)
            principled.inputs["Roughness"].default_value = 0.82
            if "Metallic" in principled.inputs:
                principled.inputs["Metallic"].default_value = 0.0
    return material


def link(builder, name: str, collection, material) -> bpy.types.Object:
    obj = builder.to_object(name, collection, material)
    obj.data.name = f"{name}_mesh"
    return obj


# --------------------------------------------------------------------------- #
# Component assembly
# --------------------------------------------------------------------------- #
def build_exterior_components(options: tb.BuildOptions) -> dict[str, object]:
    """Return the named components of the complete exterior complex."""
    builder = tb.TempleBuilder(options)
    plan = plan_positions(builder.p)

    components = {
        "Ground_Plate": builder.build_ground(),
        "Temple_Plinth": builder.build_plinth(),
        "Sanctum_Cella": builder.build_sanctum(),
        "Antrala_Vestibule": builder.build_antrala(),
        "Maha_Mandapa": builder.build_maha_mandapa(),
        "Mukha_Mandapa": builder.build_mukha_mandapa(),
        "Nandi_Mandapa": builder.build_nandi_mandapa(),
        "Nandi_Bull": builder.build_nandi(),
        "Main_Vimana": builder.build_vimana(),
        "Inner_Gopuram": builder.build_gopuram(inner=True),
        "Outer_Gopuram": builder.build_gopuram(inner=False),
        "Compound_Wall": builder.build_outer_wall(),
        "Prakara_Corridors": builder.build_prakara(),
        "Amman_Shrine": builder.build_sub_shrine(
            PARAMS.amman_shrine_centre, PARAMS.amman_shrine_size, PARAMS.amman_shrine_height
        ),
        "Murugan_Shrine": builder.build_sub_shrine(
            PARAMS.murugan_shrine_centre, PARAMS.murugan_shrine_size, PARAMS.murugan_shrine_height
        ),
        "Temple_Steps": builder.build_stairs(),
    }
    del plan
    return components


def build_cutaway_components(options: tb.BuildOptions) -> dict[str, object]:
    """The temple core (without the outer compound) for the sectioned model."""
    builder = tb.TempleBuilder(options)
    components = {
        "Core_Plinth": builder.build_plinth(),
        "Sanctum_Cella": builder.build_sanctum(),
        "Antrala_Vestibule": builder.build_antrala(),
        "Maha_Mandapa": builder.build_maha_mandapa(),
        "Mukha_Mandapa": builder.build_mukha_mandapa(),
        "Nandi_Mandapa": builder.build_nandi_mandapa(),
        "Nandi_Bull": builder.build_nandi(),
        "Main_Vimana": builder.build_vimana(),
        "Temple_Steps": builder.build_stairs(),
    }
    return components


COLLECTION_OF = {
    "Ground_Plate": "01_FOUNDATION",
    "Core_Plinth": "02_PLINTH",
    "Temple_Plinth": "02_PLINTH",
    "Sanctum_Cella": "04_MAIN_HALLS",
    "Antrala_Vestibule": "04_MAIN_HALLS",
    "Maha_Mandapa": "04_MAIN_HALLS",
    "Mukha_Mandapa": "04_MAIN_HALLS",
    "Nandi_Mandapa": "04_MAIN_HALLS",
    "Nandi_Bull": "07_NANDI_PAVILION",
    "Main_Vimana": "03_MAIN_VIMANA",
    "Inner_Gopuram": "05_ENTRANCE_GOPURAM",
    "Outer_Gopuram": "05_ENTRANCE_GOPURAM",
    "Compound_Wall": "06_COURTYARD_WALLS",
    "Prakara_Corridors": "06_COURTYARD_WALLS",
    "Amman_Shrine": "08_ARCHITECTURAL_DETAILS",
    "Murugan_Shrine": "08_ARCHITECTURAL_DETAILS",
    "Temple_Steps": "08_ARCHITECTURAL_DETAILS",
}


def apply_section_cut(objects: list[bpy.types.Object], cut_y: float) -> None:
    """Boolean section: remove everything south of ``cut_y`` (model mm)."""
    bpy.ops.object.select_all(action="DESELECT")
    cutter = bpy.data.meshes.new("SectionCutter_mesh")
    size = 4000.0
    verts = [
        (-size, -size, -size),
        (size, -size, -size),
        (size, cut_y, -size),
        (-size, cut_y, -size),
        (-size, -size, size),
        (size, -size, size),
        (size, cut_y, size),
        (-size, cut_y, size),
    ]
    faces = [
        [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
        [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7],
    ]
    cutter.from_pydata(verts, [], faces)
    cutter.validate()
    cutter.update()
    cutter_obj = bpy.data.objects.new("SectionCutter", cutter)
    bpy.context.scene.collection.objects.link(cutter_obj)

    for obj in objects:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new("SectionCut", "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.object = cutter_obj
        modifier.solver = "EXACT"
        for flag in ("use_self", "use_hole_tolerant"):
            if hasattr(modifier, flag):
                setattr(modifier, flag, True)
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(cutter_obj, do_unlink=True)


# --------------------------------------------------------------------------- #
# Cameras, lights and rendering
# --------------------------------------------------------------------------- #
def model_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                mins[axis] = min(mins[axis], world[axis])
                maxs[axis] = max(maxs[axis], world[axis])
    return mins, maxs


def add_camera(name: str, location: Vector, target: Vector, lens: float = 55.0) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name)
    camera_data.lens = lens
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    direction = target - location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    return camera


def setup_world() -> None:
    scene = bpy.context.scene
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs[0].default_value = (0.55, 0.62, 0.72, 1.0)
        background.inputs[1].default_value = 0.9


def setup_lights(mins: Vector, maxs: Vector) -> None:
    scene = bpy.context.scene
    centre = (mins + maxs) / 2.0
    radius = max((maxs - mins).x, (maxs - mins).y)

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(3.0)
    sun = bpy.data.objects.new("Key_Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = centre + Vector((radius * 0.6, -radius * 0.9, radius * 1.4))
    sun.rotation_euler = (math.radians(52), math.radians(6), math.radians(38))

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 900.0
    fill_data.size = radius * 0.8
    fill = bpy.data.objects.new("Fill_Area", fill_data)
    scene.collection.objects.link(fill)
    fill.location = centre + Vector((-radius * 0.9, -radius * 0.7, radius * 0.7))
    fill.rotation_euler = (math.radians(62), 0.0, math.radians(-52))

    rim_data = bpy.data.lights.new("Rim", type="AREA")
    rim_data.energy = 700.0
    rim_data.size = radius * 0.6
    rim = bpy.data.objects.new("Rim_Area", rim_data)
    scene.collection.objects.link(rim)
    rim.location = centre + Vector((radius * 0.4, radius * 1.0, radius * 0.9))
    rim.rotation_euler = (math.radians(64), 0.0, math.radians(200))


def fit_camera(
    name: str,
    direction: Vector,
    mins: Vector,
    maxs: Vector,
    lens: float = 55.0,
    margin: float = 1.06,
) -> bpy.types.Object:
    """Place a camera along ``direction`` so that the whole model fits the frame."""
    centre = (mins + maxs) / 2.0
    corners = [
        Vector((x, y, z))
        for x in (mins.x, maxs.x)
        for y in (mins.y, maxs.y)
        for z in (mins.z, maxs.z)
    ]
    diagonal = (maxs - mins).length
    direction = direction.normalized()
    distance = max(diagonal * 0.6, 10.0)
    camera = None
    for _ in range(80):
        location = centre + direction * distance
        camera = add_camera(name, location, centre, lens)
        matrix = camera.matrix_world.inverted()
        sensor = camera.data.sensor_width
        aspect = bpy.context.scene.render.resolution_x / max(1, bpy.context.scene.render.resolution_y)
        tan_x = (sensor / 2.0) / lens
        tan_y = tan_x / aspect
        fits = True
        for corner in corners:
            local = matrix @ corner
            depth = -local.z
            if depth <= 1e-6:
                fits = False
                break
            if abs(local.x) > depth * tan_x / margin or abs(local.y) > depth * tan_y / margin:
                fits = False
                break
        if fits:
            break
        distance *= 1.08
        bpy.data.objects.remove(camera, do_unlink=True)
        camera = None
    if camera is None:
        camera = add_camera(name, centre + direction * distance, centre, lens)
    return camera


def render_views(
    objects: list[bpy.types.Object],
    prefix: str,
    render: bool = True,
    resolution: tuple[int, int] = (1600, 1200),
    samples: int = 48,
) -> list[str]:
    """Render the four architectural views; returns the written file paths."""
    scene = bpy.context.scene
    engine = "BLENDER_EEVEE"
    try:
        scene.render.engine = engine
        scene.eevee.taa_render_samples = max(16, samples)
        if hasattr(scene.eevee, "use_raytracing"):
            scene.eevee.use_raytracing = True
        if hasattr(scene.eevee, "use_shadows"):
            scene.eevee.use_shadows = True
        if hasattr(scene.eevee, "use_gtao"):
            scene.eevee.use_gtao = True
    except TypeError:  # pragma: no cover - engine name differs between versions
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Filmic" if "Filmic" in [
        item.name for item in scene.view_settings.bl_rna.properties["view_transform"].enum_items
    ] else "Standard"

    mins, maxs = model_bounds(objects)

    views = {
        "front_elevation": (Vector((1.0, 0.0, 0.06)), 60.0),
        "three_quarter": (Vector((0.72, -0.78, 0.42)), 55.0),
        "side_elevation": (Vector((0.0, -1.0, 0.05)), 60.0),
        "aerial": (Vector((0.55, -0.62, 0.78)), 50.0),
    }

    written: list[str] = []
    for name, (direction, lens) in views.items():
        camera = fit_camera(f"CAM_{name}", direction, mins, maxs, lens)
        scene.camera = camera
        path = PREVIEW_DIR / f"{prefix}_{name}.png"
        if render:
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            written.append(str(path.relative_to(PROJECT_ROOT)))
        bpy.data.objects.remove(camera, do_unlink=True)
    return written


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
def export_stl(objects: list[bpy.types.Object], path: Path) -> dict:
    """Export the given objects to a single binary STL (millimetres)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.wm.stl_export(
        filepath=str(path),
        export_selected_objects=True,
        global_scale=1.0,
        use_scene_unit=False,
        forward_axis="Y",
        up_axis="Z",
        ascii_format=False,
        apply_modifiers=True,
    )
    info = {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "bytes": path.stat().st_size if path.exists() else 0,
    }
    return info


def object_stats(objects: list[bpy.types.Object]) -> dict:
    vertices = 0
    polygons = 0
    for obj in objects:
        if obj.type == "MESH":
            vertices += len(obj.data.vertices)
            polygons += len(obj.data.polygons)
    return {"objects": len(objects), "vertices": vertices, "polygons": polygons}


# --------------------------------------------------------------------------- #
# Variants
# --------------------------------------------------------------------------- #
def generate_exterior(args) -> dict:
    options = tb.BuildOptions(
        scale=args.scale or MASTER_SCALE,
        ornament=tb.ORNAMENT_SIMPLIFIED,
    )
    setup_scene_units()
    collections = make_collections()
    material = stone_material()

    components = build_exterior_components(options)
    objects = []
    for name, builder in components.items():
        collection = collections[COLLECTION_OF.get(name, "08_ARCHITECTURAL_DETAILS")]
        objects.append(link(builder, name, collection, material))

    setup_world()
    setup_lights(*model_bounds(objects))
    previews = render_views(objects, "brihadisvara_exterior", render=not args.no_render, samples=args.samples, resolution=(args.resolution, int(args.resolution * 0.75)))

    blend_path = BLEND_DIR / "brihadisvara_exterior.blend"
    stl_path = STL_DIR / "brihadisvara_exterior.stl"
    export_stl(objects, stl_path)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    return {
        "variant": "exterior",
        "scale": options.scale,
        "blend": str(blend_path.relative_to(PROJECT_ROOT)),
        "stl": str(stl_path.relative_to(PROJECT_ROOT)),
        "previews": previews,
        "stats": object_stats(objects),
    }


def generate_cutaway(args) -> dict:
    options = tb.BuildOptions(
        scale=args.scale or CUTAWAY_SCALE,
        ornament=tb.ORNAMENT_FULL,
        cutaway=True,
    )
    collections = make_collections()
    material = stone_material("TempleStone")

    components = build_cutaway_components(options)
    objects = []
    for name, builder in components.items():
        collection = collections[COLLECTION_OF.get(name, "08_ARCHITECTURAL_DETAILS")]
        objects.append(link(builder, name, collection, material))

    # section the model on the main axis (keep the northern half)
    apply_section_cut(objects, 0.0)

    setup_world()
    setup_lights(*model_bounds(objects))
    previews = render_views(objects, "brihadisvara_cutaway", render=not args.no_render, samples=args.samples, resolution=(args.resolution, int(args.resolution * 0.75)))

    blend_path = BLEND_DIR / "brihadisvara_cutaway.blend"
    stl_path = STL_DIR / "brihadisvara_cutaway.stl"
    export_stl(objects, stl_path)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    return {
        "variant": "cutaway",
        "scale": options.scale,
        "blend": str(blend_path.relative_to(PROJECT_ROOT)),
        "stl": str(stl_path.relative_to(PROJECT_ROOT)),
        "previews": previews,
        "stats": object_stats(objects),
    }


MODULE_PLAN = [
    ("MOD_03_Temple_Block", ["Temple_Plinth", "Sanctum_Cella", "Antrala_Vestibule", "Maha_Mandapa",
                              "Mukha_Mandapa", "Nandi_Mandapa", "Nandi_Bull", "Main_Vimana",
                              "Temple_Steps"]),
    ("MOD_04_Gopurams", ["Inner_Gopuram", "Outer_Gopuram"]),
    ("MOD_05_Compound_Wall", ["Compound_Wall"]),
    ("MOD_06_Prakara", ["Prakara_Corridors"]),
    ("MOD_07_Courtyard_Shrines", ["Amman_Shrine", "Murugan_Shrine"]),
]


def generate_modular(args) -> dict:
    """Split the exterior into modules that each fit a 250 mm build volume."""
    options = tb.BuildOptions(
        scale=args.scale or MASTER_SCALE,
        ornament=tb.ORNAMENT_SIMPLIFIED,
    )
    collections = make_collections()
    material = stone_material()
    assembly = collections["09_PRINT_ASSEMBLY"]

    builder = tb.TempleBuilder(options)
    components = build_exterior_components(options)

    module_dir = STL_DIR / "modules"
    module_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    # --- foundation, split into a western and an eastern plate ---------- #
    for name, half in (("MOD_01_Foundation_West", "west"), ("MOD_02_Foundation_East", "east")):
        plate = builder.build_ground(half=half)
        obj = link(plate, name, assembly, material)
        path = module_dir / f"{name}.stl"
        export_stl([obj], path)
        written.append(str(path.relative_to(PROJECT_ROOT)))

    # --- remaining modules ---------------------------------------------- #
    objects_by_name: dict[str, bpy.types.Object] = {}
    for name, component in components.items():
        if name == "Ground_Plate":
            continue
        collection = collections[COLLECTION_OF.get(name, "08_ARCHITECTURAL_DETAILS")]
        objects_by_name[name] = link(component, name, collection, material)

    for name, members in MODULE_PLAN:
        targets = [objects_by_name[member] for member in members if member in objects_by_name]
        if not targets:
            continue
        path = module_dir / f"{name}.stl"
        export_stl(targets, path)
        written.append(str(path.relative_to(PROJECT_ROOT)))

    blend_path = BLEND_DIR / "brihadisvara_modular.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    return {
        "variant": "modular",
        "scale": options.scale,
        "blend": str(blend_path.relative_to(PROJECT_ROOT)),
        "modules": written,
        "stats": object_stats(list(objects_by_name.values())),
    }


def apply_axis_cut(obj: bpy.types.Object, keep: str) -> None:
    """Keep only the western or eastern half of an object along X."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    cutter = bpy.data.meshes.new(f"AxisCutter_{keep}_mesh")
    size = 4000.0
    if keep == "west":
        x0, x1 = -size, 0.0
    else:
        x0, x1 = 0.0, size
    verts = [
        (x0, -size, -size), (x1, -size, -size), (x1, size, -size), (x0, size, -size),
        (x0, -size, size), (x1, -size, size), (x1, size, size), (x0, size, size),
    ]
    faces = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    cutter.from_pydata(verts, [], faces)
    cutter.validate()
    cutter.update()
    cutter_obj = bpy.data.objects.new(f"AxisCutter_{keep}", cutter)
    bpy.context.scene.collection.objects.link(cutter_obj)
    modifier = obj.modifiers.new("AxisCut", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter_obj
    modifier.solver = "EXACT"
    for flag in ("use_self", "use_hole_tolerant"):
        if hasattr(modifier, flag):
            setattr(modifier, flag, True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter_obj, do_unlink=True)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else (argv or []))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variant", default="all", choices=["all", "exterior", "cutaway", "modular"])
    parser.add_argument("--scale", type=float, default=None, help="model millimetres per real metre")
    parser.add_argument("--no-render", action="store_true", help="skip preview rendering")
    parser.add_argument("--samples", type=int, default=48)
    parser.add_argument("--resolution", type=int, default=1600, help="preview width in pixels")
    args = parser.parse_args(argv)

    for directory in (BLEND_DIR, STL_DIR, PREVIEW_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    started = time.time()
    results = {}
    variants = ["exterior", "cutaway", "modular"] if args.variant == "all" else [args.variant]
    for variant in variants:
        print(f"=== generating variant: {variant} ===")
        if variant == "exterior":
            results["exterior"] = generate_exterior(args)
        elif variant == "cutaway":
            results["cutaway"] = generate_cutaway(args)
        else:
            results["modular"] = generate_modular(args)
        print(json.dumps(results[variant], indent=2))
        reset_scene()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "blender": bpy.app.version_string,
        "duration_seconds": round(time.time() - started, 1),
        "results": results,
    }
    (PROJECT_ROOT / "src" / "documentation" / "generation_log.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print("generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
