"""Independent topology and triangle intersection checks for full wet surfaces."""

from __future__ import annotations

from collections import defaultdict


def inspect_surface(vertices, faces, expected_components=1, tolerance=1e-8):
    import numpy as np

    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    if (
        v.ndim != 2
        or v.shape[1] != 3
        or not np.isfinite(v).all()
        or f.ndim != 2
        or f.shape[1] != 3
        or len(f) == 0
        or f.min() < 0
        or f.max() >= len(v)
    ):
        raise ValueError("有限三维节点和有效三角面元为必需输入")
    triangles = v[f]
    cross = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    areas = np.linalg.norm(cross, axis=1) / 2
    invalid_area = np.flatnonzero(areas <= tolerance**2).tolist()
    duplicates = len(f) - len({tuple(sorted(row)) for row in f})
    above = np.flatnonzero(np.max(triangles[:, :, 2], axis=1) > tolerance).tolist()
    at_surface = np.flatnonzero(
        np.max(np.abs(triangles[:, :, 2]), axis=1) <= tolerance
    ).tolist()
    edges = defaultdict(list)
    for index, face in enumerate(f):
        for a, b in zip(face, np.roll(face, -1)):
            edges[min(a, b), max(a, b)].append((index, 1 if a < b else -1))
    adjacency = defaultdict(set)
    boundary, invalid_edges = [], []
    for (a, b), inc in edges.items():
        if len(inc) == 2 and inc[0][1] + inc[1][1] == 0:
            x, y = inc[0][0], inc[1][0]
            adjacency[x].add(y)
            adjacency[y].add(x)
        elif len(inc) == 1 and abs(v[a, 2]) <= tolerance and abs(v[b, 2]) <= tolerance:
            boundary.append((int(a), int(b)))
        else:
            invalid_edges.append([int(a), int(b)])
    boundary_degree = defaultdict(int)
    for a, b in boundary:
        boundary_degree[a] += 1
        boundary_degree[b] += 1
    invalid_boundary_vertices = [
        int(i) for i, degree in boundary_degree.items() if degree != 2
    ]
    remaining = set(range(len(f)))
    components = []
    while remaining:
        group = [remaining.pop()]
        stack = group.copy()
        while stack:
            for index in adjacency[stack.pop()] & remaining:
                remaining.remove(index)
                group.append(index)
                stack.append(index)
        components.append(group)
    volumes = [
        float(
            np.sum(
                np.einsum(
                    "ij,ij->i",
                    triangles[group, 0],
                    np.cross(triangles[group, 1], triangles[group, 2]),
                )
            )
            / 6
        )
        for group in components
    ]
    # A submerged internal cavity has negative orientation; it requires a CAD volume reference.
    negative = [i for i, value in enumerate(volumes) if value <= tolerance**3]
    intersections = triangle_intersections(v, f, tolerance)
    passed = not (
        invalid_area
        or duplicates
        or above
        or at_surface
        or invalid_edges
        or invalid_boundary_vertices
        or intersections
        or negative
        or len(components) != expected_components
    )
    return dict(
        passed=passed,
        nodes=len(v),
        panels=len(f),
        wetted_components=len(components),
        expected_wet_components=expected_components,
        component_volume_m3=volumes,
        zero_area_panels=invalid_area[:20],
        duplicate_faces=duplicates,
        above_water_panels=above[:20],
        waterplane_panels=at_surface[:20],
        invalid_edges=invalid_edges[:20],
        cut_edges=len(boundary),
        invalid_waterline_vertices=invalid_boundary_vertices[:20],
        self_intersections=intersections[:20],
        nonpositive_components=negative,
        intersection_method="AABB broad phase, triangle-plane intervals and coplanar polygon overlap",
    )


def triangle_intersections(vertices, faces, tolerance):
    import numpy as np
    from shapely.geometry import Polygon

    triangles = vertices[faces]
    lower, upper = triangles.min(axis=1), triangles.max(axis=1)
    order = np.argsort(lower[:, 0], kind="stable")
    ordered_lower_x = lower[order, 0]
    found = []

    def plane_cut(triangle, signed):
        points = []
        for p, d, q, e in zip(
            triangle, signed, np.roll(triangle, -1, axis=0), np.roll(signed, -1)
        ):
            if abs(d) <= tolerance:
                points.append(p)
            if (d < -tolerance and e > tolerance) or (d > tolerance and e < -tolerance):
                points.append(p + d / (d - e) * (q - p))
        return points

    for position, i in enumerate(order):
        last = int(
            np.searchsorted(ordered_lower_x, upper[i, 0] + tolerance, side="right")
        )
        candidates = order[position + 1 : last]
        candidates = candidates[
            np.all(lower[candidates] <= upper[i] + tolerance, axis=1)
            & np.all(upper[candidates] >= lower[i] - tolerance, axis=1)
        ]
        a = triangles[i]
        na = np.cross(a[1] - a[0], a[2] - a[0])
        if np.linalg.norm(na) <= tolerance**2:
            continue
        na /= np.linalg.norm(na)
        for j in candidates:
            b = triangles[j]
            nb = np.cross(b[1] - b[0], b[2] - b[0])
            if np.linalg.norm(nb) <= tolerance**2:
                continue
            nb /= np.linalg.norm(nb)
            da, db = (a - b[0]) @ nb, (b - a[0]) @ na
            if any(np.all(d > tolerance) or np.all(d < -tolerance) for d in (da, db)):
                continue
            shared = set(faces[i]) & set(faces[j])
            direction = np.cross(na, nb)
            if np.linalg.norm(direction) < 1e-10:
                if max(np.abs(db)) > tolerance:
                    continue
                axis = int(np.argmax(np.abs(na)))
                pa, pb = (
                    Polygon(np.delete(a, axis, axis=1)),
                    Polygon(np.delete(b, axis, axis=1)),
                )
                intersection = pa.intersection(pb)
                hit = intersection.area > tolerance**2 or (
                    not shared and not intersection.is_empty
                )
                if not hit and len(shared) == 1 and not intersection.is_empty:
                    point = np.delete(vertices[next(iter(shared))], axis)
                    bounds = np.array(intersection.bounds).reshape(2, 2)
                    hit = bool(np.max(np.abs(bounds - point)) > tolerance)
            else:
                ca, cb = plane_cut(a, da), plane_cut(b, db)
                if not ca or not cb:
                    continue
                direction /= np.linalg.norm(direction)
                ia, ib = (
                    [np.dot(p, direction) for p in ca],
                    [np.dot(p, direction) for p in cb],
                )
                lo, hi = max(min(ia), min(ib)), min(max(ia), max(ib))
                if hi < lo - tolerance:
                    continue
                if not shared:
                    hit = True
                elif len(shared) == 2:
                    hit = False
                else:
                    point = vertices[next(iter(shared))]
                    hit = (
                        hi - lo > tolerance
                        or abs((lo + hi) / 2 - np.dot(point, direction)) > tolerance
                    )
            if hit:
                found.append([int(i) + 1, int(j) + 1])
                if len(found) == 20:
                    return found
    return found
