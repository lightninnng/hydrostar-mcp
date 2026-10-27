"""Independent geometry, drawing and frozen-source acceptance regressions."""

from pathlib import Path
import os
import subprocess
import sys

import pytest
from pydantic import ValidationError

from hydrostar_mcp import core
from hydrostar_mcp.geometry_sources import GeometryRequest, LoftDocument
from hydrostar_mcp.geometry_workflow import GeometryService, verify_bundle
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import file_hash, save_json


def request(path="source.json", **kwargs):
    return GeometryRequest(
        project="geometry_test",
        path=path,
        units="m",
        source_note="Original synthetic geometry for acceptance tests",
        **kwargs,
    )


def document():
    # 20 x 10 x 7 solid; the waterline removes the upper 2 m.
    return {
        "schema_version": 1,
        "solids": [
            {
                "name": "own_prism",
                "axis": "x",
                "profiles": [
                    {"position": x, "points": [[-5, -5], [5, -5], [5, 2], [-5, 2]]}
                    for x in (-10, 10)
                ],
            }
        ],
    }


def wet_box(tmp_path):
    from conftest import box_mesh
    from hydrostar_mcp.geometry_kernel import source_surface, clip_and_weld

    p = box_mesh(tmp_path / "own.hst", symmetry=0)
    v, f, _ = source_surface(p, request(str(p)))
    return clip_and_weld(v, f, 1e-8)


def test_frame_units_and_right_handed_rotation():
    from hydrostar_mcp.geometry_kernel import frame_points

    r = request(axis_map=["y", "-x", "z"], translation_m=[2, 3, 4], waterline_z_m=5)
    assert frame_points([[1000, 2000, 3000]], r, 0.001) == [[4, 2, 2]]
    with pytest.raises(ValidationError, match="右手"):
        request(axis_map=["x", "y", "-z"])
    with pytest.raises(ValidationError):
        request(waterline_z_m=float("nan"))


def test_polyline_correspondence_and_station_order():
    d = document()
    d["solids"][0]["profiles"][1]["points"].append([0, 4])
    with pytest.raises(ValidationError, match="相同点数"):
        LoftDocument.model_validate(d)
    d["solids"][0]["curve"] = "spline"
    LoftDocument.model_validate(d)
    d["solids"][0]["profiles"].reverse()
    with pytest.raises(ValidationError, match="严格递增"):
        LoftDocument.model_validate(d)


def test_topology_accepts_waterline_only_and_detects_reversal_and_hole(tmp_path):
    pytest.importorskip("shapely")
    from hydrostar_mcp.surface_checks import inspect_surface

    v, f = wet_box(tmp_path)
    assert inspect_surface(v, f)["passed"]
    assert not inspect_surface(v, [p[::-1] for p in f])["passed"]
    assert not inspect_surface(v, f[1:])["passed"]
    inconsistent = [p[:] for p in f]
    inconsistent[0].reverse()
    assert inspect_surface(v, inconsistent)["invalid_edges"]
    assert inspect_surface(v, f + f[:1])["duplicate_faces"] == 1


def test_triangle_intersections_crossing_coplanar_and_shared_edge():
    np = pytest.importorskip("numpy")
    pytest.importorskip("shapely")
    from hydrostar_mcp.surface_checks import triangle_intersections

    v = np.array(
        [
            [0, 0, -1],
            [2, 0, -1],
            [0, 2, -1],
            [0.3, 0.3, -2],
            [0.3, 0.3, 0],
            [1.3, 0.3, -1],
        ],
        dtype=float,
    )
    assert triangle_intersections(v, np.array([[0, 1, 2], [3, 4, 5]]), 1e-8)
    v[3:] = [[0.2, 0.2, -1], [0.6, 0.2, -1], [0.2, 0.6, -1]]
    assert triangle_intersections(v, np.array([[0, 1, 2], [3, 4, 5]]), 1e-8)
    v[3] = [2, 2, -1]
    assert not triangle_intersections(v, np.array([[0, 1, 2], [1, 3, 2]]), 1e-8)
    # A single common node does not permit a second, overlapping edge segment.
    v[3:5] = [[1, 0, -1], [1, -1, -1]]
    assert triangle_intersections(v, np.array([[0, 1, 2], [0, 3, 4]]), 1e-8)
    v[3:5] = [[-1, 0, -1], [0, -1, -1]]
    assert not triangle_intersections(v, np.array([[0, 1, 2], [0, 3, 4]]), 1e-8)


def test_geometry_timeout_preserves_log_and_reaps_owned_descendants(tmp_path):
    from hydrostar_mcp.geometry_workflow import _run_kernel
    from hydrostar_mcp.workflow import owner_is_alive

    pid_path = tmp_path / "geometry_child.pid"
    code = (
        "import subprocess,sys,time;from pathlib import Path;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);"
        f"Path({str(pid_path)!r}).write_text(str(child.pid));"
        "print('worker started',flush=True);time.sleep(30)"
    )
    with pytest.raises(subprocess.TimeoutExpired):
        _run_kernel([sys.executable, "-c", code], tmp_path, os.environ.copy(), 2)
    assert "worker started" in (tmp_path / "kernel.log").read_text()
    assert not owner_is_alive(int(pid_path.read_text()))


def evidence():
    return {
        "source_sha256": "a" * 64,
        "tolerance_m": 0.001,
        "calibration": [{"pixel": p, "uv_m": p} for p in ([0, 0], [10, 0], [0, 10])],
        "checkpoints": [{"pixel": p, "uv_m": p} for p in ([10, 10], [5, 5])],
    }


def test_drawing_independent_scale_checks_and_residuals():
    pytest.importorskip("numpy")
    from hydrostar_mcp.geometry_kernel import validate_digitization

    e = evidence()
    validate_digitization(e)
    e["checkpoints"][0]["uv_m"] = [11, 10]
    with pytest.raises(ValueError, match="误差"):
        validate_digitization(e)
    e = evidence()
    e["calibration"].append({"pixel": [10, 10], "uv_m": [11, 10]})
    with pytest.raises(ValueError, match="残差"):
        validate_digitization(e)
    e = evidence()
    e["source_sha256"] = "z" * 64
    with pytest.raises(ValueError, match="SHA"):
        validate_digitization(e)
    e = evidence()
    e["checkpoints"][1] = e["checkpoints"][0]
    with pytest.raises(ValueError, match="不同"):
        validate_digitization(e)


def test_source_root_and_type_boundaries(tmp_path):
    source = tmp_path / "sources"
    source.mkdir()
    other = tmp_path / "other.csv"
    other.write_text("station,u,v\n", encoding="utf-8")
    service = GeometryService(tmp_path / "bundles", source)
    with pytest.raises(ValueError, match="根目录"):
        service.inspect(str(other))
    wrong = source / "untrusted.py"
    wrong.write_text("print(1)", encoding="utf-8")
    with pytest.raises(ValueError, match="格式"):
        service.inspect(str(wrong))


@pytest.fixture
def accepted_bundle(tmp_path):
    pytest.importorskip("gmsh")
    pytest.importorskip("shapely")
    pytest.importorskip("matplotlib")
    source = tmp_path / "source.json"
    save_json(source, document())
    result = GeometryService(tmp_path / "geometry", tmp_path).build(
        request(str(source), mesh_size_m=3)
    )
    assert result["status"] == "geometry_accepted", result
    return result


def test_isolated_cad_volume_and_bundle_hashes(accepted_bundle):
    result = accepted_bundle
    assert result["hydrostatics"]["volume"] == pytest.approx(1000, rel=1e-10)
    assert result["hydrostatics"]["cb"] == pytest.approx([0, 0, -2.5], abs=1e-10)
    assert result["quality"]["passed"]
    folder = Path(result["directory"])
    verify_bundle(folder / "geometry-report.json", folder / "model.hst")
    (folder / "source.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA"):
        verify_bundle(folder / "geometry-report.json", folder / "model.hst")


def test_geometry_sources_frozen_and_tamper_blocks_solve(
    service, solver, accepted_bundle
):
    result = accepted_bundle
    cfg = CaseConfig.model_validate(
        {
            "project": "geometry_test",
            "geometry": result["case_geometry"],
            "environment": {"frequency": {"min": 0.2, "max": 0.8, "step": 0.2}},
            "mechanics": {
                "model": "explicit",
                "mass_kg": 1025000,
                "cog_m": [0, 0, -3.5],
                "gyradius_m": [4, 6, 7, 0, 0, 0],
                "roll_damping_pct": 0,
                "source_note": "Original box balanced loading for frozen-source regression",
            },
        }
    )
    report = service.prepare(cfg)
    assert report["status"] == "prepared", report
    folder = Path(report["directory"])
    assert list(folder.glob("geometry-source--*"))
    snapshot = folder / "geometry-source--request.json"
    snapshot.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="输入已变化"):
        service.start(report["case_id"])
    assert "hsrdf" not in solver.calls


def test_dxf_keeps_every_corner_and_reads_mm(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    ezdxf = pytest.importorskip("ezdxf")
    pytest.importorskip("shapely")
    from hydrostar_mcp.geometry_kernel import dxf_document

    dxf = ezdxf.new()
    dxf.units = 4
    corners = [[-3000, -1000], [2000, -1000], [3000, 0], [2000, 1000], [-3000, 1000]]
    for layer in ("A", "B"):
        dxf.layers.add(layer)
        dxf.modelspace().add_lwpolyline(
            corners, close=True, dxfattribs={"layer": layer}
        )
    path = tmp_path / "own.dxf"
    dxf.saveas(path)
    r = GeometryRequest(
        project="own",
        path=str(path),
        units="file",
        station_layers={"A": -2000, "B": 2000},
        source_note="Original millimetre DXF corner regression",
    )
    loft, scale = dxf_document(path, r)
    assert scale == 0.001
    assert loft.solids[0].profiles[0].points == corners


@pytest.mark.parametrize("extension", [".step", ".iges", ".brep"])
def test_cad_declared_mm_or_explicit_brep_units(tmp_path, extension):
    pytest.importorskip("gmsh")
    pytest.importorskip("shapely")
    source = tmp_path / ("mm-box" + extension)
    # Keep all OCC calls in children: its native Windows output handles and
    # process-global state must not share pytest's capture or an MCP process.
    code = """import sys,gmsh
gmsh.initialize([],readConfigFiles=False,interruptible=False)
try:
    gmsh.option.setNumber('General.Terminal',0)
    gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    gmsh.model.add('own_mm_box')
    gmsh.model.occ.addBox(-10000,-5000,-5000,20000,10000,7000)
    gmsh.model.occ.synchronize()
    gmsh.write(sys.argv[1])
finally:
    gmsh.finalize()
"""
    subprocess.run(
        [sys.executable, "-c", code, str(source)],
        capture_output=True,
        check=True,
        timeout=60,
    )
    r = GeometryRequest(
        project="mm_box",
        path=str(source),
        units="mm" if extension == ".brep" else "file",
        mesh_size_m=4,
        source_note="Original SI conversion test using a known CAD box",
    )
    report = GeometryService(tmp_path / "converted", tmp_path).build(r)
    assert report["status"] == "geometry_accepted", report
    assert report["reference"]["cad_volume_m3"] == pytest.approx(1000, rel=1e-9)
    assert report["hydrostatics"]["volume"] == pytest.approx(1000, rel=1e-9)


@pytest.mark.parametrize("extension", [".stl", ".obj", ".ply", ".hst"])
def test_surface_adapters_preserve_displacement(tmp_path, extension):
    meshio = pytest.importorskip("meshio")
    pytest.importorskip("shapely")
    from hydrostar_mcp.geometry_kernel import build_surface
    from hydrostar_mcp.geometry_worker import write_hst

    v, f = wet_box(tmp_path)
    source = tmp_path / ("source" + extension)
    if extension == ".hst":
        write_hst(source, request(), v, f)
        r = request(str(source))
    else:
        import numpy as np

        meshio.write(
            source,
            meshio.Mesh(np.array(v) * 1000, [("triangle", f)]),
            **({"binary": True} if extension == ".stl" else {}),
        )
        r = GeometryRequest(
            project="own",
            path=str(source),
            units="mm",
            source_note="Original wet box exported in millimetres",
        )
    vertices, faces, _ = build_surface(source, r)
    output = tmp_path / "accepted.hst"
    write_hst(output, r, vertices, faces)
    assert core.hydrostatics(output)["volume"] == pytest.approx(80)


def test_image_staging_requires_tracing_and_retains_original_hash(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    from hydrostar_mcp.drawing import stage_drawing

    source = tmp_path / "source.png"
    Image.new("RGB", (320, 240), "white").save(source)
    report = stage_drawing(tmp_path, source, request(str(source)))
    assert report["status"] == "digitization_required"
    assert not (tmp_path / "model.hst").exists()
    html = (tmp_path / "digitize.html").read_text(encoding="utf-8")
    assert file_hash(source) in html
    assert "__DRAWING_DATA__" not in html


def test_pdf_page_selection_and_rendering(tmp_path):
    pdfium = pytest.importorskip("pypdfium2")
    from hydrostar_mcp.drawing import stage_drawing

    doc = pdfium.PdfDocument.new()
    doc.new_page(200, 100)
    source = tmp_path / "source.pdf"
    doc.save(str(source))
    doc.close()
    assert (
        stage_drawing(tmp_path, source, request(str(source)))["status"]
        == "digitization_required"
    )
    with pytest.raises(ValueError, match="页码"):
        stage_drawing(tmp_path, source, request(str(source), pdf_page=1))
