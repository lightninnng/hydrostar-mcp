"""Compute native body-following pressure on the mean wetted panels."""

from __future__ import annotations

import argparse
import cmath
import gzip
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__, core
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.pressure import (
    wet_panel_samples,
    pressure_points,
    body_pressure_card,
    pressure_rao_card,
    read_pressure_data,
)
from hydrostar_mcp.workflow import CaseService, digest, file_hash, save_json

KEYS = ["container_kcs_style", "tanker_kvlcc2_style", "semisub_oc4_style"]


def recipe(key):
    data = json.loads(
        (ROOT / "examples/animations" / key / "config.json").read_text(encoding="utf-8")
    )
    data["project"] = {
        "container_kcs_style": "container_pressure",
        "tanker_kvlcc2_style": "tanker_pressure",
        "semisub_oc4_style": "semisub_pressure",
    }[key]
    return CaseConfig.model_validate(data)


def run_one(key, service, old):
    cfg = recipe(key)
    wave_folder = ROOT / "examples/animations" / key
    identity = digest(dict(config=cfg.model_dump(mode="json"), offset_m=0.02))
    cached = old if old.get("config_digest") == identity else {}
    report = service.status(cached["case_id"]) if cached else service.prepare(cfg)
    print(key + ": " + report["status"], flush=True)
    if report["status"] == "prepared":
        service.start(report["case_id"])
        service.jobs[report["case_id"]][0].result(timeout=1800)
        report = service.status(report["case_id"])
    if report["status"] != "completed" or set(report["quality_gates"].values()) != {
        "passed"
    }:
        raise ValueError(report.get("error") or "Native motion gates must pass")
    directory = Path(report["directory"])
    for name, expected in report["input_hashes"].items():
        source = (directory / name).resolve()
        if (
            not source.is_relative_to(directory.resolve())
            or file_hash(source) != expected
        ):
            raise ValueError("Prepared motion inputs changed: " + name)
    motions = {d: service.result(report["case_id"], d) for d in core.DOFS}
    wave_motions = json.loads(
        (wave_folder / "motions.json").read_text(encoding="utf-8")
    )
    maximum_motion_difference = 0.0
    for d, a in motions.items():
        b = wave_motions[d]
        if (
            a["omega"] != b["omega"]
            or a["headings"] != b["headings"]
            or a["unit"] != b["unit"]
        ):
            raise ValueError("Pressure and wave conditions must agree")
        qa = cmath.rect(a["amplitude"][0][0], math.radians(a["phase"][0][0]))
        qb = cmath.rect(b["amplitude"][0][0], math.radians(b["phase"][0][0]))
        maximum_motion_difference = max(
            maximum_motion_difference, abs(qa - qb) / max(abs(qb), 0.01)
        )
    if maximum_motion_difference > 1e-5:
        raise ValueError("Pressure and wave motion responses differ")
    mesh = wet_panel_samples(directory / (cfg.project + ".hst"))
    points = pressure_points(mesh, 0.02)
    n = len(mesh["faces"])
    expected = {}
    for kind, coef, selected in [("following", 1, points), ("eulerian", 0, points[:n])]:
        expected[kind + ".prs"] = body_pressure_card(selected, coef)
        expected[kind + ".rao"] = pressure_rao_card(len(selected), kind)
    reuse = cached.get("pressure_completed") and all(
        (directory / name).exists()
        and (directory / name).read_text(encoding="ascii") == value
        for name, value in expected.items()
    )
    steps = cached.get("pressure_steps", []) if reuse else []
    if not reuse:
        for name, value in expected.items():
            (directory / name).write_text(value, encoding="ascii")
        for kind in ["following", "eulerian"]:
            for module, ext in [("hsprs", "prs"), ("hsrao", "rao")]:
                print(f"{key}: {kind} {module}, {n} wetted panels", flush=True)
                result = core.run(
                    module,
                    [kind + "." + ext, cfg.project],
                    directory,
                    timeout=1200,
                    log_path=directory
                    / "logs"
                    / ("pressure-" + kind + "-" + module + ".log"),
                )
                if not result.ok:
                    raise ValueError(
                        f"{module}: {result.error_code}; {result.log[-500:]}"
                    )
                steps.append(
                    dict(
                        module=module,
                        component=kind,
                        ok=result.ok,
                        rc=result.rc,
                        seconds=round(result.seconds, 3),
                    )
                )
    data, verification = read_pressure_data(
        directory, mesh, cfg, report["mechanics"]["cog_m"], motions
    )
    native_digest = digest(verification["native_file_sha256"])
    if reuse and native_digest != cached["native_digest"]:
        raise ValueError("Cached native pressure records changed")
    data["source_wave_field_sha256"] = file_hash(wave_folder / "field.json")
    print(
        f"{key}: incident error {verification['incident_complex_max_error']:.3g}, body-motion error {verification['hydrostatic_motion_complex_max_error']:.3g}, offset change {verification['offset_complex_change_over_global_peak']:.3g}",
        flush=True,
    )
    folder = ROOT / "examples/pressures" / key
    for sub in ["inputs", "rao", "native-samples"]:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    save_json(folder / "config.json", cfg.model_dump(mode="json"))
    save_json(folder / "pressure.json", data)
    for ext in ["hst", "rdf", "mcn", "rao"]:
        source = directory / (cfg.project + "." + ext)
        shutil.copyfile(source, folder / "inputs" / source.name)
    for name in expected:
        shutil.copyfile(directory / name, folder / "inputs" / name)
    for d in core.DOFS:
        shutil.copyfile(directory / "rao" / (d + ".rao"), folder / "rao" / (d + ".rao"))
    save_json(
        folder / "motions.json",
        {
            d: {k: a[k] for k in ["omega", "headings", "amplitude", "phase", "unit"]}
            for d, a in motions.items()
        },
    )
    sample_names = {
        f"pressure_{kind}_{i:04d}.rao"
        for kind in ["following", "eulerian", "incident"]
        for i in [1, n // 2, n]
    }
    for existing in (folder / "native-samples").glob("pressure_*.rao"):
        if existing.name not in sample_names:
            existing.unlink()
    for name in sorted(sample_names):
        shutil.copyfile(directory / "rao" / name, folder / "native-samples" / name)
    with (folder / "native-pressure-raos.jsonl.gz").open("wb") as target:
        with gzip.GzipFile(filename="", fileobj=target, mode="wb", mtime=0) as archive:
            for name in sorted(verification["native_file_sha256"]):
                content = (directory / "rao" / name).read_bytes().decode("utf-8")
                archive.write(
                    (
                        json.dumps(dict(name=name, content=content), ensure_ascii=True)
                        + "\n"
                    ).encode("ascii")
                )
    verification.update(
        schema_version=1,
        form_id=key,
        source_case_id=report["case_id"],
        computed_at_utc=report["updated_at"],
        backend=dict(
            name="HydroStar", version="8.2.0", automation_version=report["version"]
        ),
        publication_version=__version__,
        quality_gates=report["quality_gates"],
        topology=report["hschk"],
        pressure_steps=steps,
        coefficients=dict(
            incident=1.0, diffraction_radiation=1.0, hydrostatic_motion=1.0, body=1
        ),
        source_wave_motion_max_difference=maximum_motion_difference,
        pressure_gates=dict(
            native_execution="passed",
            input_integrity="passed",
            panel_coordinates="passed",
            pressure_units="passed",
            incident_analytical="passed",
            hydrostatic_motion_identity="passed",
            surface_sampling_sensitivity="passed",
            wave_motion_consistency="passed",
        ),
        model_scope=report["reference_model"],
    )
    verification["files"] = {
        p.relative_to(folder).as_posix(): file_hash(p)
        for p in sorted(folder.rglob("*"))
        if p.is_file() and p.name != "verification.json"
    }
    save_json(folder / "verification.json", verification)
    return dict(
        case_id=report["case_id"],
        directory=str(directory),
        config_digest=identity,
        pressure_completed=True,
        pressure_steps=steps,
        native_digest=native_digest,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--form", choices=KEYS)
    parser.add_argument("--frames", type=int, default=48)
    args = parser.parse_args()
    if args.frames < 12 or args.frames > 120:
        parser.error("frames must be 12..120")
    keys = [args.form] if args.form else KEYS
    index = ROOT / "output/validation/pressure_study.json"
    state = (
        json.loads(index.read_text(encoding="utf-8"))
        if index.exists()
        else dict(cases={})
    )
    if args.run:
        service = CaseService(ROOT / "output/validation/pressure_runs", ROOT)
        try:
            for key in keys:
                state["cases"][key] = run_one(key, service, state["cases"].get(key, {}))
                save_json(index, state)
        finally:
            service.close()
    if args.run or args.render:
        from hydrostar_mcp.pressure_render import render_coupled_gif

        for key in keys:
            print(key + ": rendering synchronized pressure/wave/motion", flush=True)
            folder = ROOT / "examples/pressures" / key
            settings = render_coupled_gif(
                folder,
                ROOT / "docs/assets" / (key + "_coupled.gif"),
                frames=args.frames,
            )
            save_json(folder / "render.json", settings)
            verification = json.loads(
                (folder / "verification.json").read_text(encoding="utf-8")
            )
            verification["files"] = {
                p.relative_to(folder).as_posix(): file_hash(p)
                for p in sorted(folder.rglob("*"))
                if p.is_file() and p.name != "verification.json"
            }
            save_json(folder / "verification.json", verification)
        records = []
        for key in KEYS:
            folder = ROOT / "examples/pressures" / key
            if (folder / "render.json").exists():
                records.append(
                    dict(
                        form_id=key,
                        verification_sha256=file_hash(folder / "verification.json"),
                        gif_sha256=file_hash(
                            ROOT / "docs/assets" / (key + "_coupled.gif")
                        ),
                    )
                )
        save_json(
            ROOT / "examples/pressures/index.json",
            dict(schema_version=1, cases=records),
        )
    elif not args.run:
        for key in keys:
            print(json.dumps(recipe(key).model_dump(mode="json"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
