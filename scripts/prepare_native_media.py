"""Validate and package HSprv data before command rendering with ParaView."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.animation import wave_number, waterline_loops
from hydrostar_mcp.visualization import dry_columns, whole_mesh
from hydrostar_mcp.workflow import file_hash, save_json
from scripts.native_animation_study import SETTINGS

LABELS = dict(
    container="Container hull",
    tanker="Full-form tanker",
    platform="Column semisubmersible",
    vessel="Curved station hull",
)


def read_arrays(path):
    tree = ET.parse(path)
    points = np.fromstring(tree.find(".//Points/DataArray").text, sep=" ").reshape(
        -1, 3
    )
    arrays = {
        a.get("Name"): np.fromstring(a.text, sep=" ").reshape(
            len(points), int(a.get("NumberOfComponents", "1"))
        )
        for a in tree.findall(".//PointData/DataArray")
    }
    if not np.isfinite(points).all() or not all(
        np.isfinite(a).all() for a in arrays.values()
    ):
        raise ValueError("Non-finite native fields: " + str(path))
    return points, arrays


def native_source(key):
    old_key = SETTINGS[key][0]
    if old_key is None:
        record = json.loads(
            (ROOT / "output/validation/course-vessel-wave-native.json").read_text(
                encoding="utf-8"
            )
        )
    else:
        record = json.loads(
            (ROOT / "output/validation/wavefield_study.json").read_text(
                encoding="utf-8"
            )
        )["cases"][old_key]
    return Path(record["directory"])


def prepare(key):
    work = (
        ROOT
        / "output/validation/native-views"
        / ("vessel-wave" if key == "vessel" else key)
    )
    native = json.loads((work / "native-export.json").read_text(encoding="utf-8"))
    report = json.loads((work / "report.json").read_text(encoding="utf-8"))
    if not native["ok"] or set(report["quality_gates"].values()) != {"passed"}:
        raise ValueError("Accepted native calculation and HSprv export required")
    for name, expected in native["native_files"].items():
        if file_hash(work / name) != expected:
            raise ValueError("Native export changed: " + name)
    source = native_source(key)
    if file_hash(source / (report["project"] + ".hst")) != native["mesh_sha256"]:
        raise ValueError("Source mesh differs from native animation")
    folder = ROOT / "examples/visualization/fields" / key
    (folder / "motions").mkdir(parents=True, exist_ok=True)
    motions = {}
    for dof in core.DOFS:
        p = source / "rao" / (dof + ".rao")
        motions[dof] = core.read_rao(p)
        shutil.copyfile(p, folder / "motions" / p.name)
    match = re.search(
        r"Ref.pt incident wave\s*:\s*\(([^)]+)\)",
        (source / "rao/heave.rao").read_text(encoding="utf-8"),
    )
    reference = [float(x) for x in match[1].split()]
    vertices, faces = whole_mesh(source / (report["project"] + ".hst"))
    loops = waterline_loops(vertices, faces)
    polygons = [Polygon(loop) for loop in loops]
    wave_items = ET.parse(work / "anim/wave.pvd").findall(".//DataSet")
    body_items = ET.parse(work / "anim/ship1_.pvd").findall(".//DataSet")
    frames = native["frames"]
    if len(wave_items) not in (frames, frames + 1) or len(body_items) != len(
        wave_items
    ):
        raise ValueError("Incomplete or mismatched native time series")
    omega = native["omega_rad_s"]
    period = native["period_s"]
    amplitude = native["wave_amplitude_m"]
    cog = np.array(report["mechanics"]["cog_m"])
    k = wave_number(omega, native["depth_m"], native["gravity_m_s2"])
    beta = math.radians(native["heading_deg"])
    wave_paths = [item.get("file") for item in wave_items]
    body_paths = [item.get("file") for item in body_items]
    first_wave = ET.parse(work / "anim" / wave_paths[0])
    extent = [
        int(x) for x in first_wave.find(".//StructuredGrid").get("WholeExtent").split()
    ]
    nx, ny = extent[1] - extent[0] + 1, extent[3] - extent[2] + 1
    points, _ = read_arrays(work / "anim" / wave_paths[0])
    valid_cells, active_points = [], set()
    for iy in range(ny - 1):
        for ix in range(nx - 1):
            ids = [
                iy * nx + ix,
                iy * nx + ix + 1,
                (iy + 1) * nx + ix + 1,
                (iy + 1) * nx + ix,
            ]
            cell = Polygon(points[ids, :2])
            if any(cell.intersects(poly) for poly in polygons):
                continue
            valid_cells.append(ids)
            active_points.update(ids)
    active = np.array(sorted(active_points))
    if len(active) < 100:
        raise ValueError("Insufficient exterior free-surface points")
    errors = dict(
        total_closure_m=0.0,
        z_equals_total_m=0.0,
        airy_m=0.0,
        rigid_fit_m=0.0,
        rao_motion_m=0.0,
        pressure_harmonic_residual_head_m=0.0,
        rounded_time_s=0.0,
    )
    limits = dict(
        Pressure=0.0, Total=0.0, Scattered=0.0, Diffraction=0.0, Radiation=0.0
    )
    pressure_samples = []
    body_zero = None
    physical_motion = []
    for i, (wave_item, body_item) in enumerate(zip(wave_items, body_items)):
        time = i * period / frames
        errors["rounded_time_s"] = max(
            errors["rounded_time_s"],
            abs(float(wave_item.get("timestep")) - time),
            abs(float(body_item.get("timestep")) - time),
        )
        p, arrays = read_arrays(work / "anim" / wave_item.get("file"))
        d = arrays["Displacement"]
        if d.shape != (nx * ny, 9):
            raise ValueError(
                "This exporter supports verified HSprv old-format nine-component waves"
            )
        airy = amplitude * np.cos(
            omega * time
            - k
            * (
                (p[:, 0] - reference[0]) * math.cos(beta)
                + (p[:, 1] - reference[1]) * math.sin(beta)
            )
        )
        errors["total_closure_m"] = max(
            errors["total_closure_m"],
            float(abs(d[active, :8].sum(axis=1) - d[active, 8]).max()),
        )
        errors["z_equals_total_m"] = max(
            errors["z_equals_total_m"], float(abs(p[active, 2] - d[active, 8]).max())
        )
        errors["airy_m"] = max(
            errors["airy_m"], float(abs(airy[active] - d[active, 7]).max())
        )
        for name, data in dict(
            Total=d[:, 8],
            Scattered=d[:, 8] - d[:, 7],
            Diffraction=d[:, 6],
            Radiation=d[:, :6].sum(axis=1),
        ).items():
            limits[name] = max(limits[name], float(abs(data[active]).max()))
        p, arrays = read_arrays(work / "anim" / body_item.get("file"))
        if body_zero is None:
            body_zero = p.copy()
        if not np.array_equal(p, body_zero):
            raise ValueError(
                "Body points already move; applying deformation would double the motion"
            )
        d = arrays["deformation Deformation"]
        q = p - cog
        matrix = np.zeros((len(p), 3, 6))
        matrix[:, :, :3] = np.eye(3)
        matrix[:, 0, 4] = q[:, 2]
        matrix[:, 0, 5] = -q[:, 1]
        matrix[:, 1, 3] = -q[:, 2]
        matrix[:, 1, 5] = q[:, 0]
        matrix[:, 2, 3] = q[:, 1]
        matrix[:, 2, 4] = -q[:, 0]
        fitted = np.linalg.lstsq(matrix.reshape(-1, 6), d.reshape(-1), rcond=None)[0]
        expected = []
        for j, dof in enumerate(core.DOFS):
            m = motions[dof]
            ii = min(range(len(m["omega"])), key=lambda n: abs(m["omega"][n] - omega))
            jj = m["headings"].index(native["heading_deg"])
            if abs(m["omega"][ii] - omega) > 1e-8:
                raise ValueError("Animation frequency is absent from native motions")
            expected.append(
                amplitude
                * m["amplitude"][ii][jj]
                * math.cos(omega * time + math.radians(m["phase"][ii][jj]))
                * (math.pi / 180 if j >= 3 else 1)
            )
        physical_motion.append(expected)
        errors["rigid_fit_m"] = max(
            errors["rigid_fit_m"], float(abs(matrix @ fitted - d).max())
        )
        errors["rao_motion_m"] = max(
            errors["rao_motion_m"],
            float(abs(matrix @ (fitted - np.array(expected))).max()),
        )
        pressure = arrays["ship1_Pressure"][:, 0]
        limits["Pressure"] = max(
            limits["Pressure"],
            float(abs(pressure).max())
            * native["rho_kg_m3"]
            * native["gravity_m_s2"]
            / 1000,
        )
        if i < frames:
            pressure_samples.append(pressure)
    phases = np.arange(frames) * 2 * math.pi / frames
    basis = np.column_stack((np.cos(phases), np.sin(phases)))
    coefficients = np.linalg.lstsq(basis, pressure_samples, rcond=None)[0]
    errors["pressure_harmonic_residual_head_m"] = float(
        abs(basis @ coefficients - np.array(pressure_samples)).max()
    )
    pressure_peak_head = (
        limits["Pressure"] * 1000 / (native["rho_kg_m3"] * native["gravity_m_s2"])
    )
    # HSprv writes pressure with four significant decimal digits. The residual
    # bound follows that writer resolution, independently of the model scale.
    quantization_step = 0.001 * 10 ** math.floor(
        math.log10(max(pressure_peak_head, 1e-10))
    )
    projection = basis @ np.linalg.pinv(basis)
    pressure_quantization_bound = (
        0.5 * quantization_step * (1 + abs(projection).sum(axis=1).max())
    )
    thresholds = dict(
        total_closure_m=0.0006,
        z_equals_total_m=1e-8,
        airy_m=0.0002,
        rigid_fit_m=1e-6,
        rao_motion_m=0.0002,
        pressure_harmonic_residual_head_m=pressure_quantization_bound,
        rounded_time_s=0.01,
    )
    for name, maximum in thresholds.items():
        if errors[name] > maximum:
            raise ValueError(f"{key}: {name} {errors[name]} exceeds {maximum}")
    native_card = next(
        p for p in work.glob("*.prv") if file_hash(p) == native["input_sha256"]
    )
    shutil.copyfile(native_card, folder / "animation.prv")
    # Preserve the original native bytes; the archive contains no vendor programs.
    with ZipFile(folder / "native.zip", "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(native["native_files"]):
            archive.write(work / name, Path(name).as_posix())
    cfg = report["config"]
    condition = dict(
        label=LABELS[key],
        key=key,
        omega_rad_s=omega,
        period_s=period,
        heading_deg=native["heading_deg"],
        wave_amplitude_m=amplitude,
        rho_kg_m3=native["rho_kg_m3"],
        gravity_m_s2=native["gravity_m_s2"],
        depth_m=native["depth_m"],
        wave_reference_xy_m=reference,
        cog_m=cog.tolist(),
        frames=frames,
        wave_files=wave_paths[:frames],
        body_files=body_paths[:frames],
        motion_gain=6.0,
        wave_height_gain=6.0,
        pressure_geometry_gain=1.0,
        playback_fps=10,
        colour_limits=limits,
        valid_wave_cells=valid_cells,
        native_wave_point_count=nx * ny,
        waterline_loops_xy_m=loops,
        physical_motion=physical_motion[:frames],
        dry_columns=dry_columns(cfg),
        morison=cfg["mechanics"]["morison"],
        body_panel_count=int(
            ET.parse(work / "anim" / body_paths[0])
            .find(".//Piece")
            .get("NumberOfCells")
        ),
    )
    save_json(folder / "condition.json", condition)
    record = dict(
        schema="hydrostar-native-field-export-1",
        status="hsprv_export_checked_pending_complex_fields",
        source_case_id=report["case_id"],
        source_mesh_sha256=native["mesh_sha256"],
        source_package="examples/vessel"
        if key == "vessel"
        else "examples/results/" + SETTINGS[key][0],
        native_tool="HydroStar 8.2.0 HSprv",
        native_execution=dict(ok=True, rc=native["rc"], seconds=native["seconds"]),
        method="HSprv PVD/VTU/VTS; exterior cells selected by exact HST waterline loops; ParaView rendering follows separately",
        wave_components={
            "0..5": "Motion-weighted radiation contributions, m",
            "6": "Diffraction elevation, m",
            "7": "Incident elevation, m",
            "8": "Total elevation, m",
        },
        definitions={
            "scattered": "component 8 minus component 7; diffraction plus radiation",
            "pressure": "HSprv first-order dynamic pressure on the mean wet surface; native nodal pressure head converted to kPa using rho*g/1000; wave amplitude already included",
            "motion": "Native deformation vector; compared with the actual six-DOF complex response",
            "surface_z": "Native VTS coordinates already contain total elevation; derived views replace z before applying the display gain",
        },
        component_basis="HydroStar Hstar2Paraview old-format component 8 and the native field decomposition; incident solution, total closure and motion independently checked",
        numeric_errors=errors,
        numeric_limits=thresholds,
        pressure_precision_basis="HSprv ASCII pressure has four significant digits; the harmonic residual bound is half the largest decimal quantization step times (1 + the infinity norm of the harmonic least-squares projection)",
        gates={name: "passed" for name in thresholds},
        valid_exterior_cells=len(valid_cells),
        masked_intersecting_cells=(nx - 1) * (ny - 1) - len(valid_cells),
        masking="Exclude cells intersecting a solved waterline footprint; preserve water between separate columns",
        native_frames=len(wave_items),
        displayed_frames=frames,
        time="Exact frame index times PRV TSTP; PVD timestamps are rounded by the native writer; duplicate endpoint excluded",
        native_files=native["native_files"],
        files={
            p.relative_to(folder).as_posix(): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        },
    )
    save_json(folder / "verification.json", record)
    print(
        key
        + ": native fields and motion verified, "
        + str(len(valid_cells))
        + " exterior cells",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=list(SETTINGS), action="append")
    args = parser.parse_args()
    for case in args.case or SETTINGS:
        prepare(case)
