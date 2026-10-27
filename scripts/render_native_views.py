"""Render verified HSprv fields with pvpython; save native PNG frame sequences.

Example: pvpython --force-offscreen-rendering scripts/render_native_views.py
         examples/visualization/fields/platform --output tmp/pv-platform
"""

import argparse
import json
import hashlib
from pathlib import Path

import numpy as np
from paraview import servermanager
from paraview.simple import (
    _DisableFirstRenderCameraReset,
    ColorBy,
    CreateLayout,
    CreateView,
    GetColorTransferFunction,
    GetScalarBar,
    RenderAllViews,
    SaveScreenshot,
    Show,
    TrivialProducer,
)
from vtkmodules.all import (
    vtkAppendPolyData,
    vtkCellArray,
    vtkCylinderSource,
    vtkPoints,
    vtkPolyData,
    vtkTransform,
    vtkTransformFilter,
    vtkTubeFilter,
    vtkUnstructuredGrid,
)
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy


def vtk_array(values, name):
    result = numpy_to_vtk(np.ascontiguousarray(values), deep=True)
    result.SetName(name)
    return result


def set_points(data, values):
    p = vtkPoints()
    p.SetData(numpy_to_vtk(np.ascontiguousarray(values), deep=True))
    data.SetPoints(p)


def update(source, data):
    source.GetClientSideObject().SetOutput(data)
    source.GetClientSideObject().Modified()
    source.SMProxy.MarkModified(source.SMProxy)
    source.UpdatePipeline()


def context_geometry(condition):
    append = vtkAppendPolyData()
    for x, y, radius, height in condition["dry_columns"]:
        cylinder = vtkCylinderSource()
        cylinder.SetResolution(32)
        cylinder.SetRadius(radius)
        cylinder.SetHeight(height)
        cylinder.CappingOn()
        transform = vtkTransform()
        transform.Translate(x, y, height / 2)
        transform.RotateX(90)
        converted = vtkTransformFilter()
        converted.SetInputConnection(cylinder.GetOutputPort())
        converted.SetTransform(transform)
        converted.Update()
        append.AddInputData(converted.GetOutput())
    for member in condition["morison"]:
        if member["cm"] <= 0:
            continue
        points = vtkPoints()
        points.InsertNextPoint(member["start"])
        points.InsertNextPoint(member["end"])
        line = vtkPolyData()
        line.SetPoints(points)
        cells = vtkCellArray()
        cells.InsertNextCell(2)
        cells.InsertCellPoint(0)
        cells.InsertCellPoint(1)
        line.SetLines(cells)
        tube = vtkTubeFilter()
        tube.SetInputData(line)
        tube.SetRadius(member["diameter"] / 2)
        tube.SetNumberOfSides(12)
        tube.CappingOn()
        tube.Update()
        append.AddInputData(tube.GetOutput())
    if append.GetNumberOfInputConnections(0) == 0:
        return None
    append.Update()
    result = vtkPolyData()
    result.DeepCopy(append.GetOutput())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--frames", type=int, help="Limit frames for an export probe")
    args = parser.parse_args()
    _DisableFirstRenderCameraReset()
    package = args.package.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    condition = json.loads((package / "condition.json").read_text(encoding="utf-8"))
    verification = json.loads(
        (package / "verification.json").read_text(encoding="utf-8")
    )
    if set(verification["gates"].values()) != {"passed"}:
        raise ValueError("Numerically verified native data required")
    if verification.get("accepted_display_fields", "").split()[0:1] != ["waves.json"]:
        raise ValueError("Independent full-complex field acceptance is required")
    root = Path(__file__).resolve().parent.parent
    pressure_path = root / condition["pressure_file"]
    if (
        hashlib.sha256(pressure_path.read_bytes()).hexdigest()
        != condition["pressure_file_sha256"]
    ):
        raise ValueError("Pressure source changed")
    pressure_data = json.loads(pressure_path.read_text(encoding="utf-8"))
    waves = json.loads((package / "waves.json").read_text(encoding="utf-8"))
    views = [CreateView("RenderView") for _ in range(5)]
    layout = CreateLayout(name="HydroStar scientific fields")
    cell = 0
    ids = []
    for ratio in (0.2, 0.25, 1 / 3, 0.5):
        layout.SplitHorizontal(cell, ratio)
        ids.append(2 * cell + 1)
        cell = 2 * cell + 2
    ids.append(cell)
    for view, ident in zip(views, ids):
        layout.AssignView(ident, view)
        view.UseColorPaletteForBackground = 0
        view.Background = [1, 1, 1]
        view.OrientationAxesVisibility = 1
        view.OrientationAxesLabelColor = [0.15, 0.18, 0.21]
        view.CameraParallelProjection = 1
        view.CenterAxesVisibility = 0
    layout.SetSize(3600, 680)
    variables = ["Pressure", "Total", "Scattered", "Diffraction", "Radiation"]
    sources = [TrivialProducer() for _ in range(5)]
    body_sources = [TrivialProducer() for _ in range(4)]
    context = context_geometry(condition)
    context_sources = (
        [TrivialProducer() for _ in range(5)] if context is not None else []
    )
    cells = np.array(condition["valid_wave_cells"], dtype=int)
    active = np.unique(cells)
    mapped = np.searchsorted(active, cells)
    if waves["native_point_indices"] != active.tolist():
        raise ValueError("Complex field samples do not match the exterior grid")
    original_points = np.array(waves["points_m"])
    complex_fields = {
        name: np.array([complex(*v) for v in waves[key]])
        for name, key in [
            ("Total", "total"),
            ("Incident", "incident"),
            ("Diffraction", "diffraction"),
        ]
    }
    complex_fields["Scattered"] = complex_fields["Total"] - complex_fields["Incident"]
    complex_fields["Radiation"] = (
        complex_fields["Scattered"] - complex_fields["Diffraction"]
    )
    points = np.array(pressure_data["mesh"]["vertices"])
    mean_mesh = vtkUnstructuredGrid()
    set_points(mean_mesh, points)
    faces = pressure_data["mesh"]["faces"]
    for face in faces:
        if len(face) not in (3, 4):
            raise ValueError(
                "Native pressure mesh must retain its triangles or quadrilaterals"
            )
        mean_mesh.InsertNextCell(9 if len(face) == 4 else 5, len(face), face)
    pressure_head = np.array(
        [complex(*v) for v in pressure_data["following_head"][: len(faces)]]
    )
    displays = []
    gain = condition["motion_gain"]
    count = min(args.frames or condition["frames"], condition["frames"])
    for frame in range(count):
        phase = np.exp(2j * np.pi * frame / condition["frames"])
        amplitude = condition["wave_amplitude_m"]
        mean = vtkUnstructuredGrid()
        mean.DeepCopy(mean_mesh)
        pressure = (
            amplitude
            * (pressure_head * phase).real
            * condition["rho_kg_m3"]
            * condition["gravity_m_s2"]
            / 1000
        )
        mean.GetCellData().AddArray(vtk_array(pressure, "Pressure"))
        update(sources[0], mean)
        moving = vtkUnstructuredGrid()
        moving.DeepCopy(mean_mesh)
        motion = np.array(condition["physical_motion"][frame])
        displacement = motion[:3] + np.cross(
            motion[3:], points - np.array(condition["cog_m"])
        )
        set_points(moving, points + gain * displacement)
        for index, source in enumerate(body_sources):
            update(source, mean_mesh if index == 2 else moving)
        fields = {
            name: amplitude * (complex_fields[name] * phase).real
            for name in variables[1:]
        }
        for j, (name, values) in enumerate(fields.items(), 1):
            data = vtkUnstructuredGrid()
            xyz = original_points.copy()
            xyz[:, 2] = values * condition["wave_height_gain"]
            set_points(data, xyz)
            for face in mapped:
                data.InsertNextCell(
                    9, 4, face.tolist()
                )  # actual rectangular wave samples
            data.GetPointData().AddArray(vtk_array(values, name))
            update(sources[j], data)
        if context is not None:
            update(context_sources[0], context)
            background = vtkPolyData()
            background.DeepCopy(context)
            p = vtk_to_numpy(context.GetPoints().GetData())
            motion = np.array(condition["physical_motion"][frame])
            delta = motion[:3] + np.cross(motion[3:], p - np.array(condition["cog_m"]))
            set_points(background, p + gain * delta)
            for index, source in enumerate(context_sources[1:], 1):
                update(source, context if index == 3 else background)
        if frame == 0:
            for j, (view, source, name) in enumerate(zip(views, sources, variables)):
                display = Show(source, view)
                display.Representation = "Surface With Edges" if j == 0 else "Surface"
                display.EdgeColor = [0.25, 0.29, 0.33]
                display.LineWidth = 0.4
                display.Specular = 0.08
                display.Diffuse = 0.85
                display.Ambient = 0.25
                ColorBy(display, ("CELLS" if j == 0 else "POINTS", name))
                lut = GetColorTransferFunction(name)
                bound = max(condition["colour_limits"][name], 0.00001)
                lut.RGBPoints = [
                    -bound,
                    0.129,
                    0.4,
                    0.674,
                    0,
                    0.969,
                    0.969,
                    0.969,
                    bound,
                    0.698,
                    0.094,
                    0.169,
                ]
                lut.ColorSpace = "Diverging"
                lut.RescaleTransferFunction(-bound, bound)
                display.SetScalarBarVisibility(view, True)
                bar = GetScalarBar(lut, view)
                bar.Title = "p (kPa)" if j == 0 else "Elevation (m)"
                bar.ComponentTitle = ""
                bar.TitleFontFamily = "Times"
                bar.LabelFontFamily = "Times"
                bar.TitleFontSize = 26
                bar.LabelFontSize = 24
                bar.TitleColor = [0.1, 0.13, 0.16]
                bar.LabelColor = [0.1, 0.13, 0.16]
                bar.Orientation = "Horizontal"
                bar.WindowLocation = "Any Location"
                bar.Position = [0.25, 0.075]
                bar.ScalarBarLength = 0.68
                bar.ScalarBarThickness = 14
                bar.AutomaticLabelFormat = 0
                bar.LabelFormat = "{:.3g}"
                bar.RangeLabelFormat = "{:.3g}"
                bar.DrawNanAnnotation = 0
                bar.UseCustomLabels = 1
                bar.CustomLabels = [-bound, -bound / 2, 0, bound / 2, bound]
                bar.AddRangeLabels = 0
                if j:
                    body = Show(body_sources[j - 1], view)
                    body.DiffuseColor = [0.35, 0.43, 0.48]
                    body.AmbientColor = [0.35, 0.43, 0.48]
                    body.Representation = "Surface"
                    body.ColorArrayName = ["POINTS", ""]
                if context_sources:
                    dry = Show(context_sources[j], view)
                    dry.DiffuseColor = [0.55, 0.56, 0.57]
                    dry.AmbientColor = [0.55, 0.56, 0.57]
                    dry.ColorArrayName = ["POINTS", ""]
                camera_points = points if j == 0 else original_points
                low, high = camera_points.min(axis=0), camera_points.max(axis=0)
                center = (low + high) / 2
                span = max(high[0] - low[0], high[1] - low[1])
                if j:
                    center[2] = 0
                elif context is not None:
                    center[2] -= span * 0.08
                view.CameraFocalPoint = center
                view.CameraPosition = [
                    center[0] + span * 0.55,
                    center[1] - span * 1.2,
                    center[2] + span * 0.9,
                ]
                view.CameraViewUp = [0, 0, 1]
                view.CameraParallelScale = span * (
                    0.63 if j else (0.72 if context is not None else 0.57)
                )
                displays.append(display)
        RenderAllViews()
        SaveScreenshot(
            str(output / f"frame{frame:02d}.png"), layout, ImageResolution=[3600, 680]
        )
        print("Exported native ParaView frame", frame, flush=True)
    record = dict(
        renderer="ParaView "
        + servermanager.vtkSMProxyManager.GetVersionMajor().__str__()
        + "."
        + servermanager.vtkSMProxyManager.GetVersionMinor().__str__(),
        frames=count,
        frame_size=[3600, 680],
        panels=variables,
        source="Native HSPRS/HSRAO complex fields and verified panel pressure; archived HSprv geometry/motion cross-check",
        interpolation="Actual native panel pressure as cell values; physical colour limits fixed over the cycle",
        pressure_pose="Mean wetted surface",
        motion_gain=gain,
        wave_height_gain=condition["wave_height_gain"],
    )
    (output / "render.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
