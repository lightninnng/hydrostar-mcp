"""Explicit CAD section bands and planar O-grid caps for simple coaxial solids."""

from __future__ import annotations

import math


def _plane(gmsh, axis, value, low, high):
    import numpy as np

    occ = gmsh.model.occ
    other = [k for k in range(3) if k != axis]
    center = (low + high) / 2
    center[axis] = value
    pad = max(high - low) + 1
    tags = []
    for signs in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = np.array(center)
        for k, sign in zip(other, signs):
            p[k] += sign * (high[k] - low[k] + 2 * pad) / 2
        tags.append(occ.addPoint(*p))
    curves = [occ.addLine(a, b) for a, b in zip(tags, tags[1:] + tags[:1])]
    return occ.addPlaneSurface([occ.addWire(curves)])


def _curve(gmsh, tag, samples=1024):
    import numpy as np

    lo, hi = gmsh.model.getParametrizationBounds(1, abs(tag))
    values = np.linspace(float(lo[0]), float(hi[0]), samples + 1)
    return np.array(gmsh.model.getValue(1, abs(tag), values.tolist())).reshape(-1, 3)


def _loop(gmsh, curves):
    import numpy as np

    remaining = [_curve(gmsh, int(tag)) for tag in curves]
    points = list(remaining.pop(0))
    while remaining:
        distances = [
            (np.linalg.norm(p[0] - points[-1]), i, False)
            for i, p in enumerate(remaining)
        ] + [
            (np.linalg.norm(p[-1] - points[-1]), i, True)
            for i, p in enumerate(remaining)
        ]
        error, index, reverse = min(distances)
        if error > 1e-6:
            raise ValueError("CAD 剖面曲线未形成连续闭环")
        p = remaining.pop(index)
        points.extend((p[::-1] if reverse else p)[1:])
    if np.linalg.norm(points[0] - points[-1]) > 1e-6:
        raise ValueError("环带剖面需要闭合的外轮廓")
    return np.array(points)


def _sample_ring(points, count, center):
    import numpy as np

    xy = points[:, :2] - center
    area = np.sum(xy[:-1, 0] * xy[1:, 1] - xy[1:, 0] * xy[:-1, 1]) / 2
    if area < 0:
        points = points[::-1]
        xy = xy[::-1]
    theta = np.unwrap(np.arctan2(xy[:, 1], xy[:, 0]))
    if np.min(np.diff(theta)) < -1e-6 or abs(theta[-1] - theta[0] - 2 * math.pi) > 1e-5:
        raise ValueError(
            "环带外轮廓须相对给定轴线为单值星形；"
            f"极角步长 {np.min(np.diff(theta)):.6g}，跨度 {theta[-1] - theta[0]:.6g}，中心 {center.tolist()}，轮廓范围 {np.ptp(points, axis=0).tolist()}"
        )
    desired = -math.pi / 4 + 2 * math.pi * np.arange(count) / count
    desired = (desired - theta[0]) % (2 * math.pi) + theta[0]
    return np.column_stack([np.interp(desired, theta, points[:, k]) for k in range(3)])


def _face_loops(gmsh, surface, count, center):
    _, loops = gmsh.model.occ.getCurveLoops(surface)
    return [_sample_ring(_loop(gmsh, curves), count, center) for curves in loops]


def _section(gmsh, wet, height, low, high, count, center):
    plane = _plane(gmsh, 2, height, low, high)
    made, _ = gmsh.model.occ.intersect(
        wet, [(2, plane)], removeObject=False, removeTool=True
    )
    gmsh.model.occ.synchronize()
    surfaces = [tag for dim, tag in made if dim == 2]
    if len(surfaces) != 1:
        raise ValueError("环带截面需要单一连通的同轴排水截面")
    rings = _face_loops(gmsh, surfaces[0], count, center)
    if len(rings) != 1:
        raise ValueError("内部带孔或多个轮廓的截面采用显式分区网格")
    rings[0][:, 2] = height
    return rings[0]


def _ring_area(ring):
    import numpy as np

    p = np.roll(ring, -1, axis=0)
    return float(abs(np.sum(ring[:, 0] * p[:, 1] - p[:, 0] * ring[:, 1])) / 2)


def _cap_ogrid(boundary, spacing, center):
    """Four mapped annular blocks around a Cartesian core, without a pole fan."""
    import numpy as np
    from shapely.geometry import Polygon

    count = len(boundary)
    n = count // 4
    xy = boundary[:, :2]
    radius = np.max(np.abs(xy - center), axis=0)
    half = radius * 0.35
    polygon = Polygon(xy)
    for _ in range(12):
        corners = (
            np.array(
                [
                    [half[0], -half[1]],
                    [half[0], half[1]],
                    [-half[0], half[1]],
                    [-half[0], -half[1]],
                ]
            )
            + center
        )
        if polygon.covers(Polygon(corners)):
            break
        half *= 0.8
    else:
        raise ValueError("底面中心区域需额外分区")
    inner = []
    for a, b in zip(corners, np.roll(corners, -1, axis=0)):
        inner.extend(a + (b - a) * j / n for j in range(n))
    inner = np.array(inner)
    radial_width = float(np.max(np.linalg.norm(xy - inner, axis=1)))
    core_edge = 2 * float(np.min(half)) / n
    layers = max(
        2, math.ceil(radial_width / spacing), math.ceil(radial_width / (2 * core_edge))
    )
    vertices = []
    faces = []
    rings = []
    for j in range(layers + 1):
        t = j / layers
        points = inner * (1 - t) + xy * t
        rings.append(list(range(len(vertices), len(vertices) + count)))
        vertices.extend([[p[0], p[1], boundary[0, 2]] for p in points])
    for a, b in zip(rings, rings[1:]):
        for i in range(count):
            k = (i + 1) % count
            faces.append([a[i], a[k], b[k], b[i]])
    grid = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            row.append(len(vertices))
            vertices.append(
                [
                    center[0] - half[0] + 2 * half[0] * i / n,
                    center[1] - half[1] + 2 * half[1] * j / n,
                    boundary[0, 2],
                ]
            )
        grid.append(row)
    for j in range(n):
        for i in range(n):
            faces.append(
                [grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]]
            )
    return vertices, faces


def ring_bands(gmsh, wet, low, high, request, cad_cb):
    import numpy as np

    if request.structured_axis not in (None, "z"):
        raise ValueError("当前同轴环带采用目标坐标的 z 轴")
    count = max(32, 8 * math.ceil(request.curvature_samples / 8))
    center = np.array(
        request.axis_center_xy_m if request.axis_center_xy_m is not None else cad_cb[:2]
    )
    features = {}
    boundary = gmsh.model.getBoundary(wet, combined=True, oriented=False)
    for _, tag in boundary:
        curves = {abs(t) for _, t in gmsh.model.getBoundary([(2, tag)], combined=False)}
        samples = np.vstack([_curve(gmsh, t, 16) for t in curves])
        if np.ptp(samples[:, 2]) < 1e-6:
            z = round(float(np.mean(samples[:, 2])), 8)
            for ring in _face_loops(gmsh, tag, count, center):
                ring[:, 2] = z
                if not any(
                    np.max(np.abs(ring - r)) < 1e-7 for r in features.setdefault(z, [])
                ):
                    features[z].append(ring)
    levels = sorted(features)
    if len(levels) < 2 or abs(levels[-1]) > 1e-7:
        raise ValueError(
            "环带需要平面底面、明确的水平台阶与平均水线边界；检测高程为 " + str(levels)
        )
    target = request.mesh_size_m / 2
    rings = []
    intervals = []
    for start, stop in zip(levels, levels[1:]):
        n = max(1, math.ceil((stop - start) / target))
        sample = _section(
            gmsh, wet, start + (stop - start) / 2, low, high, count, center
        )
        area = _ring_area(sample)
        bottom = min(features[start], key=lambda r: abs(_ring_area(r) - area))
        top = min(features[stop], key=lambda r: abs(_ring_area(r) - area))
        if rings and np.max(np.abs(rings[-1] - bottom)) > 1e-7:
            previous = rings[-1]
            radial_n = max(
                1,
                math.ceil(
                    float(np.max(np.linalg.norm(bottom - previous, axis=1))) / target
                ),
            )
            rings.extend(
                previous + (bottom - previous) * k / radial_n
                for k in range(1, radial_n + 1)
            )
        elif not rings:
            rings.append(bottom)
        for k in range(1, n):
            rings.append(
                _section(
                    gmsh, wet, start + (stop - start) * k / n, low, high, count, center
                )
            )
        rings.append(top)
        intervals.append(dict(z0_m=start, z1_m=stop, axial_cells=n))
    vertices = [p.tolist() for ring in rings for p in ring]
    faces = []
    for j in range(len(rings) - 1):
        for i in range(count):
            k = (i + 1) % count
            faces.append(
                [j * count + i, j * count + k, (j + 1) * count + k, (j + 1) * count + i]
            )
    cap_v, cap_f = _cap_ogrid(rings[0], target, center)
    offset = len(vertices)
    vertices.extend(cap_v)
    faces.extend([[i + offset for i in face] for face in cap_f])
    return (
        vertices,
        faces,
        dict(
            algorithm="CAD axial sections, equal-angle rings, mapped radial shoulders and four-block O-grid bottom",
            azimuth_cells=count,
            axial_intervals=intervals,
            ring_count=len(rings),
            target_axial_radial_spacing_m=target,
            axis_center_xy_m=center.tolist(),
            section_sampling="1024 samples per original CAD curve; periodic polar interpolation",
            source_shape="Original CAD sections retained; horizontal plate boundaries taken from CAD face loops",
        ),
    )


def polygon_blocks(profiles, request):
    """Conforming ruled blocks between two convex prismatic polygon contours."""
    import numpy as np
    from shapely.geometry import LineString, Polygon

    additions = [p for p in profiles or [] if p["operation"] == "add"]
    cuts = [p for p in profiles or [] if p["operation"] == "cut"]
    if len(additions) != 2 or len(cuts) != 2:
        raise ValueError("多边形环形分块需要一个等截面外体和一个贯通等截面开口")
    if any(p.get("curve", "polyline") != "polyline" for p in profiles):
        raise ValueError("多边形分块保留折角；曲线轮廓采用环带或曲面分区")
    for pair in (additions, cuts):
        if not np.allclose(
            np.array(pair[0]["points_m"])[:, :2],
            np.array(pair[1]["points_m"])[:, :2],
            atol=1e-9,
        ):
            raise ValueError("多边形环形分块需要沿 z 轴的等截面轮廓")
    outer = np.array(additions[0]["points_m"])[:, :2]
    inner = np.array(cuts[0]["points_m"])[:, :2]
    outer_polygon, inner_polygon = Polygon(outer), Polygon(inner)
    if not outer_polygon.contains(inner_polygon):
        raise ValueError("贯通开口须完整位于外体内")
    center = np.array(inner_polygon.centroid.coords[0])
    angles = sorted(
        {
            round(math.atan2(p[1] - center[1], p[0] - center[0]), 12)
            for p in np.vstack([outer, inner])
        }
    )
    radius = 4 * float(np.max(np.linalg.norm(outer - center, axis=1)))

    def ray(polygon, theta):
        target = center + radius * np.array([math.cos(theta), math.sin(theta)])
        hit = LineString([center, target]).intersection(polygon.boundary)
        if hit.geom_type != "Point":
            raise ValueError("环形分块轮廓须相对中心为单值星形")
        return np.array(hit.coords[0])

    a = np.array([ray(inner_polygon, t) for t in angles])
    b = np.array([ray(outer_polygon, t) for t in angles])
    inside, outside = [], []
    segments = []
    for i in range(len(angles)):
        j = (i + 1) % len(angles)
        n = max(
            1,
            math.ceil(
                max(np.linalg.norm(a[j] - a[i]), np.linalg.norm(b[j] - b[i]))
                / request.mesh_size_m
            ),
        )
        inside.extend(a[i] + (a[j] - a[i]) * k / n for k in range(n))
        outside.extend(b[i] + (b[j] - b[i]) * k / n for k in range(n))
        segments.append(n)
    inside, outside = np.array(inside), np.array(outside)
    count = len(inside)
    z0 = min(p[2] for p in additions[0]["points_m"] + additions[1]["points_m"])
    z1 = min(
        0.0, max(p[2] for p in additions[0]["points_m"] + additions[1]["points_m"])
    )
    cut_low = min(p[2] for p in cuts[0]["points_m"] + cuts[1]["points_m"])
    cut_high = max(p[2] for p in cuts[0]["points_m"] + cuts[1]["points_m"])
    if not cut_low < z0 or cut_high < z1 or z0 >= z1:
        raise ValueError("开口须贯通湿体的底面与水线")
    nz = max(1, math.ceil((z1 - z0) / request.mesh_size_m))
    nr = max(
        1,
        math.ceil(
            float(np.max(np.linalg.norm(outside - inside, axis=1)))
            / request.mesh_size_m
        ),
    )
    vertices = []
    faces = []

    def add(points, z):
        ids = list(range(len(vertices), len(vertices) + len(points)))
        vertices.extend([[p[0], p[1], z] for p in points])
        return ids

    def band(a, b, reverse=False):
        for i in range(count):
            k = (i + 1) % count
            face = [a[i], a[k], b[k], b[i]]
            faces.append(face[::-1] if reverse else face)

    for points, reverse in ((outside, False), (inside, True)):
        rings = [add(points, z0 + (z1 - z0) * j / nz) for j in range(nz + 1)]
        for lower, upper in zip(rings, rings[1:]):
            band(lower, upper, reverse)
    bottom = [add(inside + (outside - inside) * j / nr, z0) for j in range(nr + 1)]
    for inner_ring, outer_ring in zip(bottom, bottom[1:]):
        band(inner_ring, outer_ring)
    return (
        vertices,
        faces,
        dict(
            algorithm="Feature-ray matching, mapped polygon annulus and conforming vertical blocks",
            perimeter_cells=count,
            axial_cells=nz,
            radial_cells=nr,
            feature_edge_segments=segments,
            center_xy_m=center.tolist(),
            source_shape="Original polygon vertices and a through prismatic opening",
        ),
    )


def _surface_wet_arc(gmsh, surface, count):
    import numpy as np

    curves = {abs(t) for _, t in gmsh.model.getBoundary([(2, surface)], combined=False)}
    pieces = [_curve(gmsh, t) for t in sorted(curves)]
    pieces = [p for p in pieces if np.max(np.abs(p[:, 2])) > 1e-7]
    starts = [
        (p[k, 1], i, k)
        for i, p in enumerate(pieces)
        for k in (0, -1)
        if abs(p[k, 2]) < 1e-6
    ]
    if len(starts) != 2:
        raise ValueError("站位网格需要由两侧水线端点连接的单一湿剖面")
    _, index, end = max(starts)
    first = pieces.pop(index)
    points = list(first[::-1] if end == -1 else first)
    while pieces:
        choices = [
            (np.linalg.norm(p[k] - points[-1]), i, k)
            for i, p in enumerate(pieces)
            for k in (0, -1)
        ]
        error, index, end = min(choices)
        if error > 1e-6:
            raise ValueError("站位湿剖面曲线不连续")
        piece = pieces.pop(index)
        points.extend((piece[::-1] if end == -1 else piece)[1:])
    points = np.array(points)
    keel = int(np.argmin(points[:, 2]))
    if keel in (0, len(points) - 1):
        raise ValueError("湿剖面需要明确的底部及两侧水线")

    def resample(p, n):
        distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        samples = np.linspace(0, distance[-1], n + 1)
        return np.column_stack(
            [np.interp(samples, distance, p[:, k]) for k in range(3)]
        )

    a = resample(points[: keel + 1], count // 2)
    b = resample(points[keel:], count // 2)
    arc = np.vstack([a, b[1:]])
    arc[[0, -1], 2] = 0
    return arc


def _axial_wet_arc(gmsh, wet, station, low, high, count):
    plane = _plane(gmsh, 0, station, low, high)
    made, _ = gmsh.model.occ.intersect(
        wet, [(2, plane)], removeObject=False, removeTool=True
    )
    gmsh.model.occ.synchronize()
    surfaces = [t for dim, t in made if dim == 2]
    if len(surfaces) != 1:
        raise ValueError("站位网格需要单一连通的船体剖面")
    result = _surface_wet_arc(gmsh, surfaces[0], count)
    result[:, 0] = station
    return result


def _cap_mesh(gmsh, arc, direction):
    import numpy as np

    original = gmsh.model.getCurrent()
    gmsh.model.add(original + "_end_cap")
    try:
        occ = gmsh.model.occ
        spacing = float(np.median(np.linalg.norm(np.diff(arc, axis=0), axis=1)))
        closing = max(1, math.ceil(float(np.linalg.norm(arc[0] - arc[-1])) / spacing))
        points = list(arc)
        points.extend(
            arc[-1] + (arc[0] - arc[-1]) * j / closing for j in range(1, closing)
        )
        tags = [occ.addPoint(*p) for p in points]
        curves = [occ.addLine(a, b) for a, b in zip(tags, tags[1:] + tags[:1])]
        surface = occ.addPlaneSurface([occ.addWire(curves)])
        occ.synchronize()
        for curve in curves:
            gmsh.model.mesh.setTransfiniteCurve(curve, 2)
        gmsh.option.setNumber("Mesh.MeshSizeMax", spacing * 1.3)
        gmsh.option.setNumber("Mesh.MeshSizeMin", spacing * 0.2)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
        gmsh.option.setNumber("Mesh.Algorithm", 8)
        gmsh.option.setNumber("Mesh.RecombineAll", 1)
        gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)
        gmsh.option.setNumber("Mesh.RecombineMinimumQuality", 0.2)
        gmsh.model.mesh.generate(2)
        ids, coordinates, _ = gmsh.model.mesh.getNodes()
        coordinates = np.array(coordinates).reshape(-1, 3)
        lookup = {int(tag): i for i, tag in enumerate(ids)}
        kinds, _, elements = gmsh.model.mesh.getElements(2, surface)
        faces = []
        for kind, elements in zip(kinds, elements):
            if kind not in (2, 3):
                raise ValueError("端封板采用一阶三角或四边形")
            for face in np.array(elements).reshape(-1, 3 if kind == 2 else 4):
                face = [lookup[int(i)] for i in face]
                p = coordinates[face]
                if np.cross(p[1] - p[0], p[2] - p[0])[0] * direction < 0:
                    face.reverse()
                faces.append(face)
        return coordinates.tolist(), faces
    finally:
        gmsh.model.remove()
        gmsh.model.setCurrent(original)


def station_bands(gmsh, wet, low, high, profiles, request):
    import numpy as np

    if (
        not profiles
        or len({p["solid"] for p in profiles}) != 1
        or any(p["operation"] != "add" for p in profiles)
    ):
        raise ValueError("站位带网格需要单一放样船体的源剖面")
    if any(p.get("curve") != "spline" for p in profiles):
        raise ValueError("站位带采用平顺插值剖面；折角型线采用特征分区以保留角点")
    if any(np.ptp(np.array(p["points_m"])[:, 0]) > 1e-7 for p in profiles):
        raise ValueError("站位带网格采用目标 x 轴为纵向")
    x0 = min(p["points_m"][0][0] for p in profiles)
    x1 = max(p["points_m"][0][0] for p in profiles)
    count = 2 * math.ceil(request.curvature_samples / 2)
    longitudinal = request.longitudinal_cells or max(
        32, math.ceil(math.pi * (x1 - x0) / request.mesh_size_m)
    )
    if longitudinal * count > request.max_panels:
        raise ValueError("站位与剖面分段已超过本次面元预算")
    t = np.linspace(0, 1, longitudinal + 1)
    blend = request.longitudinal_grading_blend
    stations = x0 + (x1 - x0) * (blend * t + (1 - blend) * (1 - np.cos(np.pi * t)) / 2)
    stations = np.r_[
        stations[0],
        (stations[0] + stations[1]) / 2,
        stations[1:-1],
        (stations[-2] + stations[-1]) / 2,
        stations[-1],
    ]
    longitudinal = len(stations) - 1
    rings = [_axial_wet_arc(gmsh, wet, float(x), low, high, count) for x in stations]
    vertices = [p.tolist() for ring in rings for p in ring]
    faces = []
    width = count + 1
    for j in range(longitudinal):
        for i in range(count):
            faces.append(
                [
                    j * width + i,
                    (j + 1) * width + i,
                    (j + 1) * width + i + 1,
                    j * width + i + 1,
                ]
            )
    for ring, direction in ((rings[0], -1), (rings[-1], 1)):
        cap_v, cap_f = _cap_mesh(gmsh, ring, direction)
        shift = len(vertices)
        vertices.extend(cap_v)
        faces.extend([[i + shift for i in face] for face in cap_f])
    return (
        vertices,
        faces,
        dict(
            algorithm="CAD station cuts, matched keel/waterline arc bands and cosine longitudinal grading",
            longitudinal_cells=longitudinal,
            longitudinal_grading_blend=blend,
            finite_end_interval_subdivisions=2,
            wet_section_cells=count,
            stations_m=stations.tolist(),
            source_shape="Original loft CAD cross-sections, sampled on each side of the keel",
            local_triangles="Planar finite end-cap transitions only",
        ),
    )
