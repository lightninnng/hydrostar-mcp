"""Export mean wet meshes from the manual's HSprv -> ParaView route.

pvpython --disable-registry --force-offscreen-rendering scripts/render_geometry_meshes.py
"""

import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from paraview import servermanager
from paraview.simple import (
    _DisableFirstRenderCameraReset,
    CreateLayout,
    CreateView,
    PVDReader,
    RenderAllViews,
    SaveScreenshot,
    Show,
    Text,
)
from vtkmodules.all import vtkPolyData, vtkStaticPointLocator
from vtkmodules.util.numpy_support import vtk_to_numpy

from render_native_views import set_points

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "examples/geometry"
CASES = (
    ("lofted_vessel", "Curved-section hull"),
    ("moonpool_caisson", "Through-moonpool caisson"),
    ("cad_spar", "Curved Spar with a heave plate"),
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mesh_check(data, surface, native_frame):
    """Independently match every native cell to accepted HST connectivity."""
    expected = np.asarray(surface["vertices"])
    target = vtkPolyData()
    set_points(target, expected)
    locator = vtkStaticPointLocator()
    locator.SetDataSet(target)
    locator.BuildLocator()
    points = vtk_to_numpy(data.GetPoints().GetData())
    mapping = [locator.FindClosestPoint(p) for p in points]
    error = float(np.max(np.linalg.norm(points - expected[mapping], axis=1)))
    array = ET.parse(native_frame).find(".//Points/DataArray")
    if array.attrib.get("format") != "ascii":
        raise ValueError("Expected the inspected native ASCII coordinate format")
    # The geometry path quantizes to four significant digits before writing
    # padded eight-decimal VTU text. Prove that conversion for every coordinate.
    matched = expected[mapping]
    quantized = np.array([[float(f"{v:.3e}") for v in row] for row in matched])
    rounding_passed = np.array_equal(points, quantized.astype(points.dtype))
    halfsteps = np.array(
        [
            [0.5 * 10 ** (math.floor(math.log10(abs(v))) - 3) if v else 0 for v in row]
            for row in matched
        ]
    )
    bounds = halfsteps + np.finfo(np.float32).eps * np.abs(points)
    bound = float(np.max(np.linalg.norm(bounds, axis=1)))
    actual = []
    padded_triangles = 0
    for i in range(data.GetNumberOfCells()):
        cell = data.GetCell(i)
        ids = [mapping[cell.GetPointId(j)] for j in range(cell.GetNumberOfPoints())]
        if len(ids) == 4 and ids[-1] == ids[-2] and len(set(ids)) == 3:
            ids.pop()
            padded_triangles += 1
        actual.append(tuple(sorted(ids)))
    wanted = [tuple(sorted(face)) for face in surface["faces"]]
    if (
        not rounding_passed
        or len(set(mapping)) != len(expected)
        or sorted(actual) != sorted(wanted)
    ):
        raise ValueError(
            f"Native/HST panel connectivity mismatch: {error} m, {len(actual)}/{len(wanted)}"
        )
    return error, bound, padded_triangles, points


def main():
    _DisableFirstRenderCameraReset()
    layout = CreateLayout(name="Budgeted native wet meshes")
    layout.SplitHorizontal(0, 1 / 3)
    layout.SplitHorizontal(2, 0.5)
    layout.SetSize(2700, 1160)
    records = []
    for i, ((key, title), cell) in enumerate(zip(CASES, (1, 5, 6))):
        folder = BASE / key
        native = read(folder / "visualization/native-mesh.json")
        summary = read(folder / "verification.json")
        geometry = read(folder / "geometry/geometry-report.json")
        cfg = read(folder / "config.json")
        if not native["ok"] or set(summary["quality_gates"].values()) != {"passed"}:
            raise ValueError("Accepted native source required")
        for name, expected in native["files"].items():
            if digest(folder / name) != expected:
                raise ValueError("Native export changed: " + name)
        if native["mesh_sha256"] != digest(
            folder / "inputs" / (cfg["project"] + ".hst")
        ):
            raise ValueError("Solved HST differs from HSprv source")
        surface = read(folder / "geometry/surface.json")
        if (
            digest(folder / "geometry/surface.json")
            != geometry["files"]["surface.json"]
        ):
            raise ValueError("Accepted surface changed")
        pvd = folder / native["dataset"]
        first = ET.parse(pvd).find(".//DataSet")
        first_time = float(first.attrib["timestep"])
        source = PVDReader(FileName=str(pvd))
        source.UpdatePipeline(first_time)
        data = servermanager.Fetch(source)
        while data.IsA("vtkMultiBlockDataSet"):
            if data.GetNumberOfBlocks() != 1:
                raise ValueError("Single native wet body required")
            data = data.GetBlock(0)
        error, rounding_bound, padded_triangles, points = mesh_check(
            data, surface, pvd.parent / first.attrib["file"]
        )
        view = CreateView("RenderView")
        layout.AssignView(cell, view)
        view.ViewTime = first_time
        view.UseColorPaletteForBackground = 0
        view.Background = [1, 1, 1]
        view.OrientationAxesVisibility = 1
        view.OrientationAxesLabelColor = [0.15, 0.20, 0.24]
        view.CameraParallelProjection = 1
        view.CenterAxesVisibility = 0
        display = Show(source, view)
        display.Representation = "Surface With Edges"
        display.ColorArrayName = ["POINTS", ""]
        display.DiffuseColor = [0.63, 0.76, 0.79]
        display.AmbientColor = [0.63, 0.76, 0.79]
        display.EdgeColor = [0.16, 0.28, 0.33]
        display.LineWidth = 0.8
        display.Ambient = 0.35
        display.Diffuse = 0.75
        low, high = points.min(axis=0), points.max(axis=0)
        center = (low + high) / 2
        span = max(high - low)
        direction = np.array([0.55, -1.2, 0.9])
        forward = -direction / np.linalg.norm(direction)
        right = np.cross(forward, [0, 0, 1])
        right /= np.linalg.norm(right)
        upward = np.cross(right, forward)
        projected = np.column_stack([points @ right, points @ upward])
        midpoint = (projected.min(axis=0) + projected.max(axis=0)) / 2
        center += right * (midpoint[0] - center @ right)
        center += upward * (midpoint[1] - center @ upward)
        width, height = np.ptp(projected, axis=0)
        scale = max(height / (2 * 0.70), width / (2 * (900 / 1160) * 0.86))
        center += upward * (0.03 * scale)
        view.CameraFocalPoint = center
        view.CameraPosition = center + span * direction
        view.CameraViewUp = [0, 0, 1]
        view.CameraParallelScale = scale
        total = summary["resource_policy"]["full_equivalent_total"]
        if total > 3000:
            raise ValueError("3000 total panel budget exceeded")
        label = Text()
        label.Text = f"({chr(97 + i)}) {title}\n{len(surface['faces']):,} wet; {total:,} total / 3,000"
        annotation = Show(label, view)
        annotation.FontFamily = "Times"
        annotation.FontSize = 25
        annotation.Color = [0.09, 0.16, 0.20]
        annotation.WindowLocation = "Upper Left Corner"
        footer = Text()
        footer.Text = (
            "Mean wet mesh; coordinates in m\nGeometry gain 1x; orthographic view"
        )
        note = Show(footer, view)
        note.FontFamily = "Times"
        note.FontSize = 23
        note.Color = [0.27, 0.34, 0.38]
        note.WindowLocation = "Lower Right Corner"
        records.append(
            dict(
                key=key,
                native_export=f"{key}/visualization/native-mesh.json",
                native_export_sha256=digest(folder / "visualization/native-mesh.json"),
                mesh_sha256=native["mesh_sha256"],
                wet_panels=len(surface["faces"]),
                full_equivalent_total=total,
                max_native_coordinate_error_m=error,
                coordinate_rounding_check="passed",
                native_triangle_padding_count=padded_triangles,
                max_native_coordinate_rounding_bound_m=rounding_bound,
                coordinate_precision="All native coordinates equal exact HST coordinates rounded to four significant digits and read as Float32. Native VTU pads HST triangles by repeating their last vertex; cell matching removes that padding only. Exact coordinates and panel types remain in HST.",
                connectivity="Every native triangle/quadrilateral matches the accepted HST",
            )
        )
    RenderAllViews()
    output = ROOT / "docs/assets/geometry-source-cases.png"
    SaveScreenshot(
        str(output),
        layout,
        ImageResolution=[2700, 1160],
        FontScaling="Do not scale fonts",
    )
    receipt = dict(
        renderer=f"ParaView {servermanager.vtkSMProxyManager.GetVersionMajor()}.{servermanager.vtkSMProxyManager.GetVersionMinor()}",
        workflow="HSprv native PVD -> ParaView PVDReader -> SaveScreenshot; mean geometry, deformation off",
        cases=records,
        geometry_gain=1,
        coordinate_unit="m",
        output="docs/assets/geometry-source-cases.png",
        output_sha256=digest(output),
        renderer_script_sha256=digest(Path(__file__)),
    )
    (BASE / "native-mesh-views.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Exported three HSprv/ParaView wet meshes; exact native panel connectivity checked",
        flush=True,
    )


if __name__ == "__main__":
    main()
