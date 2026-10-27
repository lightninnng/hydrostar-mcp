"""Single-process geometry worker; commercial solver execution stays in CaseService."""

from __future__ import annotations

import math
from pathlib import Path
import sys
import traceback

from . import __version__, core
from .geometry_sources import FORMATS, GeometryRequest
from .workflow import file_hash, save_json


def write_hst(path, request, vertices, faces):
    lines = [
        f"PROJECT {request.project}",
        "USER SOURCE_GEOMETRY_PIPELINE",
        "NBBODY 1",
        "SYMMETRY 1 0",
        f"NUMPANEL 1 1 {len(faces)}",
        "ZFSURFACE 0",
        f"RHO {request.rho_kg_m3:.15g}",
        f"GRAVITY {request.gravity_m_s2:.15g}",
        "COORDINATES TYPE 0",
    ]
    lines.extend(
        f"{i} " + " ".join(f"{v:.15g}" for v in point)
        for i, point in enumerate(vertices, 1)
    )
    lines += ["ENDCOORDINATES", "PANEL TYPE 0"]
    lines.extend(
        " ".join(str(i + 1) for i in (face if len(face) == 4 else face + face[-1:]))
        for face in faces
    )
    path.write_text("\n".join(lines + ["ENDPANEL", "ENDFILE", ""]), encoding="ascii")


def plot_surface(folder, vertices, faces, reference, output_name="geometry-qa.png"):
    import numpy as np
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MaxNLocator
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from .visualization import _scientific_style

    _scientific_style(plt)
    v = np.array(vertices)
    profiles = [np.array(p["points_m"]) for p in reference.get("source_profiles") or []]
    extent = np.vstack([v, *profiles])
    low, high = extent.min(axis=0), extent.max(axis=0)
    span = np.maximum(high - low, 1)
    fig = plt.figure(figsize=(13.6, 6.8))
    axis = fig.add_axes([0.015, 0.18, 0.50, 0.66], projection="3d")
    axis.add_collection3d(
        Poly3DCollection(
            [v[face] for face in faces],
            facecolor="#4e819c",
            edgecolor="#334b5c",
            lw=0.18,
            alpha=0.85,
        )
    )
    for p in profiles:
        p = np.vstack([p, p[:1]])
        axis.plot(*p.T, color="#a64833", lw=0.9, alpha=0.75)
    axis.set(
        xlim=(low[0], high[0]),
        ylim=(low[1], high[1]),
        zlim=(low[2], high[2]),
    )
    axis.set_box_aspect(span)
    axis.view_init(23, -55)
    axis.set_axis_off()
    fig.text(0.265, 0.85, "(a) Accepted wetted surface", ha="center", fontsize=11)
    side = fig.add_axes([0.59, 0.57, 0.38, 0.23])
    plan = fig.add_axes([0.59, 0.17, 0.38, 0.25])
    for target, a, b, label in [
        (side, 0, 2, "(b) Longitudinal projection"),
        (plan, 0, 1, "(c) Plan projection"),
    ]:
        polygons = [v[face + face[:1]][:, [a, b]] for face in faces]
        target.add_collection(
            LineCollection(polygons, colors="#426c84", linewidths=0.22, alpha=0.55)
        )
        for p in profiles:
            p = np.vstack([p, p[:1]])
            target.plot(p[:, a], p[:, b], color="#a64833", lw=0.65, alpha=0.8)
        target.set_xlim(low[a] - 0.03 * span[a], high[a] + 0.03 * span[a])
        target.set_ylim(low[b] - 0.08 * span[b], high[b] + 0.08 * span[b])
        target.set(xlabel="xyz"[a] + " (m)", ylabel="xyz"[b] + " (m)")
        target.set_title(label, loc="left", pad=8)
        target.xaxis.set_major_locator(MaxNLocator(5))
        target.yaxis.set_major_locator(MaxNLocator(4))
        target.spines[["top", "right"]].set_visible(False)
        target.grid(alpha=0.2)
    side.axhline(0, color="#526278", ls="--", lw=0.8)
    if profiles:
        fig.legend(
            [Line2D([], [], color="#a64833", lw=1)],
            ["Original source sections"],
            loc="lower left",
            bbox_to_anchor=(0.12, 0.09),
            frameon=False,
        )
    fig.suptitle("Geometry acceptance and source reconstruction", fontsize=14, y=0.95)
    fig.text(
        0.5,
        0.035,
        "Coordinates in m. Equal spatial scales in the 3D view; projection axes use the labelled scales. Dashed line: z = 0.",
        ha="center",
        fontsize=9,
        color="#526278",
    )
    destination = folder / output_name
    fig.savefig(destination, dpi=300)
    if output_name != "geometry-qa.png":
        fig.savefig(destination.with_suffix(".pdf"))
    plt.close(fig)


def run(folder):
    from .geometry_kernel import build_surface
    from .surface_checks import inspect_surface
    from .panel_checks import inspect_panels

    request = GeometryRequest.model_validate_json(
        (folder / "request.json").read_text(encoding="utf-8")
    )
    source = next(folder.glob("source.*"))
    if source.suffix.lower() == ".json":
        import json

        evidence = json.loads(source.read_text(encoding="utf-8-sig")).get(
            "digitization_evidence"
        )
        if evidence:
            drawings = list(folder.glob("drawing-source.*"))
            if len(drawings) != 1 or file_hash(drawings[0]) != evidence.get(
                "source_sha256"
            ):
                raise ValueError("描线资料的原图快照或 SHA-256 核验失败")
    if FORMATS[source.suffix.lower()] == "drawing":
        from .drawing import stage_drawing

        return stage_drawing(folder, source, request)
    vertices, faces, reference = build_surface(source, request)
    quality = inspect_surface(
        vertices, faces, request.expected_wet_components, request.weld_tolerance_m * 10
    )
    topology_passed = quality["passed"]
    quality["panel_quality"] = inspect_panels(
        vertices, faces, request.panel_quality.model_dump()
    )
    if (
        request.panel_layout
        in {"quad_dominant", "ring_bands", "polygon_blocks", "station_bands"}
        and reference["kernel"] == "OpenCASCADE/Gmsh"
    ):
        quality["quad_fraction_required"] = request.minimum_quad_fraction
        quality["quad_fraction_passed"] = (
            quality["panel_quality"]["quad_fraction"] >= request.minimum_quad_fraction
        )
    quality["passed"] = (
        quality["passed"]
        and quality["panel_quality"]["passed"]
        and quality.get("quad_fraction_passed", True)
    )
    if not quality["passed"]:
        save_json(
            folder / "candidate-surface.json",
            dict(vertices=vertices, faces=faces, reference=reference),
        )
        return dict(
            status="failed",
            quality=quality,
            error=dict(
                code="GEOMETRY_PANEL_QUALITY_FAILED"
                if topology_passed
                else "GEOMETRY_TOPOLOGY_FAILED",
                detail="面元比例、形状或相邻尺度未通过本次显式门限"
                if topology_passed
                else "湿表面拓扑、边界、方向或自交检查失败",
            ),
        )
    hst = folder / "model.hst"
    write_hst(hst, request, vertices, faces)
    hyd = core.hydrostatics(hst)
    fidelity = {}
    if "cad_volume_m3" in reference:
        fidelity["cad_volume_relative_error"] = abs(
            hyd["volume"] / reference["cad_volume_m3"] - 1
        )
        fidelity["cad_cb_distance_m"] = math.dist(hyd["cb"], reference["cad_cb_m"])
        span = max(
            max(p[k] for p in vertices) - min(p[k] for p in vertices) for k in range(3)
        )
        fidelity["cad_cb_tolerance_m"] = max(0.002, 0.0005 * span)
        if (
            fidelity["cad_volume_relative_error"] > request.volume_tolerance_relative
            or fidelity["cad_cb_distance_m"] > fidelity["cad_cb_tolerance_m"]
        ):
            return dict(
                status="failed",
                quality=quality,
                fidelity=fidelity,
                error=dict(
                    code="CAD_MESH_FIDELITY_FAILED",
                    detail="请细化湿表面并核对排水体积与浮心偏差",
                ),
            )
    if request.expected_volume_m3 is not None:
        fidelity["specified_volume_relative_error"] = abs(
            hyd["volume"] / request.expected_volume_m3 - 1
        )
        if (
            fidelity["specified_volume_relative_error"]
            > request.volume_tolerance_relative
        ):
            return dict(
                status="failed",
                quality=quality,
                fidelity=fidelity,
                error=dict(
                    code="SOURCE_VOLUME_MISMATCH",
                    detail="湿面体积与明确给定的源排水量不一致",
                ),
            )
    save_json(
        folder / "surface.json",
        dict(vertices=vertices, faces=faces, reference=reference),
    )
    plot_surface(folder, vertices, faces, reference)
    return dict(
        schema="hydrostar-geometry-bundle-1",
        version=__version__,
        status="geometry_accepted",
        request=request.model_dump(),
        quality=quality,
        generator_sources={
            name: file_hash(Path(__file__).with_name(name))
            for name in (
                "geometry_worker.py",
                "geometry_kernel.py",
                "geometry_sources.py",
                "surface_checks.py",
                "panel_checks.py",
                "structured_panels.py",
            )
        },
        fidelity=fidelity,
        hydrostatics=hyd,
        reference=reference,
        geometry_gates=dict(
            source_units="passed",
            coordinate_frame="passed",
            waterline_clipping="passed",
            topology="passed",
            self_intersection="passed",
            orientation="passed",
            panel_shape="passed",
            panel_layout="passed",
            fidelity="passed" if fidelity else "source_reference_pending",
        ),
        physics_status="Geometry accepted; use prepare_case and start_case for native hydrodynamic validation",
    )


def main():
    folder = Path(sys.argv[1]).resolve()
    try:
        report = run(folder)
    except ModuleNotFoundError as exc:
        report = dict(
            status="failed",
            error=dict(
                code="GEOMETRY_DEPENDENCY_MISSING",
                detail=f"缺少 {exc.name}；请安装 hydrostar-mcp[geometry]",
            ),
        )
    except Exception as exc:
        traceback.print_exc()
        report = dict(
            status="failed",
            error=dict(code="GEOMETRY_CONVERSION_FAILED", detail=str(exc)),
        )
    if report["status"] in {"geometry_accepted", "digitization_required"}:
        report["files"] = {
            p.name: file_hash(p)
            for p in folder.iterdir()
            if p.is_file() and p.name not in {"kernel.log", "geometry-report.json"}
        }
    save_json(folder / "geometry-report.json", report)
    return int(report["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
