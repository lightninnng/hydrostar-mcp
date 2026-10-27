"""Native first-order pressure sampling on mean wetted BEM panels."""

from __future__ import annotations

import math
from pathlib import Path
from .visualization import whole_mesh


def wet_panel_samples(hst):
    vertices, faces = whole_mesh(hst)
    centers, normals, areas = [], [], []
    for face in faces:
        points = [vertices[i] for i in face]
        area = 0.0
        moment = [0.0] * 3
        vector = [0.0] * 3
        a = points[0]
        for j in range(1, len(points) - 1):
            b, c = points[j : j + 2]
            u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
            cross = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            ]
            triangle_area = math.sqrt(sum(x * x for x in cross)) / 2
            area += triangle_area
            for k in range(3):
                vector[k] += cross[k]
                moment[k] += triangle_area * (a[k] + b[k] + c[k]) / 3
        length = math.sqrt(sum(x * x for x in vector))
        if area <= 1e-12 or length <= 1e-12:
            raise ValueError("Nonzero planar wet panels are required")
        center = [v / area for v in moment]
        if center[2] >= 0:
            raise ValueError("Pressure collocation must lie below the mean waterline")
        centers.append(center)
        normals.append([v / length for v in vector])
        areas.append(area)
    return dict(
        vertices=vertices, faces=faces, centers=centers, normals=normals, areas_m2=areas
    )


def body_pressure_card(points, hydrostatic_motion):
    if hydrostatic_motion not in (0, 1):
        raise ValueError("COEFHDS must be 0 or 1")
    lines = ["ZFSURFACE 0", "WAVEDECOMPOSITION", "POINTS"]
    lines += [f"{i} {x:.12g} {y:.12g} {z:.12g}" for i, x, y, z in points]
    lines += [
        "ENDPTS",
        "COEFINC 1",
        "COEFRDF 1",
        f"COEFHDS {hydrostatic_motion}",
        "BODY 1",
        "ENDFILE",
    ]
    return "\n".join(lines) + "\n"


def pressure_points(mesh, offset_m=0.02):
    points = []
    for offset in (0.0, offset_m):
        for c, n in zip(mesh["centers"], mesh["normals"]):
            points.append([len(points) + 1, *[c[k] + offset * n[k] for k in range(3)]])
    return points


def pressure_rao_card(count, kind):
    if kind not in ("following", "eulerian"):
        raise ValueError("Unknown pressure component")
    return "".join(
        f"PRESSURE POINT {i} FILE pressure_{kind}_{i:04d}.rao\n"
        + (
            f"WAVEDEC INC POINT {i} FILE pressure_incident_{i:04d}.rao\n"
            if kind == "following"
            else ""
        )
        for i in range(1, count + 1)
    )


def native_pressure(path, point, omega, heading):
    import cmath
    import re
    from . import core

    raw = core.read_rao(path)
    if raw["omega"] != [omega] or raw["headings"] != [heading]:
        raise ValueError("Native pressure frequency/heading mismatch")
    kind = "incident" if Path(path).name.startswith("pressure_incident_") else "total"
    if raw["unit"] not in ({"m", "m/m"} if kind == "incident" else {"m/m"}):
        raise ValueError("Native pressure must be a normalized water-column head")
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(r"Reference point of body 0:\s*\(([^)]+)\)", text)
    xyz = [float(v) for v in match[1].split()] if match else []
    if len(xyz) != 3 or max(abs(a - b) for a, b in zip(xyz, point)) > 0.00051:
        raise ValueError("Native pressure point coordinates changed")
    reference = [
        float(v) for v in raw["metadata"]["REF.PT INCIDENT WAVE"].strip("() ").split()
    ]
    if len(reference) != 2:
        raise ValueError("Invalid wave reference in native pressure record")
    return cmath.rect(
        raw["amplitude"][0][0], math.radians(raw["phase"][0][0])
    ), reference


def verify_pressure_physics(data):
    import cmath
    from .animation import wave_number

    n = len(data["mesh"]["faces"])
    points = data["points"]
    if len(points) != 2 * n or any(
        len(data[k]) != expected
        for k, expected in [
            ("following_head", 2 * n),
            ("incident_head", 2 * n),
            ("eulerian_head", n),
        ]
    ):
        raise ValueError("Incomplete panel pressure records")
    for key in ("following_head", "incident_head", "eulerian_head"):
        if not all(math.isfinite(v) for pair in data[key] for v in pair):
            raise ValueError("Non-finite pressure coefficient")
    k = wave_number(data["omega_rad_s"], data["depth_m"], data["gravity_m_s2"])
    beta = math.radians(data["heading_deg"])
    ref = data["wave_reference_xy_m"]
    q = [complex(*pair) for pair in data["motion_complex"]]
    cg = data["cog_m"]
    maximum_incident = 0.0
    maximum_correction = 0.0
    amplitudes = [abs(complex(*pair)) for pair in data["following_head"][:n]]
    peak = max(amplitudes)
    if peak <= 1e-12:
        raise ValueError("Nonzero native pressure is required")
    for i, (identifier, x, y, z) in enumerate(points):
        if identifier != i + 1 or z >= 0:
            raise ValueError(
                "Pressure points must have ordered IDs below the mean free surface"
            )
        expected = math.cosh(k * (z + data["depth_m"])) / math.cosh(k * data["depth_m"])
        expected *= cmath.exp(
            -1j * k * ((x - ref[0]) * math.cos(beta) + (y - ref[1]) * math.sin(beta))
        )
        maximum_incident = max(
            maximum_incident, abs(complex(*data["incident_head"][i]) - expected)
        )
        if i < n:
            dz = q[2] + math.pi / 180 * (q[3] * (y - cg[1]) - q[4] * (x - cg[0]))
            error = (
                complex(*data["following_head"][i])
                - complex(*data["eulerian_head"][i])
                + dz
            )
            maximum_correction = max(maximum_correction, abs(error))
    shift_error = (
        max(
            abs(
                complex(*data["following_head"][i + n])
                - complex(*data["following_head"][i])
            )
            for i in range(n)
        )
        / peak
    )
    scale = max(1.0, peak, max(abs(complex(*v)) for v in data["eulerian_head"]))
    if maximum_incident > 2e-5:
        raise ValueError(
            f"Incident pressure failed the finite-depth analytical check: {maximum_incident}"
        )
    if maximum_correction > 2e-5 * scale:
        raise ValueError(
            f"Body-following pressure correction failed: {maximum_correction}"
        )
    if shift_error > 0.02:
        raise ValueError(
            f"Pressure sampling sensitivity exceeds 2% of the global peak: {shift_error}"
        )
    return dict(
        panel_count=n,
        collocation_count=2 * n,
        native_record_count=5 * n,
        incident_complex_max_error=maximum_incident,
        hydrostatic_motion_complex_max_error=maximum_correction,
        outward_offset_m=data["outward_offset_m"],
        offset_complex_change_over_global_peak=shift_error,
        following_head_global_peak=peak,
        pressure_colour_limit_kpa=data["rho_kg_m3"]
        * data["gravity_m_s2"]
        * data["wave_amplitude_m"]
        * peak
        / 1000,
    )


def read_pressure_data(directory, mesh, cfg, cog, motions, offset_m=0.02):
    import hashlib
    import cmath

    points = pressure_points(mesh, offset_m)
    n = len(mesh["faces"])
    fields = {key: [] for key in ["following_head", "incident_head", "eulerian_head"]}
    hashes = {}
    reference = None
    for kind, key, count in [
        ("following", "following_head", 2 * n),
        ("incident", "incident_head", 2 * n),
        ("eulerian", "eulerian_head", n),
    ]:
        for i in range(count):
            name = f"pressure_{kind}_{i + 1:04d}.rao"
            path = Path(directory) / "rao" / name
            value, ref = native_pressure(
                path,
                points[i][1:],
                cfg.environment.frequency.min,
                cfg.environment.headings.min,
            )
            if reference is not None and ref != reference:
                raise ValueError("Pressure wave-reference points disagree")
            reference = ref
            fields[key].append([value.real, value.imag])
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    q = [
        cmath.rect(
            motions[d]["amplitude"][0][0], math.radians(motions[d]["phase"][0][0])
        )
        for d in ["surge", "sway", "heave", "roll", "pitch", "yaw"]
    ]
    data = dict(
        schema_version=1,
        form_id=cfg.reference_form,
        omega_rad_s=cfg.environment.frequency.min,
        heading_deg=cfg.environment.headings.min,
        wave_amplitude_m=cfg.mechanics.wave_amplitude_m,
        depth_m=cfg.environment.depth,
        gravity_m_s2=cfg.environment.gravity_m_s2,
        rho_kg_m3=cfg.environment.rho_kg_m3,
        cog_m=cog,
        wave_reference_xy_m=reference,
        phase_convention="real(H*exp(+i*omega*t)); phase lead",
        pressure_definition="First-order body-following pressure perturbation on mean wetted BEM panels; still-water pressure excluded",
        raw_transfer_unit="metres of water-column head per metre of incident-wave amplitude",
        display_unit="kPa",
        pressure_colour_gain=1.0,
        mesh=mesh,
        points=points,
        outward_offset_m=offset_m,
        motion_complex=[[v.real, v.imag] for v in q],
        mean_static_pressure_kpa=[
            -cfg.environment.rho_kg_m3 * cfg.environment.gravity_m_s2 * c[2] / 1000
            for c in mesh["centers"]
        ],
        **fields,
    )
    return data, dict(**verify_pressure_physics(data), native_file_sha256=hashes)
