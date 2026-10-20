"""Parametric definition of the Brihadisvara Temple model.

All *architectural* dimensions in this module are expressed in **real-world
metres** taken from the published record (see
``src/documentation/model_dimensions.md`` for the citation of every value).
The model scale is applied at build time through :data:`Scale`, so the same
numbers drive the 1:1000 master model and the 1:320 detail model.

Coordinate convention (identical in Blender, FreeCAD, STL and STEP):

* ``X`` -> east / west, the **long** axis of the complex (240.79 m real).
* ``Y`` -> north / south, the **short** axis of the complex (121.92 m real).
* ``Z`` -> up, ``Z = 0`` at the underside of the main base (the printing bed
  contact surface).
* Origin ``(0, 0, 0)`` is the centre of the sanctum (garbhagriha), which is
  also the centre of the vimana and the centre of the main east-west axis.

The prompt's shorthand "X = temple width, Y = temple length" is honoured for
the *core building* (its north-south width lies along Y, its east-west length
along X); because the whole complex is wider east-west than north-south, the
complex's long dimension necessarily runs along X.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Model scale
# --------------------------------------------------------------------------- #
#: Master scale of the complete complex: 1 mm of model = 1 m of building
#: (scale 1:1000).  Model millimetres = real metres * SCALE_MM_PER_M.
MASTER_SCALE = 1.0

#: Detail scale of the cut-away core model (1:320).
CUTAWAY_SCALE = 1000.0 / 320.0  # = 3.125 mm of model per metre of building

#: Model millimetres per real metre.
SCALE_MM_PER_M = MASTER_SCALE

#: Minimum printable thickness of a modelled detail at the master scale.
#: Features that would fall below this are amplified (documented as
#: "detail amplification") instead of being dropped.
MIN_PRINTABLE_DETAIL_MM = 1.0

#: Nominal FDM nozzle used for the printability rules.
NOZZLE_DIAMETER_MM = 0.4


# --------------------------------------------------------------------------- #
# Real-world dimensions (metres)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TempleParameters:
    """Real-world dimensions of the temple complex, in metres."""

    # -- compound -------------------------------------------------------- #
    complex_length_x: float = 240.79      # east-west, Wikipedia/Balasubrahmanyam
    complex_width_y: float = 121.92        # north-south
    complex_west_offset: float = 45.0     # sanctum centre -> west compound wall

    # -- main plinth / platform ----------------------------------------- #
    platform_step_heights: tuple = (0.80, 0.60, 0.50)   # three courses
    platform_step_offsets: tuple = (1.30, 1.10, 0.90)   # plan inset per course
    platform_height: float = 1.90         # top of the temple platform above z=0

    # -- sanctum (garbhagriha) ------------------------------------------ #
    sanctum_width: float = 6.40           # square cella
    sanctum_wall_thickness: float = 1.40
    sanctum_height: float = 12.50         # cella wall height above platform
    linga_height: float = 8.70            # monolithic linga (two storeys)

    # -- ambulatory passage (pradakshina patha) ------------------------- #
    ambulatory_width: float = 1.80        # passage width around the cella
    ambulatory_wall_thickness: float = 1.00

    # -- antrala (vestibule between cella and maha-mandapa) -------------- #
    antrala_depth: float = 2.60
    antrala_width: float = 5.00

    # -- halls (maha-mandapa, mukha-mandapa) ---------------------------- #
    maha_mandapa_x: float = 17.80
    maha_mandapa_y: float = 15.00
    maha_mandapa_pillars_per_side: int = 6
    maha_mandapa_wall_height: float = 8.60

    mukha_mandapa_x: float = 11.10
    mukha_mandapa_y: float = 11.20
    mukha_mandapa_pillars_per_side: int = 4
    mukha_mandapa_wall_height: float = 8.00

    nandi_mandapa_x: float = 12.00
    nandi_mandapa_y: float = 11.00
    nandi_mandapa_wall_height: float = 7.60

    # -- vimana (tower over the sanctum) -------------------------------- #
    vimana_base_side: float = 30.18       # square base of the superstructure
    vimana_storey_count: int = 13         # tapering square storeys
    vimana_lower_height: float = 5.50     # aditala block below the storeys
    vimana_storey_height: float = 2.87    # mean height of one tapering storey
    vimana_top_side: float = 9.00         # plan of the highest tapering storey
    vimana_cornice_height: float = 0.55
    vimana_cornice_projection: float = 0.45
    vimana_griva_height: float = 2.80     # top granite block (7.77 m side)
    vimana_griva_side: float = 7.77
    vimana_sikhara_height: float = 2.00   # ribbed cupola above the griva
    vimana_finial_height: float = 3.83    # stupi (stupi height 3.81 m cited)

    # -- gopurams -------------------------------------------------------- #
    inner_gopuram_x: float = 6.00         # depth along the axis
    inner_gopuram_y: float = 11.00        # width across the axis
    inner_gopuram_height: float = 30.00   # 30 m high, less than half the vimana
    inner_gopuram_storeys: int = 5
    inner_gopuram_centre_x: float = 100.0

    outer_gopuram_x: float = 6.00
    outer_gopuram_y: float = 12.00
    outer_gopuram_height: float = 12.00
    outer_gopuram_centre_x: float = 177.0

    # -- enclosure walls and prakara ------------------------------------ #
    outer_wall_thickness: float = 1.20
    outer_wall_height: float = 3.50
    prakara_wall_height: float = 4.20
    prakara_roof_thickness: float = 0.60
    prakara_pillar_width: float = 0.60
    prakara_pillar_spacing: float = 3.00
    prakara_x_min: float = -33.0
    prakara_x_max: float = 140.0
    prakara_y_min: float = -40.0
    prakara_y_max: float = 40.0

    # -- nandi ----------------------------------------------------------- #
    nandi_length: float = 5.94
    nandi_breadth: float = 2.59
    nandi_height: float = 3.65
    nandi_centre_x: float = 51.50
    nandi_centre_y: float = 0.0

    # -- sub-shrines in the courtyard (16th-17th c. Nayaka additions) ---- #
    amman_shrine_centre: tuple = (72.0, -14.0)
    amman_shrine_size: tuple = (7.0, 7.0)
    amman_shrine_height: float = 9.0
    murugan_shrine_centre: tuple = (72.0, 14.0)
    murugan_shrine_size: tuple = (6.0, 6.0)
    murugan_shrine_height: float = 8.0

    # -- stairs ---------------------------------------------------------- #
    stair_width: float = 6.00
    stair_riser: float = 0.19
    stair_tread: float = 0.32

    # -- mouldings ------------------------------------------------------- #
    cornice_height: float = 0.60
    cornice_projection: float = 0.35
    base_moulding_height: float = 0.55
    base_moulding_projection: float = 0.40
    pillar_base_height: float = 0.70
    pillar_base_projection: float = 0.22
    pillar_shaft_height: float = 4.60
    pillar_capital_height: float = 0.65
    pillar_capital_projection: float = 0.30
    pillar_radius: float = 0.34

    def __post_init__(self) -> None:  # pragma: no cover - sanity only
        assert self.vimana_storey_count > 0
        assert self.complex_length_x > self.complex_width_y

    # -- derived --------------------------------------------------------- #
    @property
    def vimana_total_height(self) -> float:
        """Height of the vimana above the temple platform (finial tip).

        This includes the height of the sanctuary block that carries the
        aditala, so that ``platform_height + vimana_total_height`` equals the
        published elevation of the temple (65.83 m).
        """
        return (
            self.sanctum_height
            + self.vimana_lower_height
            + self.vimana_storey_count * self.vimana_storey_height
            + self.vimana_griva_height
            + self.vimana_sikhara_height
            + self.vimana_finial_height
        )

    @property
    def sanctum_outer_side(self) -> float:
        """Outer face of the ambulatory wall around the cella."""
        return self.sanctum_width + 2 * (self.ambulatory_width + self.ambulatory_wall_thickness)

    @property
    def vimana_base_z(self) -> float:
        return self.platform_height


PARAMS = TempleParameters()


# --------------------------------------------------------------------------- #
# Derived plan positions (real metres, X east, Y north)
# --------------------------------------------------------------------------- #
def plan_positions(p: TempleParameters = PARAMS) -> dict:
    """Return the axial plan positions of the principal volumes."""
    half = p.vimana_base_side / 2.0
    sanctum_outer = p.sanctum_outer_side / 2.0

    antrala_x0 = sanctum_outer
    antrala_x1 = antrala_x0 + p.antrala_depth

    maha_x0 = antrala_x1
    maha_x1 = maha_x0 + p.maha_mandapa_x

    mukha_x0 = maha_x1
    mukha_x1 = mukha_x0 + p.mukha_mandapa_x

    nandi_x0 = mukha_x1 + 3.50
    nandi_x1 = nandi_x0 + p.nandi_mandapa_x

    return {
        "vimana_x0": -half,
        "vimana_x1": half,
        "sanctum_x0": -p.sanctum_width / 2,
        "sanctum_x1": p.sanctum_width / 2,
        "ambulatory_x0": -sanctum_outer,
        "ambulatory_x1": sanctum_outer,
        "antrala_x0": antrala_x0,
        "antrala_x1": antrala_x1,
        "maha_x0": maha_x0,
        "maha_x1": maha_x1,
        "mukha_x0": mukha_x0,
        "mukha_x1": mukha_x1,
        "nandi_x0": nandi_x0,
        "nandi_x1": nandi_x1,
        "inner_gopuram_x0": p.inner_gopuram_centre_x - p.inner_gopuram_x / 2,
        "inner_gopuram_x1": p.inner_gopuram_centre_x + p.inner_gopuram_x / 2,
        "outer_gopuram_x0": p.outer_gopuram_centre_x - p.outer_gopuram_x / 2,
        "outer_gopuram_x1": p.outer_gopuram_centre_x + p.outer_gopuram_x / 2,
        "complex_x0": -p.complex_west_offset,
        "complex_x1": -p.complex_west_offset + p.complex_length_x,
        "complex_y0": -p.complex_width_y / 2,
        "complex_y1": p.complex_width_y / 2,
    }


# --------------------------------------------------------------------------- #
# Print profile (assumptions, see src/documentation/print_settings.md)
# --------------------------------------------------------------------------- #
@dataclass
class PrintProfile:
    """Generic FDM assumptions; no specific printer is claimed."""

    name: str = "generic-fdm-040"
    build_volume_mm: tuple = (250.0, 250.0, 250.0)
    nozzle_diameter_mm: float = 0.4
    layer_height_mm: float = 0.20
    material: str = "PLA / PETG"
    min_wall_mm: float = 2.4
    min_detail_mm: float = 1.2
    joint_clearance_mm: float = 0.30
    support_strategy: str = "tree supports for the gopuram and nandi only"

    def fits(self, size_mm: tuple) -> bool:
        return all(a <= b for a, b in zip(size_mm, self.build_volume_mm))


PRINT_PROFILE = PrintProfile()
