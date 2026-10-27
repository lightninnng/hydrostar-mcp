"""Extract complex HSPRS fields and pressures for independently checked animation."""

import argparse
import cmath
import gzip
import json
import math
from pathlib import Path
import shutil
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.animation import pressure_card, wave_number
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.pressure import (
    body_pressure_card,
    pressure_points,
    pressure_rao_card,
    read_pressure_data,
    wet_panel_samples,
)
from hydrostar_mcp.workflow import file_hash, save_json
from scripts.prepare_native_media import native_source, read_arrays
from scripts.native_animation_study import SETTINGS


def run_native(work, project, module, card):
    result = core.run(
        module,
        [card, project],
        work,
        timeout=1200,
        log_path=work
        / "logs"
        / ("validated-" + module + "-" + card.replace(".", "-") + ".log"),
    )
    if not result.ok:
        raise ValueError(f"{module}: {result.error_code} {result.log[-500:]}")
    return dict(
        module=module, input=card, ok=True, rc=result.rc, seconds=result.seconds
    )


def archive_raos(destination, paths):
    with destination.open("wb") as target:
        with gzip.GzipFile(filename="", fileobj=target, mode="wb", mtime=0) as archive:
            for path in sorted(paths):
                archive.write(
                    (
                        json.dumps(
                            dict(
                            name=path.name, content=path.read_bytes().decode("utf-8")
                            ),
                            ensure_ascii=True,
                        )
                        + "\n"
                    ).encode("ascii")
                )


def study(key):
    work = (
        ROOT
        / "output/validation/native-views"
        / ("vessel-wave" if key == "vessel" else key)
    )
    folder = ROOT / "examples/visualization/fields" / key
    condition = json.loads((folder / "condition.json").read_text(encoding="utf-8"))
    report = json.loads((work / "report.json").read_text(encoding="utf-8"))
    project = report["project"]
    first, _ = read_arrays(work / "anim" / condition["wave_files"][0])
    active = np.unique(condition["valid_wave_cells"])
    points = [[i + 1, *first[j, :2], 0.0] for i, j in enumerate(active)]
    omega, heading = condition["omega_rad_s"], condition["heading_deg"]
    input_prs = pressure_card(points)
    input_rao = "".join(
        f"PRESSURE POINT {i} FILE verified_total_{i:04d}.rao\nWAVEDEC INC POINT {i} FILE verified_inc_{i:04d}.rao\nWAVEDEC DIF POINT {i} FILE verified_dif_{i:04d}.rao\n"
        for i, *_ in points
    )
    selected = np.linspace(0, len(points) - 1, 5, dtype=int)
    cog = condition["cog_m"]
    input_rao += "".join(
        f"WAVEDEC RAD{d} POINT {i + 1} AT {cog[0]:.12g} {cog[1]:.12g} {cog[2]:.12g} FILE verified_rad{d}_{i + 1:04d}.rao\n"
        for i in selected
        for d in range(1, 7)
    )
    (work / "verified-wave.prs").write_text(input_prs, encoding="ascii")
    (work / "verified-wave.rao").write_text(input_rao, encoding="ascii")
    cached = work / "verified-wave-completed.json"
    expected = {
        "prs": file_hash(work / "verified-wave.prs"),
        "rao": file_hash(work / "verified-wave.rao"),
    }
    old_cache = json.loads(cached.read_text()) if cached.exists() else {}
    if old_cache.get("inputs") == expected:
        if old_cache.get("raw_hashes") and any(
            file_hash(work / "rao" / name) != h
            for name, h in old_cache["raw_hashes"].items()
        ):
            raise ValueError("Cached native wave extraction changed")
        steps = old_cache["steps"]
    else:
        print(key + ": extract complete complex wave fields from HSPRS", flush=True)
        steps = [
            run_native(work, project, "hsprs", "verified-wave.prs"),
            run_native(work, project, "hsrao", "verified-wave.rao"),
        ]
        save_json(cached, dict(inputs=expected, steps=steps))
    names = []

    def read(name):
        names.append(name)
        raw = core.read_rao(work / "rao" / name)
        if raw["omega"] != [omega] or raw["headings"] != [heading]:
            raise ValueError("Unexpected wave-field condition")
        if raw["unit"] not in ("m", "m/m"):
            raise ValueError("Unexpected native head/elevation unit")
        return raw["amplitude"][0][0] * cmath.exp(1j * math.radians(raw["phase"][0][0]))

    fields = {name: [] for name in ("total", "incident", "diffraction")}
    for i, *_ in points:
        for field, code in [
            ("total", "total"),
            ("incident", "inc"),
            ("diffraction", "dif"),
        ]:
            fields[field].append(read(f"verified_{code}_{i:04d}.rao"))
    motions = {
        d: core.read_rao(native_source(key) / "rao" / (d + ".rao")) for d in core.DOFS
    }
    q = []
    for j, dof in enumerate(core.DOFS):
        raw = motions[dof]
        a, b = raw["omega"].index(omega), raw["headings"].index(heading)
        q.append(
            raw["amplitude"][a][b]
            * cmath.exp(1j * math.radians(raw["phase"][a][b]))
            * (math.pi / 180 if j >= 3 else 1)
        )
    radiation = (
        np.array(fields["total"])
        - np.array(fields["incident"])
        - np.array(fields["diffraction"])
    )
    radiation_error = 0.0
    for i in selected:
        expected_rad = sum(
            1j * omega * q[d] * read(f"verified_rad{d + 1}_{i + 1:04d}.rao")
            for d in range(6)
        )
        radiation_error = max(radiation_error, abs(radiation[i] - expected_rad))
    k = wave_number(omega, condition["depth_m"], condition["gravity_m_s2"])
    beta = math.radians(heading)
    reference = condition["wave_reference_xy_m"]
    analytical = [
        cmath.exp(
            -1j
            * k
            * (
                (p[1] - reference[0]) * math.cos(beta)
                + (p[2] - reference[1]) * math.sin(beta)
            )
        )
        for p in points
    ]
    incident_error = float(np.max(abs(np.array(fields["incident"]) - analytical)))
    if incident_error > 2e-5 or radiation_error > 5e-5:
        raise ValueError(
            "Complex native field validation failed: "
            + str((incident_error, radiation_error))
        )
    wave = dict(
        schema="hydrostar-complex-fields-1",
        native_point_indices=active.tolist(),
        points_m=[p[1:] for p in points],
        convention="A*Re(H*exp(+i*omega*t)); native complex head/elevation per unit incident amplitude",
        **{name: [[v.real, v.imag] for v in values] for name, values in fields.items()},
    )
    save_json(folder / "waves.json", wave)
    archive_raos(
        folder / "wave-raos.jsonl.gz",
        [work / "rao" / name for name in sorted(set(names))],
    )
    save_json(
        cached,
        dict(
            inputs=expected,
            steps=steps,
            raw_hashes={
                name: file_hash(work / "rao" / name) for name in sorted(set(names))
            },
        ),
    )
    (folder / "wave.prs").write_text(input_prs, encoding="ascii")
    (folder / "wave.rao").write_text(input_rao, encoding="ascii")
    # Quantify the old-format HSprv reconstruction independently, keeping all
    # original files unchanged. Only HSPRS complex fields feed the public views.
    samples = []
    for file in condition["wave_files"]:
        _, arrays = read_arrays(work / "anim" / file)
        samples.append(arrays["Displacement"][active])
    phases = np.arange(condition["frames"]) * 2 * math.pi / condition["frames"]
    basis = np.column_stack((np.cos(phases), -np.sin(phases)))
    fitted = np.linalg.lstsq(
        basis, np.array(samples).reshape(condition["frames"], -1), rcond=None
    )[0].reshape(2, len(active), 9)
    fitted = fitted[0] + 1j * fitted[1]
    amplitude = condition["wave_amplitude_m"]
    hsprv_errors = {
        label: float(
            np.max(abs(fitted[:, column] - amplitude * np.array(fields[field])))
        )
        for label, column, field in [
            ("incident", 7, "incident"),
            ("diffraction", 6, "diffraction"),
            ("total", 8, "total"),
        ]
    }
    if hsprv_errors["incident"] > 0.0005 or hsprv_errors["diffraction"] > 0.0005:
        raise ValueError("HSprv incident/diffraction correspondence failed")
    if key == "vessel":
        cfg = report["config"].copy()
        cfg["mechanics"] = {**cfg["mechanics"], "wave_amplitude_m": amplitude}
        cfg = CaseConfig.model_validate(cfg)
        mesh = wet_panel_samples(work / (project + ".hst"))
        n = len(mesh["faces"])
        ppoints = pressure_points(mesh, 0.02)
        pressure_steps = []
        pressure_cache = work / "verified-pressure-completed.json"
        if pressure_cache.exists():
            pressure_steps = json.loads(pressure_cache.read_text())["steps"]
        else:
            for kind, coef, chosen in [
                ("following", 1, ppoints),
                ("eulerian", 0, ppoints[:n]),
            ]:
                (work / (kind + ".prs")).write_text(
                    body_pressure_card(chosen, coef), encoding="ascii"
                )
                (work / (kind + ".rao")).write_text(
                    pressure_rao_card(len(chosen), kind), encoding="ascii"
                )
                print(
                    key + ": native " + kind + " pressure on " + str(n) + " panels",
                    flush=True,
                )
                pressure_steps += [
                    run_native(work, project, "hsprs", kind + ".prs"),
                    run_native(work, project, "hsrao", kind + ".rao"),
                ]
            save_json(pressure_cache, dict(steps=pressure_steps))
        pressure, pcheck = read_pressure_data(work, mesh, cfg, cog, motions)
        save_json(folder / "pressure.json", pressure)
        save_json(folder / "pressure-verification.json", pcheck)
        archive_raos(
            folder / "pressure-raos.jsonl.gz",
            [work / "rao" / name for name in pcheck["native_file_sha256"]],
        )
        for kind in ("following", "eulerian"):
            for ext in ("prs", "rao"):
                shutil.copyfile(work / (kind + "." + ext), folder / (kind + "." + ext))
        pressure_path = "examples/visualization/fields/vessel/pressure.json"
        pcheck_path = "examples/visualization/fields/vessel/pressure-verification.json"
        comparison = json.loads(
            (ROOT / "output/validation/course-vessel-wave-comparison.json").read_text(
                encoding="utf-8"
            )
        )
        save_json(folder / "sweep-comparison.json", comparison)
    else:
        pressure_path = "examples/pressures/" + SETTINGS[key][0] + "/pressure.json"
        pcheck_path = "examples/pressures/" + SETTINGS[key][0] + "/verification.json"
        pressure = json.loads((ROOT / pressure_path).read_text(encoding="utf-8"))
        pcheck = json.loads((ROOT / pcheck_path).read_text(encoding="utf-8"))
        pressure_steps = pcheck["pressure_steps"]
        for j, dof in enumerate(core.DOFS):
            stored = complex(*pressure["motion_complex"][j]) * (
                math.pi / 180 if j >= 3 else 1
            )
            if abs(stored - q[j]) > 1e-5:
                raise ValueError(
                    "Archived pressure motions differ from the field calculation"
                )
    # Fixed colour limits come from complex amplitudes, covering the entire cycle.
    head = np.array(
        [
            complex(*v)
            for v in pressure["following_head"][: len(pressure["mesh"]["faces"])]
        ]
    )
    condition["colour_limits"] = {
        "Pressure": float(abs(head).max())
        * amplitude
        * condition["rho_kg_m3"]
        * condition["gravity_m_s2"]
        / 1000,
        "Total": float(abs(np.array(fields["total"])).max()) * amplitude,
        "Scattered": float(
            abs(np.array(fields["total"]) - np.array(fields["incident"])).max()
        )
        * amplitude,
        "Diffraction": float(abs(np.array(fields["diffraction"])).max()) * amplitude,
        "Radiation": float(abs(radiation).max()) * amplitude,
    }
    condition["pressure_file"] = pressure_path
    condition["pressure_file_sha256"] = file_hash(ROOT / pressure_path)
    save_json(folder / "condition.json", condition)
    (folder / "inputs").mkdir(exist_ok=True)
    for ext in ("hst", "rdf", "mcn", "rao"):
        shutil.copyfile(
            native_source(key) / (project + "." + ext),
            folder / "inputs" / (project + "." + ext),
        )
    record = json.loads((folder / "verification.json").read_text(encoding="utf-8"))
    record["method"] = (
        "Native HSPRS/HSRAO complex fields and verified panel-following pressure; HSprv geometry/motion archived; ParaView command rendering"
    )
    record["status"] = "numerically_verified"
    record["definitions"]["pressure"] = (
        "Native body-following first-order pressure perturbation at the mean wet panels, kPa; equilibrium hydrostatic pressure stored separately"
    )
    record["accepted_display_fields"] = (
        "waves.json plus the explicitly linked pressure file; raw HSprv total and nodal pressure are retained as diagnostics"
    )
    record["hsprv_crosscheck"] = dict(
        complex_max_errors_m=hsprv_errors,
        raw_total_used_for_display=False,
        finding="Old-format HSprv motion-induced wave reconstruction differs from independently extracted full-complex HSPRS fields; displayed total, scattered and radiation use HSPRS",
    )
    record["wave_validation"] = dict(
        incident_complex_error=incident_error,
        radiation_complex_error=float(radiation_error),
        incident_limit=2e-5,
        radiation_limit=5e-5,
        unit="m/m",
        steps=steps,
        raw_files={name: file_hash(work / "rao" / name) for name in sorted(set(names))},
    )
    record["pressure_validation"] = dict(
        data=pressure_path,
        data_sha256=file_hash(ROOT / pressure_path),
        verification=pcheck_path,
        incident_complex_error=pcheck["incident_complex_max_error"],
        motion_correction_complex_error=pcheck["hydrostatic_motion_complex_max_error"],
        offset_change_over_peak=pcheck["offset_complex_change_over_global_peak"],
        steps=pressure_steps,
    )
    record["gates"].update(
        native_complex_wave="passed",
        native_radiation_motion="passed",
        body_pressure_identity="passed",
        body_pressure_sampling="passed",
    )
    record["files"] = {
        p.relative_to(folder).as_posix(): file_hash(p)
        for p in folder.rglob("*")
        if p.is_file() and p.name != "verification.json"
    }
    save_json(folder / "verification.json", record)
    print(
        key
        + ": verified complex wave/pressure fields ready; HSprv raw total discrepancy "
        + str(hsprv_errors["total"]),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case", choices=["vessel", "container", "tanker", "platform"], action="append"
    )
    args = parser.parse_args()
    for key in args.case or ["vessel", "container", "tanker", "platform"]:
        study(key)
