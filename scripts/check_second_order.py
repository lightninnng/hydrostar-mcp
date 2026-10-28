"""Verify the portable native drift/QTF package without running HydroStar."""

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.second_order import read_integration_mesh
from hydrostar_mcp.workflow import file_hash
from scripts.export_second_order import (
    COMPONENTS,
    PACKAGE,
    compare_surfaces,
    read,
    require,
    review,
)
from scripts.second_order_ring_surface import waterlines
from scripts.second_order_surface import shape_quality


def check_surface(package, evaluated):
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union

    hst = package / "inputs/platform2.hst"
    geometry = read_integration_mesh(hst)
    report = evaluated["surface"]
    nodes = {i: point for i, point in enumerate(geometry["vertices"])}
    faces = geometry["faces"]
    polygons = [Polygon([nodes[i][:2] for i in cell]) for cell in faces]
    require(
        all(p.is_valid and p.area > 0 for p in polygons),
        "Actual HST integration polygons invalid",
    )
    union = unary_union(polygons)
    outside = Polygon(
        [
            (110 * math.cos(i * math.pi / 36), 110 * math.sin(i * math.pi / 36))
            for i in range(37)
        ]
    )
    domain = outside.difference(unary_union(waterlines(hst)))
    require(
        abs(sum(p.area for p in polygons) - union.area) < 1e-6,
        "Actual HST surface overlaps",
    )
    require(
        domain.symmetric_difference(union).area < 1e-6,
        "Actual HST exterior coverage incomplete",
    )
    owners = {}
    for index, cell in enumerate(faces):
        for a, b in zip(cell, cell[1:] + cell[:1]):
            owners.setdefault(tuple(sorted((a, b))), []).append(index)
        xy = [nodes[i] for i in cell]
        signed = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(xy, xy[1:] + xy[:1]))
        require(signed < 0, "Actual integration normal must point down")
    require(
        all(len(x) <= 2 for x in owners.values()), "Nonmanifold actual integration edge"
    )
    require(
        all(
            LineString([nodes[i][:2] for i in edge])
            .difference(domain.boundary.buffer(1e-6))
            .length
            < 1e-6
            for edge, cells in owners.items()
            if len(cells) == 1
        ),
        "Actual integration internal seam",
    )
    quality = [shape_quality(nodes, cell) for cell in faces]
    ratios = [
        math.sqrt(
            max(quality[a]["area"], quality[b]["area"])
            / min(quality[a]["area"], quality[b]["area"])
        )
        for cells in owners.values()
        if len(cells) == 2
        for a, b in [cells]
    ]
    require(
        min(q["min_angle"] for q in quality) >= 10
        and max(q["max_angle"] for q in quality) <= 170
        and max(q["edge_ratio"] for q in quality) <= 8
        and max(ratios) <= 2
        and all(q["convex"] for q in quality),
        "Actual HST integration shape gate",
    )
    native = read(package / "geometry/native-surface-check.json")
    require(
        native["status"] == "verified"
        and native["source_hst_sha256"] == file_hash(hst),
        "Native integration check source",
    )
    require(
        native["half_domain_panels"] == len(faces) == report["half_domain_panels"],
        "Native integration check count",
    )
    require(
        abs(native["area_m2"] - domain.area) < 1e-6
        and abs(native["overlap_m2"]) < 1e-6
        and native["downward_normal_max_error"] < 1e-9,
        "Native integration check area or normal",
    )
    require(
        report["generator_script_sha256"]
        == file_hash(ROOT / "scripts/second_order_ring_surface.py")
        and report["quality_utility_sha256"]
        == file_hash(ROOT / "scripts/second_order_surface.py"),
        "Integration generator source changed",
    )
    require(
        report["structured_annular_quadrilaterals_full"] == 648
        and report["angular_divisions_full"] == 72,
        "Structured annular topology differs",
    )


def check_second_order():
    main = review(PACKAGE, portable=True)
    coarse_package = PACKAGE / "sensitivity/coarse"
    coarse = review(coarse_package, portable=True)
    for package, evaluated in ((PACKAGE, main), (coarse_package, coarse)):
        check_surface(package, evaluated)
    record = read(PACKAGE / "verification.json")
    require(
        record["status"] == "verified_with_component_limitations",
        "Second-order component scope missing",
    )
    require(
        record["visual_review"] == "verified", "Second-order figures need visual review"
    )
    require(
        record["export_script_sha256"]
        == file_hash(ROOT / "scripts/export_second_order.py"),
        "Second-order exporter changed",
    )
    sensitivity, _, _ = compare_surfaces(main, coarse)
    for component in COMPONENTS:
        for key, value in sensitivity[component].items():
            require(
                math.isclose(
                    record["surface_sensitivity"][component][key],
                    value,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                ),
                "Second-order sensitivity data changed",
            )
        require(
            record["component_acceptance"][component]
            == (
                "convergence_required"
                if component == "mz"
                else "passed_example_sensitivity_gate"
            ),
            "Second-order acceptance scope changed",
        )
    require(
        record["main_total_panels"]
        == main["state"]["mesh"]["full_equivalent_total_including_exterior"]
        <= 3000,
        "Second-order main budget",
    )
    require(
        record["comparison_total_panels"]
        == coarse["state"]["mesh"]["full_equivalent_total_including_exterior"]
        <= 3000,
        "Second-order comparison budget",
    )
    for name, expected in record["files"].items():
        require(
            file_hash(PACKAGE / name) == expected,
            "Second-order package changed: " + name,
        )
    for name, item in record["figures"].items():
        require(
            file_hash(ROOT / name) == item["sha256"],
            "Second-order figure changed: " + name,
        )
    mesh = read(PACKAGE / "mesh-view.json")
    require(
        mesh["visual_review"] == "verified"
        and mesh["source_sha256"] == file_hash(PACKAGE / "inputs/platform2.hst")
        and mesh["output_sha256"] == file_hash(ROOT / mesh["output"])
        and mesh["script_sha256"]
        == file_hash(ROOT / "scripts/render_second_order_mesh.py"),
        "Second-order native mesh view source",
    )
    data = read(PACKAGE / "qtf.json")
    require(
        data["valid_pair_mask"] == main["mask"] and data["valid_pair_count"] == 36,
        "Published QTF valid pair mask",
    )
    count = 0
    for name in COMPONENTS:
        for i, row in enumerate(main["mask"]):
            for j, ok in enumerate(row):
                expected = main["loads"][name]["values"][0][i][j] if ok else None
                require(
                    data["loads"][name][i][j] == expected,
                    "Published complex QTF differs from raw native output",
                )
                count += int(ok)
    delivery = read(PACKAGE / "delivery.json")
    require(
        delivery["status"] == "verified_with_component_limitations"
        and delivery["spc"]["status"] == "not_applicable",
        "Second-order native delivery scope",
    )
    from scripts.animate_second_order import check_animations

    return dict(
        second_order_studies=2,
        valid_second_order_complex_coefficients=count,
        structured_exterior_total_panels=record["main_total_panels"],
        yaw_component="convergence_required",
        **check_animations(),
    )


if __name__ == "__main__":
    print(json.dumps(check_second_order(), indent=2))
