"""Unit tests for the mesh construction helpers and the temple builder.

These run in plain CPython: :mod:`temple_geom` has no Blender dependency and
:mod:`temple_build` only uses it, so the whole model can be built and
inspected without a Blender installation.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "scripts"))

from temple_build import BuildOptions, TempleBuilder  # noqa: E402
from temple_geom import MeshBuilder, chamfered_loop, rectangular_loop  # noqa: E402
from temple_params import PARAMS  # noqa: E402


def bounds(builder: MeshBuilder):
    xs = [v[0] for v in builder.verts]
    ys = [v[1] for v in builder.verts]
    zs = [v[2] for v in builder.verts]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


class TestMeshBuilder(unittest.TestCase):
    def test_box_has_six_quad_faces(self):
        builder = MeshBuilder()
        builder.add_box(0, 0, 10, 20, 0, 5)
        self.assertEqual(len(builder.faces), 6)
        self.assertEqual(len(builder.verts), 8)
        for face in builder.faces:
            self.assertEqual(len(face), 4)

    def test_prism_extrudes_a_polygon(self):
        builder = MeshBuilder()
        builder.add_prism(rectangular_loop(0, 0, 4, 6), 0, 2)
        self.assertEqual(len(builder.faces), 6)  # 4 sides + 2 caps
        (x0, y0, z0), (x1, y1, z1) = bounds(builder)
        self.assertEqual((x0, y0, z0), (-2.0, -3.0, 0.0))
        self.assertEqual((x1, y1, z1), (2.0, 3.0, 2.0))

    def test_wall_with_opening_creates_several_bands(self):
        builder = MeshBuilder()
        builder.add_wall_with_openings("x", 0, 10, 0.4, 0, 4, openings=[(4, 6, 0, 2.4)])
        # two full-height piers plus the lintel above the opening
        self.assertEqual(len(builder.faces), 3 * 6)

    def test_lathe_creates_a_closed_solid(self):
        builder = MeshBuilder()
        builder.add_lathe([(2.0, 0.0), (2.0, 3.0), (0.0, 4.0)], (0, 0), segments=8)
        self.assertGreater(len(builder.faces), 8)
        self.assertGreater(len(builder.verts), 8)

    def test_chamfered_loop_has_eight_vertices(self):
        self.assertEqual(len(chamfered_loop(0, 0, 10, 10, 1.5)), 8)


class TestTempleBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = TempleBuilder(BuildOptions(scale=1.0))

    def test_vimana_reaches_the_expected_height(self):
        mb = self.builder.build_vimana()
        (_, _, z0), (_, _, z1) = bounds(mb)
        self.assertAlmostEqual(z0, PARAMS.platform_height + PARAMS.sanctum_height, places=3)
        self.assertAlmostEqual(z1, 65.83, places=1)

    def test_vimana_base_is_square_and_correctly_sized(self):
        mb = self.builder.build_vimana()
        (x0, y0, _), (x1, y1, _) = bounds(mb)
        # the bounding box includes the projecting base cornice
        cornice = self.builder.amp_m(PARAMS.cornice_projection, 0.9)
        self.assertAlmostEqual(x1 - x0, PARAMS.vimana_base_side + 2 * cornice, places=2)
        self.assertAlmostEqual(y1 - y0, PARAMS.vimana_base_side + 2 * cornice, places=2)
        self.assertAlmostEqual(x0, -PARAMS.vimana_base_side / 2 - cornice, places=3)

    def test_ground_plate_is_flat_and_below_the_datum(self):
        mb = self.builder.build_ground()
        (_, _, z0), (_, _, z1) = bounds(mb)
        self.assertLess(z0, 0.0)
        self.assertGreater(z1, 0.0)

    def test_ground_half_plates_meet_on_a_common_joint(self):
        west = self.builder.build_ground(half="west")
        east = self.builder.build_ground(half="east")
        (_, _, _), (wx1, _, _) = bounds(west)
        (ex0, _, _), (_, _, _) = bounds(east)
        self.assertAlmostEqual(wx1, ex0, places=6)
        # the joint lies east of the temple block, in the open courtyard
        self.assertGreater(wx1, 0.0)
        self.assertLess(wx1, PARAMS.complex_length_x)

    def test_sanctum_encloses_a_square_cella(self):
        mb = self.builder.build_sanctum()
        (x0, y0, _), (x1, y1, _) = bounds(mb)
        self.assertAlmostEqual(x1 - x0, PARAMS.sanctum_outer_side, places=2)
        self.assertAlmostEqual(y1 - y0, PARAMS.sanctum_outer_side, places=2)

    def test_halls_are_connected_along_the_axis(self):
        plan_positions = __import__("temple_params").plan_positions(PARAMS)
        self.assertAlmostEqual(plan_positions["maha_x0"], plan_positions["antrala_x1"], places=6)
        self.assertAlmostEqual(plan_positions["mukha_x0"], plan_positions["maha_x1"], places=6)
        self.assertLess(plan_positions["mukha_x1"], plan_positions["nandi_x0"])

    def test_nandi_faces_the_sanctum(self):
        # the bull's head points to the west, towards the sanctum
        mb = self.builder.build_nandi()
        (x0, _, _), (x1, _, _) = bounds(mb)
        self.assertLess(x0, PARAMS.nandi_centre_x)
        self.assertGreater(x1, PARAMS.nandi_centre_x)

    def test_gopuram_is_lower_than_the_vimana(self):
        mb = self.builder.build_gopuram(inner=True)
        (_, _, _), (_, _, z1) = bounds(mb)
        self.assertLess(z1, PARAMS.vimana_total_height + PARAMS.platform_height)

    def test_every_component_produces_geometry(self):
        for name in ("build_ground", "build_plinth", "build_sanctum", "build_antrala",
                     "build_maha_mandapa", "build_mukha_mandapa", "build_nandi_mandapa",
                     "build_nandi", "build_vimana", "build_gopuram", "build_outer_wall",
                     "build_prakara", "build_stairs"):
            mb = getattr(self.builder, name)()
            self.assertGreater(len(mb.faces), 0, f"{name} produced no faces")


if __name__ == "__main__":
    unittest.main()
