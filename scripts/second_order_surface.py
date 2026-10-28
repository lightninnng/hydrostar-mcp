"""Conforming exterior integration mesh for the platform's multiple waterlines."""

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.workflow import file_hash, save_json


def shape_quality(nodes, cell):
    from shapely.geometry import Polygon

    points = [nodes[i] for i in cell]
    lengths = [
        math.dist(p, points[(j + 1) % len(points)]) for j, p in enumerate(points)
    ]
    angles = []
    for i, point in enumerate(points):
        a = [v - w for v, w in zip(points[i - 1], point)]
        b = [v - w for v, w in zip(points[(i + 1) % len(points)], point)]
        angles.append(
            math.degrees(
                math.acos(
                    max(
                        -1.0,
                        min(
                            1.0,
                            sum(x * y for x, y in zip(a, b))
                            / math.dist(a, [0, 0, 0])
                            / math.dist(b, [0, 0, 0]),
                        ),
                    )
                )
            )
        )
    polygon = Polygon([p[:2] for p in points])
    return dict(
        min_angle=min(angles),
        max_angle=max(angles),
        edge_ratio=max(lengths) / min(lengths),
        area=polygon.area,
        convex=abs(polygon.convex_hull.area - polygon.area) < 1e-9,
    )


def improve_transitions(nodes, panels):
    """Reselect a tri/quad diagonal to remove thin three-point arc caps."""
    from shapely.geometry import Polygon

    coordinate_ids = {
        tuple(round(v, 10) for v in xyz[:2]): tag for tag, xyz in nodes.items()
    }
    repairs = []
    for index in range(len(panels)):
        cell = panels[index]
        if len(cell) != 3:
            continue
        owners = {}
        for i, face in enumerate(panels):
            for a, b in zip(face, face[1:] + face[:1]):
                owners.setdefault(tuple(sorted((a, b))), []).append(i)
        neighbors = {
            other
            for a, b in zip(cell, cell[1:] + cell[:1])
            for other in owners[tuple(sorted((a, b)))]
            if other != index and len(panels[other]) == 4
        }
        current_quality = shape_quality(nodes, cell)
        if current_quality["max_angle"] <= 170 and all(
            math.sqrt(
                max(
                    current_quality["area"], shape_quality(nodes, panels[other])["area"]
                )
                / min(
                    current_quality["area"], shape_quality(nodes, panels[other])["area"]
                )
            )
            <= 2
            for other in neighbors
        ):
            continue
        candidates = []
        for other in neighbors:
            merged = Polygon([nodes[i][:2] for i in cell]).union(
                Polygon([nodes[i][:2] for i in panels[other]])
            )
            if not isinstance(merged, Polygon) or merged.interiors:
                continue
            boundary = list(merged.exterior.coords)[:-1]
            if len(boundary) != 5:
                continue
            ids = [coordinate_ids[tuple(round(v, 10) for v in p)] for p in boundary]
            for offset in range(5):
                rotated = ids[offset:] + ids[:offset]
                tri, quad = rotated[:3], [rotated[i] for i in (0, 2, 3, 4)]
                qualities = [shape_quality(nodes, p) for p in (tri, quad)]
                if any(
                    not q["convex"]
                    or q["min_angle"] < 10
                    or q["max_angle"] > 170
                    or q["edge_ratio"] > 8
                    for q in qualities
                ):
                    continue
                if (
                    math.sqrt(
                        max(q["area"] for q in qualities)
                        / min(q["area"] for q in qualities)
                    )
                    > 2
                ):
                    continue
                candidates.append(
                    (min(q["min_angle"] for q in qualities), other, tri, quad)
                )
        if not candidates:
            continue
        _, other, tri, quad = max(candidates)
        panels[index], panels[other] = tri, quad
        repairs.append(
            dict(
                triangle=index + 1,
                quadrilateral=other + 1,
                method="Conforming tri/quad diagonal reselection; boundary vertices unchanged",
            )
        )
    return repairs


def relax_interior(nodes, panels, fixed_nodes=()):
    """Improve integration cells while fixing every physical boundary vertex."""
    owners, incident, neighbors = {}, {}, {}
    for index, cell in enumerate(panels):
        for a, b in zip(cell, cell[1:] + cell[:1]):
            owners.setdefault(tuple(sorted((a, b))), []).append(index)
            neighbors.setdefault(a, set()).add(b)
            neighbors.setdefault(b, set()).add(a)
        for tag in cell:
            incident.setdefault(tag, set()).add(index)
    fixed = {tag for edge, faces in owners.items() if len(faces) == 1 for tag in edge}
    fixed.update(fixed_nodes)
    adjacent = [faces for faces in owners.values() if len(faces) == 2]

    def score(indices):
        quality = {index: shape_quality(nodes, panels[index]) for index in indices}
        result = sum(
            max(0, 11 - q["min_angle"]) ** 2
            + max(0, q["max_angle"] - 169) ** 2
            + 10 * max(0, q["edge_ratio"] - 8) ** 2
            + (0 if q["convex"] and q["area"] > 1e-9 else 1e6)
            for q in quality.values()
        )
        for a, b in adjacent:
            if a in indices and b in indices:
                ratio = math.sqrt(
                    max(quality[a]["area"], quality[b]["area"])
                    / max(1e-12, min(quality[a]["area"], quality[b]["area"]))
                )
                result += 30 * max(0, ratio - 1.98) ** 2
        return result

    moved = 0
    for iteration in range(40):
        quality = [shape_quality(nodes, cell) for cell in panels]
        bad = {
            index
            for index, q in enumerate(quality)
            if q["max_angle"] > 170
            or q["min_angle"] < 10
            or q["edge_ratio"] > 8
            or not q["convex"]
        }
        for a, b in adjacent:
            if (
                math.sqrt(
                    max(quality[a]["area"], quality[b]["area"])
                    / min(quality[a]["area"], quality[b]["area"])
                )
                > 2
            ):
                bad.update((a, b))
        if not bad:
            return dict(
                iterations=iteration,
                moved_vertices=moved,
                boundaries="Every physical outer, symmetry and waterline boundary fixed",
            )
        candidates = sorted({tag for index in bad for tag in panels[index]} - fixed)
        improved = False
        for tag in candidates:
            affected = set(incident[tag])
            affected.update(
                other
                for a, b in adjacent
                for other in (a, b)
                if a in incident[tag] or b in incident[tag]
            )
            baseline = score(affected)
            if baseline < 1e-12:
                continue
            original = nodes[tag][:]
            target = [
                sum(nodes[other][j] for other in neighbors[tag]) / len(neighbors[tag])
                for j in range(3)
            ]
            best, point = baseline, original
            for weight in (0.25, 0.5, 0.75, 1.0):
                trial = [a + weight * (b - a) for a, b in zip(original, target)]
                nodes[tag] = trial
                value = score(affected)
                if value < best - 1e-9:
                    best, point = value, trial[:]
            nodes[tag] = point
            if best < baseline - 1e-9:
                moved += 1
                improved = True
        if not improved:
            break
    from scipy.optimize import minimize

    active = sorted({tag for index in bad for tag in panels[index]} - fixed)
    active = sorted(
        set(active)
        | {other for tag in active for other in neighbors[tag] if other not in fixed}
    )
    affected = {index for tag in active for index in incident[tag]}
    affected.update(
        other for a, b in adjacent for other in (a, b) if a in affected or b in affected
    )
    initial = [v for tag in active for v in nodes[tag][:2]]
    bounds = []
    for tag in active:
        reach = min(math.dist(nodes[tag], nodes[n]) for n in neighbors[tag]) * 0.75
        bounds.extend((value - reach, value + reach) for value in nodes[tag][:2])

    def objective(values):
        for i, tag in enumerate(active):
            nodes[tag] = [float(values[2 * i]), float(values[2 * i + 1]), 0.0]
        return score(affected) + 1e-6 * sum(
            (a - b) ** 2 for a, b in zip(values, initial)
        )

    optimized = minimize(
        objective,
        initial,
        method="L-BFGS-B",
        bounds=bounds,
        options=dict(maxiter=120, maxfun=12000, ftol=1e-13, gtol=1e-8),
    )
    objective(optimized.x)
    return dict(
        iterations=iteration + 1,
        moved_vertices=moved,
        local_optimization="Bounded interior-node L-BFGS-B; physical boundaries fixed",
        optimization_success=bool(optimized.success),
        boundaries="Every physical outer, symmetry and waterline boundary fixed",
    )


def surface_mesh(original, output, *, outer_size=12.0):
    import gmsh
    import numpy as np
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    loops = json.loads(
        (ROOT / "examples/visualization/fields/platform/condition.json").read_text(
            encoding="utf-8"
        )
    )["waterline_loops_xy_m"]
    outside = Polygon(
        [
            (110 * math.cos(i * math.pi / 48), 110 * math.sin(i * math.pi / 48))
            for i in range(49)
        ]
    )
    domain = outside.difference(unary_union([Polygon(loop) for loop in loops]))
    if not isinstance(domain, Polygon) or not domain.is_valid:
        raise ValueError(
            "A valid half-domain with all actual waterline cut-outs is required"
        )
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("platform_exterior_surface")
        curves, waterline_curves, outer_curves, point_sizes = [], [], [], []
        all_loops = [domain.exterior, *domain.interiors]
        for ring in all_loops:
            coords = list(ring.coords)[:-1]
            tags = []
            for x, y in coords:
                radius = math.hypot(x, y)
                # Preserved native waterline vertices supply the near-body scale.
                size = outer_size if radius > 109.99 else 2.5
                tags.append(gmsh.model.geo.addPoint(x, y, 0, size))
                point_sizes.append(size)
            lines = [
                gmsh.model.geo.addLine(tags[i], tags[(i + 1) % len(tags)])
                for i in range(len(tags))
            ]
            for i, line in enumerate(lines):
                a, b = coords[i], coords[(i + 1) % len(coords)]
                if math.dist(a, b) < 4.0:
                    waterline_curves.append(line)
                if min(math.hypot(*a), math.hypot(*b)) > 109.99:
                    outer_curves.append(line)
            curves.append(gmsh.model.geo.addCurveLoop(lines))
        face = gmsh.model.geo.addPlaneSurface(curves)
        gmsh.model.geo.synchronize()
        # One segment per native waterline edge preserves hull/surface conformity.
        for line in waterline_curves:
            gmsh.model.mesh.setTransfiniteCurve(line, 2)
        gmsh.option.setNumber("Mesh.Algorithm", 8)
        gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
        gmsh.option.setNumber("Mesh.RecombineAll", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 2.2)
        gmsh.option.setNumber("Mesh.MeshSizeMax", outer_size)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        distance = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(distance, "CurvesList", waterline_curves)
        gmsh.model.mesh.field.setNumber(distance, "Sampling", 20)
        threshold = gmsh.model.mesh.field.add("Threshold")
        for name, value in dict(
            InField=distance, SizeMin=2.5, SizeMax=outer_size, DistMin=2.0, DistMax=14.0
        ).items():
            gmsh.model.mesh.field.setNumber(threshold, name, value)
        gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
        layer = gmsh.model.mesh.field.add("BoundaryLayer")
        gmsh.model.mesh.field.setNumbers(layer, "CurvesList", outer_curves)
        for name, value in dict(Size=6.0, Thickness=12.0, Ratio=1.2, Quads=1).items():
            gmsh.model.mesh.field.setNumber(layer, name, value)
        gmsh.model.mesh.field.setAsBoundaryLayer(layer)
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.optimize("Relocate2D", niter=30)
        node_tags, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {
            int(tag): list(map(float, p))
            for tag, p in zip(node_tags, np.array(xyz).reshape(-1, 3))
        }
        types, _, connections = gmsh.model.mesh.getElements(2, face)
        panels = []
        for kind, values in zip(types, connections):
            if kind not in (2, 3):
                raise ValueError(
                    "Only linear triangle or quadrilateral surface panels are accepted"
                )
            count = 3 if kind == 2 else 4
            panels.extend(
                [list(map(int, cell)) for cell in np.array(values).reshape(-1, count)]
            )
    finally:
        gmsh.finalize()
    return finalize_surface(
        original, output, nodes, panels, domain, outer_size=outer_size
    )


def finalize_surface(
    original,
    output,
    nodes,
    panels,
    domain,
    *,
    outer_size,
    repair=True,
    method="Conforming quadrilateral-dominant half-domain outside every actual waterline, circular boundary at the origin",
    extra=None,
):
    import gmsh
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    repairs = improve_transitions(nodes, panels) if repair else []
    relaxation = (
        relax_interior(nodes, panels)
        if repair
        else dict(method="Sector quality checked before symmetry replication")
    )
    shapes = [Polygon([nodes[i][:2] for i in cell]) for cell in panels]
    if any(not p.is_valid or p.area <= 1e-10 for p in shapes):
        raise ValueError("Invalid exterior integration panel")
    covered = unary_union(shapes)
    overlap = sum(p.area for p in shapes) - covered.area
    missing = domain.symmetric_difference(covered).area
    if max(overlap, missing) > 1e-7 * domain.area:
        raise ValueError("Exterior integration coverage or overlap failed")
    quad_count = sum(len(p) == 4 for p in panels)
    if quad_count / len(panels) < 0.8:
        raise ValueError("Exterior integration mesh must be quadrilateral dominant")
    old_nodes, wet_panels, _ = core.read_hst(original)
    quality = [shape_quality(nodes, p) for p in panels]
    edge_owners = {}
    for i, cell in enumerate(panels):
        for a, b in zip(cell, cell[1:] + cell[:1]):
            edge_owners.setdefault(tuple(sorted((a, b))), []).append(i)
    if any(len(owners) > 2 for owners in edge_owners.values()):
        raise ValueError("Nonmanifold integration edge")
    boundary_edges = [edge for edge, owners in edge_owners.items() if len(owners) == 1]
    from shapely.geometry import LineString

    if any(
        LineString([nodes[i][:2] for i in edge])
        .difference(domain.boundary.buffer(1e-6))
        .length
        > 1e-6
        for edge in boundary_edges
    ):
        raise ValueError("Integration mesh has an internal seam or hanging edge")
    neighbor_ratios = [
        math.sqrt(
            max(quality[a]["area"], quality[b]["area"])
            / min(quality[a]["area"], quality[b]["area"])
        )
        for owners in edge_owners.values()
        if len(owners) == 2
        for a, b in [owners]
    ]
    metrics = dict(
        min_corner_deg=min(q["min_angle"] for q in quality),
        max_corner_deg=max(q["max_angle"] for q in quality),
        max_edge_ratio=max(q["edge_ratio"] for q in quality),
        max_neighbor_size_ratio=max(neighbor_ratios),
        nonconvex=sum(not q["convex"] for q in quality),
    )
    if (
        metrics["nonconvex"]
        or metrics["min_corner_deg"] < 10
        or metrics["max_corner_deg"] > 170
        or metrics["max_edge_ratio"] > 8
        or metrics["max_neighbor_size_ratio"] > 2
    ):
        output.parent.mkdir(parents=True, exist_ok=True)
        save_json(
            output.with_suffix(".rejected.json"),
            dict(
                status="failed_shape_gate",
                metrics=metrics,
                vertices=nodes,
                panels=panels,
            ),
        )
        raise ValueError("Exterior panel shape gate: " + str(metrics))
    baseline = json.loads(
        original.with_name("report.json").read_text(encoding="utf-8")
    )["hslec"]
    total = (
        len(wet_panels) + baseline["waterplane_panels"] + len(panels)
    ) * 2 ** baseline["symmetry"]
    if total > 3000:
        raise ValueError(
            f"Exterior surface exceeds the 3000 total-panel budget: {total}"
        )
    coordinates = {
        tuple(round(v, 8) for v in xyz): tag for tag, xyz in old_nodes.items()
    }
    mapped, new = {}, {}
    next_id = max(old_nodes) + 1
    for tag, xyz in nodes.items():
        key = tuple(round(v, 8) for v in xyz)
        if key not in coordinates:
            coordinates[key] = next_id
            new[next_id] = xyz
            next_id += 1
        mapped[tag] = coordinates[key]
    native_panels = []
    for cell, polygon in zip(panels, shapes):
        cell = [mapped[tag] for tag in cell]
        if polygon.exterior.is_ccw:
            cell.reverse()  # Native exterior free-surface normals point down.
        if len(cell) == 3:
            cell.append(cell[-1])
        native_panels.append(cell)
    wet_waterline_edges = {
        tuple(sorted((a, b)))
        for cell in wet_panels
        for a, b in zip(cell, cell[1:] + cell[:1])
        if abs(old_nodes[a][2]) < 1e-8 and abs(old_nodes[b][2]) < 1e-8
    }
    mapped_boundary = {
        tuple(sorted(mapped[i] for i in edge)) for edge in boundary_edges
    }
    if not wet_waterline_edges or not wet_waterline_edges <= mapped_boundary:
        raise ValueError(
            "Every native wet waterline edge must share its integration edge and node IDs"
        )
    text = original.read_text(encoding="ascii")
    text = text.replace("PROJECT oc4_style", "PROJECT platform2")
    text = text.replace(
        "COORDINATES TYPE 0",
        f"NFREESURFACE {len(panels)} {len(wet_panels) + 1} {len(wet_panels) + len(panels)}\nCOORDINATES TYPE 0",
    )
    extra_nodes = "".join(
        f"{tag} " + " ".join(f"{v:.12g}" for v in xyz) + "\n"
        for tag, xyz in new.items()
    )
    extra_panels = "".join(" ".join(map(str, cell)) + "\n" for cell in native_panels)
    text = text.replace("ENDCOORDINATES", extra_nodes + "ENDCOORDINATES")
    text = text.replace("ENDPANEL", extra_panels + "ENDPANEL")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="ascii", newline="\n")
    after_nodes, after_panels, _ = core.read_hst(output)
    if [[old_nodes[i] for i in p] for p in wet_panels] != [
        [after_nodes[i] for i in p] for p in after_panels
    ]:
        raise ValueError("Accepted native wet connectivity changed")
    report = dict(
        method=method,
        generator="Gmsh " + gmsh.__version__,
        outer_radius_m=110,
        half_domain_panels=len(panels),
        quadrilaterals=quad_count,
        triangles=len(panels) - quad_count,
        quad_fraction=quad_count / len(panels),
        expected_half_area_m2=domain.area,
        overlap_m2=overlap,
        uncovered_or_extra_m2=missing,
        outer_mesh_size_m=outer_size,
        waterline_mesh_size_m=2.5,
        source_hst_sha256=file_hash(original),
        output_hst_sha256=file_hash(output),
        generator_script_sha256=file_hash(Path(__file__)),
        full_equivalent_total_including_exterior=total,
        panel_quality=metrics,
        shared_native_waterline_edges=len(wet_waterline_edges),
        interior_seams=0,
        triangle_transition_repairs=repairs,
        interior_relaxation=relaxation,
        vertices=nodes,
        panels=panels,
    )
    if extra:
        report.update(extra)
    save_json(output.with_suffix(".surface.json"), report)
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=float, default=12.0)
    args = parser.parse_args()
    result = surface_mesh(args.source, args.output, outer_size=args.size)
    print(
        {
            k: result[k]
            for k in (
                "half_domain_panels",
                "quadrilaterals",
                "triangles",
                "overlap_m2",
                "uncovered_or_extra_m2",
            )
        }
    )
