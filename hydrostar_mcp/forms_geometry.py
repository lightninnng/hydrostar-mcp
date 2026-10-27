"""Source-informed hull families; original scalar-to-panel discretization.

Section hulls are transparent design proxies. Column geometry follows published
OC4 dimensions; slender connectors are represented separately in the mechanics.
"""

import hashlib
import math
from pathlib import Path

from .geometry import _mesh
from .core import integrate_mesh


class Surface:
    def __init__(self):
        self.nodes = {}
        self.ids = {}
        self.panels = []

    def node(self, p):
        key = tuple(round(v, 10) for v in p)
        if key not in self.ids:
            self.ids[key] = len(self.nodes) + 1
            self.nodes[self.ids[key]] = tuple(p)
        return self.ids[key]

    def face(self, points):
        ids = list(dict.fromkeys(self.node(p) for p in points))
        if len(ids) < 3:
            return
        p, q, r = (self.nodes[i] for i in ids[:3])
        u = [q[k] - p[k] for k in range(3)]
        v = [r[k] - p[k] for k in range(3)]
        cross = [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        ]
        norm = math.sqrt(sum(v * v for v in cross))
        if norm < 1e-10:
            return
        if (
            len(ids) == 4
            and abs(sum(cross[k] * (self.nodes[ids[3]][k] - p[k]) for k in range(3)))
            / norm
            > 1e-8
        ):
            self.face([self.nodes[ids[0]], self.nodes[ids[1]], self.nodes[ids[2]]])
            self.face([self.nodes[ids[0]], self.nodes[ids[2]], self.nodes[ids[3]]])
        else:
            self.panels.append(tuple(ids if len(ids) == 4 else ids + [ids[-1]]))


def smooth(v):
    return v * v * (3 - 2 * v)


def hull_ring(g, s, n):
    """Flat bottom -> circular bilge -> side, resampled by sectional arc length."""
    b, T = g["beam"] / 2, g["draft"]
    a, c, p = g["parallel_start"], g["parallel_end"], g["fullness_exponent"]
    if s < a:
        f = smooth(s / a) ** g["aft_fullness_exponent"]
        width = g["transom_width_ratio"] + (1 - g["transom_width_ratio"]) * f
        depth = g["transom_draft_ratio"] + (1 - g["transom_draft_ratio"]) * smooth(
            s / a
        )
    elif s > c:
        t = (s - c) / (1 - c)
        width = (1 - t**p) ** 0.8
        depth = 1 - 0.3 * smooth(t)
    else:
        width = depth = 1.0
    radius = math.sqrt((1 - g["midship_coefficient"]) * b * T / (1 - math.pi / 4))
    radius = min(radius, b * 0.8, T * 0.8)
    raw = []
    for j in range(21):
        raw.append(((b - radius) * j / 20, -T))
    for j in range(1, 41):
        t = math.pi * j / 80
        raw.append(
            (b - radius + radius * math.sin(t), -T + radius - radius * math.cos(t))
        )
    for j in range(1, 41):
        raw.append((b, (-T + radius) * (1 - j / 40)))
    profile = []
    advance = smooth(max(0, min(1, (s - 0.72) / 0.28)))
    bulb_window = math.sin(math.pi * max(0, min(1, (s - 0.72) / 0.28))) ** 2
    for y, z in raw:
        v = (z + T) / T
        bell = math.sin(math.pi * min(1, v / 0.82)) ** 2 if v < 0.82 else 0.0
        x = (
            g["length"] * (s - 0.5)
            + g["length"] * g["bulb_length_ratio"] * advance * bell
        )
        yy = width * y + b * g["bulb_breadth_ratio"] * bulb_window * bell
        point = (x, yy, z * depth)
        if not profile or math.dist(profile[-1], point) > 1e-10:
            profile.append(point)
    lengths = [0.0]
    for A, B in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.dist(A, B))
    out = []
    k = 1
    for j in range(n + 1):
        target = lengths[-1] * j / n
        while k < len(lengths) - 1 and lengths[k] < target:
            k += 1
        f = (target - lengths[k - 1]) / (lengths[k] - lengths[k - 1])
        out.append(
            tuple(profile[k - 1][d] * (1 - f) + profile[k][d] * f for d in range(3))
        )
    return out


def loft_hull(g, nl, ns):
    surface = Surface()
    rings = []
    for i in range(nl + 1):
        n = ns
        if min(i, nl - i) < 3:
            n = max(4, ns // 2)
        rings.append(hull_ring(g, i / nl, n))
    for A, B in zip(rings, rings[1:]):
        na, nb = len(A) - 1, len(B) - 1
        i = j = 0
        while i < na or j < nb:
            va = (i + 1) / na if i < na else math.inf
            vb = (j + 1) / nb if j < nb else math.inf
            if abs(va - vb) < 1e-10:
                surface.face([A[i], A[i + 1], B[j + 1], B[j]])
                i += 1
                j += 1
            elif va < vb:
                surface.face([A[i], A[i + 1], B[j]])
                i += 1
            else:
                surface.face([A[i], B[j + 1], B[j]])
                j += 1
    A = rings[0]
    center = (A[0][0], max(p[1] for p in A) / 2, min(p[2] for p in A) / 2)
    outline = [(A[0][0], 0, 0)] + list(reversed(A))
    for p, q in zip(outline, outline[1:] + outline[:1]):
        surface.face([center, p, q])
    return surface, rings


def waterplane(rings):
    points = [r[-1] for r in rings]
    # Both halves; top bow is at x=L/2 while the submerged bulb protrudes forward.
    polygon = [(p[0], p[1]) for p in points] + [(p[0], -p[1]) for p in reversed(points)]
    area = mx = iy = ix = 0.0
    for (x, y), (xx, yy) in zip(polygon, polygon[1:] + polygon[:1]):
        cross = x * yy - xx * y
        area += cross / 2
        mx += (x + xx) * cross / 6
        ix += (y * y + y * yy + yy * yy) * cross / 12
        iy += (x * x + x * xx + xx * xx) * cross / 12
    sign = 1 if area > 0 else -1
    return abs(area), [ix * sign, iy * sign - mx * mx / area * sign]


def build_section_hull(g, rho, gravity):
    surface, rings = loft_hull(g, g["n_length"], g["n_section"])
    # Independent denser quadrature mesh, with all production shape parameters fixed.
    ref, ref_rings = loft_hull(g, 192, 48)
    h = integrate_mesh(ref.nodes, ref.panels, {"SYMMETRY_BODY": [[1, 1]]})
    aw, iw = waterplane(ref_rings)
    mesh_aw, mesh_iw = waterplane(rings)
    reference = dict(
        volume_m3=h["volume"],
        cb_m=list(h["cb"]),
        waterplane_area_m2=aw,
        waterplane_inertia_m4=iw,
        mesh_waterplane_area_m2=mesh_aw,
        mesh_waterplane_inertia_m4=mesh_iw,
        basis="independent 192x48 surface quadrature of the same sectional proxy",
        mesh_tolerances=dict(volume_relative=0.015, cb_distance_m=0.002 * g["length"]),
        features=[
            "flat_bottom",
            "circular_bilge",
            "parallel_midbody",
            "transom",
            "raised_afterbody",
            "bulbous_forebody",
            "raked_stem",
        ],
        comparison_scope="source-informed family reconstruction; exact benchmark offsets are not reconstructed",
    )
    return _mesh(
        g,
        surface.nodes,
        surface.panels,
        reference,
        rho,
        gravity,
        geometry_origin="source_informed_sectional_proxy",
    )


def add_stepped_column(surface, cx, cy, steps, g, half):
    count = g["n_azimuth"]
    h = g["target_panel_m"]
    # The polygon area equals the nominal circular area at every radius.
    correction = math.sqrt(2 * math.pi / (count * math.sin(2 * math.pi / count)))
    angles = (
        [math.pi * j / (count // 2) for j in range(count // 2 + 1)]
        if half
        else [2 * math.pi * j / count for j in range(count + 1)]
    )

    def ring(radius, z):
        return [
            (
                cx + radius * correction * math.cos(t),
                cy + radius * correction * math.sin(t),
                z,
            )
            for t in angles
        ]

    for (z0, r0), (z1, r1) in zip(steps, steps[1:]):
        n = max(1, math.ceil(max(abs(z1 - z0), abs(r1 - r0)) / h))
        for k in range(n):
            a, b = k / n, (k + 1) / n
            A = ring(r0 + (r1 - r0) * a, z0 + (z1 - z0) * a)
            B = ring(r0 + (r1 - r0) * b, z0 + (z1 - z0) * b)
            for i in range(len(angles) - 1):
                surface.face([A[i], A[i + 1], B[i + 1], B[i]])
    z, r = steps[0]
    n = max(1, math.ceil(r / h))
    for k in range(n):
        A, B = ring(r * k / n, z), ring(r * (k + 1) / n, z)
        for i in range(len(angles) - 1):
            surface.face([A[i], A[i + 1], B[i + 1], B[i]])


def build_column_semi(g, rho, gravity):
    surface = Surface()
    R = g["offset_radius"]
    T = g["draft"]
    hb = g["base_height"]
    rc, ru, rb = (
        g[k] / 2 for k in ("center_diameter", "upper_diameter", "base_diameter")
    )
    add_stepped_column(surface, 0, 0, [(-T, rc), (0, rc)], g, True)
    for cx, cy, half in [(-R, 0, True), (R / 2, math.sqrt(3) * R / 2, False)]:
        add_stepped_column(
            surface, cx, cy, [(-T, rb), (-T + hb, rb), (-T + hb, ru), (0, ru)], g, half
        )
    vols = [
        math.pi * rc * rc * T,
        3 * math.pi * rb * rb * hb,
        3 * math.pi * ru * ru * (T - hb),
    ]
    zs = [-T / 2, -T + hb / 2, -(T - hb) / 2]
    volume = sum(vols)
    aw = math.pi * (rc * rc + 3 * ru * ru)
    iw = math.pi * (rc**4 + 3 * ru**4) / 4 + math.pi * ru * ru * 1.5 * R * R
    reference = dict(
        volume_m3=volume,
        cb_m=[0, 0, sum(v * z for v, z in zip(vols, zs)) / volume],
        waterplane_area_m2=aw,
        waterplane_inertia_m4=[iw, iw],
        expected_wet_components=3,
        connectivity_basis="Four BEM columns, three wet components in y>=0; dry/physical Morison frame connects the complete rigid structure",
        mesh_tolerances=dict(volume_relative=1e-8, cb_distance_m=1e-6),
        basis="analytic stepped circular cylinders with area-conserving polygonal rings",
        features=[
            "central_tower_column",
            "three_offset_columns",
            "enlarged_base_columns",
            "slender_delta_and_y_frame",
            "cross_braces",
        ],
        mesh_radial_scale=math.sqrt(
            2 * math.pi / (g["n_azimuth"] * math.sin(2 * math.pi / g["n_azimuth"]))
        ),
    )
    return _mesh(
        g,
        surface.nodes,
        surface.panels,
        reference,
        rho,
        gravity,
        geometry_origin="OC4_scalar_dimensions_original_mesh",
    )


def build_form(g, rho=1025.0, gravity=9.81):
    mesh = {"section_hull": build_section_hull, "column_semisub": build_column_semi}[
        g["type"]
    ](g, rho, gravity)
    mesh.provenance["additional_generator_sources"] = {
        "forms_geometry.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    }
    return mesh
