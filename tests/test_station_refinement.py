"""Local station refinement preserves source rings and enforces its panel cap."""

import math
from types import SimpleNamespace

import pytest

from hydrostar_mcp.geometry_sources import GeometryRequest
from hydrostar_mcp.structured_panels import _adaptive_station_rings


def curved_section(x):
    np = pytest.importorskip("numpy")
    theta = np.linspace(0, math.pi, 9)
    return np.column_stack(
        [np.full(9, x), (1 + 0.01 * x) * np.cos(theta), -(1 + 0.01 * x) * np.sin(theta)]
    )


def refinement_request(max_panels=3000):
    return SimpleNamespace(
        max_panels=max_panels,
        panel_quality=GeometryRequest(
            project="station_test",
            path="own.csv",
            units="m",
            source_note="Analytic regression",
        ).panel_quality,
    )


def test_refinement_controls_long_edges_without_moving_existing_sections():
    np = pytest.importorskip("numpy")
    original = [0.0, 5.0, 10.0]
    stations, rings, report = _adaptive_station_rings(
        original, curved_section, 8, 4, refinement_request()
    )
    assert set(original).issubset(stations)
    assert len(stations) > len(original)
    assert report["maximum_band_warpage_deg"] <= 0.95 * 5
    for x in original:
        np.testing.assert_array_equal(rings[stations.index(x)], curved_section(x))
    # Independently evaluate the actual accepted quadrilaterals.
    for left, right in zip(rings, rings[1:]):
        for i in range(8):
            p = np.array([left[i], right[i], right[i + 1], left[i + 1]])
            a = np.cross(p[1] - p[0], p[2] - p[0])
            b = np.cross(p[2] - p[0], p[3] - p[0])
            cosine = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            assert math.degrees(math.acos(np.clip(cosine, -1, 1))) <= 4.75
            edges = np.linalg.norm(p - np.roll(p, 1, axis=0), axis=1)
            assert max(edges) / min(edges) <= 8


def test_refinement_stops_at_explicit_wet_panel_budget():
    with pytest.raises(ValueError, match="预算"):
        _adaptive_station_rings(
            [0, 5, 10], curved_section, 8, 4, refinement_request(20)
        )


def test_initial_station_mesh_must_fit_budget_before_sampling():
    def unexpected_sample(_):
        raise AssertionError("Initial count should be checked before CAD sampling")

    with pytest.raises(ValueError, match="初始站位"):
        _adaptive_station_rings(
            [0, 1, 2], unexpected_sample, 8, 4, refinement_request(19)
        )
