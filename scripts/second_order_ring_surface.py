"""Structured annular integration mesh, with a repeated 60-degree inner sector.

This topology is specific to the original three-column platform. Native wet
panels and their waterline vertices are retained. All integration panels count
towards the same 3000-panel budget as the wet body and waterplane.
"""

import argparse
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.visualization import whole_mesh
from hydrostar_mcp.workflow import file_hash
from scripts.second_order_surface import (
    finalize_surface,
    improve_transitions,
    relax_interior,
)


def waterlines(original):
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union

    vertices, faces = whole_mesh(original)
    coordinates, edges = {}, set()
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            if max(abs(vertices[k][2]) for k in (a, b)) > 1e-7:
                continue
            keys = []
            for k in (a, b):
                key = tuple(round(v, 7) for v in vertices[k][:2])
                coordinates[key] = vertices[k][:2]
                keys.append(key)
            edges.add(tuple(sorted(keys)))
    loops = [
        Polygon([coordinates[tuple(p)] for p in list(loop.exterior.coords)[:-1]])
        for loop in polygonize(unary_union([LineString(edge) for edge in edges]))
    ]
    if len(loops) != 4 or any(len(p.exterior.coords) != 25 for p in loops):
        raise ValueError(
            "This sector topology requires the four native 24-edge waterlines"
        )
    return loops


def surface_mesh(original, output, *, outer_size=6.5):
    import gmsh
    import numpy as np
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union

    loops = waterlines(original)
    centre = min(loops, key=lambda p: math.hypot(p.centroid.x, p.centroid.y))
    column = max(loops, key=lambda p: p.centroid.y)
    r0 = sum(math.hypot(x, y) for x, y in list(centre.exterior.coords)[:-1]) / 24
    c = [column.centroid.x, column.centroid.y]
    distance = math.hypot(*c)
    rc = sum(math.dist([x, y], c) for x, y in list(column.exterior.coords)[:-1]) / 24
    if abs(math.atan2(c[1], c[0]) - math.pi / 3) > 1e-7:
        raise ValueError("The source platform must have its upper column at 60 degrees")
    angles = [i * math.pi / 36 for i in range(13)]
    inner_radius = 50.0
    radii = [inner_radius]
    for width in np.linspace(5.0, 25 / 3, 9):
        radii.append(radii[-1] + float(width))

    def circle(radius, cx=0.0, cy=0.0):
        return Polygon(
            [
                (
                    cx + radius * math.cos(i * math.pi / 12),
                    cy + radius * math.sin(i * math.pi / 12),
                )
                for i in range(24)
            ]
        )

    ideal_centre = circle(r0)
    ideal_column = circle(rc, distance / 2, distance * math.sqrt(3) / 2)
    sector = Polygon(
        [(0, 0)]
        + [(inner_radius * math.cos(a), inner_radius * math.sin(a)) for a in angles]
    )
    inner = sector.difference(unary_union([ideal_centre, ideal_column]))
    if not isinstance(inner, Polygon) or not inner.is_valid or inner.interiors:
        raise ValueError("A simply connected fundamental sector is required")
    coords = []
    for x, y in list(inner.exterior.coords)[:-1]:
        # Snap roundoff at the two sector rays before building geometry entities.
        if abs(y) < 1e-7:
            y = 0.0
        if abs(x * math.sqrt(3) - y) < 1e-7:
            radius = math.hypot(x, y)
            x, y = radius / 2, radius * math.sqrt(3) / 2
        if not coords or math.dist((x, y), coords[-1]) > 1e-7:
            coords.append((x, y))
    if math.dist(coords[0], coords[-1]) < 1e-7:
        coords.pop()
    inner = Polygon(coords)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("platform_fundamental_sector")
        tags = [gmsh.model.geo.addPoint(x, y, 0, outer_size) for x, y in coords]
        lines = [
            gmsh.model.geo.addLine(tags[i], tags[(i + 1) % len(tags)])
            for i in range(len(tags))
        ]
        face = gmsh.model.geo.addPlaneSurface([gmsh.model.geo.addCurveLoop(lines)])
        gmsh.model.geo.synchronize()
        native_curves, interface_curves = [], []
        for i, line in enumerate(lines):
            a, b = coords[i], coords[(i + 1) % len(coords)]
            if min(math.hypot(*p) for p in (a, b)) > inner_radius - 1e-6:
                interface_curves.append(line)
            elif (
                ideal_centre.boundary.distance(
                    Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                )
                < 1e-6
                or ideal_column.boundary.distance(
                    Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                )
                < 1e-6
            ):
                native_curves.append(line)
        for line in native_curves + interface_curves:
            gmsh.model.mesh.setTransfiniteCurve(line, 2)
        gmsh.option.setNumber("Mesh.Algorithm", 8)
        gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
        gmsh.option.setNumber("Mesh.RecombineAll", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 1.5)
        gmsh.option.setNumber("Mesh.MeshSizeMax", outer_size)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        field = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(field, "CurvesList", native_curves)
        gmsh.model.mesh.field.setNumber(field, "Sampling", 20)
        threshold = gmsh.model.mesh.field.add("Threshold")
        for key, value in dict(
            InField=field, SizeMin=2.5, SizeMax=outer_size, DistMin=2, DistMax=14
        ).items():
            gmsh.model.mesh.field.setNumber(threshold, key, value)
        gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
        layer = gmsh.model.mesh.field.add("BoundaryLayer")
        gmsh.model.mesh.field.setNumbers(layer, "CurvesList", interface_curves)
        for key, value in dict(Size=5.8, Thickness=5.9, Ratio=1.2, Quads=1).items():
            gmsh.model.mesh.field.setNumber(layer, key, value)
        gmsh.model.mesh.field.setAsBoundaryLayer(layer)
        gmsh.model.mesh.generate(2)
        gmsh.model.mesh.optimize("Relocate2D", niter=30)
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {
            int(tag): list(map(float, p))
            for tag, p in zip(ids, np.array(xyz).reshape(-1, 3))
        }
        types, _, connections = gmsh.model.mesh.getElements(2, face)
        panels = []
        for kind, values in zip(types, connections):
            if kind not in (2, 3):
                raise ValueError("Linear integration panels required")
            panels.extend(
                [
                    list(map(int, p))
                    for p in np.array(values).reshape(-1, 3 if kind == 2 else 4)
                ]
            )
    finally:
        gmsh.finalize()
    repaired = improve_transitions(nodes, panels)
    relaxed = relax_interior(nodes, panels)
    inner_count = len(panels)
    existing = {tuple(round(v, 7) for v in p[:2]): i for i, p in nodes.items()}

    def node(x, y):
        key = (round(x, 7), round(y, 7))
        if key not in existing:
            tag = max(nodes, default=0) + 1
            existing[key] = tag
            nodes[tag] = [x, y, 0.0]
        return existing[key]

    for a, b in zip(radii, radii[1:]):
        for t, u in zip(angles, angles[1:]):
            panels.append(
                [
                    node(a * math.cos(t), a * math.sin(t)),
                    node(b * math.cos(t), b * math.sin(t)),
                    node(b * math.cos(u), b * math.sin(u)),
                    node(a * math.cos(u), a * math.sin(u)),
                ]
            )
    half_nodes, half_panels, merged = {}, [], {}
    wet_nodes, wet_panels, _ = core.read_hst(original)
    waterline_points = [
        wet_nodes[tag]
        for tag in {
            i for panel in wet_panels for i in panel if abs(wet_nodes[i][2]) < 1e-7
        }
    ]
    for operation in range(3):
        mapping = {}
        for tag, (x, y, _) in nodes.items():
            if operation == 1:  # Reflection about the 60-degree ray.
                x, y = -x / 2 + y * math.sqrt(3) / 2, x * math.sqrt(3) / 2 + y / 2
            elif operation == 2:
                x, y = -x / 2 - y * math.sqrt(3) / 2, x * math.sqrt(3) / 2 - y / 2
            nearest = min(waterline_points, key=lambda p: math.dist((x, y), p[:2]))
            if math.dist((x, y), nearest[:2]) < 1e-6:
                x, y = nearest[:2]
            if abs(y) < 1e-7:
                y = 0.0
            key = (round(x, 7), round(y, 7))
            if key not in merged:
                index = len(half_nodes) + 1
                merged[key] = index
                half_nodes[index] = [x, y, 0.0]
            mapping[tag] = merged[key]
        half_panels.extend([[mapping[i] for i in panel] for panel in panels])
    outside = Polygon(
        [
            (110 * math.cos(i * math.pi / 36), 110 * math.sin(i * math.pi / 36))
            for i in range(37)
        ]
    )
    domain = outside.difference(unary_union(loops))
    return finalize_surface(
        original,
        output,
        half_nodes,
        half_panels,
        domain,
        outer_size=outer_size,
        repair=False,
        method="Nine structured annular bands, 72 equal angular divisions; conforming 60-degree inner sector repeated by reflection and rotation",
        extra=dict(
            generator_script_sha256=file_hash(Path(__file__)),
            quality_utility_sha256=file_hash(ROOT / "scripts/second_order_surface.py"),
            angular_divisions_full=72,
            annular_radii_m=radii,
            structured_annular_quadrilaterals_full=648,
            fundamental_inner_panels=inner_count,
            fundamental_repairs=repaired,
            fundamental_relaxation=relaxed,
            sector_degrees=60,
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=float, default=6.5)
    args = parser.parse_args()
    result = surface_mesh(args.source, args.output, outer_size=args.size)
    print(
        {
            key: result[key]
            for key in (
                "half_domain_panels",
                "quadrilaterals",
                "triangles",
                "panel_quality",
                "full_equivalent_total_including_exterior",
            )
        }
    )
