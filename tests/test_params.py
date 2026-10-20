"""Unit tests for the Brihadisvara Temple parameter set.

Run with::

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "scripts"))

from temple_params import (  # noqa: E402
    CUTAWAY_SCALE,
    MASTER_SCALE,
    PARAMS,
    PRINT_PROFILE,
    plan_positions,
)


class TestParameters(unittest.TestCase):
    def test_vimana_total_height_matches_published_elevation(self):
        # Wikipedia lists the elevation of the temple as 65.83 m; the model is
        # built so that the finial tip reaches that height above the ground.
        self.assertAlmostEqual(PARAMS.vimana_total_height + PARAMS.platform_height, 65.83, places=1)

    def test_vimana_storey_count(self):
        self.assertEqual(PARAMS.vimana_storey_count, 13)

    def test_vimana_base_side(self):
        self.assertAlmostEqual(PARAMS.vimana_base_side, 30.18, places=2)

    def test_gopuram_is_shorter_than_the_vimana(self):
        self.assertLess(PARAMS.inner_gopuram_height, PARAMS.vimana_total_height / 2)

    def test_nandi_dimensions(self):
        self.assertAlmostEqual(PARAMS.nandi_length, 5.94, places=2)
        self.assertAlmostEqual(PARAMS.nandi_height, 3.65, places=2)

    def test_scales(self):
        self.assertAlmostEqual(MASTER_SCALE, 1.0, places=6)          # 1:1000
        self.assertAlmostEqual(CUTAWAY_SCALE, 1000.0 / 320.0, places=6)  # 1:320


class TestPlan(unittest.TestCase):
    def setUp(self):
        self.plan = plan_positions(PARAMS)

    def test_axial_order_west_to_east(self):
        order = [
            "vimana_x0", "ambulatory_x0", "antrala_x0", "maha_x0",
            "mukha_x0", "nandi_x0", "inner_gopuram_x0", "outer_gopuram_x0",
        ]
        values = [self.plan[key] for key in order]
        for previous, following in zip(values, values[1:]):
            self.assertLess(previous, following)

    def test_compound_contains_every_building(self):
        self.assertLess(self.plan["complex_x0"], self.plan["vimana_x0"])
        self.assertGreater(self.plan["complex_x1"], self.plan["outer_gopuram_x1"])
        self.assertLess(self.plan["complex_y0"], -PARAMS.vimana_base_side / 2)
        self.assertGreater(self.plan["complex_y1"], PARAMS.vimana_base_side / 2)

    def test_compound_dimensions(self):
        length = self.plan["complex_x1"] - self.plan["complex_x0"]
        width = self.plan["complex_y1"] - self.plan["complex_y0"]
        self.assertAlmostEqual(length, PARAMS.complex_length_x, places=3)
        self.assertAlmostEqual(width, PARAMS.complex_width_y, places=3)

    def test_nandi_sits_on_the_axis_inside_its_mandapa(self):
        self.assertTrue(self.plan["nandi_x0"] < PARAMS.nandi_centre_x < self.plan["nandi_x1"])
        self.assertAlmostEqual(PARAMS.nandi_centre_y, 0.0, places=6)


class TestPrintProfile(unittest.TestCase):
    def test_master_model_fits_the_assumed_build_volume(self):
        size = (
            PARAMS.complex_length_x * MASTER_SCALE,
            PARAMS.complex_width_y * MASTER_SCALE,
            (PARAMS.vimana_total_height + PARAMS.platform_height) * MASTER_SCALE,
        )
        self.assertTrue(PRINT_PROFILE.fits(size), f"master model {size} does not fit")

    def test_cutaway_fits_the_assumed_build_volume(self):
        plan = plan_positions(PARAMS)
        length = (plan["nandi_x1"] - plan["vimana_x0"]) * CUTAWAY_SCALE
        height = (PARAMS.vimana_total_height + PARAMS.platform_height) * CUTAWAY_SCALE
        self.assertTrue(PRINT_PROFILE.fits((length, 60.0, height)))


if __name__ == "__main__":
    unittest.main()
