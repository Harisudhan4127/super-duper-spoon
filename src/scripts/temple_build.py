"""Construction of the Brihadisvara Temple model geometry.

The builder works in **real-world metres** (the values in
:mod:`temple_params`) and converts to model millimetres when it writes
vertices, so the same source produces the 1:1000 master model and the 1:320
detail model.

Every component is a separate :class:`~temple_geom.MeshBuilder` so that it can
be exported as an individual, printable part or grouped into a modular set.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from temple_geom import (
    MeshBuilder,
    chamfered_loop,
    rectangular_loop,
)
from temple_params import PARAMS, PrintProfile, TempleParameters, plan_positions

# --------------------------------------------------------------------------- #
# Ornament levels
# --------------------------------------------------------------------------- #
#: 0 = massing only, 1 = simplified (master 1:1000 model), 2 = full (detail
#: 1:320 model).  Level 1 amplifies sub-millimetre features so that they stay
#: printable instead of vanishing.
ORNAMENT_FULL = 2
ORNAMENT_SIMPLIFIED = 1
ORNAMENT_MASSING = 0


@dataclass
class BuildOptions:
    """Options controlling one build of the temple."""

    scale: float = 1.0                    # model millimetres per real metre
    ornament: int = ORNAMENT_SIMPLIFIED
    profile: PrintProfile = None          # type: ignore[assignment]
    cutaway: bool = False                 # omit the near half of walls/roofs
    cut_plane: float = 0.0                # cut plane in model millimetres (Y)

    def __post_init__(self) -> None:
        if self.profile is None:
            from temple_params import PRINT_PROFILE

            self.profile = PRINT_PROFILE


class TempleBuilder:
    """Builds the temple components into individual mesh builders."""

    def __init__(self, options: BuildOptions | None = None, params: TempleParameters = PARAMS):
        self.options = options or BuildOptions()
        self.p = params
        self.k = self.options.scale
        self.plan = plan_positions(params)

    # -- unit helpers ---------------------------------------------------- #
    def m(self, value: float) -> float:
        """Real metres -> model millimetres."""
        return value * self.k

    def amp(self, metres: float, minimum_mm: float = 0.9) -> float:
        """Amplify a feature so that it stays printable at the current scale.

        Returns the *model millimetre* size of a feature that is ``metres``
        long in reality, never smaller than ``minimum_mm``.
        """
        raw = self.m(metres)
        return raw if raw >= minimum_mm else minimum_mm

    def amp_m(self, metres: float, minimum_mm: float = 0.9) -> float:
        """Same as :meth:`amp` but returns the value back in real metres."""
        return self.amp(metres, minimum_mm) / self.k

    def wall(
        self,
        mb: MeshBuilder,
        axis: str,
        start: float,
        end: float,
        thickness: float,
        z0: float,
        z1: float,
        openings: tuple = (),
        offset: float = 0.0,
    ) -> None:
        """Add a wall given in **real metres**; converted to model millimetres.

        ``openings`` are ``(u0, u1, v0, v1)`` tuples, also in real metres.
        """
        mb.add_wall_with_openings(
            axis,
            self.m(start),
            self.m(end),
            self.m(thickness),
            self.m(z0),
            self.m(z1),
            openings=[(self.m(u0), self.m(u1), self.m(v0), self.m(v1)) for u0, u1, v0, v1 in openings],
            offset=self.m(offset),
        )

    # ================================================================== #
    # 01 - ground plate and courtyard floor
    # ================================================================== #
    def build_ground(self, half: str | None = None) -> MeshBuilder:
        """Base plate (and courtyard skin).

        ``half`` selects one half of the plate ("west" or "east") so that the
        foundation can be printed as two smaller modules.
        """
        mb = MeshBuilder()
        p = self.p
        plan = self.plan

        # printing bed contact plate, slightly larger than the compound
        margin = 1.0
        split_x = self.m(plan["nandi_x1"] + 2.0)
        x0 = self.m(plan["complex_x0"] - margin)
        x1 = self.m(plan["complex_x1"] + margin)
        y0 = self.m(plan["complex_y0"] - margin)
        y1 = self.m(plan["complex_y1"] + margin)
        if half == "west":
            x1 = split_x
        elif half == "east":
            x0 = split_x
        plate_t = 1.2
        mb.add_box(x0, y0, x1, y1, -self.m(plate_t), 0.0)

        # courtyard surface (a very thin skin so the plate stays the datum)
        skin = 0.4
        skin_x0 = x0 if half else self.m(plan["complex_x0"])
        skin_x1 = x1 if half else self.m(plan["complex_x1"])
        mb.add_box(
            skin_x0,
            self.m(plan["complex_y0"]),
            skin_x1,
            self.m(plan["complex_y1"]),
            0.0,
            skin,
        )
        # the compound is not perfectly level in reality; a 0.4 mm skin keeps
        # the printing bed flat while the architecture sits on top of it.
        del p
        return mb

    # ================================================================== #
    # 02 - stepped main plinth of the temple block
    # ================================================================== #
    def build_plinth(self) -> MeshBuilder:
        mb = MeshBuilder()
        p = self.p
        plan = self.plan

        # footprint of the temple block: vimana + halls + nandi mandapa
        bx0 = plan["vimana_x0"]
        bx1 = plan["nandi_x1"]
        by0 = -p.vimana_base_side / 2
        by1 = p.vimana_base_side / 2

        z = 0.0
        for height, offset in zip(p.platform_step_heights, p.platform_step_offsets):
            mb.add_box(
                self.m(bx0 - offset),
                self.m(by0 - offset),
                self.m(bx1 + offset),
                self.m(by1 + offset),
                self.m(z),
                self.m(z + height),
            )
            z += height

        # the platform top is flat: fill the core volume so the model is solid
        mb.add_box(
            self.m(bx0),
            self.m(by0),
            self.m(bx1),
            self.m(by1),
            self.m(z),
            self.m(p.platform_height),
        )
        return mb

    # ================================================================== #
    # 03 - main vimana (the tower)
    # ================================================================== #
    def build_vimana(self) -> MeshBuilder:
        mb = MeshBuilder()
        p = self.p
        options = self.options

        base_side = p.vimana_base_side
        top_side = p.vimana_top_side
        z_base = p.vimana_base_z + p.sanctum_height      # top of the sanctuary block
        z_aditala = z_base
        storey_h = p.vimana_storey_height
        count = p.vimana_storey_count

        # ---- aditala (square base block of the superstructure) ---------- #
        mb.add_box(
            self.m(-base_side / 2),
            self.m(-base_side / 2),
            self.m(base_side / 2),
            self.m(base_side / 2),
            self.m(z_aditala),
            self.m(z_aditala + p.vimana_lower_height),
        )
        # base moulding of the aditala
        self._add_storey_cornice(
            mb,
            side=base_side,
            z0=z_aditala,
            z1=z_aditala + 0.9,
        )
        self._add_storey_cornice(
            mb,
            side=base_side,
            z0=z_aditala + p.vimana_lower_height - p.vimana_cornice_height,
            z1=z_aditala + p.vimana_lower_height,
        )
        if options.ornament >= ORNAMENT_SIMPLIFIED:
            self._add_storey_articulation(
                mb,
                side=base_side,
                z0=z_aditala,
                z1=z_aditala + p.vimana_lower_height,
                bays=4,
            )

        # ---- the tapering square storeys ------------------------------- #
        z = z_aditala + p.vimana_lower_height
        for index in range(count):
            t0 = index / count
            t1 = (index + 1) / count
            side0 = self._taper(base_side, top_side, t0)
            side1 = self._taper(base_side, top_side, t1)
            mb.add_tapered_box(
                (0.0, 0.0),
                (side0, side0),
                (side1, side1),
                self.m(z),
                self.m(z + storey_h - p.vimana_cornice_height),
            )
            self._add_storey_cornice(
                mb,
                side=side1,
                z0=z + storey_h - p.vimana_cornice_height,
                z1=z + storey_h,
            )
            if options.ornament >= ORNAMENT_SIMPLIFIED:
                self._add_storey_articulation(
                    mb,
                    side=side1,
                    z0=z,
                    z1=z + storey_h - p.vimana_cornice_height,
                    bays=4,
                )
            z += storey_h

        # ---- griva: the single granite block on top -------------------- #
        griva_side = p.vimana_griva_side
        mb.add_box(
            self.m(-griva_side / 2),
            self.m(-griva_side / 2),
            self.m(griva_side / 2),
            self.m(griva_side / 2),
            self.m(z),
            self.m(z + p.vimana_griva_height),
        )
        # corner Nandi pairs (1.98 x 1.68 m)
        if options.ornament >= ORNAMENT_SIMPLIFIED:
            nandi_w = 1.68
            nandi_d = 1.98
            offset = griva_side / 2 - nandi_d / 2
            for sx in (-1, 1):
                for sy in (-1, 1):
                    cx = sx * offset
                    cy = sy * (griva_side / 2 - nandi_w / 2)
                    mb.add_box(
                        self.m(cx - nandi_d / 2),
                        self.m(cy - nandi_w / 2),
                        self.m(cx + nandi_d / 2),
                        self.m(cy + nandi_w / 2),
                        self.m(z + p.vimana_griva_height),
                        self.m(z + p.vimana_griva_height + 1.2),
                    )
        z += p.vimana_griva_height

        # ---- sikhara: ribbed cupola ------------------------------------- #
        radius = griva_side / 2
        profile = [
            (radius * 1.02, 0.0),
            (radius * 1.02, 0.25),
            (radius * 0.92, 0.35),
            (radius * 0.86, 0.55),
            (radius * 0.72, 0.70),
            (radius * 0.60, 0.90),
            (radius * 0.44, 1.10),
            (radius * 0.26, 1.45),
            (radius * 0.12, 1.80),
            (0.0, 2.00),
        ]
        sikhara_profile = [(self.m(r), self.m(z + p.vimana_sikhara_height * (h / 2.00))) for r, h in profile]
        mb.add_lathe(sikhara_profile, (0.0, 0.0), segments=16, cap_bottom=False, cap_top=False)
        z += p.vimana_sikhara_height

        # ---- stupi: the finial ------------------------------------------ #
        finial = [
            (0.95, 0.00),
            (0.95, 0.30),
            (0.70, 0.45),
            (0.70, 0.80),
            (0.55, 1.05),
            (0.62, 1.35),
            (0.50, 1.70),
            (0.34, 2.10),
            (0.22, 2.60),
            (0.16, 3.10),
            (0.10, 3.50),
            (0.0, 3.83),
        ]
        finial_profile = [(self.m(r), self.m(z + h)) for r, h in finial]
        mb.add_lathe(finial_profile, (0.0, 0.0), segments=12, cap_bottom=False, cap_top=False)

        return mb

    def _taper(self, base: float, top: float, t: float) -> float:
        """Plan side of a storey at fraction ``t`` up the tapering section.

        The exponent (>1) keeps the lower half of the tower close to vertical
        and concentrates the recession in the upper storeys, which matches the
        convex silhouette of the Brihadisvara vimana in the reference
        photographs.
        """
        return base - (base - top) * (t ** 1.35)

    def _add_storey_cornice(self, mb: MeshBuilder, side: float, z0: float, z1: float) -> None:
        """Projecting kapota band that separates two storeys."""
        projection = self.amp_m(self.p.cornice_projection, 0.9)
        height = self.amp_m(self.p.vimana_cornice_height, 0.9)
        outer = side + 2 * projection
        mb.add_box(
            self.m(-outer / 2),
            self.m(-outer / 2),
            self.m(outer / 2),
            self.m(outer / 2),
            self.m(z1 - height),
            self.m(z1),
        )

    def _add_storey_articulation(
        self,
        mb: MeshBuilder,
        side: float,
        z0: float,
        z1: float,
        bays: int,
    ) -> None:
        """Pilaster rhythm and small kuta/sala motifs on the four faces."""
        if bays < 1:
            return
        depth = self.amp_m(0.30, 0.7)
        width = self.amp_m(0.95, 1.0)
        height = z1 - z0
        motif_h = min(height * 0.55, self.amp_m(1.10, 1.0))
        motif_w = self.amp_m(0.90, 1.0)

        half = side / 2
        pitch = side / bays
        for face in range(4):
            for index in range(bays):
                offset = -half + pitch * (index + 0.5)
                if abs(offset) > half - pitch * 0.15:
                    continue
                if face == 0:      # +Y
                    cx, cy = offset, half
                    mb.add_box(
                        self.m(cx - width / 2),
                        self.m(cy),
                        self.m(cx + width / 2),
                        self.m(cy + depth),
                        self.m(z0 + height * 0.15),
                        self.m(z0 + height * 0.9),
                    )
                elif face == 1:    # -Y
                    cx, cy = offset, -half
                    mb.add_box(
                        self.m(cx - width / 2),
                        self.m(cy - depth),
                        self.m(cx + width / 2),
                        self.m(cy),
                        self.m(z0 + height * 0.15),
                        self.m(z0 + height * 0.9),
                    )
                elif face == 2:    # +X
                    cx, cy = half, offset
                    mb.add_box(
                        self.m(cx),
                        self.m(cy - width / 2),
                        self.m(cx + depth),
                        self.m(cy + width / 2),
                        self.m(z0 + height * 0.15),
                        self.m(z0 + height * 0.9),
                    )
                else:              # -X
                    cx, cy = -half, offset
                    mb.add_box(
                        self.m(cx - depth),
                        self.m(cy - width / 2),
                        self.m(cx),
                        self.m(cy + width / 2),
                        self.m(z0 + height * 0.15),
                        self.m(z0 + height * 0.9),
                    )

                # small kuta (miniature shrine) motif between the pilasters
                if index % 2 == 0:
                    mo = offset + pitch * 0.5
                    if abs(mo) > half - pitch * 0.3:
                        continue
                    self._add_kuta(mb, face, mo, half, depth, motif_w, motif_h, z0 + height * 0.25)

    def _add_kuta(
        self,
        mb: MeshBuilder,
        face: int,
        offset: float,
        half: float,
        depth: float,
        width: float,
        height: float,
        z0: float,
    ) -> None:
        """A small projecting shrine motif (kuta) on one face."""
        cap = self.amp_m(0.35, 0.8)
        if face == 0:
            mb.add_box(
                self.m(offset - width / 2), self.m(half), self.m(offset + width / 2),
                self.m(half + depth * 0.45), self.m(z0), self.m(z0 + height),
            )
            mb.add_box(
                self.m(offset - width * 0.65), self.m(half), self.m(offset + width * 0.65),
                self.m(half + depth * 0.55), self.m(z0 + height), self.m(z0 + height + cap),
            )
        elif face == 1:
            mb.add_box(
                self.m(offset - width / 2), self.m(-half - depth * 0.45), self.m(offset + width / 2),
                self.m(-half), self.m(z0), self.m(z0 + height),
            )
            mb.add_box(
                self.m(offset - width * 0.65), self.m(-half - depth * 0.55), self.m(offset + width * 0.65),
                self.m(-half), self.m(z0 + height), self.m(z0 + height + cap),
            )
        elif face == 2:
            mb.add_box(
                self.m(half), self.m(offset - width / 2), self.m(half + depth * 0.45),
                self.m(offset + width / 2), self.m(z0), self.m(z0 + height),
            )
            mb.add_box(
                self.m(half), self.m(offset - width * 0.65), self.m(half + depth * 0.55),
                self.m(offset + width * 0.65), self.m(z0 + height), self.m(z0 + height + cap),
            )
        else:
            mb.add_box(
                self.m(-half - depth * 0.45), self.m(offset - width / 2), self.m(-half),
                self.m(offset + width / 2), self.m(z0), self.m(z0 + height),
            )
            mb.add_box(
                self.m(-half - depth * 0.55), self.m(offset - width * 0.65), self.m(-half),
                self.m(offset + width * 0.65), self.m(z0 + height), self.m(z0 + height + cap),
            )

    # ================================================================== #
    # 04 - sanctum, ambulatory passage and antrala
    # ================================================================== #
    def build_sanctum(self) -> MeshBuilder:
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        z0 = p.platform_height
        z1 = z0 + p.sanctum_height

        half_s = p.sanctum_width / 2
        half_a = p.sanctum_outer_side / 2
        wall_t = p.sanctum_wall_thickness
        amb_w = p.ambulatory_width

        # cella walls (four walls with a door on the east axis)
        door_w = 2.0
        door_h = 4.2
        for face in range(4):
            if face == 2:  # +X (east) wall with the entrance
                self.wall(
                    mb,
                    "y",
                    -half_s,
                    half_s,
                    wall_t,
                    z0,
                    z1,
                    openings=[(-door_w / 2, door_w / 2, z0, z0 + door_h)],
                    offset=half_s - wall_t / 2,
                )
            else:
                if face == 0:
                    axis, start, end, offset = "x", -half_s, half_s, half_s - wall_t / 2
                elif face == 1:
                    axis, start, end, offset = "x", -half_s, half_s, -half_s + wall_t / 2
                else:
                    axis, start, end, offset = "y", -half_s, half_s, -half_s + wall_t / 2
                self.wall(mb, axis, start, end, wall_t, z0, z1, offset=offset)

        # ambulatory outer wall (pradakshina patha)
        outer_t = p.ambulatory_wall_thickness
        for face in range(4):
            if face == 2:
                self.wall(
                    mb,
                    "y",
                    -half_a,
                    half_a,
                    outer_t,
                    z0,
                    z1,
                    openings=[(-2.4, 2.4, z0, z0 + 4.6)],
                    offset=half_a - outer_t / 2,
                )
            else:
                if face == 0:
                    axis, start, end, offset = "x", -half_a, half_a, half_a - outer_t / 2
                elif face == 1:
                    axis, start, end, offset = "x", -half_a, half_a, -half_a + outer_t / 2
                else:
                    axis, start, end, offset = "y", -half_a, half_a, -half_a + outer_t / 2
                self.wall(mb, axis, start, end, outer_t, z0, z1, offset=offset)

        # floor of the cella and of the ambulatory passage
        mb.add_box(
            self.m(-half_s), self.m(-half_s), self.m(half_s), self.m(half_s),
            self.m(z0 - 0.1), self.m(z0 + 0.05),
        )
        mb.add_box(
            self.m(-half_a), self.m(-half_a), self.m(half_a), self.m(half_a),
            self.m(z0 - 0.1), self.m(z0 + 0.03),
        )

        # the great linga (8.70 m high, occupying two storeys of the cella)
        if self.options.ornament >= ORNAMENT_SIMPLIFIED:
            linga = [
                (1.55, 0.00),
                (1.55, 0.45),
                (1.30, 0.70),
                (1.05, 1.10),
                (0.95, 2.60),
                (0.90, 5.20),
                (0.86, 7.10),
                (0.82, 7.90),
                (0.72, 8.30),
                (0.40, 8.55),
                (0.0, 8.70),
            ]
            profile = [(self.m(r), self.m(z0 + h)) for r, h in linga]
            mb.add_lathe(profile, (0.0, 0.0), segments=24)

        # roof slab of the sanctuary block (carries the aditala)
        mb.add_box(
            self.m(-half_a), self.m(-half_a), self.m(half_a), self.m(half_a),
            self.m(z1), self.m(z1 + 0.6),
        )
        del plan
        return mb

    def build_antrala(self) -> MeshBuilder:
        """The vestibule linking the ambulatory passage to the maha-mandapa."""
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        z0 = p.platform_height
        z1 = z0 + p.sanctum_height
        x0, x1 = plan["antrala_x0"], plan["antrala_x1"]
        half_w = p.antrala_width / 2
        t = p.ambulatory_wall_thickness
        mb.add_box(
            self.m(x0), self.m(-half_w), self.m(x1), self.m(half_w),
            self.m(z0 - 0.1), self.m(z0 + 0.05),
        )
        for sign in (-1, 1):
            self.wall(mb, "x", x0, x1, t, z0, z1, offset=sign * (half_w - t / 2))
        mb.add_box(
            self.m(x0), self.m(-half_w), self.m(x1), self.m(half_w),
            self.m(z1), self.m(z1 + 0.5),
        )
        return mb

    # ================================================================== #
    # 05 - pillared halls
    # ================================================================== #
    def _build_hall(
        self,
        name: str,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        wall_height: float,
        pillars_per_side: int,
        z0: float,
        with_roof: bool = True,
    ) -> MeshBuilder:
        """A square pillared hall with a corniced roof (mandapa)."""
        mb = MeshBuilder()
        p = self.p
        wall_t = p.ambulatory_wall_thickness
        door_w = 2.4
        door_h = 4.4

        # floor
        mb.add_box(self.m(x0), self.m(y0), self.m(x1), self.m(y1), self.m(z0 - 0.1), self.m(z0 + 0.05))

        # enclosure walls with a doorway on the axis
        self.wall(
            mb, "y", y0, y1, wall_t, z0, z0 + wall_height,
            openings=[(-door_w / 2, door_w / 2, z0, z0 + door_h)], offset=x1 - wall_t / 2,
        )
        self.wall(mb, "y", y0, y1, wall_t, z0, z0 + wall_height, offset=x0 + wall_t / 2)
        self.wall(mb, "x", x0, x1, wall_t, z0, z0 + wall_height, offset=y0 + wall_t / 2)
        self.wall(mb, "x", x0, x1, wall_t, z0, z0 + wall_height, offset=y1 - wall_t / 2)

        # internal colonnade
        for axis, start, end, fixed in (
            ("x", x0 + 1.6, x1 - 1.6, y0 + 1.6),
            ("x", x0 + 1.6, x1 - 1.6, y1 - 1.6),
        ):
            self._add_pillar_row(mb, axis, start, end, fixed, z0, wall_height)
        for axis, start, end, fixed in (
            ("y", y0 + 1.6, y1 - 1.6, x0 + 1.6),
            ("y", y0 + 1.6, y1 - 1.6, x1 - 1.6),
        ):
            self._add_pillar_row(mb, axis, start, end, fixed, z0, wall_height)

        # roof: stepped Dravidian profile with a cornice
        if with_roof:
            self._add_hall_roof(mb, x0, x1, y0, y1, z0 + wall_height)
        return mb

    def _add_pillar_row(
        self,
        mb: MeshBuilder,
        axis: str,
        start: float,
        end: float,
        fixed: float,
        z0: float,
        height: float,
    ) -> None:
        """A row of pillars along ``axis`` at the given offset."""
        p = self.p
        count = max(2, int(round((end - start) / 3.2)))
        pitch = (end - start) / (count - 1) if count > 1 else 0.0
        for index in range(count):
            pos = start + pitch * index
            self._add_pillar(mb, axis, pos, fixed, z0, height)

    def _add_pillar(
        self,
        mb: MeshBuilder,
        axis: str,
        pos: float,
        fixed: float,
        z0: float,
        height: float,
    ) -> None:
        """A Chola-style pillar: moulded base, octagonal shaft, capital."""
        p = self.p
        r = p.pillar_radius
        base_h = self.amp_m(p.pillar_base_height, 0.9)
        cap_h = self.amp_m(p.pillar_capital_height, 0.9)
        shaft_h = height - base_h - cap_h

        def place(px: float, py: float, sx: float, sy: float, z_from: float, z_to: float) -> None:
            mb.add_box(
                self.m(px - sx / 2), self.m(py - sy / 2), self.m(px + sx / 2), self.m(py + sy / 2),
                self.m(z_from), self.m(z_to),
            )

        if axis == "x":
            cx, cy = pos, fixed
        else:
            cx, cy = fixed, pos

        place(cx, cy, r * 2.6, r * 2.6, z0, z0 + base_h * 0.45)
        place(cx, cy, r * 2.2, r * 2.2, z0 + base_h * 0.45, z0 + base_h)
        place(cx, cy, r * 1.8, r * 1.8, z0 + base_h, z0 + base_h + shaft_h)
        place(cx, cy, r * 2.2, r * 2.2, z0 + base_h + shaft_h, z0 + height - cap_h * 0.4)
        place(cx, cy, r * 2.6, r * 2.6, z0 + height - cap_h * 0.4, z0 + height)

    def _add_hall_roof(self, mb: MeshBuilder, x0: float, x1: float, y0: float, y1: float, z: float) -> None:
        """Stepped Dravidian roof: cornice, two receding courses and a ridge."""
        p = self.p
        corn_h = self.amp_m(p.cornice_height, 0.9)
        corn_pr = self.amp_m(p.cornice_projection, 0.9)
        course_h = self.amp_m(0.70, 0.8)
        inset = self.amp_m(0.80, 0.9)

        # cornice band
        mb.add_box(
            self.m(x0 - corn_pr), self.m(y0 - corn_pr), self.m(x1 + corn_pr), self.m(y1 + corn_pr),
            self.m(z), self.m(z + corn_h),
        )
        # first receding course
        mb.add_box(
            self.m(x0), self.m(y0), self.m(x1), self.m(y1),
            self.m(z + corn_h), self.m(z + corn_h + course_h),
        )
        # second receding course
        mb.add_box(
            self.m(x0 + inset), self.m(y0 + inset), self.m(x1 - inset), self.m(y1 - inset),
            self.m(z + corn_h + course_h), self.m(z + corn_h + 2 * course_h),
        )
        # ridge along the long axis
        if (x1 - x0) >= (y1 - y0):
            mb.add_box(
                self.m(x0 + 1.4), self.m((y0 + y1) / 2 - 1.3), self.m(x1 - 1.4), self.m((y0 + y1) / 2 + 1.3),
                self.m(z + corn_h + 2 * course_h), self.m(z + corn_h + 2 * course_h + course_h),
            )
        else:
            mb.add_box(
                self.m((x0 + x1) / 2 - 1.3), self.m(y0 + 1.4), self.m((x0 + x1) / 2 + 1.3), self.m(y1 - 1.4),
                self.m(z + corn_h + 2 * course_h), self.m(z + corn_h + 2 * course_h + course_h),
            )

    def build_connecting_passage(self) -> MeshBuilder:
        """The short covered passage that links the mukha-mandapa to the Nandi hall.

        Without it the sequence of halls would be a row of separate buildings;
        with it the interior of the temple is a single connected route:
        Nandi hall -> mukha-mandapa -> maha-mandapa -> antrala -> ambulatory
        passage -> sanctum.
        """
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        x0 = plan["mukha_x1"]
        x1 = plan["nandi_x0"]
        half_w = 3.0
        wall_t = p.ambulatory_wall_thickness
        z0 = p.platform_height
        z1 = z0 + 6.4

        # floor
        mb.add_box(self.m(x0), self.m(-half_w), self.m(x1), self.m(half_w), self.m(z0 - 0.1), self.m(z0 + 0.05))
        # side walls
        for sign in (-1, 1):
            self.wall(mb, "x", x0, x1, wall_t, z0, z1, offset=sign * (half_w - wall_t / 2))
        # flat roof with a cornice
        corn_h = self.amp_m(p.cornice_height, 0.9)
        corn_pr = self.amp_m(p.cornice_projection, 0.9)
        mb.add_box(
            self.m(x0 - corn_pr), self.m(-half_w - corn_pr), self.m(x1 + corn_pr), self.m(half_w + corn_pr),
            self.m(z1), self.m(z1 + corn_h),
        )
        mb.add_box(
            self.m(x0), self.m(-half_w), self.m(x1), self.m(half_w),
            self.m(z1 + corn_h), self.m(z1 + corn_h + 0.7),
        )
        return mb

    def build_hall_roofs(self) -> MeshBuilder:
        """The removable roof section of the three halls.

        The cut-away model keeps the roofs as a separate part so that the
        interior can be opened; the piece is located by the spigot and socket
        described in ``src/documentation/print_settings.md``.
        """
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        for x0, x1, half_y, height in (
            (plan["maha_x0"], plan["maha_x1"], p.maha_mandapa_y / 2, p.maha_mandapa_wall_height),
            (plan["mukha_x0"], plan["mukha_x1"], p.mukha_mandapa_y / 2, p.mukha_mandapa_wall_height),
            (plan["nandi_x0"], plan["nandi_x1"], p.nandi_mandapa_y / 2, p.nandi_mandapa_wall_height),
        ):
            self._add_hall_roof(mb, x0, x1, -half_y, half_y, p.platform_height + height)
        return mb

    def build_maha_mandapa(self) -> MeshBuilder:
        p = self.p
        plan = self.plan
        return self._build_hall(
            "maha_mandapa",
            plan["maha_x0"],
            plan["maha_x1"],
            -p.maha_mandapa_y / 2,
            p.maha_mandapa_y / 2,
            p.maha_mandapa_wall_height,
            p.maha_mandapa_pillars_per_side,
            p.platform_height,
            with_roof=not self.options.cutaway,
        )

    def build_mukha_mandapa(self) -> MeshBuilder:
        p = self.p
        plan = self.plan
        return self._build_hall(
            "mukha_mandapa",
            plan["mukha_x0"],
            plan["mukha_x1"],
            -p.mukha_mandapa_y / 2,
            p.mukha_mandapa_y / 2,
            p.mukha_mandapa_wall_height,
            p.mukha_mandapa_pillars_per_side,
            p.platform_height,
            with_roof=not self.options.cutaway,
        )

    def build_nandi_mandapa(self) -> MeshBuilder:
        p = self.p
        plan = self.plan
        return self._build_hall(
            "nandi_mandapa",
            plan["nandi_x0"],
            plan["nandi_x1"],
            -p.nandi_mandapa_y / 2,
            p.nandi_mandapa_y / 2,
            p.nandi_mandapa_wall_height,
            4,
            p.platform_height,
            with_roof=not self.options.cutaway,
        )

    # ================================================================== #
    # 06 - the monolithic Nandi
    # ================================================================== #
    def build_nandi(self) -> MeshBuilder:
        """A simplified but recognisable seated bull facing the sanctum."""
        mb = MeshBuilder()
        p = self.p
        length = p.nandi_length
        breadth = p.nandi_breadth
        height = p.nandi_height
        cx = p.nandi_centre_x
        cy = p.nandi_centre_y
        z0 = p.platform_height

        # pedestal
        mb.add_box(
            self.m(cx - length / 2 - 0.3), self.m(cy - breadth / 2 - 0.3),
            self.m(cx + length / 2 + 0.3), self.m(cy + breadth / 2 + 0.3),
            self.m(z0), self.m(z0 + 0.55),
        )
        base = z0 + 0.55

        # body: a chamfered block, wider at the haunches
        body_len = length * 0.68
        body_h = height * 0.42
        body = chamfered_loop(cx + length * 0.08, cy, body_len, breadth * 0.92, breadth * 0.22)
        top_body = chamfered_loop(cx + length * 0.08, cy, body_len * 0.82, breadth * 0.78, breadth * 0.2)
        mb.add_frustum(body, top_body, self.m(base), self.m(base + body_h))

        # chest and head, facing west (towards the sanctum)
        head_x = cx - length * 0.34
        mb.add_box(
            self.m(head_x - breadth * 0.34), self.m(cy - breadth * 0.30),
            self.m(head_x + breadth * 0.30), self.m(cy + breadth * 0.30),
            self.m(base + body_h * 0.55), self.m(base + body_h * 1.35),
        )
        # muzzle
        mb.add_box(
            self.m(head_x - breadth * 0.52), self.m(cy - breadth * 0.20),
            self.m(head_x - breadth * 0.26), self.m(cy + breadth * 0.20),
            self.m(base + body_h * 0.62), self.m(base + body_h * 1.02),
        )
        # horns
        for sign in (-1, 1):
            horn = [
                (0.0, 0.0),
                (0.16, 0.10),
                (0.22, 0.30),
                (0.12, 0.46),
                (0.0, 0.52),
            ]
            profile = [(self.m(r), self.m(base + body_h * 1.30 + h)) for r, h in horn]
            mb.add_lathe(profile, (self.m(head_x + breadth * 0.10), self.m(cy + sign * breadth * 0.26)), segments=8)
        # forelegs
        for sign in (-1, 1):
            mb.add_box(
                self.m(cx - length * 0.22), self.m(cy + sign * breadth * 0.28 - breadth * 0.13),
                self.m(cx - length * 0.10), self.m(cy + sign * breadth * 0.28 + breadth * 0.13),
                self.m(base), self.m(base + body_h * 0.6),
            )
        # hind legs
        for sign in (-1, 1):
            mb.add_box(
                self.m(cx + length * 0.24), self.m(cy + sign * breadth * 0.30 - breadth * 0.16),
                self.m(cx + length * 0.36), self.m(cy + sign * breadth * 0.30 + breadth * 0.16),
                self.m(base), self.m(base + body_h * 0.75),
            )
        return mb

    # ================================================================== #
    # 07 - gopurams
    # ================================================================== #
    def build_gopuram(self, inner: bool = True) -> MeshBuilder:
        """A stepped Dravidian gateway tower with a barrel-vaulted passage."""
        mb = MeshBuilder()
        p = self.p
        if inner:
            depth = p.inner_gopuram_x
            width = p.inner_gopuram_y
            height = p.inner_gopuram_height
            storeys = p.inner_gopuram_storeys
            cx = p.inner_gopuram_centre_x
        else:
            depth = p.outer_gopuram_x
            width = p.outer_gopuram_y
            height = p.outer_gopuram_height
            storeys = 3
            cx = p.outer_gopuram_centre_x

        z0 = 0.4
        passage_w = 4.0
        passage_h = 4.6
        wall = (width - passage_w) / 2

        # base block: two piers plus the vault over the passage
        for sign in (-1, 1):
            mb.add_box(
                self.m(cx - depth / 2),
                self.m(sign * passage_w / 2),
                self.m(cx + depth / 2),
                self.m(sign * width / 2),
                self.m(z0),
                self.m(z0 + height * 0.30),
            )
        self._add_barrel_vault(mb, cx, passage_w, z0, z0 + passage_h, depth)

        # stepped storeys above the base block
        base_z = z0 + height * 0.30
        remaining = height - (base_z - z0)
        storey_h = remaining / storeys
        for index in range(storeys):
            t0 = index / storeys
            t1 = (index + 1) / storeys
            w = width * (1.0 - 0.28 * t0)
            d = depth * (1.0 - 0.24 * t0)
            z_start = base_z + storey_h * index
            z_end = base_z + storey_h * (index + 1)
            # each storey is a near vertical block; the setback happens at the
            # cornice, which is what gives a Dravidian gopuram its stepped
            # silhouette
            mb.add_tapered_box(
                (cx, 0.0), (w, d), (w, d), self.m(z_start), self.m(z_end)
            )
            proj = self.amp_m(0.55, 1.0)
            mb.add_box(
                self.m(cx - d / 2 - proj), self.m(-w / 2 - proj),
                self.m(cx + d / 2 + proj), self.m(w / 2 + proj),
                self.m(z_end - 0.9), self.m(z_end),
            )
            # parapet kutas along the two long faces
            if self.options.ornament >= ORNAMENT_SIMPLIFIED:
                kuta_h = self.amp_m(0.6, 0.8)
                kuta_w = self.amp_m(0.6, 0.8)
                count = max(3, int(w / 2.2))
                for k in range(count):
                    offset = -w / 2 + w * (k + 0.5) / count
                    for sign in (-1, 1):
                        mb.add_box(
                            self.m(cx + sign * (d / 2 + proj * 0.2) - kuta_w / 2),
                            self.m(offset - kuta_w / 2),
                            self.m(cx + sign * (d / 2 + proj * 0.2) + kuta_w / 2),
                            self.m(offset + kuta_w / 2),
                            self.m(z_end), self.m(z_end + kuta_h),
                        )

        # crowning shikhara of the gopuram
        top = base_z + remaining
        radius = width * 0.24
        shikhara = [
            (radius, 0.0),
            (radius * 0.85, 0.35),
            (radius * 0.60, 0.65),
            (radius * 0.30, 0.85),
            (0.0, 1.0),
        ]
        profile = [(self.m(r), self.m(top + h * 1.2)) for r, h in shikhara]
        mb.add_lathe(profile, (self.m(cx), 0.0), segments=12, cap_bottom=False, cap_top=False)
        return mb

    def _add_barrel_vault(
        self,
        mb: MeshBuilder,
        cx: float,
        passage_w: float,
        z0: float,
        z1: float,
        depth: float,
    ) -> None:
        """A barrel-vaulted passage built as an extruded arch ring."""
        radius = passage_w / 2
        steps = 12
        outer_r = radius + 0.8
        polygon: list[tuple[float, float]] = []
        for index in range(steps + 1):
            angle = math.pi * index / steps
            polygon.append((cx - radius + outer_r * math.cos(angle), z0 + radius + outer_r * math.sin(angle)))
        for index in range(steps, -1, -1):
            angle = math.pi * index / steps
            polygon.append((cx - radius + radius * math.cos(angle), z0 + radius + radius * math.sin(angle)))
        # the polygon is in the XZ plane; extrude it along Y
        half = depth / 2
        y0 = -half
        y1 = half
        lower = mb.add_verts([(x, y0, z) for x, z in polygon])
        upper = mb.add_verts([(x, y1, z) for x, z in polygon])
        count = len(polygon)
        for index in range(count):
            nxt = (index + 1) % count
            mb.add_face([lower[index], lower[nxt], upper[nxt], upper[index]])
        mb.add_face(list(reversed(lower)))
        mb.add_face(list(upper))
        # spandrel walls above the vault, up to the top of the base block
        del z1

    # ================================================================== #
    # 08 - compound wall and prakara corridors
    # ================================================================== #
    def build_outer_wall(self) -> MeshBuilder:
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        t = p.outer_wall_thickness
        h = p.outer_wall_height
        gate_w = 6.0
        gate_h = 7.0
        gate_x = p.outer_gopuram_centre_x

        x0, x1 = plan["complex_x0"], plan["complex_x1"]
        y0, y1 = plan["complex_y0"], plan["complex_y1"]

        # south and north walls (running along X)
        for y in (y0 + t / 2, y1 - t / 2):
            self.wall(mb, "x", x0, x1, t, 0.0, h, offset=y)
        # west wall
        self.wall(mb, "y", y0, y1, t, 0.0, h, offset=x0 + t / 2)
        # east wall with the main gateway opening
        self.wall(
            mb, "y", y0, y1, t, 0.0, h,
            openings=[(-gate_w / 2, gate_w / 2, 0.0, gate_h)],
            offset=x1 - t / 2,
        )
        del gate_x
        return mb

    def build_prakara(self) -> MeshBuilder:
        """The pillared covered veranda that frames the courtyard."""
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        h = p.prakara_wall_height
        wall_t = p.outer_wall_thickness
        x0, x1 = p.prakara_x_min, p.prakara_x_max
        y0, y1 = p.prakara_y_min, p.prakara_y_max
        roof_t = p.prakara_roof_thickness
        pillar_r = p.pillar_radius * 0.9

        # corridors: north, south, east and west arms
        arms = [
            ("x", x0, x1, y0 + 1.5),
            ("x", x0, x1, y1 - 1.5),
            ("y", y0 + 1.5, y1 - 1.5, x0 + 1.5),
            ("y", y0 + 1.5, y1 - 1.5, x1 - 1.5),
        ]
        for axis, start, end, fixed in arms:
            self._add_corridor(mb, axis, start, end, fixed, h, wall_t, roof_t, pillar_r)
        del plan
        return mb

    def _add_corridor(
        self,
        mb: MeshBuilder,
        axis: str,
        start: float,
        end: float,
        fixed: float,
        height: float,
        wall_t: float,
        roof_t: float,
        pillar_r: float,
    ) -> None:
        """One arm of the pillared veranda: back wall, columns and roof."""
        p = self.p
        spacing = p.prakara_pillar_spacing
        count = max(2, int(round((end - start) / spacing)))
        pitch = (end - start) / (count - 1) if count > 1 else 0.0

        # back wall
        if axis == "x":
            mb.add_box(
                self.m(start), self.m(fixed - wall_t / 2), self.m(end), self.m(fixed + wall_t / 2),
                self.m(0.0), self.m(height),
            )
            roof_x0, roof_x1 = start, end
            roof_y0, roof_y1 = fixed - 1.2, fixed + 2.0
        else:
            mb.add_box(
                self.m(fixed - wall_t / 2), self.m(start), self.m(fixed + wall_t / 2), self.m(end),
                self.m(0.0), self.m(height),
            )
            roof_x0, roof_x1 = fixed - 1.2, fixed + 2.0
            roof_y0, roof_y1 = start, end

        # columns
        for index in range(count):
            pos = start + pitch * index
            if axis == "x":
                cx, cy = pos, fixed + 1.4
            else:
                cx, cy = fixed + 1.4, pos
            mb.add_box(
                self.m(cx - pillar_r), self.m(cy - pillar_r), self.m(cx + pillar_r), self.m(cy + pillar_r),
                self.m(0.0), self.m(height * 0.78),
            )
            # capital
            mb.add_box(
                self.m(cx - pillar_r * 1.4), self.m(cy - pillar_r * 1.4),
                self.m(cx + pillar_r * 1.4), self.m(cy + pillar_r * 1.4),
                self.m(height * 0.78), self.m(height * 0.88),
            )

        # entablature and roof
        mb.add_box(
            self.m(roof_x0), self.m(roof_y0), self.m(roof_x1), self.m(roof_y1),
            self.m(height * 0.88), self.m(height),
        )
        mb.add_box(
            self.m(roof_x0 - 0.3), self.m(roof_y0 - 0.3), self.m(roof_x1 + 0.3), self.m(roof_y1 + 0.3),
            self.m(height), self.m(height + roof_t),
        )

    # ================================================================== #
    # 09 - subsidiary shrines and stairs
    # ================================================================== #
    def build_sub_shrine(self, centre: tuple[float, float], size: tuple[float, float], height: float) -> MeshBuilder:
        """A small subsidiary shrine with a domed shikhara."""
        mb = MeshBuilder()
        cx, cy = centre
        w, d = size
        z0 = 0.4
        mb.add_box(
            self.m(cx - w / 2 - 0.4), self.m(cy - d / 2 - 0.4), self.m(cx + w / 2 + 0.4), self.m(cy + d / 2 + 0.4),
            self.m(z0), self.m(z0 + 0.8),
        )
        mb.add_box(
            self.m(cx - w / 2), self.m(cy - d / 2), self.m(cx + w / 2), self.m(cy + d / 2),
            self.m(z0 + 0.8), self.m(z0 + height * 0.6),
        )
        # cornice
        mb.add_box(
            self.m(cx - w / 2 - 0.5), self.m(cy - d / 2 - 0.5), self.m(cx + w / 2 + 0.5), self.m(cy + d / 2 + 0.5),
            self.m(z0 + height * 0.6), self.m(z0 + height * 0.68),
        )
        # shikhara
        radius = w * 0.42
        shikhara = [
            (radius, 0.0),
            (radius * 0.90, 0.30),
            (radius * 0.70, 0.62),
            (radius * 0.42, 0.85),
            (0.0, 1.0),
        ]
        profile = [(self.m(r), self.m(z0 + height * 0.68 + h * height * 0.32)) for r, h in shikhara]
        mb.add_lathe(profile, (self.m(cx), self.m(cy)), segments=12, cap_bottom=False, cap_top=False)
        return mb

    def build_stairs(self) -> MeshBuilder:
        """The flight of steps up to the temple platform on the main axis."""
        mb = MeshBuilder()
        p = self.p
        plan = self.plan
        z_top = p.platform_height
        steps = int(round(z_top / p.stair_riser))
        riser = z_top / steps
        width = p.stair_width
        # flight in front of the nandi mandapa
        x_start = plan["nandi_x1"] + 0.2
        mb.add_stairs(
            self.m(x_start), 1, self.m(width), 0.0, 0.0, self.m(z_top), self.m(riser), self.m(p.stair_tread)
        )
        return mb
