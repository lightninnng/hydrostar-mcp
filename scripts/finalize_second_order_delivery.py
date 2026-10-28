"""Record completed visual review and finalize the native second-order delivery."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.workflow import file_hash, save_json
from scripts.export_second_order import PACKAGE, read, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Record actual review of the final mesh, PNGs and rendered PDFs",
    )
    args = parser.parse_args()
    require(
        args.reviewed,
        "Actual visual review must be completed before recording this stage",
    )
    for package in (PACKAGE, PACKAGE / "sensitivity/coarse"):
        state = read(package / "execution.json")
        items = []
        purposes = {
            "platform2.hst": "Actual wet and exterior integration mesh; metres; symmetry=1",
            "platform2.rdf": "First-order and difference frequencies; rad/s; heading degrees; depth metres",
            "platform2.mcn": "Fixed mass kg, CG metres, inertia and restoring/damping in native units",
            "drift.dft": "Mean drift, near-field and far-field formulations",
            "full.qtf": "Full difference-frequency QTF; near-field; QUADPACK; NBES=30",
            "results.rao": "Extraction instructions for six motions, drift and complex QTFs",
        }
        for name, expected in state["input_hashes"].items():
            path = package / "inputs" / name
            require(
                file_hash(path) == expected, "Native delivery input changed: " + name
            )
            items.append(
                dict(
                    path=path.relative_to(package).as_posix(),
                    purpose=purposes[name],
                    status="executed_and_verified",
                    sha256=expected,
                )
            )
        for name, expected in state["result_files"].items():
            path = package / "rao" / name
            require(
                file_hash(path) == expected, "Native delivery output changed: " + name
            )
            items.append(
                dict(
                    path=path.relative_to(package).as_posix(),
                    purpose="Native complex load or motion output; see file heading and verification scope",
                    status="generated_and_verified",
                    sha256=expected,
                )
            )
        delivery = dict(
            schema="hydrostar-native-second-order-delivery-1",
            status="verified_with_component_limitations",
            files=items,
            working_directory="Copy inputs/* into a new working directory; native databases and rao/ are generated there",
            execution_order=[
                dict(
                    module=s["module"],
                    arguments=[s["input"], "platform2"],
                    mpi_processes=2
                    if s["module"] in ("hsrdf", "hsdft", "hsamg", "hsqtf")
                    else 1,
                    status="verified",
                )
                for s in state["steps"]
            ],
            budget=dict(
                default_limit=3000,
                full_equivalent_total=state["mesh"][
                    "full_equivalent_total_including_exterior"
                ],
                includes=[
                    "wet body",
                    "waterplane",
                    "exterior integration surface",
                    "symmetry expansion",
                ],
            ),
            mesh_acceptance_limits=dict(
                minimum_quad_fraction=0.8,
                min_corner_deg=10,
                max_corner_deg=170,
                max_edge_ratio=8,
                max_neighbor_size_ratio=2,
                max_overlap_m2=1e-6,
                max_uncovered_or_extra_m2=1e-6,
                waterline_conformity="Every native wet waterline edge shares node IDs and a complete integration edge",
                internal_seams=0,
                nonconvex=0,
                integration_plane_z_m=0,
            ),
            units=dict(
                coordinates="m",
                frequency="rad/s",
                headings="deg",
                force_qtf="N/m^2",
                moment_qtf="N m/m^2",
                translation_rao="m/m",
                rotation_rao="deg/m",
            ),
            complex_convention="Native CPLXTYPE 0: real, imaginary; omega2=omega1+difference",
            spc=dict(
                status="not_applicable",
                reason="Regular-wave mean drift and difference-frequency loads; spectral statistics require a separate sea-state input",
            ),
            databases=dict(
                status="regenerable_from_delivered_inputs",
                paths=["bin/", "hdf/"],
                native_mesh_check="geometry/native-surface-check.json",
            ),
            acceptance="verification.json at the main package; yaw moment requires further own-scale convergence before engineering load use",
        )
        save_json(package / "delivery.json", delivery)
    mesh = read(PACKAGE / "mesh-view.json")
    mesh["visual_review"] = "verified"
    mesh["review_notes"] = (
        "Actual native connectivity visible; regular outer annuli, compatible near-body transitions, complete titles, units and geometry gain"
    )
    save_json(PACKAGE / "mesh-view.json", mesh)
    record = read(PACKAGE / "verification.json")
    record["visual_review"] = "verified"
    record["review_notes"] = (
        "All four scientific PNGs and rendered vector PDFs inspected; six component titles, frequency axes, units, legends and native sample points retained"
    )
    record["files"] = {
        p.relative_to(PACKAGE).as_posix(): file_hash(p)
        for p in PACKAGE.rglob("*")
        if p.is_file() and p.name != "verification.json"
    }
    save_json(PACKAGE / "verification.json", record)
    print("Finalized the native second-order delivery with component acceptance scope")


if __name__ == "__main__":
    main()
