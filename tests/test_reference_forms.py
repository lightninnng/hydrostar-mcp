"""Source-driven parameters, geometry fidelity, inertia and workflow contracts."""

import copy
import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrostar_mcp import core, geometry
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.reference_forms import FORMS, catalog, make_case
from hydrostar_mcp.workflow import file_hash


@pytest.mark.parametrize("name", list(FORMS))
def test_source_recipe_has_independent_geometry_and_explicit_acceptance(service, name):
    cfg = make_case(name)
    p = service.plan(cfg)
    assert p["status"] == "planned"
    assert p["independent_mesh_quality"]["passed"]
    assert p["geometry_provenance"]["external_mesh_files"] == []
    assert not p["reference_model"]["engineering_acceptance"]["ready"]
    assert p["reference_model"]["sources"]
    values = p["reference_model"]["scalar_comparison"]
    if cfg.geometry.type == "section_hull":
        assert abs(values["volume_relative"]) < 0.01
        assert abs(values["lcb_error_percent_length"]) < 0.1
    else:
        assert abs(values["total_volume_relative"]) < 0.001
        assert p["independent_mesh_quality"]["connected_wet_surfaces"] == 3


@pytest.mark.parametrize("name", list(FORMS))
def test_reference_case_native_path_and_archived_generator(service, solver, name):
    cfg = make_case(name)
    r = service.prepare(cfg)
    assert r["status"] == "prepared", r.get("error")
    path = Path(r["directory"])
    assert (
        file_hash(path / "forms_geometry.py")
        == r["geometry_provenance"]["additional_generator_sources"]["forms_geometry.py"]
    )
    assert r["reference_model"]["form_id"] == name
    text = (path / (cfg.project + ".mcn")).read_text()
    assert ("HYDSWPLANE" in text) == (cfg.geometry.type == "section_hull")
    service.start(r["case_id"])
    service.jobs[r["case_id"]][0].result(timeout=10)
    assert service.status(r["case_id"])["status"] == "completed"


def test_builtin_bow_is_asymmetric_and_feature_sensitive():
    cfg = make_case("container_kcs_style")
    g = cfg.geometry.model_dump()
    original = geometry.build(g)
    g.update(bulb_length_ratio=0.0, bulb_breadth_ratio=0.0)
    plain = geometry.build(g)
    assert max(p[0] for p in original.nodes.values()) > cfg.geometry.length / 2
    assert max(p[0] for p in plain.nodes.values()) == pytest.approx(
        cfg.geometry.length / 2
    )
    assert original.hydrostatics()["cb"][0] != pytest.approx(
        plain.hydrostatics()["cb"][0]
    )


def test_column_bem_and_morison_volume_are_separate():
    cfg = make_case("semisub_oc4_style")
    mesh = geometry.build(cfg.geometry.model_dump())
    hyd = mesh.hydrostatics()
    physical = [m.model_dump() for m in cfg.mechanics.morison if m.cm > 0]
    virtual = [m.model_dump() for m in cfg.mechanics.morison if m.cm == 0]
    assert len(physical) == 15 and len(virtual) == 7
    assert core.morison_displacement(virtual)["volume_m3"] == 0
    total = hyd["volume"] + core.morison_displacement(physical)["volume_m3"]
    assert cfg.mechanics.mass_kg == pytest.approx(1025 * total)
    core.validate_passive_matrix(cfg.mechanics.linear_damping_matrix)


def test_cylinder_and_given_inertia_parallel_axis_are_physical():
    comps = [
        dict(
            name="cylinder",
            mass_fraction=1.0,
            shape="vertical_cylinder",
            size_m=[4.0, 4.0, 6.0],
            center_m=[0.0, 0.0, 0.0],
        )
    ]
    m = geometry.combine_box_masses(100.0, comps)
    assert [m["inertia_kg_m2"][i][i] for i in range(3)] == pytest.approx(
        [400.0, 400.0, 200.0]
    )
    rigid = copy.deepcopy(comps)
    rigid[0].update(
        shape="rigid_body", gyradius_m=[2.0, 2.0, math.sqrt(2), 0.0, 0.0, 0.0]
    )
    got = geometry.combine_box_masses(100.0, rigid)["inertia_kg_m2"]
    assert [v for row in got for v in row] == pytest.approx(
        [v for row in m["inertia_kg_m2"] for v in row]
    )


def test_reference_tag_matches_geometry_family():
    with pytest.raises(ValidationError, match="构型"):
        CaseConfig(reference_form="semisub_oc4_style")
    assert catalog()["forms"]["tanker_kvlcc2_style"]["source_correction"]
    cfg = make_case("semisub_oc4_style").model_dump()
    point = next(c for c in cfg["mechanics"]["components"] if c["shape"] == "point")
    point["size_m"] = [1.0, 0.0, 0.0]
    with pytest.raises(ValidationError, match="点质量"):
        CaseConfig.model_validate(cfg)
