"""Original multi-source geometry cases and native single-body validation runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.geometry_sources import GeometryRequest
from hydrostar_mcp.geometry_workflow import GeometryService, verify_bundle
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import CaseService, file_hash, save_json

SOURCE = ROOT / "examples/geometry/sources"
STUDY = ROOT / "output/validation/geometry_source_study.json"
RECIPES = {
    "lofted_vessel": dict(
        file="vessel-stations.csv",
        units="mm",
        mesh_size_m=4.5,
        section_curve="spline",
        longitudinal_ruled=False,
        spline_seam="lowest_z",
        panel_layout="station_bands",
        structured_axis="x",
        curvature_samples=48,
        longitudinal_cells=192,
        max_panels=12000,
        minimum_quad_fraction=0.95,
        panel_quality=dict(
            max_edge_ratio=5,
            min_corner_deg=20,
            max_corner_deg=155,
            max_warpage_deg=5,
            max_neighbor_size_ratio=1.8,
        ),
        depth=80.0,
    ),
    "moonpool_caisson": dict(
        file="moonpool-sections.json",
        units="m",
        mesh_size_m=4.0,
        depth=100.0,
        panel_layout="polygon_blocks",
        max_panels=12000,
        structured_axis="z",
        minimum_quad_fraction=1.0,
        panel_quality=dict(
            max_edge_ratio=5,
            min_corner_deg=15,
            max_corner_deg=165,
            max_warpage_deg=2,
            max_neighbor_size_ratio=1.8,
        ),
    ),
    "cad_spar": dict(
        file="stepped-spar.step",
        units="file",
        mesh_size_m=0.7,
        curvature_samples=96,
        panel_layout="ring_bands",
        structured_axis="z",
        axis_center_xy_m=[0.0, 0.0],
        minimum_quad_fraction=1.0,
        max_panels=12000,
        panel_quality=dict(
            max_edge_ratio=4,
            min_corner_deg=20,
            max_corner_deg=150,
            max_warpage_deg=2,
            max_neighbor_size_ratio=1.8,
        ),
        depth=150.0,
    ),
}


def make_sources():
    names = (
        "vessel-stations.csv",
        "moonpool-sections.json",
        "stepped-spar.step",
        "polygon-stations.dxf",
        "source-notes.json",
    )
    existing = [name for name in names if (SOURCE / name).exists()]
    if existing:
        if len(existing) != len(names):
            raise FileExistsError(
                "Source set is incomplete; construct a new study in an empty source directory"
            )
        print("Retaining the complete original source set", flush=True)
        return
    import gmsh
    import ezdxf

    SOURCE.mkdir(parents=True, exist_ok=True)
    with (SOURCE / "vessel-stations.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["station", "u", "v"])
        for x, fullness, draft in [
            (-60, 0.12, 3.0),
            (-54, 0.35, 5.8),
            (-42, 0.72, 7.5),
            (-24, 0.98, 8.0),
            (0, 1.0, 8.0),
            (24, 0.95, 7.8),
            (43, 0.64, 6.5),
            (54, 0.26, 4.2),
            (60, 0.045, 2.0),
        ]:
            for i in range(16):
                angle = i * math.tau / 16
                y = (
                    11
                    * fullness
                    * math.copysign(abs(math.cos(angle)) ** 0.75, math.cos(angle))
                )
                z = (4 - draft) / 2 + (4 + draft) / 2 * math.sin(angle)
                writer.writerow([x * 1000, y * 1000, z * 1000])
    outer = [
        [-35.0, -10.0],
        [-25.0, -20.0],
        [25.0, -20.0],
        [35.0, -10.0],
        [35.0, 10.0],
        [25.0, 20.0],
        [-25.0, 20.0],
        [-35.0, 10.0],
    ]
    inner = [[-10.0, -6.0], [10.0, -6.0], [10.0, 6.0], [-10.0, 6.0]]
    save_json(
        SOURCE / "moonpool-sections.json",
        dict(
            schema_version=1,
            solids=[
                dict(
                    name="chamfered_hull",
                    axis="z",
                    profiles=[
                        dict(position=-10.0, points=outer),
                        dict(position=5.0, points=outer),
                    ],
                ),
                dict(
                    name="through_moonpool",
                    operation="cut",
                    axis="z",
                    profiles=[
                        dict(position=-12.0, points=inner),
                        dict(position=7.0, points=inner),
                    ],
                ),
            ],
        ),
    )
    # Source STEP is deliberately authored in millimetres, matching its declared unit.
    gmsh.initialize([], readConfigFiles=False, run=False, interruptible=False)
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
    gmsh.model.add("original_spar")
    occ = gmsh.model.occ
    try:
        wires = []
        for z, rx, ry in [
            (-20, 6.5, 6.0),
            (-16, 6.5, 6.0),
            (-12, 5.0, 4.8),
            (-5, 4.2, 4.0),
            (2, 4.5, 4.2),
            (10, 4.5, 4.2),
        ]:
            tags = [
                occ.addPoint(
                    1000 * rx * math.cos(i * math.tau / 16),
                    1000 * ry * math.sin(i * math.tau / 16),
                    1000 * z,
                )
                for i in range(16)
            ]
            wires.append(
                occ.addWire([occ.addSpline(tags + tags[:1])], checkClosed=True)
            )
        body = occ.addThruSections(
            wires, makeSolid=True, makeRuled=False, maxDegree=3, smoothing=False
        )
        plate = occ.addCylinder(0, 0, -19000, 0, 0, 800, 9500)
        made, _ = occ.fuse(body, [(3, plate)], removeObject=True, removeTool=True)
        occ.synchronize()
        if len(made) != 1 or made[0][0] != 3:
            raise ValueError(
                "Original STEP source should contain one displacement solid"
            )
        gmsh.write(str(SOURCE / "stepped-spar.step"))
    finally:
        gmsh.finalize()
    # A DXF profile stack exercises named layers and exact preservation of polygon corners.
    doc = ezdxf.new("R2010")
    doc.units = 4
    for layer in ("BOTTOM", "TOP"):
        doc.layers.add(layer)
        doc.modelspace().add_lwpolyline(
            [[x * 1000, y * 1000] for x, y in outer],
            close=True,
            dxfattribs={"layer": layer},
        )
    doc.saveas(SOURCE / "polygon-stations.dxf")
    save_json(
        SOURCE / "source-notes.json",
        dict(
            origin="original project geometry, authored from the scalars in geometry_source_study.py",
            external_meshes=[],
            vessel="Closed station profiles in millimetres; interpolating curved sections and smooth longitudinal interpolation; curve seams placed on the keel side; finite narrow end caps.",
            moonpool="Chamfered polygon displacement hull with a through opening; constructive subtraction.",
            spar="Millimetre STEP solid with curved, varying elliptical sections and a connected finite-thickness heave plate.",
            physics="Demonstration displacement envelopes; explicit loading and damping assumptions are recorded per native case.",
        ),
    )


def build_case(key, folder):
    recipe = RECIPES[key].copy()
    recipe.pop("depth")
    filename = recipe.pop("file")
    request = GeometryRequest(
        project=key,
        path=(SOURCE / filename).relative_to(ROOT).as_posix(),
        source_note="Original project source geometry from geometry_source_study.py. Curved vessel: closed interpolating sections, smooth longitudinal loft, keel-side spline seam and finite narrow end caps. CAD envelopes and loading are demonstrator assumptions.",
        **recipe,
    )
    service = GeometryService(ROOT / "output/validation/geometry_runs", ROOT)
    result = service.build(request)
    print(key + ": " + result["status"], flush=True)
    if result["status"] != "geometry_accepted":
        save_json(ROOT / "output/validation" / (key + "-geometry-failure.json"), result)
        raise ValueError(json.dumps(result.get("error") or result.get("quality")))
    # Preserve the accepted data bundle byte for byte before preparing a native case.
    target = folder / "geometry"
    if target.exists():
        raise ValueError(
            "Geometry bundle already exists; review the study record before replacing it"
        )
    shutil.copytree(
        result["directory"],
        target,
        ignore=shutil.ignore_patterns("kernel.log", "cache"),
    )
    verify_bundle(target / "geometry-report.json", target / "model.hst")
    return result


def native_config(key, folder):
    existing = folder / "config.json"
    if existing.is_file():
        cfg = json.loads(existing.read_text(encoding="utf-8"))
        cfg["geometry"]["path"] = (
            (folder / "geometry/model.hst").relative_to(ROOT).as_posix()
        )
        cfg["geometry"]["source_manifest"] = (
            (folder / "geometry/geometry-report.json").relative_to(ROOT).as_posix()
        )
        return CaseConfig.model_validate(cfg)
    report = json.loads(
        (folder / "geometry/geometry-report.json").read_text(encoding="utf-8")
    )
    hyd = report["hydrostatics"]
    surface = json.loads((folder / "geometry/surface.json").read_text(encoding="utf-8"))
    span = [
        max(p[k] for p in surface["vertices"]) - min(p[k] for p in surface["vertices"])
        for k in range(3)
    ]
    radii = [
        math.sqrt((span[1] ** 2 + span[2] ** 2) / 12),
        math.sqrt((span[0] ** 2 + span[2] ** 2) / 12),
        math.sqrt((span[0] ** 2 + span[1] ** 2) / 12),
        0.0,
        0.0,
        0.0,
    ]
    return CaseConfig.model_validate(
        dict(
            project=key,
            object_type="ship" if key == "lofted_vessel" else "floating_structure",
            geometry=dict(
                type="hst",
                path=(folder / "geometry/model.hst").relative_to(ROOT).as_posix(),
                source_manifest=(folder / "geometry/geometry-report.json")
                .relative_to(ROOT)
                .as_posix(),
                expected_volume_m3=report["reference"]["cad_volume_m3"],
                volume_relative_tolerance=0.005,
            ),
            environment=dict(
                depth=RECIPES[key]["depth"],
                frequency=dict(min=0.2, max=0.8, step=0.1),
                headings=dict(min=0.0, max=180.0, step=60.0),
            ),
            mechanics=dict(
                model="explicit",
                mass_kg=1025 * hyd["volume"],
                cog_m=[hyd["cb"][0], hyd["cb"][1], hyd["cb"][2] - 1.0],
                gyradius_m=radii,
                roll_damping_pct=5.0,
                source_note="Course/simplified-analysis assumption: mass balanced to the accepted mesh displacement, CG 1 m below integrated CB, bounding-envelope gyradii and 5% additional roll damping; zero speed and static external preload.",
            ),
        )
    )


def execute(key, folder, study):
    cfg = native_config(key, folder)
    service = CaseService(ROOT / "output/validation/general_geometry_native", ROOT)
    try:
        report = service.prepare(cfg)
        if report["status"] != "prepared":
            save_json(
                ROOT / "output/validation" / (key + "-native-failure.json"), report
            )
            raise ValueError(key + ": native preparation " + report["status"])
        service.start(report["case_id"])
        while True:
            report = service.status(report["case_id"])
            if report["status"] not in {"queued", "running"}:
                break
            time.sleep(0.5)
        if report["status"] != "completed" or set(report["quality_gates"].values()) != {
            "passed"
        }:
            save_json(
                ROOT / "output/validation" / (key + "-native-failure.json"), report
            )
            raise ValueError(key + ": native " + report["status"])
        study["cases"][key] = dict(
            case_id=report["case_id"],
            directory=report["directory"],
            status=report["status"],
            quality_gates=report["quality_gates"],
        )
        save_json(STUDY, study)
        save_json(folder / "config.json", cfg.model_dump())
        (folder / "inputs").mkdir(exist_ok=True)
        (folder / "rao").mkdir(exist_ok=True)
        directory = Path(report["directory"])
        for extension in ("hst", "rdf", "mcn", "rao"):
            shutil.copyfile(
                directory / (cfg.project + "." + extension),
                folder / "inputs" / (cfg.project + "." + extension),
            )
        motions = {}
        for dof in ("surge", "sway", "heave", "roll", "pitch", "yaw"):
            shutil.copyfile(
                directory / "rao" / (dof + ".rao"), folder / "rao" / (dof + ".rao")
            )
            data = service.result(report["case_id"], dof)
            motions[dof] = {
                k: data[k] for k in ("omega", "headings", "amplitude", "phase", "unit")
            }
        save_json(folder / "motions.json", motions)
        summary = dict(
            source_case_id=report["case_id"],
            quality_gates=report["quality_gates"],
            hydrostatics=report["hydrostatics"],
            hslec=report["hslec"],
            hschk=report["hschk"],
            solver_mechanics=report["solver_mechanics"],
            geometry_source_validation=report["geometry_source_validation"],
            steps=[
                {k: s[k] for k in ("module", "ok", "rc", "seconds")}
                for s in report["steps"]
            ],
            engineering_acceptance=dict(
                ready=False,
                scope="Own geometry and simplified rigid-body assumptions; target-specific validation remains an evidence requirement.",
            ),
        )
        summary["files"] = {
            p.relative_to(folder).as_posix(): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        }
        save_json(folder / "verification.json", summary)
        print(key + ": native six gates passed", flush=True)
    finally:
        service.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--form", choices=list(RECIPES))
    args = parser.parse_args()
    if args.sources:
        make_sources()
    study = (
        json.loads(STUDY.read_text(encoding="utf-8"))
        if STUDY.is_file()
        else dict(cases={})
    )
    for key in [args.form] if args.form else RECIPES:
        folder = ROOT / "examples/geometry" / key
        folder.mkdir(parents=True, exist_ok=True)
        if args.build:
            manifest = folder / "geometry/geometry-report.json"
            if manifest.is_file():
                accepted = verify_bundle(manifest, folder / "geometry/model.hst")
                source = SOURCE / RECIPES[key]["file"]
                snapshot = "source" + source.suffix.lower()
                if file_hash(source) != accepted["files"][snapshot]:
                    raise ValueError(
                        "Source differs from the accepted bundle; create a separate geometry study"
                    )
                controls = {
                    k: v for k, v in RECIPES[key].items() if k not in {"file", "depth"}
                }
                actual = GeometryRequest.model_validate(
                    accepted["request"]
                ).model_dump()
                if any(actual[k] != value for k, value in controls.items()):
                    raise ValueError(
                        "Mesh recipe differs from the accepted bundle; build the changed study in a separate directory"
                    )
                print(key + ": reusing verified geometry bundle", flush=True)
            else:
                build_case(key, folder)
        if args.run:
            execute(key, folder, study)


if __name__ == "__main__":
    main()
