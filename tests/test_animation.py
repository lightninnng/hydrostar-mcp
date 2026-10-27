import cmath
import math

import pytest

from hydrostar_mcp import core
from hydrostar_mcp.animation import (
    harmonic,
    wave_number,
    rigid_displacement,
    field_grid,
    inside_or_near,
)
from pathlib import Path


def test_native_phase_is_a_lead_and_reconstruction_is_periodic():
    value = cmath.rect(2, math.pi / 2)
    assert harmonic(value, 1, 0, amplitude=0.5) == pytest.approx(0, abs=1e-12)
    assert harmonic(value, 1, math.pi / 2, amplitude=0.5) == pytest.approx(-1)
    assert harmonic(value, 1, 2 * math.pi, amplitude=0.5) == pytest.approx(
        harmonic(value, 1, 0, amplitude=0.5)
    )


def test_finite_depth_dispersion_is_satisfied():
    k = wave_number(0.5, 80)
    assert 9.81 * k * math.tanh(k * 80) == pytest.approx(0.5**2, rel=1e-12)


def test_small_angle_rigid_motion_rotates_about_cog():
    displacement = rigid_displacement([[11, 0, -1]], [0, 0, 0.2, 0, 1, 0], [1, 0, -1])
    assert displacement[0, 2] == pytest.approx(0.2 - math.radians(1) * 10)
    assert displacement[0, 0] == pytest.approx(0)


def test_generated_field_grid_excludes_four_column_waterlines():
    path = (
        Path(__file__).resolve().parent.parent
        / "examples/results/semisub_oc4_style/inputs/oc4_style.hst"
    )
    grid = field_grid(path, size=21)
    assert len(grid["waterlines"]) == 4
    assert all(
        not any(
            inside_or_near((x, y), p, grid["clearance_m"]) for p in grid["waterlines"]
        )
        for _, x, y, _ in grid["points"]
    )


def test_native_error_marker_fails_even_when_exit_code_is_zero():
    assert (
        core.log_error("[ERROR] Index -1 does not exist, check HSprs") == "INPUT_ERROR"
    )


def test_strict_text_parser_rejects_incomplete_archived_record():
    with pytest.raises(ValueError):
        core.read_rao_text("#UNIT : m/m\n#HEADING 60\n0.5 1 0\n", "archived-native.rao")
