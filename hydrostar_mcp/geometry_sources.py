"""Typed, unit-aware requests for general geometry preprocessing."""

from __future__ import annotations

from typing import Annotated, Literal
from pydantic import Field, model_validator
from .models import Model, Positive, Vector3
from .core import identifier, RECOMMENDED_MAX_PANELS


class PanelQuality(Model):
    max_edge_ratio: Annotated[float, Field(ge=1, le=20)] = 8.0
    min_corner_deg: Annotated[float, Field(gt=0, le=45)] = 10.0
    max_corner_deg: Annotated[float, Field(ge=135, lt=180)] = 170.0
    max_warpage_deg: Annotated[float, Field(gt=0, le=15)] = 5.0
    max_neighbor_size_ratio: Annotated[float, Field(gt=1, le=5)] = 2.0


class GeometryRequest(Model):
    project: str
    path: str
    units: Literal["m", "cm", "mm", "file"]
    waterline_z_m: float = 0.0
    rho_kg_m3: Positive = 1025.0
    gravity_m_s2: Positive = 9.81
    axis_map: Annotated[list[str], Field(min_length=3, max_length=3)] = Field(
        default_factory=lambda: ["x", "y", "z"]
    )
    translation_m: Vector3 = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    mesh_size_m: Positive = 3.0
    panel_layout: Literal[
        "quad_dominant", "ring_bands", "polygon_blocks", "station_bands", "triangular"
    ] = "quad_dominant"
    structured_axis: Literal["x", "y", "z"] | None = None
    longitudinal_cells: Annotated[int, Field(ge=8, le=1000)] | None = None
    longitudinal_grading_blend: Annotated[float, Field(ge=0, le=1)] = 0.2
    axis_center_xy_m: (
        Annotated[list[float], Field(min_length=2, max_length=2)] | None
    ) = None
    minimum_quad_fraction: Annotated[float, Field(ge=0, le=1)] = 0.8
    panel_quality: PanelQuality = Field(default_factory=PanelQuality)
    curvature_samples: Annotated[int, Field(ge=16, le=128)] = 32
    curve_tolerance_m: Annotated[float, Field(gt=0, le=0.1)] = 0.005
    weld_tolerance_m: Annotated[float, Field(gt=0, le=0.0001)] = 1e-8
    section_axis: Literal["x", "y", "z"] = "x"
    section_curve: Literal["polyline", "spline"] = "polyline"
    longitudinal_ruled: bool = True
    spline_seam: Literal["source", "lowest_z"] = "source"
    mirror_half_sections: bool = False
    station_layers: dict[str, float] = Field(default_factory=dict)
    expected_volume_m3: Positive | None = None
    volume_tolerance_relative: Annotated[float, Field(gt=0, le=0.05)] = 0.005
    expected_wet_components: Annotated[int, Field(ge=1, le=100)] = 1
    flip_normals: bool = False
    max_panels: Annotated[int, Field(ge=20, le=50000)] = RECOMMENDED_MAX_PANELS
    timeout_s: Annotated[float, Field(gt=0, le=1800)] = 600.0
    source_note: str = Field(min_length=10, max_length=2000)
    pdf_page: Annotated[int, Field(ge=0)] = 0

    @model_validator(mode="after")
    def coordinate_frame(self):
        identifier(self.project)
        if {v.lstrip("-") for v in self.axis_map} != {"x", "y", "z"} or any(
            v not in ("x", "y", "z", "-x", "-y", "-z") for v in self.axis_map
        ):
            raise ValueError("axis_map 必须是 x、y、z 的带符号排列")
        # Preserve a right-handed frame; a reflection needs explicit mesh winding treatment.
        axes = ["xyz".index(v.lstrip("-")) for v in self.axis_map]
        inversions = sum(axes[i] > axes[j] for i in range(3) for j in range(i + 1, 3))
        if (-1) ** (inversions + sum(v.startswith("-") for v in self.axis_map)) < 0:
            raise ValueError(
                "axis_map 须保持右手坐标系；请用旋转和显式法向检查处理镜像"
            )
        if self.weld_tolerance_m >= self.curve_tolerance_m / 10:
            raise ValueError("节点合并容差应至少比型线离散容差小一个数量级")
        return self


FORMATS = {
    ".json": "loft_sections",
    ".csv": "station_table",
    ".dxf": "station_curves",
    ".step": "cad_solid",
    ".stp": "cad_solid",
    ".iges": "cad_solid",
    ".igs": "cad_solid",
    ".brep": "cad_solid",
    ".stl": "surface_mesh",
    ".obj": "surface_mesh",
    ".ply": "surface_mesh",
    ".hst": "native_mesh",
    ".png": "drawing",
    ".jpg": "drawing",
    ".jpeg": "drawing",
    ".tif": "drawing",
    ".tiff": "drawing",
    ".pdf": "drawing",
}


def format_catalog():
    return {
        "units": "SI after explicit source units and a right-handed coordinate transform",
        "formats": FORMATS,
        "loft": "Closed ordered profiles in JSON or station,u,v CSV; polyline chines or interpolating splines",
        "dxf": "Named station layers with closed LWPOLYLINE/POLYLINE/SPLINE/CIRCLE/ELLIPSE profiles",
        "cad": "Closed STEP/IGES/BREP solids, converted through OpenCASCADE and cut at the mean waterline",
        "mesh": "Oriented surface triangles/quads, clipped at the mean waterline",
        "drawing": "Calibrated tracing workspace; metric sections are reviewed before meshing",
        "physics": "Geometry feeds the existing single-rigid-body first-order BEM/Morison workflow",
        "panel_layouts": {
            "ring_bands": "Coaxial CAD sections, equal-angle ring bands, radial shoulders and an O-grid bottom",
            "station_bands": "One smooth x-axis loft, matched keel/waterline profiles and graded longitudinal stations",
            "polygon_blocks": "One constant z-axis polygon prism with one through opening; feature-matched blocks",
            "quad_dominant": "General CAD transfinite patches and quadrilateral-oriented recombination; explicit quality gates",
            "triangular": "Explicit triangular layout for comparison and locally suitable topology",
        },
    }


class Profile(Model):
    position: float
    points: Annotated[list[list[float]], Field(min_length=3, max_length=5000)]

    @model_validator(mode="after")
    def points_2d(self):
        if any(len(p) != 2 for p in self.points):
            raise ValueError("每个剖面点采用 [u,v] 两个坐标")
        return self


class LoftSolid(Model):
    name: str
    operation: Literal["add", "cut"] = "add"
    axis: Literal["x", "y", "z"] = "x"
    curve: Literal["polyline", "spline"] = "polyline"
    ruled: bool = True
    profiles: Annotated[list[Profile], Field(min_length=2, max_length=200)]

    @model_validator(mode="after")
    def ordered_profiles(self):
        positions = [p.position for p in self.profiles]
        if any(a >= b for a, b in zip(positions, positions[1:])):
            raise ValueError("放样剖面位置须严格递增")
        if (
            self.curve == "polyline"
            and len({len(p.points) for p in self.profiles}) != 1
        ):
            raise ValueError("对应剖面采用相同点数及特征顺序，以核验折角与曲线对应关系")
        return self


class LoftDocument(Model):
    schema_version: Literal[1] = 1
    solids: Annotated[list[LoftSolid], Field(min_length=1, max_length=100)]
    digitization_evidence: dict | None = None
