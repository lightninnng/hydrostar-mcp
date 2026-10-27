from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import CaseService
from conftest import CHECK_LOG, box_mesh


def finish(service, case_id):
    future, _ = service.jobs[case_id]
    future.result(timeout=10)
    return service.status(case_id)


def test_generate_inputs_works_without_solver(service, solver):
    report = service.generate(CaseConfig())
    assert report["status"] == "generated"
    assert solver.calls == []
    directory = Path(report["directory"])
    assert all(
        (directory / ("barge100." + ext)).is_file()
        for ext in ("mri", "rdf", "mcn", "rao")
    )
    assert "MASS_BODY 1 18450000" in (directory / "barge100.mcn").read_text()
    with pytest.raises(ValueError):
        service.start(report["case_id"])


def test_complete_chain_and_all_output_units(service, solver):
    prepared = service.prepare(CaseConfig(output_point_m=[50, 0, 0]))
    assert prepared["status"] == "prepared"
    assert prepared["hschk"]["pass"]
    assert prepared["hydrostatics"]["volume"] == pytest.approx(18000)
    service.start(prepared["case_id"])
    report = finish(service, prepared["case_id"])
    assert report["status"] == "completed"
    assert solver.calls == ["hsmsh", "hslec", "hschk", "hsrdf", "hsmcn", "hsrao"]
    assert len(report["results"]) == 7
    assert set(report["quality_gates"].values()) == {"passed"}
    assert service.result(prepared["case_id"], "roll")["unit"] == "deg/m"
    assert len(service.result(prepared["case_id"])["amplitude"]) == 36


@pytest.mark.parametrize(
    "module,expected",
    [
        ("hsmsh", ["hsmsh"]),
        ("hslec", ["hsmsh", "hslec"]),
        ("hschk", ["hsmsh", "hslec", "hschk"]),
        ("hsrdf", ["hsmsh", "hslec", "hschk", "hsrdf"]),
        ("hsmcn", ["hsmsh", "hslec", "hschk", "hsrdf", "hsmcn"]),
        ("hsrao", ["hsmsh", "hslec", "hschk", "hsrdf", "hsmcn", "hsrao"]),
    ],
)
def test_failure_stops_downstream(service, solver, module, expected):
    solver.fail_module = module
    report = service.prepare(CaseConfig())
    if report["status"] == "prepared":
        service.start(report["case_id"])
        report = finish(service, report["case_id"])
    assert report["status"] == "failed"
    assert solver.calls == expected
    with pytest.raises(ValueError):
        service.result(report["case_id"])


def test_topology_nonzero_is_a_hard_stop(service, solver):
    solver.check_log = CHECK_LOG.replace("superpositions = 0", "superpositions = 3")
    report = service.prepare(CaseConfig())
    assert report["status"] == "failed"
    assert report["error"]["code"] == "MESH_REJECTED"
    assert "hsrdf" not in solver.calls


def test_missing_mesh_count_never_defaults_to_zero(service, solver):
    solver.hslec_log = "Nb panels on hulls 752"
    report = service.prepare(CaseConfig())
    assert report["error"]["code"] == "INCOMPLETE_MESH_REPORT"
    assert solver.calls == ["hsmsh", "hslec"]


def test_budget_requires_confirmation_before_any_write(service, solver):
    cfg = CaseConfig(recommended_max_panels=100)
    report = service.prepare(cfg)
    assert report["status"] == "needs_confirmation"
    assert report["stage"] == "before_generation"
    assert not service.root.exists()
    assert solver.calls == []
    # Deliberately confirm this synthetic test case only.
    prepared = service.prepare(cfg, report["confirmation_token"])
    assert prepared["status"] == "needs_confirmation"
    assert prepared["stage"] == "before_solver"
    blocked = service.start(prepared["case_id"])
    assert blocked["status"] == "needs_confirmation"
    assert "hsrdf" not in solver.calls
    service.start(prepared["case_id"], prepared["confirmation_token"])
    assert finish(service, prepared["case_id"])["status"] == "completed"


def test_confirmation_is_bound_to_configuration(service, solver):
    a = CaseConfig(recommended_max_panels=100)
    token = service.plan(a)["confirmation_token"]
    b = CaseConfig(project="changed", recommended_max_panels=100)
    assert service.prepare(b, token)["stage"] == "before_generation"
    assert not solver.calls


def test_measured_budget_cannot_be_hidden_by_low_estimate(service, solver):
    solver.waterplane = 1000
    report = service.prepare(CaseConfig())
    assert report["status"] == "needs_confirmation"
    assert report["mesh_screening"]["full_equivalent_panels"] == 3504
    assert service.start(report["case_id"])["status"] == "needs_confirmation"


def test_input_tampering_requires_prepare_again(service, solver):
    report = service.prepare(CaseConfig())
    path = Path(report["directory"]) / "barge100.mcn"
    path.write_text(path.read_text() + "# changed")
    with pytest.raises(ValueError, match="输入已变化"):
        service.start(report["case_id"])
    assert "hsrdf" not in solver.calls


def test_result_tampering_is_rejected(service, solver):
    report = service.prepare(CaseConfig())
    service.start(report["case_id"])
    finish(service, report["case_id"])
    path = Path(report["directory"]) / "rao/heave.rao"
    path.write_text(path.read_text() + "# changed")
    with pytest.raises(ValueError, match="结果已改变"):
        service.result(report["case_id"])


def test_missing_one_requested_rao_fails_the_whole_case(service, solver):
    solver.omit_rao = "yaw.rao"
    report = service.prepare(CaseConfig())
    service.start(report["case_id"])
    report = finish(service, report["case_id"])
    assert report["status"] == "failed"
    assert report["error"]["code"] == "RESULT_VALIDATION_FAILED"


def test_reruns_use_new_directories_and_never_old_outputs(service, solver):
    first = service.prepare(CaseConfig())
    service.start(first["case_id"])
    finish(service, first["case_id"])
    solver.fail_module = "hsmsh"
    second = service.prepare(CaseConfig())
    assert first["directory"] != second["directory"]
    assert second["status"] == "failed"
    with pytest.raises(ValueError):
        service.result(second["case_id"])


def test_ready_case_can_be_started_by_new_service(service, solver):
    prepared = service.prepare(CaseConfig())
    reopened = CaseService(service.root, service.source_root)
    try:
        reopened.start(prepared["case_id"])
        assert finish(reopened, prepared["case_id"])["status"] == "completed"
    finally:
        reopened.close()


def test_source_traversal_and_case_traversal_rejected(service):
    with pytest.raises(ValueError):
        service.source_path("../outside.hst")
    with pytest.raises(ValueError):
        service.case_path("../case")


def test_live_owner_is_not_reported_as_a_server_restart(service, solver):
    import os
    from hydrostar_mcp.workflow import save_json

    report = service.prepare(CaseConfig())
    report.update(status="running", owner_pid=os.getpid())
    save_json(Path(report["directory"]) / "report.json", report)
    assert service.status(report["case_id"])["status"] == "running"


def test_cancel_request_stops_before_next_solver(service, solver):
    from threading import Event

    report = service.prepare(CaseConfig())
    cancel = Event()
    cancel.set()
    service._solve(Path(report["directory"]), report, cancel)
    assert service.status(report["case_id"])["status"] == "cancelled"
    assert "hsrdf" not in solver.calls


def test_explicit_damping_cannot_be_silently_guessed():
    with pytest.raises(ValidationError, match="roll_damping_pct"):
        CaseConfig(
            mechanics=dict(
                model="explicit",
                mass_kg=18450000,
                cog_m=[0, 0, 0],
                gyradius_m=[8, 28, 29, 0, 0, 0],
                source_note="loading report",
            )
        )


def test_imported_mesh_requires_explicit_mass_data():
    with pytest.raises(ValidationError):
        CaseConfig(geometry={"type": "hst", "path": "a.hst"})


def test_real_cog_does_not_get_replaced_by_buoyancy(service):
    cfg = CaseConfig(
        mechanics=dict(
            model="explicit",
            roll_damping_pct=0,
            mass_kg=18450000,
            cog_m=[0, 0, -1],
            gyradius_m=[8, 28, 29, 0, 0, 0],
            source_note="test loading report",
        )
    )
    report = service.generate(cfg)
    assert report["plan"]["mechanics"]["cog_m"] == [0, 0, -1]
    assert (
        "COGPOINT_BODY 1 0 0 -1"
        in (Path(report["directory"]) / "barge100.mcn").read_text()
    )


def test_mass_mismatch_is_rejected_before_generation(service):
    cfg = CaseConfig(
        mechanics=dict(
            model="explicit",
            roll_damping_pct=0,
            mass_kg=184500000,
            cog_m=[0, 0, 0],
            gyradius_m=[8, 28, 29, 0, 0, 0],
            source_note="bad mass",
        )
    )
    with pytest.raises(ValueError, match="不平衡"):
        service.generate(cfg)
    assert not service.root.exists()


def test_static_mooring_pretension_is_included_in_balance(service):
    # 1,000,000 kg less than buoyancy is balanced by a downward 9.81 MN force.
    cfg = CaseConfig(
        mechanics=dict(
            model="explicit",
            roll_damping_pct=0,
            mass_kg=17450000,
            cog_m=[0, 0, 0],
            gyradius_m=[8, 28, 29, 0, 0, 0],
            vertical_external_force_n=-9810000,
            source_note="synthetic pretension example",
        )
    )
    assert service.plan(cfg)["mechanics"][
        "equilibrium_relative_error"
    ] == pytest.approx(0)


def test_morison_requires_explicit_linearization():
    member = dict(start=[0, 0, -3], end=[1, 0, 0], diameter=1, cd=1)
    with pytest.raises(ValidationError):
        CaseConfig(mechanics={"morison": [member]})


def test_floating_structure_requires_finite_depth():
    with pytest.raises(ValidationError):
        CaseConfig(object_type="floating_structure")


def test_extra_fields_and_nonfinite_values_rejected():
    with pytest.raises(ValidationError):
        CaseConfig(geometery={})
    with pytest.raises(ValidationError):
        CaseConfig(environment={"rho_kg_m3": float("nan")})


def test_imported_constants_must_match_case(service, tmp_path):
    box_mesh(tmp_path / "box.hst")
    cfg = CaseConfig(
        geometry={"type": "hst", "path": "box.hst"},
        mechanics=dict(
            model="explicit",
            roll_damping_pct=0,
            mass_kg=82000,
            cog_m=[0, 0, -1],
            gyradius_m=[2, 3, 3, 0, 0, 0],
            source_note="synthetic example",
        ),
        environment={"rho_kg_m3": 1000},
    )
    with pytest.raises(ValueError, match="不一致"):
        service.plan(cfg)


@pytest.mark.parametrize(
    "name",
    [
        "barge100",
        "barge_explicit",
        "semisub",
        "curved_hull",
        "container_kcs_style",
        "tanker_kvlcc2_style",
        "semisub_oc4_style",
        "imported_mesh",
    ],
)
def test_supplied_examples_export_with_provenance(tmp_path, name):
    repo = Path(__file__).resolve().parent.parent
    service = CaseService(root=tmp_path / "exports", source_root=repo)
    try:
        config = CaseConfig.model_validate_json(
            (repo / "examples" / f"{name}.json").read_text(encoding="utf-8")
        )
        result = service.generate(config)
        assert result["status"] == "generated"
        assert result["input_hashes"]
        assert result["steps"] == []
    finally:
        service.close()


def test_morison_original_mass_is_rejected_before_generation(tmp_path):
    box_mesh(tmp_path / "box.hst")
    service = CaseService(root=tmp_path / "exports", source_root=tmp_path)
    try:
        cfg = CaseConfig(
            geometry=dict(type="hst", path="box.hst"),
            mechanics=dict(
                model="explicit",
                mass_kg=82000.0,
                cog_m=[0.0, 0.0, -1.0],
                gyradius_m=[2.0, 3.0, 3.0, 0.0, 0.0, 0.0],
                roll_damping_pct=0.0,
                source_note="Synthetic box and external physical cylinder; mass deliberately omits the cylinder",
                morison=[
                    dict(
                        start=[-4.0, 4.0, -1.0],
                        end=[4.0, 4.0, -1.0],
                        diameter=1.0,
                        cm=2.0,
                        cd=0.0,
                    )
                ],
            ),
        )
        with pytest.raises(ValueError, match="不平衡"):
            service.generate(cfg)
        assert not service.root.exists()
    finally:
        service.close()


def test_solver_equilibrium_warning_stops_before_rao(service, solver):
    solver.hsmcn_log = (
        "!!! Warning the ship is not balanced !!!\nRelative Error = 6.149 %"
    )
    report = service.prepare(CaseConfig())
    service.start(report["case_id"])
    report = finish(service, report["case_id"])
    assert report["status"] == "failed"
    assert report["quality_gates"]["static_equilibrium"] == "failed"
    assert report["error"]["code"] == "SOLVER_EQUILIBRIUM_FAILED"
    assert "hsrao" not in solver.calls


def test_horizontal_gravity_buoyancy_offset_has_a_gate(service):
    cfg = CaseConfig(
        mechanics=dict(
            model="explicit",
            roll_damping_pct=0,
            mass_kg=18450000,
            cog_m=[1, 0, -1],
            gyradius_m=[8, 28, 29, 0, 0, 0],
            source_note="course assumption",
        )
    )
    with pytest.raises(ValueError, match="水平偏距"):
        service.plan(cfg)


def test_static_preload_must_have_a_verified_solver_input(service):
    cfg = CaseConfig(
        mechanics=dict(
            model="explicit",
            roll_damping_pct=0,
            mass_kg=17450000,
            cog_m=[0, 0, 0],
            gyradius_m=[8, 28, 29, 0, 0, 0],
            vertical_external_force_n=-9810000,
            source_note="planning example",
        )
    )
    assert service.plan(cfg)["mechanics"][
        "equilibrium_relative_error"
    ] == pytest.approx(0)
    with pytest.raises(ValueError, match="预载输入"):
        service.generate(cfg)
    assert not service.root.exists()
