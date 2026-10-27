"""Export verified native examples to a portable, publication-ready showcase."""

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__, core
from hydrostar_mcp.reference_forms import FORMS, SOURCES
from hydrostar_mcp.visualization import whole_mesh, plot_rao, plot_geometry, LABELS
from hydrostar_mcp.workflow import CaseService, file_hash, save_json


def export(study_path, destination, assets):
    study = json.loads(Path(study_path).read_text(encoding="utf-8"))
    records = []
    models = []
    for key in FORMS:
        case = study["cases"][key]
        directory = Path(case["directory"])
        service = CaseService(root=directory.parent)
        try:
            report = service.status(case["case_id"])
            if report["status"] != "completed" or set(
                report["quality_gates"].values()
            ) != {"passed"}:
                raise ValueError(
                    f"A completed, accepted native solve is required: {key}"
                )
            cfg = report["config"]
            project = cfg["project"]
            responses = {d: service.result(case["case_id"], d) for d in core.DOFS}
            folder = Path(destination) / key
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "inputs").mkdir(exist_ok=True)
            (folder / "rao").mkdir(exist_ok=True)
            save_json(folder / "config.json", cfg)
            for ext in ("hst", "rdf", "mcn", "rao"):
                source = directory / (project + "." + ext)
                shutil.copyfile(source, folder / "inputs" / source.name)
            for dof in core.DOFS:
                shutil.copyfile(
                    directory / "rao" / (dof + ".rao"), folder / "rao" / (dof + ".rao")
                )
            motions = {
                d: {
                    k: a[k] for k in ("omega", "headings", "unit", "amplitude", "phase")
                }
                for d, a in responses.items()
            }
            save_json(folder / "motions.json", motions)
            reference = report["reference_model"]
            summary = dict(
                schema_version=1,
                form_id=key,
                label=FORMS[key]["label"],
                source_case_id=case["case_id"],
                backend=dict(
                    name="HydroStar",
                    version="8.2.0",
                    automation_version=report["version"],
                ),
                publication_version=__version__,
                computed_at_utc=report["updated_at"],
                frequency_count=len(responses["heave"]["omega"]),
                heading_count=len(responses["heave"]["headings"]),
                quality_gates=report["quality_gates"],
                hydrostatics=report["hydrostatics"],
                mesh=report["hslec"],
                topology=report["hschk"],
                solver_mechanics=report["solver_mechanics"],
                mechanics={
                    k: report["mechanics"][k]
                    for k in (
                        "mass_kg",
                        "cog_m",
                        "gyradius_m",
                        "total_displacement_m3",
                        "total_cb_m",
                        "equilibrium_relative_error",
                    )
                },
                reference_model=reference,
                steps=[
                    {k: s[k] for k in ("module", "ok", "rc", "seconds")}
                    for s in report["steps"]
                ],
                provenance=dict(
                    geometry_origin="project_parameter_generator",
                    external_mesh_files=[],
                    parameter_sha256=report["geometry_provenance"]["parameter_sha256"],
                    original_generator_sha256=report["geometry_provenance"][
                        "generator_sha256"
                    ],
                    additional_generator_sources=report["geometry_provenance"].get(
                        "additional_generator_sources", {}
                    ),
                ),
            )
            summary["files"] = {
                p.relative_to(folder).as_posix(): file_hash(p)
                for p in sorted(folder.rglob("*"))
                if p.is_file() and p.name != "summary.json"
            }
            save_json(folder / "summary.json", summary)
            vertices, faces = whole_mesh(folder / "inputs" / (project + ".hst"))
            model = dict(
                key=key,
                label=LABELS[key],
                config=cfg,
                summary=summary,
                vertices=[[round(v, 6) for v in p] for p in vertices],
                faces=faces,
                responses=motions,
            )
            models.append(model)
            plot_rao(
                motions,
                Path(assets) / (key + "_rao.png"),
                title=LABELS[key] + " | Native six-DOF RAO",
            )
            records.append(
                dict(
                    form_id=key,
                    path=key + "/summary.json",
                    summary_sha256=file_hash(folder / "summary.json"),
                )
            )
        finally:
            service.close()
    plot_geometry(models, Path(assets) / "reference-geometry.png")
    save_json(
        Path(destination) / "index.json",
        dict(schema_version=1, cases=records, case_count=len(records)),
    )
    save_json(ROOT / "docs/data/showcase.json", dict(schema_version=1, cases=models))
    save_json(
        ROOT / "docs/references/sources.json",
        dict(sources=SOURCES, verified_date="2026-10-27"),
    )
    return models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--study",
        type=Path,
        default=ROOT / "output/validation/reference_form_study.json",
    )
    parser.add_argument("--destination", type=Path, default=ROOT / "examples/results")
    parser.add_argument("--assets", type=Path, default=ROOT / "docs/assets")
    args = parser.parse_args()
    export(args.study, args.destination, args.assets)
    print(f"Exported 3 verified native cases to {args.destination}")


if __name__ == "__main__":
    raise SystemExit(main())
