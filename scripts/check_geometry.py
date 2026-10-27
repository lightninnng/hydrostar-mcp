"""Verify the portable general-geometry examples without a native solver."""

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__, core
from hydrostar_mcp.geometry_workflow import verify_bundle
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import file_hash


def check_geometry():
    def require(value, reason):
        if not value:
            raise ValueError(reason)

    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    base = ROOT / "examples/geometry"
    index = read(base / "index.json")
    require(
        index == read(ROOT / "docs/data/geometry.json"),
        "Geometry gallery data mismatch",
    )
    require(index["publication_version"] == __version__, "Geometry publication version")
    require(
        {c["key"] for c in index["cases"]}
        == {"lofted_vessel", "moonpool_caisson", "cad_spar"},
        "Geometry cases",
    )
    values = 0
    coarse = base / "sensitivity/cad_spar_coarse"
    coarse_native = read(coarse / "verification.json")
    coarse_geometry = read(coarse / "geometry/geometry-report.json")
    entries = index["cases"] + [
        dict(
            key="sensitivity/cad_spar_coarse",
            summary_sha256=file_hash(coarse / "verification.json"),
            volume_m3=coarse_native["hydrostatics"]["volume"],
            panels=coarse_geometry["quality"]["panels"],
        )
    ]
    sensitivity_values = 0
    for entry in entries:
        folder = base / entry["key"]
        report = verify_bundle(
            folder / "geometry/geometry-report.json", folder / "geometry/model.hst"
        )
        native = read(folder / "verification.json")
        require(
            file_hash(folder / "verification.json") == entry["summary_sha256"],
            "Geometry native summary hash",
        )
        require(
            set(native["quality_gates"].values()) == {"passed"}
            and len(native["quality_gates"]) == 6,
            "Geometry native gates",
        )
        require(
            not native["engineering_acceptance"]["ready"],
            "Purpose acceptance classification",
        )
        require(
            native["hschk"]["pass"]
            and all(v == 0 for k, v in native["hschk"].items() if k != "pass"),
            "Native topology",
        )
        actual = {
            p.relative_to(folder).as_posix()
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        }
        require(actual == set(native["files"]), "Geometry unindexed files")
        for name, expected in native["files"].items():
            path = (folder / name).resolve()
            require(
                path.is_relative_to(folder.resolve()) and file_hash(path) == expected,
                "Geometry file hash: " + name,
            )
        cfg = CaseConfig.model_validate(read(folder / "config.json"))
        require(
            all(s["ok"] and s["rc"] == 0 for s in native["steps"]),
            "Geometry native module execution",
        )
        delivery = read(folder / "delivery.json")
        expected_inputs = {
            f"inputs/{cfg.project}.{extension}"
            for extension in ("hst", "rdf", "mcn", "rao")
        }
        require(
            set(delivery["input_files"]) == expected_inputs, "Native delivery inputs"
        )
        require(
            set(delivery["output_files"]) == {f"rao/{dof}.rao" for dof in core.DOFS},
            "Native delivery outputs",
        )
        for name, record in {
            **delivery["input_files"],
            **delivery["output_files"],
        }.items():
            require(
                record["status"] == "validated"
                and record["sha256"] == file_hash(folder / name),
                "Native delivery state/hash: " + name,
            )
        total = (
            native["hslec"]["hull_panels"] + native["hslec"]["waterplane_panels"]
        ) * 2 ** native["hslec"]["symmetry"]
        require(
            native["resource_policy"]["default_full_equivalent_total_budget"] == 3000
            and native["resource_policy"]["full_equivalent_total"] == total
            and delivery["resource_policy"] == native["resource_policy"],
            "Full-equivalent total panel budget record",
        )
        require(
            file_hash(folder / "inputs" / (cfg.project + ".hst"))
            == file_hash(folder / "geometry/model.hst"),
            "Solved mesh differs from accepted source",
        )
        hyd = core.hydrostatics(folder / "geometry/model.hst")
        require(
            math.isclose(hyd["volume"], entry["volume_m3"], rel_tol=1e-10),
            "Geometry mesh volume",
        )
        require(
            report["fidelity"]["cad_volume_relative_error"]
            <= report["request"]["volume_tolerance_relative"],
            "CAD volume gate",
        )
        require(
            report["fidelity"]["cad_cb_distance_m"]
            <= report["fidelity"]["cad_cb_tolerance_m"],
            "CAD buoyancy centre gate",
        )
        require(
            set(report["generator_sources"])
            >= {
                "geometry_worker.py",
                "geometry_kernel.py",
                "geometry_sources.py",
                "surface_checks.py",
            },
            "Geometry generation provenance",
        )
        require(
            {"panel_checks.py", "structured_panels.py"}
            <= set(report["generator_sources"]),
            "Structured meshing provenance",
        )
        panel = report["quality"]["panel_quality"]
        require(
            panel["passed"]
            and panel["quad_fraction"] >= report["request"]["minimum_quad_fraction"]
            and panel["quadrilaterals"] + panel["triangles"]
            == entry["panels"]
            == native["hslec"]["hull_panels"],
            "Native panel shape/layout gates",
        )
        motions = read(folder / "motions.json")
        for dof in core.DOFS:
            raw = core.read_rao(folder / "rao" / (dof + ".rao"))
            require(
                motions[dof] == {k: raw[k] for k in motions[dof]},
                "Geometry native/JSON arrays",
            )
            for field in ("amplitude", "phase"):
                require(
                    all(math.isfinite(v) for row in raw[field] for v in row),
                    "Geometry finite responses",
                )
                if folder == coarse:
                    sensitivity_values += sum(map(len, raw[field]))
                else:
                    values += sum(map(len, raw[field]))
    for name, expected in index["figures"].items():
        require(
            file_hash(ROOT / "docs/assets" / name) == expected, "Geometry figure hash"
        )
    comparison_path = ROOT / index["mesh_comparison"]["path"]
    require(
        file_hash(comparison_path) == index["mesh_comparison"]["sha256"],
        "Mesh comparison hash",
    )
    comparison = read(comparison_path)
    from scripts.export_mesh_comparison import comparison_data

    require(
        {k: v for k, v in comparison.items() if k != "figures"} == comparison_data(),
        "Fixed-physics mesh comparison and metrics",
    )
    return dict(
        general_geometry_native_cases=3,
        general_geometry_response_values=values,
        sensitivity_native_cases=1,
        sensitivity_response_values=sensitivity_values,
    )


if __name__ == "__main__":
    print(json.dumps(check_geometry(), indent=2))
