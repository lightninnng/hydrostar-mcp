"""Verified harmonic wave fields and scientific GIFs from native HSPRS/HSRAO."""

from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

from . import core
from .visualization import LABELS, dry_columns, whole_mesh, _scientific_style


def harmonic(value, omega, time, amplitude=1.0):
    """HydroStar v7+: response = a Re[H exp(+i omega t)], phase is a lead."""
    return amplitude * (value * cmath.exp(1j * omega * time)).real


def wave_number(omega, depth, gravity=9.81):
    low, high = (
        0.0,
        max(omega * omega / gravity, omega / math.sqrt(gravity * depth)) * 2,
    )
    while gravity * high * math.tanh(high * depth) < omega * omega:
        high *= 2
    for _ in range(80):
        middle = (low + high) / 2
        if gravity * middle * math.tanh(middle * depth) < omega * omega:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def waterline_loops(vertices, faces):
    """Trace exact z=0 boundary edges of the reflected solved wet mesh."""
    edges = set()
    for face in faces:
        for i, a in enumerate(face):
            b = face[(i + 1) % len(face)]
            pa, pb = vertices[a], vertices[b]
            if abs(pa[2]) < 1e-7 and abs(pb[2]) < 1e-7:
                axy, bxy = (
                    tuple(round(v, 7) for v in pa[:2]),
                    tuple(round(v, 7) for v in pb[:2]),
                )
                if axy != bxy:
                    edges.add(tuple(sorted((axy, bxy))))
    adjacency = {}
    for a, b in edges:
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    if not adjacency or any(len(n) != 2 for n in adjacency.values()):
        raise ValueError("Waterline must consist of closed, degree-two loops")
    loops = []
    while edges:
        start, following = min(edges)
        polygon = [start]
        previous, current = start, following
        edges.remove(tuple(sorted((start, following))))
        while current != start:
            polygon.append(current)
            nxt = next(p for p in adjacency[current] if p != previous)
            edge = tuple(sorted((current, nxt)))
            if edge not in edges:
                raise ValueError("Repeated or incomplete waterline edge")
            edges.remove(edge)
            previous, current = current, nxt
        loops.append(polygon)
    return loops


def inside_or_near(point, polygon, clearance):
    x, y = point
    inside = False
    for i, (ax, ay) in enumerate(polygon):
        bx, by = polygon[(i + 1) % len(polygon)]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
        dx, dy = bx - ax, by - ay
        fraction = max(
            0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy))
        )
        if math.hypot(x - ax - fraction * dx, y - ay - fraction * dy) <= clearance:
            return True
    return inside


def field_grid(hst, size=51, clearance=0.65):
    vertices, faces = whole_mesh(hst)
    loops = waterline_loops(vertices, faces)
    low = [min(p[k] for p in vertices) for k in range(2)]
    high = [max(p[k] for p in vertices) for k in range(2)]
    center = [(a + b) / 2 for a, b in zip(low, high)]
    span = high[0] - low[0]
    if span / (high[1] - low[1]) > 3:
        ranges = [
            (center[0] - span * 0.85, center[0] + span * 0.85),
            (center[1] - span * 0.6, center[1] + span * 0.6),
        ]
    else:
        extent = max(high[k] - low[k] for k in range(2)) * 1.3
        ranges = [(center[k] - extent, center[k] + extent) for k in range(2)]
    axes = [[a + (b - a) * i / (size - 1) for i in range(size)] for a, b in ranges]
    points, indices = [], []
    for iy, y in enumerate(axes[1]):
        for ix, x in enumerate(axes[0]):
            if any(inside_or_near((x, y), loop, clearance) for loop in loops):
                continue
            points.append([len(points) + 1, x, y, 0.0])
            indices.append([iy, ix])
    return dict(
        x=axes[0],
        y=axes[1],
        points=points,
        indices=indices,
        waterlines=loops,
        clearance_m=clearance,
    )


def pressure_card(points, incident_only=False):
    lines = ["ZFSURFACE 0", "WAVEDECOMPOSITION", "POINTS"]
    lines += [f"{i} {x:.12g} {y:.12g} {z:.12g}" for i, x, y, z in points]
    lines += [
        "ENDPTS",
        "COEFINC 1",
        f"COEFRDF {0 if incident_only else 1}",
        "COEFHDS 0",
        "ENDFILE",
    ]
    return "\n".join(lines) + "\n"


def field_rao_card(points):
    return "".join(
        f"PRESSURE POINT {i} FILE field_total_{i:04d}.rao\n"
        f"WAVEDEC INC POINT {i} FILE field_incident_{i:04d}.rao\n"
        for i, *_ in points
    )


def read_native_field(directory, grid, omega, heading, depth, gravity):
    fields = {"total": [], "incident": []}
    raw_hashes = {}
    import hashlib

    k = wave_number(omega, depth, gravity)
    beta = math.radians(heading)
    maximum_error = 0.0
    wave_reference = None
    for i, x, y, _ in grid["points"]:
        for kind in fields:
            name = f"field_{kind}_{i:04d}.rao"
            path = Path(directory) / "rao" / name
            raw = core.read_rao(path)
            if raw["omega"] != [omega] or raw["headings"] != [heading]:
                raise ValueError("Field frequency/heading mismatch: " + name)
            allowed = {"m/m"} if kind == "total" else {"m", "m/m"}
            if raw["unit"] not in allowed:
                raise ValueError("Unexpected native free-surface unit: " + name)
            text = path.read_text(encoding="utf-8")
            import re

            match = re.search(r"Reference point of body 0:\s*\(([^)]+)\)", text)
            values = [float(v) for v in match[1].split()] if match else []
            if (
                len(values) != 3
                or max(abs(a - b) for a, b in zip(values, [x, y, 0])) > 0.00051
            ):
                raise ValueError("Native field point coordinates changed: " + name)
            reference = [
                float(v)
                for v in raw["metadata"]["REF.PT INCIDENT WAVE"].strip("() ").split()
            ]
            if (
                len(reference) != 2
                or wave_reference is not None
                and reference != wave_reference
            ):
                raise ValueError("Inconsistent native incident-wave reference")
            wave_reference = reference
            value = cmath.rect(raw["amplitude"][0][0], math.radians(raw["phase"][0][0]))
            fields[kind].append([value.real, value.imag])
            raw_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = cmath.exp(
            -1j
            * k
            * (
                (x - wave_reference[0]) * math.cos(beta)
                + (y - wave_reference[1]) * math.sin(beta)
            )
        )
        value = complex(*fields["incident"][-1])
        maximum_error = max(maximum_error, abs(expected - value))
    if maximum_error > 2e-5:
        raise ValueError(
            f"Native incident field failed analytical complex check: {maximum_error}"
        )
    return fields, dict(
        incident_complex_max_error=maximum_error,
        wave_reference_xy_m=wave_reference,
        point_count=len(grid["points"]),
        native_file_sha256=raw_hashes,
    )


def rigid_displacement(vertices, motion, cog):
    import numpy as np

    points = np.asarray(vertices, dtype=float)
    q = np.asarray(motion, dtype=float)
    rotation = np.deg2rad(q[3:])
    return q[:3] + np.cross(rotation, points - np.asarray(cog))


def render_wave_gif(folder, destination, frames=48, gain=6.0, width=1200):
    """Render native absolute/scattered wave elevation, with RAO-driven motion."""
    import numpy as np
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.ticker import MaxNLocator
    from matplotlib.patches import Polygon
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from PIL import Image

    folder, destination = Path(folder), Path(destination)
    field = json.loads((folder / "field.json").read_text(encoding="utf-8"))
    cfg = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    model = field["form_id"]
    responses = json.loads((folder / "motions.json").read_text(encoding="utf-8"))
    vertices, faces = whole_mesh(folder / "inputs" / (cfg["project"] + ".hst"))
    grid = field["grid"]
    omega, amplitude, heading = (
        field["omega_rad_s"],
        field["wave_amplitude_m"],
        field["heading_deg"],
    )
    period = 2 * math.pi / omega
    points = np.array(vertices)
    x, y = np.asarray(grid["x"]), np.asarray(grid["y"])
    xx, yy = np.meshgrid(x, y)
    total = np.full(xx.shape, np.nan, dtype=complex)
    incident = total.copy()
    for index, t, inc in zip(grid["indices"], field["total"], field["incident"]):
        total[tuple(index)] = complex(*t)
        incident[tuple(index)] = complex(*inc)
    scattered = total - incident
    limit_total = amplitude * np.nanmax(np.abs(total))
    limit_scatter = amplitude * np.nanmax(np.abs(scattered))
    if limit_total <= 0 or limit_scatter <= 0:
        raise ValueError("Nonzero native field required for animation")
    norm_total, norm_scatter = (
        Normalize(-limit_total, limit_total),
        Normalize(-limit_scatter, limit_scatter),
    )
    cmap = plt.get_cmap("RdBu_r")
    _scientific_style(plt)
    fig = plt.figure(figsize=(12, 6.6), dpi=width / 12)
    ax = fig.add_axes([0.025, 0.16, 0.50, 0.64], projection="3d")
    plan = fig.add_axes([0.59, 0.19, 0.35, 0.59])
    fig.suptitle(LABELS[model], fontsize=15, y=0.97)
    fig.text(
        0.5,
        0.914,
        f"Native wave field | a = {amplitude:g} m | "
        + r"$\omega$"
        + f" = {omega:g} rad/s | "
        + r"$\beta$"
        + f" = {heading:g}"
        + r"$^\circ$"
        + f" | T = {period:.3f} s",
        ha="center",
        fontsize=10,
    )
    time_label = fig.text(0.5, 0.865, "", ha="center", color="#526278")
    ax.set_title("(a) Total free-surface elevation and rigid-body motion", fontsize=10)
    plan.set_title("(b) Scattered elevation: total - incident", fontsize=10, pad=14)
    # Fixed mean-waterline masks match the linearized native field calculation.
    initial = np.real(scattered) * amplitude
    cloud = plan.pcolormesh(
        xx,
        yy,
        np.ma.masked_invalid(initial),
        cmap=cmap,
        norm=norm_scatter,
        shading="gouraud",
        rasterized=True,
    )
    for polygon in grid["waterlines"]:
        plan.add_patch(
            Polygon(polygon, facecolor="#56636f", edgecolor="#223344", lw=0.7, zorder=4)
        )
    plan.set(xlabel="x (m)", ylabel="y (m)", xlim=(x[0], x[-1]), ylim=(y[0], y[-1]))
    plan.set_aspect("equal")
    plan.tick_params(labelsize=8)
    cax1 = fig.add_axes([0.11, 0.14, 0.34, 0.018])
    cax2 = fig.add_axes([0.605, 0.14, 0.32, 0.018])
    bar1 = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm_total, cmap=cmap),
        cax=cax1,
        orientation="horizontal",
    )
    bar2 = fig.colorbar(cloud, cax=cax2, orientation="horizontal")
    bar1.set_label("Total elevation (m), physical colour scale", fontsize=9)
    bar2.set_label("Scattered elevation (m), physical colour scale", fontsize=9)
    for bar in [bar1, bar2]:
        bar.ax.tick_params(labelsize=8)
    fig.text(
        0.5,
        0.029,
        f"First-order harmonic reconstruction | 3D wave height & motion gain: {gain:g}x | Colour values: 1x | One cycle / {frames * 0.08:.2f} s playback",
        ha="center",
        color="#526278",
        fontsize=8,
    )
    body_low = np.min(points[:, :2], axis=0)
    body_high = np.max(points[:, :2], axis=0)
    body_span = body_high - body_low
    margin = max(body_span) * (0.18 if body_span[0] / body_span[1] > 3 else 0.28)
    local_bounds = [(body_low[k] - margin, body_high[k] + margin) for k in range(2)]
    cells = []
    for iy in range(len(y) - 1):
        for ix in range(len(x) - 1):
            indices = [(iy, ix), (iy, ix + 1), (iy + 1, ix + 1), (iy + 1, ix)]
            if all(
                np.isfinite(total[index])
                and local_bounds[0][0] <= xx[index] <= local_bounds[0][1]
                and local_bounds[1][0] <= yy[index] <= local_bounds[1][1]
                for index in indices
            ):
                cells.append(indices)
    base_context = []
    for cx, cy, radius, height in dry_columns(cfg):
        ring = [
            (
                cx + radius * math.cos(j * math.tau / 24),
                cy + radius * math.sin(j * math.tau / 24),
            )
            for j in range(25)
        ]
        base_context += [
            [
                (a, b, z)
                for (a, b), z in [
                    (ring[j], 0),
                    (ring[j + 1], 0),
                    (ring[j + 1], height),
                    (ring[j], height),
                ]
            ]
            for j in range(24)
        ]
    static = dict(
        xlim=local_bounds[0],
        ylim=local_bounds[1],
        zlim=(
            min(points[:, 2]) - 3,
            max([10.0] + [c[3] for c in dry_columns(cfg)]) + 5,
        ),
    )
    amplitudes = np.array([responses[d]["amplitude"][0][0] for d in core.DOFS])
    phases = np.deg2rad([responses[d]["phase"][0][0] for d in core.DOFS])
    # A fixed 256-colour GIF palette avoids frame-to-frame colour-map flicker.
    palette = []
    for rgba in cmap(np.linspace(0, 1, 160)):
        palette.extend(int(round(c * 255)) for c in rgba[:3])
    for value in np.linspace(0, 255, 64):
        palette.extend([int(value)] * 3)
    for rgb in [
        (255, 255, 255),
        (0, 0, 0),
        (34, 51, 68),
        (82, 98, 120),
        (86, 99, 111),
        (213, 94, 0),
    ]:
        palette.extend(rgb)
    palette = (palette + [255] * 768)[:768]
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette)
    images = []
    for frame in range(frames):
        phase = math.tau * frame / frames
        time = phase / omega
        eta = amplitude * np.real(total * np.exp(1j * phase))
        scattered_eta = amplitude * np.real(scattered * np.exp(1j * phase))
        motion = amplitude * amplitudes * np.cos(phase + phases)
        moved = points + gain * rigid_displacement(points, motion, field["cog_m"])
        ax.clear()
        ax.set(**static)
        ax.set_box_aspect(
            [
                local_bounds[0][1] - local_bounds[0][0],
                local_bounds[1][1] - local_bounds[1][0],
                static["zlim"][1] - static["zlim"][0],
            ]
        )
        ax.view_init(29, -55)
        ax.set(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)")
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_locator(MaxNLocator(3))
        ax.set_zticks([float(min(points[:, 2])), 0.0, 10.0])
        ax.tick_params(labelsize=7, pad=1)
        ax.set_title("(a) Total elevation and rigid-body motion", fontsize=10)
        sea = [
            [(xx[index], yy[index], gain * eta[index]) for index in cell]
            for cell in cells
        ]
        values = [np.mean([eta[index] for index in cell]) for cell in cells]
        ax.add_collection3d(
            Poly3DCollection(
                sea, facecolors=cmap(norm_total(values)), edgecolors="none", alpha=0.68
            )
        )
        ax.add_collection3d(
            Poly3DCollection(
                [moved[face] for face in faces],
                facecolor="#56636f",
                edgecolor="#283e50",
                lw=0.12,
                alpha=0.9,
            )
        )
        if base_context:
            context = np.asarray(base_context)
            moved_context = context + gain * rigid_displacement(
                context.reshape(-1, 3), motion, field["cog_m"]
            ).reshape(context.shape)
            ax.add_collection3d(
                Poly3DCollection(
                    moved_context,
                    facecolor="#879aa6",
                    edgecolor="#647785",
                    lw=0.2,
                    alpha=0.6,
                )
            )
        for member in cfg["mechanics"]["morison"]:
            if member["cm"] <= 0:
                continue
            line = np.asarray([member["start"], member["end"]], dtype=float)
            line += gain * rigid_displacement(line, motion, field["cog_m"])
            ax.plot(line[:, 0], line[:, 1], line[:, 2], color="#D55E00", lw=1.1)
        cloud.set_array(np.ma.masked_invalid(scattered_eta))
        time_label.set_text(
            f"t / T = {frame / frames:.3f} | t = {time:.3f} s | heave = {motion[2]:+.3f} m | roll = {motion[3]:+.3f} deg"
        )
        fig.canvas.draw()
        rgb = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())
        images.append(rgb.quantize(palette=palette_image, dither=Image.Dither.NONE))
        if frame in [0, frames // 4, frames // 2]:
            snapshot = destination.with_name(
                destination.stem + f"_frame{frame:02d}.png"
            )
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            rgb.save(snapshot)
    destination.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        destination,
        save_all=True,
        append_images=images[1:],
        duration=80,
        loop=0,
        disposal=2,
        optimize=False,
    )
    plt.close(fig)
    return dict(
        frames=frames,
        size_px=[width, int(round(width * 6.6 / 12))],
        duration_ms=80,
        period_s=period,
        motion_gain=gain,
        colour_gain=1.0,
        total_colour_limit_m=float(limit_total),
        scattered_colour_limit_m=float(limit_scatter),
        phase_convention="real(H*exp(+i*omega*t)); phase lead",
    )
