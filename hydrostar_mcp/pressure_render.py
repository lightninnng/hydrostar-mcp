"""Synchronized native surface-pressure, wave-elevation and rigid-motion figures."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


def render_coupled_gif(folder, destination, frames=48, gain=6.0, width=1600):
    import numpy as np
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.ticker import MaxNLocator
    from matplotlib.patches import Polygon
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from PIL import Image
    from .animation import rigid_displacement
    from .pressure import verify_pressure_physics
    from .visualization import LABELS, dry_columns, _scientific_style

    folder, destination = Path(folder), Path(destination)
    data = json.loads((folder / "pressure.json").read_text(encoding="utf-8"))
    metrics = verify_pressure_physics(data)
    cfg = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    wave_folder = folder.parents[1] / "animations" / data["form_id"]
    wave_path = wave_folder / "field.json"
    if (
        hashlib.sha256(wave_path.read_bytes()).hexdigest()
        != data["source_wave_field_sha256"]
    ):
        raise ValueError("Linked wave field changed")
    wave = json.loads(wave_path.read_text(encoding="utf-8"))
    for key in [
        "omega_rad_s",
        "heading_deg",
        "wave_amplitude_m",
        "depth_m",
        "rho_kg_m3",
        "gravity_m_s2",
    ]:
        if wave[key] != data[key]:
            raise ValueError("Wave and pressure conditions disagree")
    omega, a, beta = data["omega_rad_s"], data["wave_amplitude_m"], data["heading_deg"]
    period = math.tau / omega
    vertices = np.array(data["mesh"]["vertices"])
    faces = data["mesh"]["faces"]
    n = len(faces)
    h = np.array([complex(*v) for v in data["following_head"][:n]])
    q = np.array([complex(*v) for v in data["motion_complex"]])
    pressure_factor = data["rho_kg_m3"] * data["gravity_m_s2"] * a / 1000
    pressure_limit = metrics["pressure_colour_limit_kpa"]
    grid = wave["grid"]
    x, y = np.array(grid["x"]), np.array(grid["y"])
    xx, yy = np.meshgrid(x, y)
    total = np.full(xx.shape, np.nan, dtype=complex)
    incident = total.copy()
    for index, value, inc in zip(grid["indices"], wave["total"], wave["incident"]):
        total[tuple(index)] = complex(*value)
        incident[tuple(index)] = complex(*inc)
    scattered = total - incident
    wave_limit = float(a * np.nanmax(np.abs(total)))
    body_low = vertices.min(axis=0)
    body_high = vertices.max(axis=0)
    span = body_high - body_low
    body_bounds = [
        (body_low[k] - max(span[:2]) * 0.06, body_high[k] + max(span[:2]) * 0.06)
        for k in range(2)
    ]
    margin = max(span[:2]) * (0.18 if span[0] / span[1] > 3 else 0.28)
    wave_bounds = [(body_low[k] - margin, body_high[k] + margin) for k in range(2)]
    dry = dry_columns(cfg)
    zlim = (body_low[2] - 3, max([10.0] + [c[3] for c in dry]) + 5)
    context = []
    for cx, cy, radius, height in dry:
        ring = [
            (
                cx + radius * math.cos(j * math.tau / 24),
                cy + radius * math.sin(j * math.tau / 24),
            )
            for j in range(25)
        ]
        for j in range(24):
            context.append(
                [
                    [*ring[j], 0],
                    [*ring[j + 1], 0],
                    [*ring[j + 1], height],
                    [*ring[j], height],
                ]
            )
    cells = []
    for iy in range(len(y) - 1):
        for ix in range(len(x) - 1):
            ids = [(iy, ix), (iy, ix + 1), (iy + 1, ix + 1), (iy + 1, ix)]
            if all(
                np.isfinite(total[index])
                and wave_bounds[0][0] <= xx[index] <= wave_bounds[0][1]
                and wave_bounds[1][0] <= yy[index] <= wave_bounds[1][1]
                for index in ids
            ):
                cells.append(ids)
    _scientific_style(plt)
    fig = plt.figure(figsize=(16, 7.4), dpi=width / 16)
    axp = fig.add_axes([0.015, 0.20, 0.30, 0.59], projection="3d")
    axw = fig.add_axes([0.33, 0.20, 0.30, 0.59], projection="3d")
    fig.suptitle(LABELS[data["form_id"]].replace(" | ", ": "), fontsize=15, y=0.975)
    fig.text(
        0.5,
        0.923,
        f"Regular wave: a = {a:g} m, "
        + r"$\omega$"
        + f" = {omega:g} rad/s, "
        + r"$\beta$"
        + f" = {beta:g}"
        + r"$^\circ$"
        + f", T = {period:.3f} s.",
        ha="center",
        fontsize=10,
    )
    plan = fig.add_axes([0.705, 0.235, 0.255, 0.54])
    clock = fig.text(0.5, 0.873, "", ha="center", fontsize=9, color="#42556a")
    cmap = plt.get_cmap("RdBu_r")
    pnorm = Normalize(-pressure_limit, pressure_limit)
    wnorm = Normalize(-wave_limit, wave_limit)
    scatter_limit = float(a * np.nanmax(np.abs(scattered)))
    snorm = Normalize(-scatter_limit, scatter_limit)
    cloud = plan.pcolormesh(
        xx,
        yy,
        np.ma.masked_invalid(a * np.real(scattered)),
        cmap=cmap,
        norm=snorm,
        shading="gouraud",
        rasterized=True,
    )
    for polygon in grid["waterlines"]:
        plan.add_patch(
            Polygon(
                polygon, facecolor="#65717b", edgecolor="#334650", lw=0.65, zorder=4
            )
        )
    plan.set(xlabel="x (m)", ylabel="y (m)", xlim=(x[0], x[-1]), ylim=(y[0], y[-1]))
    plan.set_aspect("equal")
    plan.tick_params(labelsize=8)
    plan.set_title("(c) Scattered wave elevation", fontsize=10, pad=14)
    for limits, label, rect in [
        (pnorm, "Dynamic pressure perturbation, p' (kPa)", [0.055, 0.145, 0.23, 0.017]),
        (wnorm, "Total wave elevation (m)", [0.37, 0.145, 0.23, 0.017]),
        (
            snorm,
            "Scattered elevation: diffraction + radiation (m)",
            [0.72, 0.145, 0.23, 0.017],
        ),
    ]:
        bar = fig.colorbar(
            plt.cm.ScalarMappable(norm=limits, cmap=cmap),
            cax=fig.add_axes(rect),
            orientation="horizontal",
        )
        bar.set_label(label, fontsize=9)
        bar.ax.tick_params(labelsize=8)
    fig.text(
        0.5,
        0.050,
        f"Pressure and wave colour values use physical units at 1x. Rigid-body motion and 3D wave-height viewing gain: {gain:g}x.",
        ha="center",
        fontsize=8,
        color="#42556a",
    )
    fig.text(
        0.5,
        0.023,
        f"First-order perturbation on mean wetted panels; still-water pressure is stored separately. One physical cycle plays in {frames * 0.08:.2f} s.",
        ha="center",
        fontsize=8,
        color="#42556a",
    )
    palette = []
    for rgb in cmap(np.linspace(0, 1, 160))[:, :3]:
        palette.extend(int(round(v * 255)) for v in rgb)
    for gray in np.linspace(0, 255, 64):
        palette.extend([int(gray)] * 3)
    for rgb in [
        (255, 255, 255),
        (0, 0, 0),
        (34, 51, 68),
        (66, 85, 106),
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
        multiplier = np.exp(1j * phase)
        motion = a * np.real(q * multiplier)
        p = pressure_factor * np.real(h * multiplier)
        eta = a * np.real(total * multiplier)
        cloud.set_array(np.ma.masked_invalid(a * np.real(scattered * multiplier)))
        moved = vertices + gain * rigid_displacement(vertices, motion, data["cog_m"])
        for axis, bounds, title in [
            (axp, body_bounds, "(a) Body-following dynamic surface pressure"),
            (axw, wave_bounds, "(b) Total wave elevation and rigid-body motion"),
        ]:
            axis.clear()
            axis.set(
                xlim=bounds[0],
                ylim=bounds[1],
                zlim=zlim,
                xlabel="x (m)",
                ylabel="y (m)",
                zlabel="z (m)",
            )
            axis.set_box_aspect(
                [
                    bounds[0][1] - bounds[0][0],
                    bounds[1][1] - bounds[1][0],
                    zlim[1] - zlim[0],
                ],
                zoom=0.92,
            )
            axis.zaxis.labelpad = 0
            axis.view_init(25, -55)
            axis.xaxis.set_major_locator(MaxNLocator(4))
            axis.yaxis.set_major_locator(MaxNLocator(3))
            axis.set_zticks([float(body_low[2]), 0.0, 10.0])
            axis.tick_params(labelsize=7, pad=1)
            axis.set_title(title, fontsize=10)
        axp.add_collection3d(
            Poly3DCollection(
                [moved[face] for face in faces],
                facecolors=cmap(pnorm(p)),
                edgecolor="#42505c",
                lw=0.1,
                alpha=1.0,
            )
        )
        sea = [[(xx[i], yy[i], gain * eta[i]) for i in cell] for cell in cells]
        sea_values = [np.mean([eta[i] for i in cell]) for cell in cells]
        axw.add_collection3d(
            Poly3DCollection(
                sea, facecolors=cmap(wnorm(sea_values)), edgecolors="none", alpha=0.68
            )
        )
        axw.add_collection3d(
            Poly3DCollection(
                [moved[face] for face in faces],
                facecolor="#68747e",
                edgecolor="#3e4f5c",
                lw=0.1,
                alpha=0.9,
            )
        )
        for axis in [axp, axw]:
            if context:
                original = np.array(context)
                displaced = original + gain * rigid_displacement(
                    original.reshape(-1, 3), motion, data["cog_m"]
                ).reshape(original.shape)
                axis.add_collection3d(
                    Poly3DCollection(
                        displaced,
                        facecolor="#a3adb5",
                        edgecolor="#7b8a96",
                        lw=0.2,
                        alpha=0.5,
                    )
                )
            for member in cfg["mechanics"]["morison"]:
                if member["cm"] <= 0:
                    continue
                line = np.array([member["start"], member["end"]], dtype=float)
                line += gain * rigid_displacement(line, motion, data["cog_m"])
                axis.plot(line[:, 0], line[:, 1], line[:, 2], color="#7a6353", lw=1.2)
        clock.set_text(
            f"Phase t/T = {frame / frames:.3f}. Physical time = {phase / omega:.3f} s. Heave = {motion[2]:+.3f} m. Roll = {motion[3]:+.3f} deg."
        )
        fig.canvas.draw()
        image = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())
        images.append(image.quantize(palette=palette_image, dither=Image.Dither.NONE))
        if frame in [0, frames // 4, frames // 2]:
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.save(
                destination.with_name(destination.stem + f"_frame{frame:02d}.png")
            )
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
        size_px=[width, int(round(width * 7.4 / 16))],
        duration_ms=80,
        period_s=period,
        motion_gain=gain,
        wave_height_gain=gain,
        pressure_colour_gain=1.0,
        wave_colour_gain=1.0,
        pressure_colour_unit="kPa",
        wave_colour_unit="m",
        pressure_colour_limit_kpa=pressure_limit,
        total_wave_colour_limit_m=wave_limit,
        scattered_colour_limit_m=scatter_limit,
        views=[
            "body_following_pressure",
            "total_wave_and_motion",
            "scattered_wave_diffraction_and_radiation",
        ],
        pressure_definition=data["pressure_definition"],
        phase_convention=data["phase_convention"],
        synchronization="One physical phase for pressure, total and scattered wave elevation and six-DOF motion",
    )
