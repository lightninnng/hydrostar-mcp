"""Export the solved exterior integration mesh using native ParaView commands."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from paraview.simple import (
    _DisableFirstRenderCameraReset,
    CreateLayout,
    CreateView,
    SaveScreenshot,
    Show,
    Text,
    TrivialProducer,
    RenderAllViews,
)
from vtkmodules.all import vtkUnstructuredGrid

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.second_order import read_integration_mesh
from hydrostar_mcp.visualization import whole_mesh
from render_native_views import set_points, update


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dataset(vertices, faces):
    grid = vtkUnstructuredGrid()
    set_points(grid, np.array(vertices))
    for face in faces:
        grid.InsertNextCell(9 if len(face) == 4 else 5, len(face), face)
    return grid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hst", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    _DisableFirstRenderCameraReset()
    package = ROOT / "examples/second-order/platform"
    path = (args.hst or package / "inputs/platform2.hst").resolve()
    report_path = (
        path.with_suffix(".surface.json")
        if args.hst
        else package / "geometry/surface.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    total = report["full_equivalent_total_including_exterior"]
    body_points, body_faces = whole_mesh(path)
    surface = read_integration_mesh(path)
    points, faces = surface["vertices"], surface["faces"]
    if surface["symmetry"] != 1:
        raise ValueError("This export uses the accepted half-platform study")
    n = len(points)
    points = points + [[x, -y, z] for x, y, z in points]
    faces = faces + [[i + n for i in reversed(face)] for face in faces]
    layout = CreateLayout(name="Second-order integration mesh")
    layout.SplitHorizontal(0, 0.5)
    views = [CreateView("RenderView") for _ in range(2)]
    body = TrivialProducer()
    update(body, dataset(body_points, body_faces))
    external = TrivialProducer()
    update(external, dataset(points, faces))
    for i, view in enumerate(views):
        layout.AssignView(i + 1, view)
        view.UseColorPaletteForBackground = 0
        view.Background = [1, 1, 1]
        view.OrientationAxesVisibility = 1
        view.OrientationAxesLabelColor = [0.15, 0.2, 0.24]
        view.CameraParallelProjection = 1
        view.CenterAxesVisibility = 0
        mesh = Show(external, view)
        mesh.Representation = "Wireframe"
        mesh.ColorArrayName = ["POINTS", ""]
        mesh.DiffuseColor = [0.48, 0.56, 0.59]
        mesh.AmbientColor = [0.48, 0.56, 0.59]
        mesh.LineWidth = 0.6
        hull = Show(body, view)
        hull.Representation = "Surface With Edges"
        hull.ColorArrayName = ["POINTS", ""]
        hull.DiffuseColor = [0.37, 0.62, 0.72]
        hull.EdgeColor = [0.12, 0.25, 0.31]
        hull.LineWidth = 0.5
        if i == 0:
            view.CameraPosition = [230, -300, 280]
            view.CameraFocalPoint = [0, 0, -2]
            view.CameraViewUp = [0, 0, 1]
            view.CameraParallelScale = 140
            title = "(a) Actual wet body and exterior integration mesh"
            note = f"Outer radius 110 m; geometry gain 1x\n{total:,} total panels including waterplane and symmetry"
        else:
            view.CameraPosition = [0, 0, 500]
            view.CameraFocalPoint = [0, 0, 0]
            view.CameraViewUp = [0, 1, 0]
            view.CameraParallelScale = 48
            title = "(b) Conforming cut-outs at the actual waterlines"
            note = f"Exterior: {2 * report['quadrilaterals']:,} quadrilaterals and {2 * report['triangles']:,} triangles\nCoordinates in metres; all physical boundaries retained"
        for text, position, size in (
            (title, "Upper Left Corner", 25),
            (note, "Lower Right Corner", 22),
        ):
            label = Text()
            label.Text = text
            shown = Show(label, view)
            shown.FontFamily = "Times"
            shown.FontSize = size
            shown.Color = [0.1, 0.17, 0.21]
            shown.WindowLocation = position
    layout.SetSize(2400, 1060)
    RenderAllViews()
    target = (
        args.output or ROOT / "docs/assets/platform-second-order-mesh.png"
    ).resolve()
    SaveScreenshot(
        str(target),
        layout,
        ImageResolution=[2400, 1060],
        FontScaling="Do not scale fonts",
    )
    record = dict(
        renderer="ParaView",
        source=path.relative_to(ROOT).as_posix(),
        source_sha256=digest(path),
        wet_panels=len(body_faces),
        exterior_panels=len(faces),
        native_exterior_quadrilaterals=sum(len(f) == 4 for f in faces),
        native_exterior_triangles=sum(len(f) == 3 for f in faces),
        method="Actual native HST panel connectivity, symmetry expanded; global oblique view and local plan view",
        geometry_gain=1,
        script_sha256=digest(Path(__file__)),
        output=target.relative_to(ROOT).as_posix(),
        output_sha256=digest(target),
        visual_review="pending",
    )
    (
        target.with_suffix(".view.json") if args.hst else package / "mesh-view.json"
    ).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Exported the actual second-order integration mesh", flush=True)


if __name__ == "__main__":
    main()
