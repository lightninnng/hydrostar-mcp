"""Measured budgets include automatic waterplane panels and symmetry."""

from types import SimpleNamespace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from hydrostar_mcp.models import CaseConfig
from scripts import geometry_source_study as study


def test_new_study_folder_retains_published_mass_and_environment(tmp_path, monkeypatch):
    published = (
        Path(__file__).resolve().parent.parent
        / "examples/geometry/cad_spar/config.json"
    )
    config = json.loads(published.read_text(encoding="utf-8"))
    template = tmp_path / "examples/geometry/cad_spar/config.json"
    template.parent.mkdir(parents=True)
    template.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(study, "ROOT", tmp_path)
    folder = tmp_path / "separate-study"
    result = study.native_config("cad_spar", folder)
    assert result.mechanics.model_dump() == config["mechanics"]
    assert result.environment.model_dump() == config["environment"]
    assert result.geometry.path == "separate-study/geometry/model.hst"
    assert result.recommended_max_panels == 3000


@pytest.mark.parametrize("waterplane,accepted", [(500, True), (501, False)])
def test_native_preflight_enforces_full_equivalent_budget(
    tmp_path, monkeypatch, waterplane, accepted
):
    monkeypatch.setattr(study, "ROOT", tmp_path)
    (tmp_path / "mesh.hst").write_text("Frozen source mesh")
    cfg = CaseConfig.model_validate(
        dict(
            project="budget_test",
            geometry=dict(type="hst", path="mesh.hst"),
            environment=dict(frequency=dict(min=0.2, max=0.8, step=0.1)),
            mechanics=dict(
                model="explicit",
                mass_kg=1000,
                cog_m=[0, 0, -1],
                gyradius_m=[1, 1, 1, 0, 0, 0],
                roll_damping_pct=5,
                source_note="Fixed physical parameters for a budget-only test",
            ),
        )
    )

    def run(*args, **kwargs):
        kwargs["log_path"].write_text("Native preflight log")
        return SimpleNamespace(ok=True, log="Native preflight log")

    monkeypatch.setattr(study.core, "run", run)
    monkeypatch.setattr(
        study.core,
        "parse_hslec",
        lambda _: dict(
            hull_panels=1000,
            waterplane_panels=waterplane,
            symmetry=1,
        ),
    )
    if accepted:
        measured = study.measured_config(cfg, tmp_path)
        assert measured.recommended_max_panels == 3000
        assert measured.waterplane_estimate_factor == 1.5
    else:
        with pytest.raises(ValueError, match="3002/3000"):
            study.measured_config(cfg, tmp_path)
        assert not (tmp_path / "budget-preflight.json").exists()


def test_cap_keeps_boundary_and_orientation_when_source_order_reverses():
    if any(importlib.util.find_spec(name) is None for name in ("numpy", "gmsh")):
        pytest.skip("Geometry extras required")
    # Gmsh owns process-global native handles, so isolate it from pytest capture.
    code = textwrap.dedent("""
        import numpy as np
        import gmsh
        from hydrostar_mcp.structured_panels import _cap_mesh
        theta = np.linspace(-np.pi, 0, 25)
        arc = np.column_stack([np.full(25, -60.0), 1.3*np.cos(theta), 3*np.sin(theta)])
        gmsh.initialize([], readConfigFiles=False, interruptible=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.model.add('end_cap_regression')
            a, fa = _cap_mesh(gmsh, arc, -1)
            b, fb = _cap_mesh(gmsh, arc[::-1], 1)
            np.testing.assert_allclose(a, b, atol=1e-12)
            assert {tuple(sorted(f)) for f in fa} == {tuple(sorted(f)) for f in fb}
            for vertices, faces, direction in ((a, fa, -1), (b, fb, 1)):
                vertices = np.array(vertices)
                for point in arc:
                    assert np.min(np.linalg.norm(vertices-point, axis=1)) < 1e-12
                for face in faces:
                    p = vertices[face]
                    assert direction*np.cross(p[1]-p[0], p[2]-p[0])[0] > 0
        finally:
            gmsh.finalize()
    """)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
