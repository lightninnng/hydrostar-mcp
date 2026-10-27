"""Publish source geometry, native arrays and scientific figures as one dataset."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import textwrap

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__
from hydrostar_mcp.geometry_worker import plot_surface
from hydrostar_mcp.visualization import _scientific_style, plot_rao
from hydrostar_mcp.workflow import file_hash, save_json

LABELS = {
    "lofted_vessel": ("曲线站位船体", "Vessel reconstructed from curved sections"),
    "moonpool_caisson": (
        "带贯通月池的多边形浮体",
        "Polygonal caisson with a through moonpool",
    ),
    "cad_spar": ("带升沉板的曲面 Spar", "Curved CAD spar with a finite heave plate"),
}


def export():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.ticker import MaxNLocator

    _scientific_style(plt)
    assets = ROOT / "docs/assets"
    fig = plt.figure(figsize=(14, 6.3))
    cases = []
    for index, (key, labels) in enumerate(LABELS.items()):
        folder = ROOT / "examples/geometry" / key
        report = json.loads(
            (folder / "geometry/geometry-report.json").read_text(encoding="utf-8")
        )
        native = json.loads((folder / "verification.json").read_text(encoding="utf-8"))
        if report["status"] != "geometry_accepted" or set(
            native["quality_gates"].values()
        ) != {"passed"}:
            raise ValueError("Accepted geometry and native results required: " + key)
        surface = json.loads(
            (folder / "geometry/surface.json").read_text(encoding="utf-8")
        )
        motions = json.loads((folder / "motions.json").read_text(encoding="utf-8"))
        cfg = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        v, f = np.array(surface["vertices"]), np.array(surface["faces"])
        ax = fig.add_axes([0.035 + index * 0.33, 0.30, 0.28, 0.48], projection="3d")
        ax.add_collection3d(
            Poly3DCollection(
                v[f],
                facecolor="#6891a6",
                edgecolor="#355369",
                linewidth=0.12,
                alpha=0.8,
            )
        )
        low, high = v.min(axis=0), v.max(axis=0)
        ax.set(
            xlim=(low[0], high[0]),
            ylim=(low[1], high[1]),
            zlim=(low[2], max(high[2], 1)),
            xlabel="x (m)",
            ylabel="y (m)",
            zlabel="z (m)",
        )
        ax.set_box_aspect(np.maximum(high - low, 1))
        ax.view_init(23, -58)
        ax.tick_params(labelsize=8, pad=0)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.set_major_locator(MaxNLocator(3))
            axis.label.set_fontsize(9)
        if key == "lofted_vessel":
            ax.set_axis_off()
        fig.text(
            0.175 + index * 0.33,
            0.84,
            "(" + chr(97 + index) + ") " + textwrap.fill(labels[1], width=34),
            ha="center",
            va="top",
            fontsize=11,
        )
        volume = report["hydrostatics"]["volume"]
        error = report["fidelity"]["cad_volume_relative_error"]
        fig.text(
            0.04 + index * 0.33,
            0.14,
            f"{len(f):,} wetted panels\nWet extents = "
            + " × ".join(f"{d:.1f}" for d in high - low)
            + f" m\nVolume = {volume:,.3f} m³\nCAD/mesh volume difference = {100 * error:.3f}%",
            fontsize=9.5,
        )
        plot_surface(
            assets,
            surface["vertices"],
            surface["faces"],
            surface["reference"],
            output_name=key + "_geometry.png",
        )
        plot_rao(motions, assets / (key + "_rao.png"), title=labels[1])
        # Verification indexes the exact data bundle; figures outside it have their own hashes.
        native["publication_version"] = __version__
        native["files"] = {
            p.relative_to(folder).as_posix(): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        }
        save_json(folder / "verification.json", native)
        cases.append(
            dict(
                key=key,
                label=labels[0],
                label_en=labels[1],
                geometry_figure="assets/" + key + "_geometry.png",
                rao_figure="assets/" + key + "_rao.png",
                volume_m3=volume,
                cad_volume_m3=report["reference"]["cad_volume_m3"],
                volume_relative_error=error,
                cb_distance_m=report["fidelity"]["cad_cb_distance_m"],
                panels=len(f),
                waterplane_panels=native["hslec"]["waterplane_panels"],
                quality_gates=native["quality_gates"],
                frequency_count=len(motions["heave"]["omega"]),
                heading_count=len(motions["heave"]["headings"]),
                frequency_grid=cfg["environment"]["frequency"],
                summary="examples/geometry/" + key + "/verification.json",
                summary_sha256=file_hash(folder / "verification.json"),
                source_case_id=native["source_case_id"],
            )
        )
    fig.suptitle(
        "Original geometries used in native hydrodynamic calculations",
        fontsize=14,
        y=0.96,
    )
    fig.text(
        0.5,
        0.04,
        "Mean wetted surfaces. Coordinate units: m. Equal spatial scales within each view.",
        ha="center",
        fontsize=9,
        color="#526278",
    )
    fig.savefig(assets / "geometry-source-cases.png", dpi=300)
    fig.savefig(assets / "geometry-source-cases.pdf")
    plt.close(fig)
    payload = dict(
        schema="hydrostar-general-geometry-study-1",
        publication_version=__version__,
        source_origin="Original scalar construction in geometry_source_study.py; no external meshes",
        cases=cases,
    )
    payload["figures"] = {
        p.name: file_hash(p)
        for p in assets.iterdir()
        if p.name in {"geometry-source-cases.png", "geometry-source-cases.pdf"}
        or any(p.name.startswith(k + "_") for k in LABELS)
    }
    save_json(ROOT / "examples/geometry/index.json", payload)
    save_json(ROOT / "docs/data/geometry.json", payload)
    print("Published geometry cases:", len(cases))


if __name__ == "__main__":
    export()
