"""Physical pressure definitions and the full published native pressure archive."""

import cmath
import math
from pathlib import Path
import pytest
from hydrostar_mcp.pressure import (
    wet_panel_samples,
    pressure_points,
    verify_pressure_physics,
)
from hydrostar_mcp.animation import wave_number

ROOT = Path(__file__).resolve().parent.parent


def synthetic_pressure():
    omega = 0.5
    depth = 80.0
    k = wave_number(omega, depth, 10.0)
    points = [[1, 0.0, 0.0, -1.0], [2, 0.02, 0.0, -1.0]]
    incident = []
    for _, x, y, z in points:
        h = math.cosh(k * (z + depth)) / math.cosh(k * depth) * cmath.exp(-1j * k * x)
        incident.append([h.real, h.imag])
    return dict(
        mesh=dict(faces=[[0, 1, 2]]),
        points=points,
        following_head=[[0.8, 0], [0.8001, 0]],
        eulerian_head=[[1.0, 0]],
        incident_head=incident,
        motion_complex=[
            [0.0, 0.0],
            [0.0, 0.0],
            [0.2, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ],
        cog_m=[0.0, 0.0, -1.0],
        omega_rad_s=omega,
        heading_deg=0.0,
        depth_m=depth,
        gravity_m_s2=10.0,
        wave_reference_xy_m=[0.0, 0.0],
        rho_kg_m3=1000.0,
        wave_amplitude_m=0.5,
        outward_offset_m=0.02,
    )


def test_body_following_pressure_and_kpa_conversion():
    result = verify_pressure_physics(synthetic_pressure())
    assert result["hydrostatic_motion_complex_max_error"] == pytest.approx(0, abs=1e-12)
    assert result["pressure_colour_limit_kpa"] == pytest.approx(4.0)


def test_wrong_hydrostatic_sign_is_rejected():
    data = synthetic_pressure()
    data["following_head"][0] = [1.2, 0.0]
    with pytest.raises(ValueError, match="correction"):
        verify_pressure_physics(data)


def test_bad_incident_pressure_phase_is_rejected():
    data = synthetic_pressure()
    data["incident_head"][1][1] *= -1
    with pytest.raises(ValueError, match="analytical"):
        verify_pressure_physics(data)


def test_surface_sampling_instability_is_rejected():
    data = synthetic_pressure()
    data["following_head"][1] = [2.0, 0.0]
    with pytest.raises(ValueError, match="sensitivity"):
        verify_pressure_physics(data)


def test_pressure_points_follow_full_wet_mesh_outward_normals():
    mesh = wet_panel_samples(
        ROOT / "examples/pressures/semisub_oc4_style/inputs/semisub_pressure.hst"
    )
    points = pressure_points(mesh)
    assert len(mesh["faces"]) == 1656
    assert len(points) == 3312
    for center, normal, point in zip(mesh["centers"], mesh["normals"], points[1656:]):
        assert sum(v * v for v in normal) == pytest.approx(1)
        assert point[1:] == pytest.approx(
            [c + 0.02 * n for c, n in zip(center, normal)]
        )


def test_all_native_pressure_records_and_synchronized_media():
    from scripts.check_pressures import check_pressures

    result = check_pressures()
    assert result["native_pressure_cases"] == 3
    assert result["wetted_pressure_panels"] == 4430
    assert result["native_pressure_records"] == 22150


def test_readme_language_switch_is_bidirectional():
    chinese = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README.en.md").read_text(encoding="utf-8")
    assert "(README.en.md)" in chinese
    assert "(README.md)" in english
    assert "## Synchronized surface pressure, waves and motion" in english
