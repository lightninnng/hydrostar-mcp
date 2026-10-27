"""Data-only readers and an isolated OpenCASCADE/Gmsh surface-mesh kernel."""

from __future__ import annotations

import csv
import math
import re
from .geometry_sources import LoftDocument, LoftSolid, Profile


def unit_scale(units):
    if units not in {"m", "cm", "mm"}:
        raise ValueError("型值表与表面网格须显式提供 m、cm 或 mm 单位")
    return {"m": 1.0, "cm": 0.01, "mm": 0.001}[units]


def frame_points(points, request, scale=1.0):
    axes = [
        ("xyz".index(v.lstrip("-")), -1 if v.startswith("-") else 1)
        for v in request.axis_map
    ]
    return [
        [
            scale * p[index] * sign
            + request.translation_m[k]
            - (request.waterline_z_m if k == 2 else 0)
            for k, (index, sign) in enumerate(axes)
        ]
        for p in points
    ]


def profile_xyz(profile, axis):
    a = "xyz".index(axis)
    other = [i for i in range(3) if i != a]
    points = []
    for u, v in profile.points:
        point = [0.0] * 3
        point[a], point[other[0]], point[other[1]] = profile.position, u, v
        points.append(point)
    return points


def csv_document(path, request):
    groups = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"station", "u", "v"} <= set(reader.fieldnames or []):
            raise ValueError("CSV 型值表表头须包含 station,u,v；各剖面沿轮廓顺序排列")
        for row in reader:
            station, u, v = [float(row[k]) for k in ("station", "u", "v")]
            groups.setdefault(station, []).append([u, v])
    return document_from_groups(groups, request)


def document_from_groups(groups, request):
    profiles = []
    for position, points in sorted(groups.items()):
        if request.mirror_half_sections:
            if request.section_axis != "x":
                raise ValueError("半宽镜像输入采用 x 为站位轴，u 为半宽，v 为高程")
            if any(u < 0 for u, _ in points):
                raise ValueError("半宽资料应位于 u>=0")
            if abs(points[0][0]) > 1e-10 or abs(points[-1][0]) > 1e-10:
                # Connect the upper profile endpoints across the deck, retaining given coordinates.
                points = points + [[-u, v] for u, v in reversed(points)]
            else:
                points = points + [[-u, v] for u, v in reversed(points[1:-1])]
        if len(points) > 1 and points[0] == points[-1]:
            points = points[:-1]
        profiles.append(Profile(position=position, points=points))
    return LoftDocument(
        solids=[
            LoftSolid(
                name="section_body",
                axis=request.section_axis,
                curve=request.section_curve,
                ruled=request.longitudinal_ruled,
                profiles=profiles,
            )
        ]
    )


def dxf_document(path, request):
    import ezdxf
    from ezdxf.path import make_path
    from shapely.geometry import Polygon

    if not request.station_layers:
        raise ValueError("DXF 需要 station_layers 明确给出图层与站位坐标的对应关系")
    drawing = ezdxf.readfile(path)
    if request.units == "file":
        code = int(drawing.header.get("$INSUNITS", 0))
        scale = {4: 0.001, 5: 0.01, 6: 1.0}.get(code)
        if scale is None:
            raise ValueError("DXF INSUNITS 未明确为毫米、厘米或米，请显式指定 units")
    else:
        scale = unit_scale(request.units)
    groups = {}
    for layer, position in request.station_layers.items():
        entities = [e for e in drawing.modelspace() if e.dxf.layer == layer]
        if len(entities) != 1:
            raise ValueError(
                f"图层 {layer} 应包含一条已连接的闭合剖面，当前为 {len(entities)} 个图元"
            )
        entity = entities[0]
        if entity.dxftype() not in {
            "LWPOLYLINE",
            "POLYLINE",
            "SPLINE",
            "CIRCLE",
            "ELLIPSE",
        }:
            raise ValueError(f"图层 {layer} 的 {entity.dxftype()} 请先连接为闭合型线")
        curve = make_path(entity)
        if not curve.is_closed:
            raise ValueError(f"图层 {layer} 的型线尚未闭合")
        coords = list(curve.flattening(request.curve_tolerance_m / scale))
        if any(abs(p.z) > request.curve_tolerance_m / scale for p in coords):
            raise ValueError("DXF 剖面应在二维 XY 平面内；X/Y 分别作为 u/v")
        points = [[float(p.x), float(p.y)] for p in coords]
        if math.dist(points[0], points[-1]) < request.weld_tolerance_m / scale:
            points.pop()
        if not Polygon(points).is_valid:
            raise ValueError(f"图层 {layer} 的型线存在自交")
        groups[position] = points
    if max(len(p) for p in groups.values()) > 5000:
        raise ValueError("单剖面离散点数超过 5000；请核对曲线容差与源单位")
    # Preserve every supplied corner and flattened curve point. Polyline profiles
    # retain corresponding corner counts; smooth spline profiles may vary in count.
    return document_from_groups(groups, request), scale


def validate_digitization(evidence):
    import numpy as np

    if not evidence:
        return
    calibration = evidence.get("calibration", [])
    checkpoints = evidence.get("checkpoints", [])
    tolerance = evidence.get("tolerance_m", 0)
    if len(calibration) < 3 or len(checkpoints) < 2 or not (0 < tolerance <= 0.1):
        raise ValueError(
            "描线资料须有至少 3 个标定点、2 个独立检查点及明确的米制误差上限"
        )
    matrix = np.array([[*p["pixel"], 1] for p in calibration], dtype=float)
    target = np.array([p["uv_m"] for p in calibration], dtype=float)
    if (
        not np.isfinite(matrix).all()
        or not np.isfinite(target).all()
        or np.linalg.matrix_rank(matrix) < 3
    ):
        raise ValueError("图纸标定点须有限且不共线")
    fit = np.linalg.lstsq(matrix, target, rcond=None)[0]
    if np.max(np.linalg.norm(matrix @ fit - target, axis=1)) > tolerance:
        raise ValueError("图纸标定点的拟合残差超过指定米制误差上限")
    pixels = [c["pixel"] for c in calibration]
    if len({tuple(p["pixel"]) for p in checkpoints}) < 2:
        raise ValueError("须使用至少两个不同的独立检查点")
    for point in checkpoints:
        if any(math.dist(point["pixel"], pixel) < 0.1 for pixel in pixels):
            raise ValueError("独立检查点应与标定点分开")
        error = np.linalg.norm(np.r_[point["pixel"], 1] @ fit - point["uv_m"])
        if not math.isfinite(error) or error > tolerance:
            raise ValueError(f"图纸独立标定误差 {error:g} m 超过 {tolerance:g} m")
    if not re.fullmatch(r"[0-9a-f]{64}", str(evidence.get("source_sha256", ""))):
        raise ValueError("描线结果须记录源图纸 SHA-256")


def orient_cad_faces(gmsh, surface, faces, nodes, volumes, span):
    """Anchor surface winding to the CAD solid, independently of OCC face tags."""
    import numpy as np

    if not faces:
        return faces
    triangles = np.array([[nodes[i] for i in face] for face in faces])
    normals = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    areas = np.linalg.norm(normals, axis=1)
    for index in np.argsort(areas)[-3:][::-1]:
        if areas[index] <= 1e-16:
            continue
        center = triangles[index].mean(axis=0)
        closest, uv = gmsh.model.getClosestPoint(2, surface, center.tolist())
        normal = np.array(gmsh.model.getNormal(surface, uv))
        normal /= np.linalg.norm(normal)
        # Small CAD-space probes, decreasing to resolve thin connected features.
        for distance in (max(span * 1e-6, 1e-5), max(span * 1e-7, 1e-6)):
            plus = any(
                gmsh.model.isInside(3, tag, (closest + distance * normal).tolist())
                for _, tag in volumes
            )
            minus = any(
                gmsh.model.isInside(3, tag, (closest - distance * normal).tolist())
                for _, tag in volumes
            )
            if plus != minus:
                outward = -normal if plus else normal
                return (
                    faces
                    if float(normals[index] @ outward) > 0
                    else [f[::-1] for f in faces]
                )
    raise ValueError(
        f"CAD 曲面 {surface} 的内外法向判定不明确；请核对实体厚度和几何容差"
    )


def cad_surface(path, request):
    import gmsh
    import numpy as np
    from shapely.geometry import Polygon

    gmsh.initialize([], readConfigFiles=False, run=False, interruptible=False)
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.model.add(request.project)
    occ = gmsh.model.occ
    try:
        scale = unit_scale(request.units) if request.units != "file" else 1.0
        source_profiles = None
        if path.suffix.lower() in {".step", ".stp", ".igs", ".iges", ".brep"}:
            is_brep = path.suffix.lower() == ".brep"
            if (not is_brep and request.units != "file") or (
                is_brep and request.units == "file"
            ):
                raise ValueError(
                    "STEP/IGES 使用 units=file 读取文件单位；BREP 须明确指定 m、cm 或 mm"
                )
            gmsh.option.setString("Geometry.OCCTargetUnit", "M")
            if path.suffix.lower() in {".igs", ".iges"}:
                # In fresh OCC 7.8 processes, IGES unit parameters are registered
                # by the first reader construction. Discard that initialization
                # model, then explicitly re-read the original file into metres.
                gmsh.option.setString("Geometry.OCCTargetUnit", "")
                occ.importShapes(str(path))
                gmsh.model.remove()
                gmsh.model.add(request.project)
                gmsh.option.setString("Geometry.OCCTargetUnit", "M")
            entities = occ.importShapes(str(path))
            if not any(dim == 3 for dim, _ in entities):
                occ.healShapes(
                    [],
                    tolerance=request.weld_tolerance_m,
                    sewFaces=True,
                    makeSolids=True,
                )
            occ.synchronize()
            volumes = gmsh.model.getEntities(3)
            if not volumes:
                raise ValueError(
                    "CAD 尚未形成闭合实体；请修复缝隙、连接曲面并确认外部排水包络"
                )
            # Transform imported SI geometry with an explicit proper affine frame.
            affine = np.zeros((4, 4))
            affine[3, 3] = 1
            for k, axis in enumerate(request.axis_map):
                affine[k, "xyz".index(axis.lstrip("-"))] = scale * (
                    -1 if axis.startswith("-") else 1
                )
                affine[k, 3] = request.translation_m[k] - (
                    request.waterline_z_m if k == 2 else 0
                )
            occ.affineTransform(volumes, affine.reshape(-1).tolist())
        else:
            if request.units == "file" and path.suffix.lower() != ".dxf":
                raise ValueError("型值表和 JSON 剖面须明确指定 m、cm 或 mm")
            if path.suffix.lower() == ".csv":
                document = csv_document(path, request)
            elif path.suffix.lower() == ".dxf":
                document, scale = dxf_document(path, request)
            else:
                document = LoftDocument.model_validate_json(
                    path.read_text(encoding="utf-8-sig")
                )
            validate_digitization(document.digitization_evidence)
            if document.digitization_evidence and request.units != "m":
                raise ValueError("图纸描线工作区导出的剖面采用米制，请设置 units=m")
            additions, cuts, source_profiles = [], [], []
            for solid in document.solids:
                wires = []
                for profile in solid.profiles:
                    points = profile.points[:]
                    if points[0] == points[-1]:
                        points.pop()
                    polygon = Polygon(points)
                    if (
                        not polygon.is_valid
                        or polygon.area * scale**2 <= request.weld_tolerance_m**2
                    ):
                        raise ValueError(
                            f"{solid.name} 的剖面 {profile.position} 须为无自交的闭合有限面积轮廓"
                        )
                    coords = frame_points(
                        profile_xyz(
                            Profile(position=profile.position, points=points),
                            solid.axis,
                        ),
                        request,
                        scale,
                    )
                    if solid.curve == "spline" and request.spline_seam == "lowest_z":
                        first = min(range(len(coords)), key=lambda i: coords[i][2])
                        coords = coords[first:] + coords[:first]
                    tags = [occ.addPoint(*p) for p in coords]
                    if solid.curve == "spline":
                        edges = [occ.addSpline(tags + tags[:1])]
                    else:
                        edges = [
                            occ.addLine(a, b) for a, b in zip(tags, tags[1:] + tags[:1])
                        ]
                    wires.append(occ.addWire(edges, checkClosed=True))
                    source_profiles.append(
                        dict(
                            solid=solid.name,
                            operation=solid.operation,
                            position=profile.position,
                            points_m=coords,
                        )
                    )
                made = occ.addThruSections(
                    wires,
                    makeSolid=True,
                    makeRuled=solid.ruled,
                    maxDegree=3,
                    smoothing=False,
                )
                if not made or any(dim != 3 for dim, _ in made):
                    raise ValueError(f"{solid.name} 未形成封闭放样实体")
                (additions if solid.operation == "add" else cuts).extend(made)
            if not additions:
                raise ValueError("放样资料至少包含一个 add 实体")
            volumes = additions
            if cuts:
                volumes, _ = occ.cut(volumes, cuts, removeObject=True, removeTool=True)
        if len(volumes) > 1:
            volumes, _ = occ.fuse(
                volumes[:1], volumes[1:], removeObject=True, removeTool=True
            )
        occ.synchronize()
        bounds = np.array([gmsh.model.getBoundingBox(dim, tag) for dim, tag in volumes])
        low, high = bounds[:, :3].min(axis=0), bounds[:, 3:].max(axis=0)
        if low[2] >= -request.weld_tolerance_m:
            raise ValueError("外部排水实体须包含平均水线以下的体积")
        pad = max(float(np.max(high - low)), 1.0) + 1.0
        box = occ.addBox(
            float(low[0] - pad),
            float(low[1] - pad),
            float(low[2] - pad),
            float(high[0] - low[0] + 2 * pad),
            float(high[1] - low[1] + 2 * pad),
            float(-low[2] + pad),
        )
        wet, _ = occ.intersect(volumes, [(3, box)], removeObject=True, removeTool=True)
        if not wet or any(dim != 3 for dim, _ in wet):
            raise ValueError("水线裁剪后未形成有效的排水实体")
        occ.synchronize()
        cad_volume = sum(occ.getMass(dim, tag) for dim, tag in wet)
        cad_cb = [
            sum(
                occ.getMass(dim, tag) * occ.getCenterOfMass(dim, tag)[k]
                for dim, tag in wet
            )
            / cad_volume
            for k in range(3)
        ]
        # Remove leftover construction entities that are outside all final volumes.
        oriented = {
            abs(tag): (1 if tag > 0 else -1)
            for _, tag in gmsh.model.getBoundary(wet, combined=False, oriented=True)
        }
        final_boundary = set(oriented)
        gmsh.option.setNumber("Mesh.MeshSizeMin", request.mesh_size_m * 0.03)
        gmsh.option.setNumber("Mesh.MeshSizeMax", request.mesh_size_m)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", request.curvature_samples)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        # Waterline/section intersections can introduce short CAD edges. Resolve
        # their endpoints locally instead of forcing coarse cells beside them.
        curves = {
            abs(t)
            for _, t in gmsh.model.getBoundary(
                [(2, t) for t in final_boundary], combined=False
            )
        }
        short_points = set()
        shortest = request.mesh_size_m
        for curve in curves:
            length = occ.getMass(1, curve)
            if 0 < length < request.mesh_size_m / 10:
                points = gmsh.model.getBoundary([(1, curve)], combined=False)
                short_points.update(abs(t) for _, t in points)
                shortest = min(shortest, length)
        if short_points:
            distance = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(
                distance, "PointsList", sorted(short_points)
            )
            threshold = gmsh.model.mesh.field.add("Threshold")
            for name, value in {
                "InField": distance,
                "SizeMin": max(shortest / 2, request.mesh_size_m * 0.01),
                "SizeMax": request.mesh_size_m,
                "DistMin": max(shortest, request.mesh_size_m * 0.2),
                "DistMax": request.mesh_size_m / 2,
            }.items():
                gmsh.model.mesh.field.setNumber(threshold, name, value)
            gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.Algorithm", 6)
        gmsh.option.setNumber("Mesh.Smoothing", 20)
        for tag in final_boundary:
            if gmsh.model.getType(2, tag) == "Plane":
                gmsh.model.mesh.setAlgorithm(2, tag, 5)
        gmsh.model.mesh.generate(2)
        tags, coords, _ = gmsh.model.mesh.getNodes()
        nodes = {
            int(tag): point.tolist()
            for tag, point in zip(tags, np.array(coords).reshape(-1, 3))
        }
        faces = []
        for tag in sorted(final_boundary):
            surface_faces = []
            kinds, _, elements = gmsh.model.mesh.getElements(2, tag)
            for kind, connectivity in zip(kinds, elements):
                if kind != 2:
                    raise ValueError("CAD 离散采用一阶三角面元")
                for triangle in np.array(connectivity).reshape(-1, 3):
                    if all(
                        abs(nodes[int(i)][2]) <= request.weld_tolerance_m * 10
                        for i in triangle
                    ):
                        continue
                    surface_faces.append([int(i) for i in triangle])
            faces.extend(
                orient_cad_faces(
                    gmsh, tag, surface_faces, nodes, wet, float(np.max(high - low))
                )
            )
        used = sorted({i for face in faces for i in face})
        index = {tag: i for i, tag in enumerate(used)}
        return (
            [nodes[i] for i in used],
            [[index[i] for i in face] for face in faces],
            dict(
                kernel="OpenCASCADE/Gmsh",
                gmsh_version=gmsh.__version__,
                mesh_controls=dict(
                    max_size_m=request.mesh_size_m,
                    min_size_factor=0.03,
                    curvature_samples=request.curvature_samples,
                    algorithm="Frontal-Delaunay; planar Delaunay",
                    smoothing_steps=20,
                    short_edge_distance_field=True,
                ),
                cad_volume_m3=cad_volume,
                cad_cb_m=cad_cb,
                source_profiles=source_profiles,
                boundary_orientations=sorted(set(oriented.values())),
                orientation_method="CAD closest-point normals anchored by solid inside/outside probes; independently checked oriented edges",
                wet_solids=len(wet),
                curve_fit="interpolating spline"
                if request.section_curve == "spline"
                else "source curves/polyline",
            ),
        )
    finally:
        gmsh.finalize()


def source_surface(path, request):
    if path.suffix.lower() == ".hst":
        from .visualization import whole_mesh

        vertices, polygons = whole_mesh(path)
        vertices = frame_points(vertices, request, unit_scale(request.units))
    else:
        import meshio

        mesh = meshio.read(path)
        vertices = frame_points(
            mesh.points.tolist(), request, unit_scale(request.units)
        )
        polygons = []
        for block in mesh.cells:
            if block.type not in {"triangle", "quad"}:
                raise ValueError(
                    f"表面网格采用三角形或四边形面元，请先转换 {block.type}"
                )
            polygons.extend(block.data.tolist())
    faces = []
    for polygon in polygons:
        if len(polygon) == 4:
            import numpy as np

            p = np.array([vertices[i] for i in polygon])
            normal = np.cross(p[1] - p[0], p[2] - p[0])
            norm = float(np.linalg.norm(normal))
            if (
                norm < request.weld_tolerance_m**2
                or abs(np.dot(normal, p[3] - p[0])) / norm > request.curve_tolerance_m
            ):
                raise ValueError("输入四边形的平面性超出给定曲线容差")
        faces += [
            [polygon[0], polygon[i], polygon[i + 1]] for i in range(1, len(polygon) - 1)
        ]
    return (
        vertices,
        faces,
        dict(kernel="source_surface", source_panel_count=len(polygons)),
    )


def clip_and_weld(vertices, faces, tolerance):
    """Clip triangles at z=0 and weld shared points within a bounded SI tolerance."""
    import numpy as np

    vertices = np.asarray(vertices, dtype=float)
    if not np.isfinite(vertices).all():
        raise ValueError("源几何包含非有限坐标")
    output, triangles, buckets = [], [], {}

    def node(point):
        point = [float(v) for v in point]
        if abs(point[2]) <= tolerance:
            point[2] = 0.0
        key = tuple(math.floor(v / tolerance) for v in point)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for k in (-1, 0, 1):
                    for index in buckets.get((key[0] + i, key[1] + j, key[2] + k), []):
                        if math.dist(point, output[index]) <= tolerance:
                            return index
        index = len(output)
        output.append(point)
        buckets.setdefault(key, []).append(index)
        return index

    for face in faces:
        polygon = [vertices[i].copy() for i in face]
        clipped = []
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            inside_a, inside_b = a[2] <= tolerance, b[2] <= tolerance
            if inside_a:
                clipped.append(a)
            if inside_a != inside_b:
                t = -a[2] / (b[2] - a[2])
                p = a + t * (b - a)
                p[2] = 0.0
                clipped.append(p)
        if len(clipped) < 3 or all(abs(p[2]) <= tolerance for p in clipped):
            continue
        ids = list(dict.fromkeys(node(p) for p in clipped))
        for i in range(1, len(ids) - 1):
            if len({ids[0], ids[i], ids[i + 1]}) == 3:
                triangles.append([ids[0], ids[i], ids[i + 1]])
    return output, triangles


def build_surface(path, request):
    if path.suffix.lower() in {
        ".json",
        ".csv",
        ".dxf",
        ".step",
        ".stp",
        ".iges",
        ".igs",
        ".brep",
    }:
        vertices, faces, reference = cad_surface(path, request)
    else:
        vertices, faces, reference = source_surface(path, request)
    vertices, faces = clip_and_weld(vertices, faces, request.weld_tolerance_m)
    if request.flip_normals:
        faces = [list(reversed(face)) for face in faces]
    if len(faces) > request.max_panels:
        raise ValueError(
            f"湿面元 {len(faces)} 超过本次几何上限 {request.max_panels}，请调整网格尺寸"
        )
    return vertices, faces, reference
