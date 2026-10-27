import math
import sys
from threading import Event

import pytest

from hydrostar_mcp import core
from conftest import CHECK_LOG, box_mesh, mesh_from_mri


@pytest.mark.parametrize("sym,indexed", [(0, False), (1, False), (2, False), (1, True)])
def test_box_volume_centroid_area_and_symmetry(tmp_path, sym, indexed):
    result = core.hydrostatics(box_mesh(tmp_path / "box.hst", sym, indexed=indexed))
    assert result["volume"] == pytest.approx(80)
    assert result["cb"] == pytest.approx((0, 0, -1))
    assert result["wetted_area"] == pytest.approx(96)
    assert result["sym"] == sym


def test_free_surface_translation(tmp_path):
    result = core.hydrostatics(box_mesh(tmp_path / "box.hst", 1, free_surface=7))
    assert result["volume"] == pytest.approx(80)
    assert result["cb"] == pytest.approx((0, 0, 6))


def test_patch_axes_and_spacing_regression(tmp_path):
    path = tmp_path / "barge.mri"
    core.write_mri_barge(path, 100, 30, 6, 40, 8, 4)
    # Distinct sides ensure matching only the total count cannot hide swapped axes.
    assert "PATCH 1 NODE 1 2 6 5 AB_NB 8 AB_RULE 0 BC_NB 40" in path.read_text()
    assert "PATCH 2 NODE 2 3 7 6 AB_NB 4 AB_RULE 0 BC_NB 40" in path.read_text()
    assert "PATCH 3 NODE 1 4 3 2 AB_NB 4 AB_RULE 0 BC_NB 8" in path.read_text()
    mesh_from_mri(path, tmp_path / "barge.hst")
    result = core.hydrostatics(tmp_path / "barge.hst")
    assert result["n_panels"] == 544
    assert result["volume"] == pytest.approx(18000)
    assert result["wetted_area"] == pytest.approx(4560)
    assert result["max_edge"] == pytest.approx(2.5)
    assert result["max_aspect_ratio"] == pytest.approx(2.5 / 1.5)


def test_budget_uses_longest_edge_and_finite_depth():
    budget = core.budget_barge(100, 30, 6, 40, 8, 4)
    assert budget["omega_max"] == pytest.approx(
        math.sqrt(2 * math.pi * 9.81 / (8 * 2.5))
    )
    assert budget["omega_max"] < math.sqrt(2 * math.pi * 9.81 / (8 * budget["a"]))
    assert core.wave_limit(10, 5) < core.wave_limit(10, "INF")


def test_barge_estimate_covers_the_recorded_waterplane_case():
    # Actual corrected v8.2.0 case: 752 hull + 416 waterplane panels per half.
    budget = core.budget_barge(100, 30, 6, 48, 10, 4)
    advice = core.assess_budget(budget)
    assert advice["n_effective_estimate"] >= 2 * (752 + 416)
    assert advice["n_waterplane_estimate_full"] > 0


@pytest.mark.parametrize(
    "args",
    [
        (100, 30, 6, 0, 8, 4),
        (100, 30, 6, 40.5, 8, 4),
        (-1, 30, 6, 40, 8, 4),
        (100, 30, 6, True, 8, 4),
    ],
)
def test_invalid_geometry_rejected(args):
    with pytest.raises(ValueError):
        core.budget_barge(*args)


def test_unsupported_symmetry_rejected():
    with pytest.raises(ValueError):
        core.budget_barge(100, 30, 6, 40, 8, 4, sym=0)


def test_checker_requires_all_counts_and_no_fatal():
    assert core.parse_hschk(CHECK_LOG)["pass"]
    assert not core.parse_hschk(
        CHECK_LOG.replace("superpositions = 0", "superpositions = 1")
    )["pass"]
    assert not core.parse_hschk("\n".join(CHECK_LOG.splitlines()[:-1]))["pass"]
    assert not core.parse_hschk(CHECK_LOG + "\n" + CHECK_LOG)["pass"]
    assert not core.parse_hschk(CHECK_LOG + "\nforrtl: severe (151)")["pass"]


def test_rao_preserves_units_and_fortran_exponent(tmp_path):
    path = tmp_path / "x.rao"
    path.write_text(
        "#UNIT : deg/m\n#NBHEADING 2\n#HEADING 0 180\n0.1 1D0 2D0 0 180\n#ENDFILE\n"
    )
    result = core.read_rao(path)
    assert result["unit"] == "deg/m"
    assert result["amplitude"] == [[1, 2]]
    assert result["headings"] == [0, 180]


@pytest.mark.parametrize(
    "text",
    [
        "#HEADING 0 90\n0.1 1 2 3\n#ENDFILE",
        "#HEADING 0\n0.1 nan 0\n#ENDFILE",
        "#HEADING 0\n0.1 1 0",
        "#HEADING 0\n0.1 1 0\n0.1 2 0\n#ENDFILE",
        "#HEADING 0\n0.1 -1 0\n#ENDFILE",
        "#ENDFILE",
    ],
)
def test_incomplete_or_invalid_rao_rejected(tmp_path, text):
    path = tmp_path / "x.rao"
    path.write_text(text)
    with pytest.raises(ValueError):
        core.read_rao(path)


@pytest.mark.parametrize(
    "change",
    [
        lambda t: t.replace("1 2 6 5", "1 2 999 5"),
        lambda t: t.replace("SYMMETRY 1 1", "NBBODY 2\nSYMMETRY 1 1"),
        lambda t: t.replace("ENDFILE", ""),
        lambda t: t.replace("COORDINATES TYPE 0", "TRANS 1 2 3\nCOORDINATES TYPE 0"),
    ],
)
def test_hst_rejects_uninterpretable_geometry(tmp_path, change):
    path = box_mesh(tmp_path / "x.hst")
    path.write_text(change(path.read_text()))
    with pytest.raises(ValueError):
        core.hydrostatics(path)


def test_missing_nodes_are_not_skipped(tmp_path):
    path = box_mesh(tmp_path / "x.hst")
    path.write_text(path.read_text().replace("1 2 6 5", "1 2 100 5"))
    with pytest.raises(ValueError):
        core.hydrostatics(path)


def test_dry_panels_excluded_from_hydrostatics(tmp_path):
    path = box_mesh(tmp_path / "x.hst")
    text = path.read_text().replace("ENDPANEL", "1 2 6 5\nENDPANEL")
    path.write_text(text.replace("ZFSURFACE", "NUMFPONT 1 5 5\nZFSURFACE"))
    assert core.hydrostatics(path)["volume"] == pytest.approx(80)


def test_inward_normals_do_not_silently_flip(tmp_path):
    path = box_mesh(tmp_path / "x.hst")
    lines = path.read_text().splitlines()
    section = False
    for i, line in enumerate(lines):
        if line == "PANEL TYPE 0":
            section = True
            continue
        if line == "ENDPANEL":
            section = False
        if section:
            lines[i] = " ".join(reversed(line.split()))
    path.write_text("\n".join(lines))
    with pytest.raises(ValueError, match="排水量非正"):
        core.hydrostatics(path)


def test_grid_requires_exact_endpoints():
    with pytest.raises(ValueError):
        core.grid_values(0.1, 1.0, 0.2)


def test_fatal_log_even_with_zero_exit_code(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    result = core.run(
        "hsmsh", ["-c", "print('forrtl: severe (151)')"], tmp_path, timeout=5
    )
    assert not result.ok
    assert result.error_code == "FORTRAN_ERROR"


def test_license_pause_ends_without_waiting_for_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    result = core.run(
        "hsmsh",
        [
            "-u",
            "-c",
            "import time;print('All licenses in use (-22)',flush=True);time.sleep(30)",
        ],
        tmp_path,
        timeout=15,
    )
    assert result.error_code == "LICENSE_UNAVAILABLE"
    assert result.seconds < 12


def test_timeout_and_cancel(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    timed = core.run(
        "hsmsh", ["-c", "import time;time.sleep(30)"], tmp_path, timeout=0.3
    )
    assert timed.error_code == "TIMEOUT"
    cancelled = Event()
    cancelled.set()
    result = core.run(
        "hsmsh",
        ["-c", "import time;time.sleep(30)"],
        tmp_path,
        timeout=30,
        cancel=cancelled,
    )
    assert result.error_code == "CANCELLED"


def test_stale_mesh_never_reused(tmp_path, monkeypatch):
    core.write_mri_barge(tmp_path / "a.mri", 10, 4, 2, 10, 4, 2)
    (tmp_path / "PRO.hst").write_text("old mesh")
    with pytest.raises(FileExistsError):
        core.build_mesh(tmp_path, "a", tmp_path / "a.mri")


def test_timeout_terminates_owned_child_process(tmp_path, monkeypatch):
    from hydrostar_mcp.workflow import owner_is_alive

    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    pid_path = tmp_path / "owned_child.pid"
    code = (
        "import subprocess,sys,time;from pathlib import Path;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);"
        f"Path({str(pid_path)!r}).write_text(str(child.pid));time.sleep(30)"
    )
    result = core.run("hsmsh", ["-c", code], tmp_path, timeout=2)
    assert result.error_code == "TIMEOUT"
    assert pid_path.exists()
    assert not owner_is_alive(int(pid_path.read_text()))


def test_illegal_project_name_rejected():
    for name in ("../escape", "CON", "x\nENDFILE", "a/b", "a\\b"):
        with pytest.raises(ValueError):
            core.identifier(name)


def test_morison_volume_and_centroid_include_physical_members_once():
    physical = dict(start=[0, 0, -4], end=[0, 0, 0], diameter=2, cm=1)
    virtual = dict(start=[0, 0, -4], end=[0, 0, 0], diameter=20, cm=0)
    result = core.morison_displacement([physical, virtual])
    assert result["volume_m3"] == pytest.approx(4 * math.pi)
    assert result["cb_m"] == pytest.approx([0, 0, -2])
    assert result["physical_members"] == 1
    assert result["virtual_members"] == 1


def test_morison_free_surface_clipping():
    member = dict(start=[0, 0, -2], end=[0, 0, 2], diameter=2, cm=1)
    result = core.morison_displacement([member])
    assert result["volume_m3"] == pytest.approx(2 * math.pi)
    assert result["cb_m"] == pytest.approx([0, 0, -1])


@pytest.mark.parametrize(
    "radii", [[1, 1, 100, 0, 0, 0], [1, 1, 1, 2, 0, 0], [0, 1, 1, 0, 0, 0]]
)
def test_inertia_tensor_requires_physical_radii(radii):
    with pytest.raises(ValueError):
        core.validate_gyradius(radii)


def test_zero_exit_with_solver_equilibrium_warning_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    result = core.run(
        "hsmcn",
        ["-c", "print('!!! Warning the ship is not balanced !!!')"],
        tmp_path,
        timeout=5,
    )
    assert result.error_code == "SOLVER_EQUILIBRIUM_FAILED"
    assert not result.ok
