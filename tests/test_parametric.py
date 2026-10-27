"""Independent geometry identities, physical mass checks and new workflow paths."""

import copy
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrostar_mcp import core
from hydrostar_mcp.geometry import build, combine_box_masses, mesh_quality
from hydrostar_mcp.models import CaseConfig, CurvedHull, Semisub
from scripts.parametric_study import example, diagonal


@pytest.mark.parametrize("spacing", [2.0, 1.5, 1.0])
def test_semisub_union_exact_quantities_and_single_surface(spacing, tmp_path):
    mesh = build(Semisub(target_panel_m=spacing).model_dump())
    h = mesh.hydrostatics()
    assert h["volume"] == pytest.approx(2656, rel=1e-11)
    assert h["wetted_area"] == pytest.approx(2512, rel=1e-11)
    assert h["cb"] == pytest.approx([0, 0, -27680 / 2656], abs=1e-10)
    assert mesh_quality(mesh)["passed"]
    assert mesh_quality(mesh)["connected_wet_surfaces"] == 1
    assert mesh.provenance["external_mesh_files"] == []
    mesh.write(tmp_path / "own.hst", "own")
    assert core.hydrostatics(tmp_path / "own.hst")["volume"] == pytest.approx(
        h["volume"], rel=1e-10
    )


def test_curved_hull_geometry_symmetry_and_refinement():
    shifts = []
    for nl, ns in [(48, 8), (56, 12), (64, 16)]:
        mesh = build(CurvedHull(n_length=nl, n_section=ns).model_dump())
        h = mesh.hydrostatics()
        assert h["volume"] == pytest.approx(756 * math.pi, rel=1e-10)
        assert h["cb"][0] == pytest.approx(0, abs=1e-10)
        assert h["cb"][2] == pytest.approx(-1.6875, abs=0.001)
        assert max(p[1] for p in mesh.nodes.values()) == pytest.approx(7)
        assert min(p[2] for p in mesh.nodes.values()) == pytest.approx(-4.5)
        assert min(p[0] for p in mesh.nodes.values()) == -36
        assert max(p[0] for p in mesh.nodes.values()) == 36
        assert mesh_quality(mesh)["passed"]
        assert h["max_aspect_ratio"] < 5
        shifts.append(
            mesh.provenance["volume_conserving_discretization"]["maximum_node_shift_m"]
        )
    assert shifts[0] > shifts[1] > shifts[2]
    assert shifts[-1] < 0.01


def test_local_orientation_error_is_caught():
    mesh = build(Semisub().model_dump())
    mesh.panels[10] = tuple(reversed(mesh.panels[10]))
    assert not mesh_quality(mesh)["passed"]
    assert mesh_quality(mesh)["invalid_edges"]


def test_parallel_axis_mass_sum_has_independent_solution():
    components = [
        dict(
            name=str(x),
            mass_fraction=0.5,
            size_m=[2.0, 2.0, 2.0],
            center_m=[x, 0.0, 0.0],
        )
        for x in (-3.0, 3.0)
    ]
    model = combine_box_masses(10.0, components)
    assert model["cog_m"] == [0, 0, 0]
    assert [model["inertia_kg_m2"][i][i] for i in range(3)] == pytest.approx(
        [20 / 3, 290 / 3, 290 / 3]
    )
    core.validate_gyradius(model["gyradius_m"])


def test_damping_passivity_and_native_card(tmp_path):
    matrix = diagonal([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    core.write_mcn(
        tmp_path / "test.mcn",
        gyradius=[1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
        linear_damping_matrix=matrix,
    )
    assert "DAMPING_MATRIX TYPE 0 BODY 1" in (tmp_path / "test.mcn").read_text()
    bad = copy.deepcopy(matrix)
    bad[0][1] = bad[1][0] = 5.0
    with pytest.raises(ValueError, match="半正定"):
        core.validate_passive_matrix(bad)
    bad = copy.deepcopy(matrix)
    bad[1][0] = 1.0
    with pytest.raises(ValueError, match="对称"):
        core.validate_passive_matrix(bad)


@pytest.mark.parametrize("kind", ["semisub", "curved_hull"])
def test_parametric_native_workflow_path(service, solver, kind):
    cfg, _ = example(kind)
    plan = service.plan(cfg)
    assert plan["status"] == "planned"
    assert plan["mechanics"]["initial_stability"]["passed"]
    report = service.prepare(cfg)
    assert report["status"] == "prepared", report.get("error")
    assert solver.calls == ["hslec", "hschk"]
    assert (Path(report["directory"]) / "geometry.json").is_file()
    assert report["geometry_provenance"]["external_mesh_files"] == []
    service.start(report["case_id"])
    service.jobs[report["case_id"]][0].result(timeout=10)
    assert service.status(report["case_id"])["status"] == "completed"


def test_unstable_native_gm_stops_motion(service, solver):
    cfg, _ = example("semisub")
    solver.hsmcn_log = "GMxx, GMyy (-0.3, 2.0)"
    report = service.prepare(cfg)
    service.start(report["case_id"])
    service.jobs[report["case_id"]][0].result(timeout=10)
    final = service.status(report["case_id"])
    assert final["error"]["code"] == "INITIAL_STABILITY_FAILED"
    assert "hsrao" not in solver.calls


def test_invalid_components_and_connectivity_rejected():
    cfg, _ = example("semisub")
    data = cfg.model_dump(mode="json")
    data["mechanics"]["components"][0]["mass_fraction"] += 0.1
    with pytest.raises(ValidationError, match="比例之和"):
        CaseConfig.model_validate(data)
    with pytest.raises(ValidationError):
        Semisub(column_width=8.0)
