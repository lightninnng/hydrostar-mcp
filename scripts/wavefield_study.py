"""Compute and render native total/scattered wave fields for the reference cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__, core
from hydrostar_mcp.animation import (
    field_grid,
    pressure_card,
    field_rao_card,
    read_native_field,
    render_wave_gif,
)
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.reference_forms import make_case
from hydrostar_mcp.workflow import CaseService, digest, file_hash, save_json

SETTINGS = {
    "container_kcs_style": ("container_wave", 0.5, 60.0),
    "tanker_kvlcc2_style": ("tanker_wave", 0.4, 60.0),
    "semisub_oc4_style": ("semisub_wave", 0.8, 60.0),
}


def recipe(key):
    project, omega, heading = SETTINGS[key]
    data = make_case(key, project).model_dump(mode="json")
    data["environment"]["frequency"] = dict(min=omega, max=omega, step=0.005)
    data["environment"]["headings"] = dict(min=heading, max=heading, step=30.0)
    data["mechanics"]["wave_amplitude_m"] = 0.5
    data["nproc"] = 1
    return CaseConfig.model_validate(data)


def run_one(key, service, old, size):
    cfg = recipe(key)
    identity = digest(dict(config=cfg.model_dump(mode="json"), field_grid_size=size))
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
        raise ValueError(
            f"Native solve required: {report.get('error') or report['status']}"
        )
    directory = Path(report["directory"])
    responses = {d: service.result(report["case_id"], d) for d in core.DOFS}
    grid = field_grid(directory / (cfg.project + ".hst"), size)
    prs, rao = directory / "surface.prs", directory / "surface.rao"
    expected_prs, expected_rao = (
        pressure_card(grid["points"]),
        field_rao_card(grid["points"]),
    )
    reuse = (
        cached.get("field_completed")
        and prs.is_file()
        and rao.is_file()
        and prs.read_text(encoding="ascii") == expected_prs
        and rao.read_text(encoding="ascii") == expected_rao
    )
    if reuse:
        steps = cached["field_steps"]
    else:
        prs.write_text(expected_prs, encoding="ascii")
        rao.write_text(expected_rao, encoding="ascii")
        steps = []
        for module, card in [("hsprs", prs), ("hsrao", rao)]:
            print(
                f"{key}: {module} / {len(grid['points'])} exterior field points",
                flush=True,
            )
            result = core.run(
                module,
                [card.name, cfg.project],
                directory,
                timeout=900,
                log_path=directory / "logs" / ("wavefield-" + module + ".log"),
            )
            if not result.ok:
                raise ValueError(f"{module}: {result.error_code}; {result.log[-600:]}")
            steps.append(
                dict(
                    module=module,
                    ok=result.ok,
                    rc=result.rc,
                    seconds=round(result.seconds, 3),
                )
            )
    fields, verification = read_native_field(
        directory,
        grid,
        cfg.environment.frequency.min,
        cfg.environment.headings.min,
        cfg.environment.depth,
        cfg.environment.gravity_m_s2,
    )
    print(
        f"{key}: native incident complex error {verification['incident_complex_max_error']:.3g}",
        flush=True,
    )
    folder = ROOT / "examples/animations" / key
    (folder / "inputs").mkdir(parents=True, exist_ok=True)
    (folder / "native-samples").mkdir(exist_ok=True)
    (folder / "rao").mkdir(exist_ok=True)
    save_json(folder / "config.json", cfg.model_dump(mode="json"))
    for extension in ("hst", "rdf", "mcn", "rao"):
        source = directory / (cfg.project + "." + extension)
        shutil.copyfile(source, folder / "inputs" / source.name)
    for source in (prs, rao):
        shutil.copyfile(source, folder / "inputs" / source.name)
    motions = {
        d: {k: a[k] for k in ("omega", "headings", "amplitude", "phase", "unit")}
        for d, a in responses.items()
    }
    save_json(folder / "motions.json", motions)
    for dof in core.DOFS:
        shutil.copyfile(
            directory / "rao" / (dof + ".rao"), folder / "rao" / (dof + ".rao")
        )
    for i in [
        grid["points"][0][0],
        grid["points"][len(grid["points"]) // 2][0],
        grid["points"][-1][0],
    ]:
        for kind in ("total", "incident"):
            name = f"field_{kind}_{i:04d}.rao"
            shutil.copyfile(directory / "rao" / name, folder / "native-samples" / name)
    field = dict(
        schema_version=1,
        form_id=key,
        omega_rad_s=cfg.environment.frequency.min,
        heading_deg=cfg.environment.headings.min,
        wave_amplitude_m=0.5,
        depth_m=cfg.environment.depth,
        gravity_m_s2=cfg.environment.gravity_m_s2,
        rho_kg_m3=cfg.environment.rho_kg_m3,
        cog_m=report["mechanics"]["cog_m"],
        wave_reference_xy_m=verification["wave_reference_xy_m"],
        phase_convention="real(H*exp(+i*omega*t)); phase lead",
        field_definition="Absolute free-surface elevation: incident + diffraction + motion-induced radiation; COEFHDS=0",
        transfer_unit="m/m",
        incident_header_note="Native WAVEDEC INC prints m; its values are checked against a unit-amplitude analytical Airy wave",
        grid=grid,
        **fields,
    )
    save_json(folder / "field.json", field)
    import gzip

    with (folder / "native-field-raos.jsonl.gz").open("wb") as raw_bundle:
        with gzip.GzipFile(
            filename="", fileobj=raw_bundle, mode="wb", mtime=0
        ) as bundle:
            for name in sorted(verification["native_file_sha256"]):
                content = (directory / "rao" / name).read_bytes().decode("utf-8")
                bundle.write(
                    (
                        json.dumps(dict(name=name, content=content), ensure_ascii=True)
                        + "\n"
                    ).encode("ascii")
                )
    if (
        reuse
        and cached.get("native_digest") is not None
        and digest(verification["native_file_sha256"]) != cached["native_digest"]
    ):
        raise ValueError(
            "Cached native field files changed; prepare a fresh field case"
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
        solver_mechanics=report["solver_mechanics"],
        field_steps=steps,
        coefficients=dict(
            incident=1.0, diffraction_radiation=1.0, hydrostatic_motion=0.0
        ),
        field_gates=dict(
            exterior_points="passed",
            native_execution="passed",
            native_grid_units="passed",
            incident_analytical_complex="passed",
            source_hashes="passed",
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
        field_completed=True,
        field_steps=steps,
        native_digest=digest(verification["native_file_sha256"]),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render verified exported field data without running a solver",
    )
    parser.add_argument("--form", choices=list(SETTINGS))
    parser.add_argument("--grid", type=int, default=51)
    parser.add_argument("--frames", type=int, default=48)
    args = parser.parse_args()
    if args.grid < 21 or args.grid > 81 or args.frames < 12 or args.frames > 120:
        parser.error("grid must be 21..81 and frames must be 12..120")
    keys = [args.form] if args.form else list(SETTINGS)
    index_path = ROOT / "output/validation/wavefield_study.json"
    state = (
        json.loads(index_path.read_text(encoding="utf-8"))
        if index_path.exists()
        else dict(cases={})
    )
    if args.run:
        service = CaseService(ROOT / "output/validation/wavefield_runs", ROOT)
        try:
            for key in keys:
                state["cases"][key] = run_one(
                    key, service, state["cases"].get(key, {}), args.grid
                )
                save_json(index_path, state)
        finally:
            service.close()
    if args.run or args.render:
        for key in keys:
            print(key + ": rendering GIF", flush=True)
            folder = ROOT / "examples/animations" / key
            settings = render_wave_gif(
                folder, ROOT / "docs/assets" / (key + "_wave.gif"), frames=args.frames
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
            print(key + ": GIF saved", flush=True)
        available = []
        for key in SETTINGS:
            folder = ROOT / "examples/animations" / key
            if (folder / "render.json").exists():
                available.append(
                    dict(
                        form_id=key,
                        verification_sha256=file_hash(folder / "verification.json"),
                        gif="../../docs/assets/" + key + "_wave.gif",
                        gif_sha256=file_hash(
                            ROOT / "docs/assets" / (key + "_wave.gif")
                        ),
                    )
                )
        save_json(
            ROOT / "examples/animations/index.json",
            dict(schema_version=1, cases=available),
        )
    else:
        for key in keys:
            print(json.dumps(recipe(key).model_dump(mode="json"), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
