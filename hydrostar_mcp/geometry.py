"""Original deterministic teaching geometries, generated only from scalar parameters.

No installed sample or external mesh is read here. Coordinates use SI units,
x longitudinal, y port, z upward, and z=0 at the equilibrium waterline.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

from .core import integrate_mesh


@dataclass
class Mesh:
    nodes: dict
    panels: list
    meta: dict
    reference: dict
    provenance: dict

    def hydrostatics(self):
        return integrate_mesh(self.nodes, self.panels, self.meta)

    def write(self, path, project):
        rows = [
            f"PROJECT {project}",
            "USER PARAMETRIC_GENERATOR",
            "NBBODY 1",
            "SYMMETRY 1 1",
            f"NUMPANEL 1 1 {len(self.panels)}",
            "ZFSURFACE 0",
            f"RHO {self.meta['RHO'][0][0]:.12g}",
            f"GRAVITY {self.meta['GRAVITY'][0][0]:.12g}",
            "COORDINATES TYPE 0",
        ]
        rows += [
            f"{i} " + " ".join(f"{v:.12g}" for v in p) for i, p in self.nodes.items()
        ]
        rows += ["ENDCOORDINATES", "PANEL TYPE 0"]
        rows += [" ".join(map(str, p)) for p in self.panels]
        Path(path).write_text(
            "\n".join(rows + ["ENDPANEL", "ENDFILE", ""]), encoding="ascii"
        )


def _mesh(g, nodes, panels, reference, rho, gravity, **extra):
    return Mesh(
        nodes,
        panels,
        {
            "SYMMETRY_BODY": [[1, 1]],
            "ZFSURFACE": [[0]],
            "RHO": [[rho]],
            "GRAVITY": [[gravity]],
        },
        reference,
        dict(
            origin="generated_from_project_parameters",
            external_mesh_files=[],
            generator="hydrostar_mcp.geometry",
            generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            parameter_sha256=hashlib.sha256(
                json.dumps(g, sort_keys=True).encode()
            ).hexdigest(),
            **extra,
        ),
    )


def semisub_boxes(g, dry=False):
    """Non-overlapping boxes meeting at faces; full-body component geometry."""
    L, w, h, T = (
        g[k] for k in ("pontoon_length", "pontoon_width", "pontoon_height", "draft")
    )
    a, b, c, bh = (
        g[k] for k in ("column_x", "pontoon_y", "column_width", "crossbeam_height")
    )
    boxes = []
    for y in (-b, b):
        boxes.append(((-L / 2, y - w / 2, -T), (L / 2, y + w / 2, -T + h)))
        for x in (-a, a):
            boxes.append(((x - c / 2, y - c / 2, -T + h), (x + c / 2, y + c / 2, 0.0)))
    gap = 2 * b - w
    for x in (-a, a):
        boxes.append(((x - c / 2, -gap / 2, -T), (x + c / 2, gap / 2, -T + bh)))
    if dry:
        height = g["freeboard"]
        for x in (-a, a):
            for y in (-b, b):
                boxes.append(
                    ((x - c / 2, y - c / 2, 0), (x + c / 2, y + c / 2, height))
                )
        d, t = g["deck_width"], g["deck_thickness"]
        boxes.append(((-d / 2, -d / 2, height), (d / 2, d / 2, height + t)))
    return boxes


def build_semisub(g, rho=1025.0, gravity=9.81):
    boxes = [
        ((lo[0], max(0, lo[1]), lo[2]), hi) for lo, hi in semisub_boxes(g) if hi[1] > 0
    ]
    axes = []
    for k in range(3):
        breaks = sorted({v[k] for box in boxes for v in box})
        axis = [breaks[0]]
        for lo, hi in zip(breaks, breaks[1:]):
            n = math.ceil((hi - lo) / g["target_panel_m"] - 1e-12)
            axis.extend(lo + (hi - lo) * i / n for i in range(1, n + 1))
        axes.append(axis)
    xs, ys, zs = axes
    occupied = set()
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            for k in range(len(zs) - 1):
                p = [(axis[t] + axis[t + 1]) / 2 for axis, t in zip(axes, (i, j, k))]
                if any(all(lo[d] < p[d] < hi[d] for d in range(3)) for lo, hi in boxes):
                    occupied.add((i, j, k))
    nodes, ids, panels = {}, {}, []

    def face(indices):
        out = []
        for index in indices:
            if index not in ids:
                ids[index] = len(ids) + 1
                nodes[ids[index]] = tuple(axes[d][index[d]] for d in range(3))
            out.append(ids[index])
        panels.append(tuple(out))

    for i, j, k in sorted(occupied):
        if (i - 1, j, k) not in occupied:
            face([(i, j, k), (i, j, k + 1), (i, j + 1, k + 1), (i, j + 1, k)])
        if (i + 1, j, k) not in occupied:
            face(
                [
                    (i + 1, j, k),
                    (i + 1, j + 1, k),
                    (i + 1, j + 1, k + 1),
                    (i + 1, j, k + 1),
                ]
            )
        if (i, j - 1, k) not in occupied and ys[j] > 1e-10:
            face([(i, j, k), (i + 1, j, k), (i + 1, j, k + 1), (i, j, k + 1)])
        if (i, j + 1, k) not in occupied:
            face(
                [
                    (i, j + 1, k),
                    (i, j + 1, k + 1),
                    (i + 1, j + 1, k + 1),
                    (i + 1, j + 1, k),
                ]
            )
        if (i, j, k - 1) not in occupied:
            face([(i, j, k), (i, j + 1, k), (i + 1, j + 1, k), (i + 1, j, k)])
        if (i, j, k + 1) not in occupied and zs[k + 1] < -1e-10:
            face(
                [
                    (i, j, k + 1),
                    (i + 1, j, k + 1),
                    (i + 1, j + 1, k + 1),
                    (i, j + 1, k + 1),
                ]
            )
    L, w, h, T, a, b, c, bh = (
        g[k]
        for k in (
            "pontoon_length",
            "pontoon_width",
            "pontoon_height",
            "draft",
            "column_x",
            "pontoon_y",
            "column_width",
            "crossbeam_height",
        )
    )
    gap, ch = 2 * b - w, T - h
    vols = [2 * L * w * h, 4 * c * c * ch, 2 * c * gap * bh]
    centers = [-T + h / 2, -ch / 2, -T + bh / 2]
    volume = sum(vols)
    area = (
        4 * (L * w + L * h + w * h)
        + 16 * c * ch
        - 4 * c * c
        + 4 * (c * gap - c * bh + gap * bh)
    )
    ref = dict(
        volume_m3=volume,
        cb_m=[0, 0, sum(v * z for v, z in zip(vols, centers)) / volume],
        wetted_area_m2=area,
        waterplane_area_m2=4 * c * c,
        waterplane_inertia_m4=[
            4 * (c**4 / 12 + c * c * b * b),
            4 * (c**4 / 12 + c * c * a * a),
        ],
        basis="exact non-overlapping box union; interfaces removed",
    )
    return _mesh(
        g,
        nodes,
        panels,
        ref,
        rho,
        gravity,
        discretization="conforming Cartesian union boundary; y>=0; wet panels only",
    )


def build_curved_hull(g, rho=1025.0, gravity=9.81):
    """Lower half ellipsoid, with homothetic rings and planar trapezoids.

    A small documented ring-radius correction holds displacement constant across
    levels. Bow/stern, length, maximum beam and draft stay fixed.
    """
    a, b, c = g["length"] / 2, g["beam"] / 2, g["draft"]
    nl, ns = g["n_length"], g["n_section"]
    counts = []
    for i in range(1, nl):
        n, distance = ns, min(i, nl - i)
        while n % 2 == 0 and n > 3 and distance < n / 2:
            n //= 2
        counts.append(n)

    def make(scale):
        nodes, panels, rings = {1: (-a, 0.0, 0.0)}, [], []
        for i, n in enumerate(counts, 1):
            phi = math.pi * i / nl
            r = min(1.0, scale * math.sin(phi))
            ring = []
            for j in range(n + 1):
                theta = math.pi * j / (2 * n)
                ident = len(nodes) + 1
                nodes[ident] = (
                    -a * math.cos(phi),
                    b * r * math.sin(theta),
                    -c * r * math.cos(theta) if j < n else 0.0,
                )
                ring.append(ident)
            rings.append(ring)
        tip = len(nodes) + 1
        nodes[tip] = (a, 0.0, 0.0)

        def tri(p, q, r):
            panels.append((p, q, r, r))

        for j in range(len(rings[0]) - 1):
            tri(1, rings[0][j + 1], rings[0][j])
        for A, B in zip(rings, rings[1:]):
            na, nb = len(A) - 1, len(B) - 1
            ia = ib = 0
            while ia < na or ib < nb:
                va = (ia + 1) / na if ia < na else math.inf
                vb = (ib + 1) / nb if ib < nb else math.inf
                if abs(va - vb) < 1e-12:
                    if abs(ia / na - ib / nb) < 1e-12:
                        panels.append((A[ia], A[ia + 1], B[ib + 1], B[ib]))
                    else:
                        tri(A[ia], A[ia + 1], B[ib])
                        tri(A[ia + 1], B[ib + 1], B[ib])
                    ia += 1
                    ib += 1
                elif va < vb:
                    tri(A[ia], A[ia + 1], B[ib])
                    ia += 1
                else:
                    tri(A[ia], B[ib + 1], B[ib])
                    ib += 1
        for j in range(len(rings[-1]) - 1):
            tri(rings[-1][j], rings[-1][j + 1], tip)
        # Mirror the bow-side transition triangulation exactly to the stern.
        # This preserves fore/aft symmetry even where ring counts change.
        lookup = {tuple(round(v, 10) for v in p): i for i, p in nodes.items()}
        left = [p for p in panels if max(nodes[i][0] for i in p) < 1e-8]
        panels = left + [
            tuple(
                lookup[
                    (
                        -round(nodes[i][0], 10),
                        round(nodes[i][1], 10),
                        round(nodes[i][2], 10),
                    )
                ]
                for i in reversed(p)
            )
            for p in left
        ]
        return nodes, panels

    reference = dict(
        volume_m3=2 * math.pi * a * b * c / 3,
        cb_m=[0, 0, -3 * c / 8],
        waterplane_area_m2=math.pi * a * b,
        waterplane_inertia_m4=[math.pi * a * b**3 / 4, math.pi * b * a**3 / 4],
        basis="analytic lower half ellipsoid",
    )
    raw_nodes, panels = make(1.0)
    meta = {"SYMMETRY_BODY": [[1, 1]]}
    raw_volume = integrate_mesh(raw_nodes, panels, meta)["volume"]
    lo, hi = 1.0, 1.05
    if integrate_mesh(make(hi)[0], panels, meta)["volume"] < reference["volume_m3"]:
        raise ValueError("船体离散过粗；半径修正超过 5%，请细化网格")
    for _ in range(36):
        mid = (lo + hi) / 2
        nodes, _ = make(mid)
        if integrate_mesh(nodes, panels, meta)["volume"] < reference["volume_m3"]:
            lo = mid
        else:
            hi = mid
    scale = (lo + hi) / 2
    nodes, panels = make(scale)
    return _mesh(
        g,
        nodes,
        panels,
        reference,
        rho,
        gravity,
        formula="x=-L/2*cos(phi); y=B/2*r*sin(theta); z=-T*r*cos(theta); r=min(1,s*sin(phi))",
        volume_conserving_discretization=dict(
            raw_volume_relative_error=(raw_volume / reference["volume_m3"] - 1),
            radial_scale=scale,
            maximum_node_shift_m=max(math.dist(nodes[i], raw_nodes[i]) for i in nodes),
        ),
        ring_sections=counts,
    )


def build(g, rho=1025.0, gravity=9.81):
    if g["type"] in ("section_hull", "column_semisub"):
        from .forms_geometry import build_form

        return build_form(g, rho, gravity)
    return {"semisub": build_semisub, "curved_hull": build_curved_hull}[g["type"]](
        g, rho, gravity
    )


def mesh_quality(mesh):
    """Oriented edge incidence, one connected wet surface, and planar panels."""
    edges = defaultdict(list)
    bad_planarity = []
    for i, panel in enumerate(mesh.panels):
        ids = list(dict.fromkeys(panel))
        for u, v in zip(ids, ids[1:] + ids[:1]):
            edges[min(u, v), max(u, v)].append((i, 1 if u < v else -1))
        if len(ids) == 4:
            p, q, r, s = (mesh.nodes[v] for v in ids)
            u = [q[k] - p[k] for k in range(3)]
            v = [r[k] - p[k] for k in range(3)]
            cross = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            ]
            norm = math.sqrt(sum(x * x for x in cross))
            distance = (
                abs(sum(cross[k] * (s[k] - p[k]) for k in range(3))) / norm
                if norm
                else math.inf
            )
            if distance > 1e-8:
                bad_planarity.append(i + 1)
    adjacency = defaultdict(set)
    bad_edges = []
    boundary = 0
    for (u, v), inc in edges.items():
        if len(inc) == 2 and inc[0][1] + inc[1][1] == 0:
            a, b = inc[0][0], inc[1][0]
            adjacency[a].add(b)
            adjacency[b].add(a)
        elif len(inc) == 1 and any(
            abs(mesh.nodes[u][k]) < 1e-8 and abs(mesh.nodes[v][k]) < 1e-8
            for k in (1, 2)
        ):
            boundary += 1
        else:
            bad_edges.append([u, v])
    remaining = set(range(len(mesh.panels)))
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            for neighbor in adjacency[stack.pop()] & remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    expected = mesh.reference.get("expected_wet_components", 1)
    return dict(
        passed=not bad_edges and not bad_planarity and components == expected,
        connected_wet_surfaces=components,
        expected_wet_surfaces=expected,
        invalid_edges=bad_edges[:20],
        nonplanar_panels=bad_planarity[:20],
        permitted_cut_edges=boundary,
    )


def combine_box_masses(total_mass, components):
    """Aggregate box/cylinder/point/given-rigid-body inertia using parallel axes."""
    if not math.isclose(sum(c["mass_fraction"] for c in components), 1, abs_tol=1e-10):
        raise ValueError("质量分量比例之和必须为 1")
    cog = [
        sum(c["mass_fraction"] * c["center_m"][k] for c in components) for k in range(3)
    ]
    tensor = [[0.0] * 3 for _ in range(3)]
    for c in components:
        f = c["mass_fraction"]
        size = c["size_m"]
        d = [c["center_m"][k] - cog[k] for k in range(3)]
        shape = c.get("shape", "box")
        own = [[0.0] * 3 for _ in range(3)]
        if shape == "box":
            for i in range(3):
                own[i][i] = sum(size[k] ** 2 for k in range(3) if k != i) / 12
        elif shape == "vertical_cylinder":
            radius = size[0] / 2
            height = size[2]
            own[0][0] = own[1][1] = (3 * radius**2 + height**2) / 12
            own[2][2] = radius**2 / 2
        elif shape == "rigid_body":
            r = c["gyradius_m"]
            for i in range(3):
                own[i][i] = r[i] ** 2
            for k, (i, j) in enumerate(((0, 1), (0, 2), (1, 2)), 3):
                own[i][j] = own[j][i] = math.copysign(r[k] ** 2, r[k])
        for i in range(3):
            for j in range(3):
                value = (
                    own[i][j] + (sum(v * v for v in d) if i == j else 0) - d[i] * d[j]
                )
                tensor[i][j] += f * total_mass * value
    radii = [math.sqrt(tensor[i][i] / total_mass) for i in range(3)]
    radii += [
        math.copysign(math.sqrt(abs(tensor[i][j]) / total_mass), tensor[i][j])
        for i, j in ((0, 1), (0, 2), (1, 2))
    ]
    return dict(
        mass_kg=total_mass,
        cog_m=cog,
        gyradius_m=radii,
        inertia_kg_m2=tensor,
        components=[
            dict(**c, mass_kg=total_mass * c["mass_fraction"]) for c in components
        ],
    )
