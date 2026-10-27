"""Independent shape and neighbouring-size checks for native BEM panels."""

from __future__ import annotations

from collections import defaultdict


def inspect_panels(vertices, faces, limits):
    import numpy as np

    nodes = np.asarray(vertices, dtype=float)
    edges = defaultdict(list)
    sizes, ratios, warp, minimum, maximum = [], [], [], [], []
    invalid, violations = [], []
    for index, face in enumerate(faces):
        p = nodes[face]
        e = np.roll(p, -1, axis=0) - p
        length = np.linalg.norm(e, axis=1)
        if np.min(length) <= 1e-12:
            invalid.append(index + 1)
            sizes.append(0.0)
            ratios.append(0.0)
            warp.append(180.0)
            minimum.append(0.0)
            maximum.append(180.0)
            continue
        corners = np.cross(np.roll(e, 1, axis=0), e)
        normal = np.sum(corners, axis=0)
        norm = np.linalg.norm(normal)
        convex = norm > 1e-15 and np.all(corners @ normal > 1e-15)
        angle = np.degrees(
            np.arccos(
                np.clip(
                    np.sum(-np.roll(e, 1, axis=0) * e, axis=1)
                    / (length * np.roll(length, 1)),
                    -1,
                    1,
                )
            )
        )
        area = 0.0
        for k in range(1, len(face) - 1):
            area += np.linalg.norm(np.cross(p[k] - p[0], p[k + 1] - p[0])) / 2
        warpage = 0.0
        if len(face) == 4:
            a = np.cross(p[1] - p[0], p[2] - p[0])
            b = np.cross(p[2] - p[0], p[3] - p[0])
            denominator = np.linalg.norm(a) * np.linalg.norm(b)
            warpage = (
                float(np.degrees(np.arccos(np.clip(np.dot(a, b) / denominator, -1, 1))))
                if denominator > 1e-24
                else 180.0
            )
        ratio = float(np.max(length) / np.min(length))
        sizes.append(float(np.sqrt(area)))
        ratios.append(ratio)
        warp.append(warpage)
        minimum.append(float(np.min(angle)))
        maximum.append(float(np.max(angle)))
        if not convex:
            invalid.append(index + 1)
        if (
            ratio > limits["max_edge_ratio"]
            or minimum[-1] < limits["min_corner_deg"]
            or maximum[-1] > limits["max_corner_deg"]
            or warpage > limits["max_warpage_deg"]
        ):
            violations.append(index + 1)
        for a, b in zip(face, face[1:] + face[:1]):
            edges[min(a, b), max(a, b)].append(index)
    adjacent = []
    bad_transitions = []
    for pair in edges.values():
        if len(pair) == 2:
            a, b = pair
            ratio = max(sizes[a], sizes[b]) / max(min(sizes[a], sizes[b]), 1e-30)
            adjacent.append(ratio)
            if ratio > limits["max_neighbor_size_ratio"]:
                bad_transitions.append([a + 1, b + 1])

    def distribution(values):
        return (
            {
                "p50": float(np.percentile(values, 50)),
                "p95": float(np.percentile(values, 95)),
                "max": float(max(values)),
            }
            if values
            else {"p50": 0.0, "p95": 0.0, "max": 0.0}
        )

    return dict(
        passed=not (invalid or violations or bad_transitions),
        quadrilaterals=sum(len(p) == 4 for p in faces),
        triangles=sum(len(p) == 3 for p in faces),
        quad_fraction=sum(len(p) == 4 for p in faces) / len(faces),
        limits=limits,
        edge_ratio=distribution(ratios),
        warpage_deg=distribution(warp),
        minimum_corner_deg=min(minimum),
        maximum_corner_deg=max(maximum),
        adjacent_size_ratio=distribution(adjacent),
        invalid_convexity=invalid[:20],
        shape_violations=violations[:20],
        adjacent_size_violations=bad_transitions[:20],
        size_definition="sqrt(panel area); adjacent panels share a complete native edge",
        warpage_definition="angle between normals of triangles (0,1,2) and (0,2,3)",
    )
