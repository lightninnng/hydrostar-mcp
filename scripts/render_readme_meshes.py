"""Export the four accepted solved wet meshes using ParaView, without a solve.

Run with pvpython --force-offscreen-rendering scripts/render_readme_meshes.py.
The surface connectivity is the same verified HST connectivity used for pressure.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from paraview import servermanager
from paraview.simple import (
    _DisableFirstRenderCameraReset,
    CreateLayout,
    CreateView,
    RenderAllViews,
    SaveScreenshot,
    Show,
    Text,
    TrivialProducer,
)
from vtkmodules.all import vtkUnstructuredGrid
from vtkmodules.util.numpy_support import vtk_to_numpy

from render_native_views import context_geometry, set_points, update

ROOT = Path(__file__).resolve().parent.parent
CASES = (
    ("vessel", "Curved station hull", None),
    ("platform", "Column semisubmersible", "semisub_oc4_style"),
    ("container", "Container hull", "container_kcs_style"),
    ("tanker", "Full-form tanker", "tanker_kvlcc2_style"),
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/assets/readme-meshes.png"
    )
    args = parser.parse_args()
    _DisableFirstRenderCameraReset()
    layout = CreateLayout(name="Accepted native wet meshes")
    layout.SplitHorizontal(0, 0.5)
    layout.SplitVertical(1, 0.5)
    layout.SplitVertical(2, 0.5)
    layout.SetSize(2400, 1520)
    provenance = []
    for index, ((key, label, original), cell) in enumerate(zip(CASES, (3, 5, 4, 6))):
        package = ROOT / "examples/visualization/fields" / key
        condition = read(package / "condition.json")
        verification = read(package / "verification.json")
        if set(verification["gates"].values()) != {"passed"}:
            raise ValueError("Accepted native fields required: " + key)
        pressure_path = ROOT / condition["pressure_file"]
        if digest(pressure_path) != condition["pressure_file_sha256"]:
            raise ValueError("Pressure mesh source changed: " + key)
        mesh = read(pressure_path)["mesh"]
        summary_path = (
            ROOT / "examples/results" / original / "summary.json"
            if original
            else ROOT / "examples/vessel/verification.json"
        )
        summary = read(summary_path)
        if set(summary["quality_gates"].values()) != {"passed"}:
            raise ValueError("Accepted solver gates required: " + key)
        counts = summary["mesh" if original else "hslec"]
        wet = counts["hull_panels"] * 2 ** counts["symmetry"]
        total = (counts["hull_panels"] + counts["waterplane_panels"]) * 2 ** counts[
            "symmetry"
        ]
        if len(mesh["faces"]) != wet:
            raise ValueError("Expanded wet panel count differs: " + key)
        points = np.array(mesh["vertices"], dtype=float)
        data = vtkUnstructuredGrid()
        set_points(data, points)
        for face in mesh["faces"]:
            if len(face) not in (3, 4):
                raise ValueError("Actual native triangle or quadrilateral required")
            data.InsertNextCell(9 if len(face) == 4 else 5, len(face), face)
        view = CreateView("RenderView")
        layout.AssignView(cell, view)
        view.UseColorPaletteForBackground = 0
        view.Background = [1, 1, 1]
        view.OrientationAxesVisibility = 1
        view.OrientationAxesLabelColor = [0.15, 0.20, 0.24]
        view.CameraParallelProjection = 1
        view.CenterAxesVisibility = 0
        source = TrivialProducer()
        update(source, data)
        display = Show(source, view)
        display.Representation = "Surface With Edges"
        display.ColorArrayName = ["POINTS", ""]
        display.DiffuseColor = [0.63, 0.76, 0.79]
        display.AmbientColor = [0.63, 0.76, 0.79]
        display.EdgeColor = [0.16, 0.28, 0.33]
        display.LineWidth = 0.8
        display.Ambient = 0.35
        display.Diffuse = 0.75
        display.Specular = 0.12
        context = context_geometry(condition)
        camera_points = points
        if context is not None:
            context_source = TrivialProducer()
            update(context_source, context)
            dry = Show(context_source, view)
            dry.ColorArrayName = ["POINTS", ""]
            dry.DiffuseColor = [0.63, 0.65, 0.66]
            dry.AmbientColor = [0.63, 0.65, 0.66]
            camera_points = np.vstack(
                (points, vtk_to_numpy(context.GetPoints().GetData()))
            )
        low, high = camera_points.min(axis=0), camera_points.max(axis=0)
        center = (low + high) / 2
        span = max(high[0] - low[0], high[1] - low[1])
        center[2] += span * (-0.02 if context is not None else 0.045)
        view.CameraFocalPoint = center
        view.CameraPosition = [
            center[0] + 0.55 * span,
            center[1] - 1.2 * span,
            center[2] + 0.9 * span,
        ]
        view.CameraViewUp = [0, 0, 1]
        view.CameraParallelScale = span * (0.63 if context is not None else 0.34)
        title = Text()
        title.Text = f"({chr(97 + index)}) {label}\n{wet:,} wet panels; {total:,} total including waterplane"
        annotation = Show(title, view)
        annotation.FontFamily = "Times"
        annotation.FontSize = 28
        annotation.Color = [0.09, 0.16, 0.20]
        annotation.WindowLocation = "Upper Left Corner"
        footer = Text()
        size = points.max(axis=0) - points.min(axis=0)
        footer.Text = (
            f"Wet extents: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} m\n"
            "Geometry gain 1x; view fitted individually"
        )
        note = Show(footer, view)
        note.FontFamily = "Times"
        note.FontSize = 23
        note.Color = [0.27, 0.34, 0.38]
        note.WindowLocation = "Lower Right Corner"
        provenance.append(
            dict(
                key=key,
                source=pressure_path.relative_to(ROOT).as_posix(),
                source_sha256=digest(pressure_path),
                wet_panels=wet,
                total_panels=total,
                wet_extents_m=size.tolist(),
                acceptance=summary_path.relative_to(ROOT).as_posix(),
                acceptance_sha256=digest(summary_path),
            )
        )
    RenderAllViews()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    SaveScreenshot(
        str(args.output.resolve()),
        layout,
        ImageResolution=[2400, 1520],
        FontScaling="Do not scale fonts",
    )
    manifest = dict(
        renderer="ParaView "
        + str(servermanager.vtkSMProxyManager.GetVersionMajor())
        + "."
        + str(servermanager.vtkSMProxyManager.GetVersionMinor()),
        method="Actual accepted HST wet panel connectivity, symmetry expanded; native ParaView command export",
        geometry_gain=1,
        views="Orthographic, fitted independently; dry context in grey",
        waterplane="Included in the total panel count; wet surface shown",
        cases=provenance,
        output=args.output.resolve().relative_to(ROOT).as_posix(),
        output_sha256=digest(args.output),
        renderer_script_sha256=digest(Path(__file__)),
    )
    (ROOT / "examples/visualization/readme-meshes.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("Exported four accepted native wet meshes", flush=True)


if __name__ == "__main__":
    main()
