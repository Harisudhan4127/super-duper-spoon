"""Low-level mesh construction helpers used by the temple generators.

The helpers build geometry from explicit vertex/face lists (no booleans, no
remesh, no modifiers) so that every exported mesh is deterministic and has
predictable topology.  All coordinates passed in are **model millimetres**.

Only :mod:`bpy` is imported lazily so that the parameter and geometry modules
can be unit-tested with plain CPython.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

Vector2 = tuple[float, float]
Vector3 = tuple[float, float, float]


@dataclass
class MeshBuilder:
    """Accumulates vertices and faces of one (or many) solid parts."""

    verts: list[Vector3] = field(default_factory=list)
    faces: list[list[int]] = field(default_factory=list)
    part_materials: dict[str, int] = field(default_factory=dict)
    _current_part: str = "default"

    # -- bookkeeping ----------------------------------------------------- #
    def begin_part(self, name: str) -> None:
        self._current_part = name

    def add_verts(self, points: Iterable[Vector3]) -> list[int]:
        start = len(self.verts)
        self.verts.extend(tuple(float(c) for c in p) for p in points)
        return list(range(start, len(self.verts)))

    def add_face(self, indices: Sequence[int]) -> None:
        if len(indices) >= 3:
            self.faces.append(list(indices))

    # -- primitives ------------------------------------------------------ #
    def add_box(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        z0: float,
        z1: float,
    ) -> None:
        """Axis aligned box given by its two opposite corners."""
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        if z1 < z0:
            z0, z1 = z1, z0
        if x1 == x0 or y1 == y0 or z1 == z0:
            return
        base = self.add_verts(
            [
                (x0, y0, z0),
                (x1, y0, z0),
                (x1, y1, z0),
                (x0, y1, z0),
                (x0, y0, z1),
                (x1, y0, z1),
                (x1, y1, z1),
                (x0, y1, z1),
            ]
        )
        b = base
        self.add_face([b[0], b[3], b[2], b[1]])          # bottom  (-Z)
        self.add_face([b[4], b[5], b[6], b[7]])          # top     (+Z)
        self.add_face([b[0], b[1], b[5], b[4]])          # -Y
        self.add_face([b[1], b[2], b[6], b[5]])          # +X
        self.add_face([b[2], b[3], b[7], b[6]])          # +Y
        self.add_face([b[3], b[0], b[4], b[7]])          # -X

    def add_prism(
        self,
        polygon: Sequence[Vector2],
        z0: float,
        z1: float,
        cap_bottom: bool = True,
        cap_top: bool = True,
    ) -> None:
        """Extrude a CCW 2-D polygon between two heights."""
        if len(polygon) < 3 or z1 <= z0:
            return
        count = len(polygon)
        lower = self.add_verts([(x, y, z0) for x, y in polygon])
        upper = self.add_verts([(x, y, z1) for x, y in polygon])
        for index in range(count):
            nxt = (index + 1) % count
            self.add_face([lower[index], lower[nxt], upper[nxt], upper[index]])
        if cap_bottom:
            self.add_face(list(reversed(lower)))
        if cap_top:
            self.add_face(list(upper))

    def add_frustum(
        self,
        bottom: Sequence[Vector2],
        top: Sequence[Vector2],
        z0: float,
        z1: float,
        cap_bottom: bool = True,
        cap_top: bool = True,
    ) -> None:
        """Connect two closed loops of equal length (CCW) between two heights."""
        if len(bottom) != len(top) or len(bottom) < 3 or z1 <= z0:
            return
        count = len(bottom)
        lower = self.add_verts([(x, y, z0) for x, y in bottom])
        upper = self.add_verts([(x, y, z1) for x, y in top])
        for index in range(count):
            nxt = (index + 1) % count
            self.add_face([lower[index], lower[nxt], upper[nxt], upper[index]])
        if cap_bottom:
            self.add_face(list(reversed(lower)))
        if cap_top:
            self.add_face(list(upper))

    def add_tapered_box(
        self,
        centre: Vector2,
        bottom_size: tuple[float, float],
        top_size: tuple[float, float],
        z0: float,
        z1: float,
    ) -> None:
        """Rectangular frustum centred on ``centre``."""
        cx, cy = centre
        bw, bd = bottom_size
        tw, td = top_size
        bottom = [
            (cx - bw / 2, cy - bd / 2),
            (cx + bw / 2, cy - bd / 2),
            (cx + bw / 2, cy + bd / 2),
            (cx - bw / 2, cy + bd / 2),
        ]
        top = [
            (cx - tw / 2, cy - td / 2),
            (cx + tw / 2, cy - td / 2),
            (cx + tw / 2, cy + td / 2),
            (cx - tw / 2, cy + td / 2),
        ]
        self.add_frustum(bottom, top, z0, z1)

    def add_lathe(
        self,
        profile: Sequence[tuple[float, float]],
        centre: Vector2,
        segments: int = 32,
        cap_bottom: bool = True,
        cap_top: bool = True,
    ) -> None:
        """Revolve a (radius, z) profile around the Z axis at ``centre``."""
        if len(profile) < 2:
            return
        cx, cy = centre
        rings: list[list[int]] = []
        for radius, z in profile:
            if abs(radius) < 1e-9:
                rings.append(self.add_verts([(cx, cy, z)]))
            else:
                ring_points = []
                for index in range(segments):
                    angle = 2.0 * math.pi * index / segments
                    ring_points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle), z))
                rings.append(self.add_verts(ring_points))

        for ring_index in range(len(rings) - 1):
            lower = rings[ring_index]
            upper = rings[ring_index + 1]
            if len(lower) == 1 and len(upper) == 1:
                continue
            if len(lower) == 1:
                apex = lower[0]
                for index in range(segments):
                    self.add_face([apex, upper[index], upper[(index + 1) % segments]])
            elif len(upper) == 1:
                apex = upper[0]
                for index in range(segments):
                    self.add_face([lower[index], apex, lower[(index + 1) % segments]])
            else:
                for index in range(segments):
                    nxt = (index + 1) % segments
                    self.add_face([lower[index], lower[nxt], upper[nxt], upper[index]])

        if cap_bottom and len(rings[0]) > 1:
            self.add_face(list(reversed(rings[0])))
        if cap_top and len(rings[-1]) > 1:
            self.add_face(list(rings[-1]))

    def add_wall_with_openings(
        self,
        axis: str,
        start: float,
        end: float,
        thickness: float,
        z0: float,
        z1: float,
        openings: Sequence[tuple[float, float, float, float]] = (),
        offset: float = 0.0,
    ) -> None:
        """Build a straight wall (optionally with door/window openings).

        ``axis`` is ``"x"`` (wall runs along X, thickness along Y) or ``"y"``.
        ``openings`` are ``(u0, u1, v0, v1)`` tuples in the wall's own
        coordinate system: ``u`` along the wall, ``v`` vertical.
        """
        if end <= start or z1 <= z0:
            return

        def _box(u0: float, u1: float, v0: float, v1: float) -> None:
            if axis == "x":
                self.add_box(u0, offset - thickness / 2, u1, offset + thickness / 2, v0, v1)
            else:
                self.add_box(offset - thickness / 2, u0, offset + thickness / 2, u1, v0, v1)

        # split the wall into vertical bands around the openings
        cuts: list[tuple[float, float, float, float]] = []
        cursor = start
        for u0, u1, v0, v1 in sorted(openings, key=lambda o: o[0]):
            u0 = max(start, min(end, u0))
            u1 = max(start, min(end, u1))
            if u1 <= u0:
                continue
            if u0 > cursor:
                cuts.append((cursor, u0, z0, z1))
            cuts.append((u0, u1, z0, v0))       # below the opening
            cuts.append((u0, u1, v1, z1))       # above the opening
            cursor = u1
        if cursor < end:
            cuts.append((cursor, end, z0, z1))

        for u0, u1, v0, v1 in cuts:
            if u1 - u0 > 1e-6 and v1 - v0 > 1e-6:
                _box(u0, u1, v0, v1)

    def add_stairs(
        self,
        x_start: float,
        direction: int,
        width: float,
        y_centre: float,
        z_bottom: float,
        z_top: float,
        riser: float,
        tread: float,
    ) -> None:
        """A flight of steps climbing along +X (direction=+1) or -X."""
        steps = max(1, int(round((z_top - z_bottom) / riser)))
        step_h = (z_top - z_bottom) / steps
        for index in range(steps):
            x0 = x_start + direction * index * tread
            x1 = x0 + direction * tread
            z = z_bottom + step_h * (index + 1)
            if direction > 0:
                self.add_box(x0, y_centre - width / 2, x1, y_centre + width / 2, z_bottom, z)
            else:
                self.add_box(x1, y_centre - width / 2, x0, y_centre + width / 2, z_bottom, z)

    # -- output ---------------------------------------------------------- #
    def to_object(self, name: str, collection, material=None, smooth: bool = False):
        """Create a Blender object from the accumulated geometry."""
        import bpy  # local import: keeps the module importable outside Blender

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        mesh.validate(verbose=False)
        mesh.update()
        if smooth:
            for polygon in mesh.polygons:
                polygon.use_smooth = True
        if material is not None:
            mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        return obj


# --------------------------------------------------------------------------- #
# Profile helpers
# --------------------------------------------------------------------------- #
def rectangular_loop(cx: float, cy: float, width: float, depth: float) -> list[Vector2]:
    """CCW rectangle loop."""
    return [
        (cx - width / 2, cy - depth / 2),
        (cx + width / 2, cy - depth / 2),
        (cx + width / 2, cy + depth / 2),
        (cx - width / 2, cy + depth / 2),
    ]


def chamfered_loop(cx: float, cy: float, width: float, depth: float, chamfer: float) -> list[Vector2]:
    """Rectangle with the four corners cut back (octagonal profile)."""
    cx0, cx1 = cx - width / 2, cx + width / 2
    cy0, cy1 = cy - depth / 2, cy + depth / 2
    ch = min(chamfer, width / 2.6, depth / 2.6)
    return [
        (cx0 + ch, cy0),
        (cx1 - ch, cy0),
        (cx1, cy0 + ch),
        (cx1, cy1 - ch),
        (cx1 - ch, cy1),
        (cx0 + ch, cy1),
        (cx0, cy1 - ch),
        (cx0, cy0 + ch),
    ]


def scaled_loop(loop: Sequence[Vector2], cx: float, cy: float, factor: float) -> list[Vector2]:
    """Scale a loop about its own centre."""
    return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in loop]
