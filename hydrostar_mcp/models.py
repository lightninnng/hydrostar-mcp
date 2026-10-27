"""Validated semantic input shared by the CLI and MCP schemas."""

from __future__ import annotations

import math
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .core import (
    DOFS,
    grid_values,
    identifier,
    validate_gyradius,
    validate_passive_matrix,
)

Positive = Annotated[float, Field(gt=0)]
Nonnegative = Annotated[float, Field(ge=0)]
Vector3 = Annotated[list[float], Field(min_length=3, max_length=3)]
Radii6 = Annotated[list[float], Field(min_length=6, max_length=6)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)


class Barge(Model):
    type: Literal["barge"] = "barge"
    length: Positive = 100.0
    beam: Positive = 30.0
    draft: Positive = 6.0
    n_length: Annotated[int, Field(gt=0, strict=True)] = 48
    n_half_beam: Annotated[int, Field(gt=0, strict=True)] = 10
    n_draft: Annotated[int, Field(gt=0, strict=True)] = 4


class ImportedMesh(Model):
    type: Literal["hst"] = "hst"
    path: str = Field(
        description="HST path relative to HS_SOURCE_ROOT; resolved paths must stay inside it"
    )
    expected_volume_m3: Positive | None = None


class Semisub(Model):
    type: Literal["semisub"] = "semisub"
    pontoon_length: Positive = 36.0
    pontoon_width: Positive = 6.0
    pontoon_height: Positive = 4.0
    draft: Positive = 14.0
    column_x: Positive = 12.0
    pontoon_y: Positive = 12.0
    column_width: Positive = 4.0
    crossbeam_height: Positive = 2.0
    freeboard: Positive = 6.0
    deck_width: Positive = 32.0
    deck_thickness: Positive = 2.0
    target_panel_m: Annotated[float, Field(ge=0.25)] = 1.5

    @model_validator(mode="after")
    def connected_geometry(self):
        if (
            self.column_width > self.pontoon_width
            or self.column_x + self.column_width / 2 >= self.pontoon_length / 2
        ):
            raise ValueError("立柱应完整落在浮筒顶面内")
        if (
            2 * self.column_x <= self.column_width
            or 2 * self.pontoon_y <= self.pontoon_width
        ):
            raise ValueError("立柱和两浮筒应保持分离间距")
        if (
            self.draft <= self.pontoon_height
            or self.crossbeam_height > self.pontoon_height
        ):
            raise ValueError("吃水应高于浮筒顶面，横梁高度应处于浮筒高度内")
        if (
            self.deck_width / 2
            < max(self.column_x, self.pontoon_y) + self.column_width / 2
        ):
            raise ValueError("干甲板应覆盖四立柱顶面")
        return self


class CurvedHull(Model):
    type: Literal["curved_hull"] = "curved_hull"
    length: Positive = 72.0
    beam: Positive = 14.0
    draft: Positive = 4.5
    n_length: Annotated[int, Field(ge=24, le=192, multiple_of=2)] = 56
    n_section: Annotated[int, Field(ge=4, le=32)] = 12


class SectionHull(Model):
    type: Literal["section_hull"] = "section_hull"
    family: Literal["container", "tanker"] = "container"
    length: Positive = 230.0
    beam: Positive = 32.2
    draft: Positive = 10.8
    midship_coefficient: Annotated[float, Field(gt=0.9, lt=1)] = 0.985
    parallel_start: Annotated[float, Field(gt=0.05, lt=0.5)] = 0.25
    parallel_end: Annotated[float, Field(gt=0.5, lt=0.9)] = 0.60
    fullness_exponent: Annotated[float, Field(gt=0.25, le=8)] = 1.0
    aft_fullness_exponent: Annotated[float, Field(gt=0.25, le=8)] = 1.0
    transom_width_ratio: Annotated[float, Field(gt=0, lt=1)] = 0.45
    transom_draft_ratio: Annotated[float, Field(gt=0, le=1)] = 0.35
    bulb_length_ratio: Annotated[float, Field(ge=0, le=0.05)] = 0.025
    bulb_breadth_ratio: Annotated[float, Field(ge=0, le=0.3)] = 0.15
    n_length: Annotated[int, Field(ge=32, le=160)] = 48
    n_section: Annotated[int, Field(ge=6, le=24)] = 12


class ColumnSemi(Model):
    type: Literal["column_semisub"] = "column_semisub"
    draft: Positive = 20.0
    offset_radius: Positive = 28.86751346
    center_diameter: Positive = 6.5
    upper_diameter: Positive = 12.0
    base_diameter: Positive = 24.0
    base_height: Positive = 6.0
    freeboard: Positive = 12.0
    n_azimuth: Annotated[int, Field(ge=16, le=64, multiple_of=4)] = 24
    target_panel_m: Annotated[float, Field(ge=1)] = 2.0

    @model_validator(mode="after")
    def separated_columns(self):
        if self.base_height >= self.draft or self.upper_diameter >= self.base_diameter:
            raise ValueError("扩底半潜须满足基柱高度小于吃水、基柱直径大于上柱直径")
        if self.offset_radius <= (self.center_diameter + self.base_diameter) / 2:
            raise ValueError("中心柱与偏置柱应保持分离")
        if math.sqrt(3) * self.offset_radius <= self.base_diameter:
            raise ValueError("三偏置基柱应保持分离")
        return self


class BoxMassComponent(Model):
    name: str = Field(min_length=1, max_length=80)
    mass_fraction: Annotated[float, Field(gt=0, le=1)]
    size_m: Vector3
    center_m: Vector3
    shape: Literal["box", "vertical_cylinder", "point", "rigid_body"] = "box"
    gyradius_m: Radii6 | None = None

    @model_validator(mode="after")
    def positive_size(self):
        if self.shape == "point" and any(v != 0 for v in self.size_m):
            raise ValueError("点质量的 size_m 应为 [0,0,0]")
        if self.shape != "point" and any(v <= 0 for v in self.size_m):
            raise ValueError("有效质量分量尺寸须为正")
        if self.shape == "vertical_cylinder" and not math.isclose(
            self.size_m[0], self.size_m[1]
        ):
            raise ValueError("竖直圆柱的前两项尺寸应为同一直径")
        if self.shape == "rigid_body":
            if self.gyradius_m is None:
                raise ValueError("刚体质量分量须提供关于自身重心的 gyradius_m")
            validate_gyradius(self.gyradius_m)
        elif self.gyradius_m is not None:
            raise ValueError("gyradius_m 仅用于 rigid_body 分量")
        return self


class Frequency(Model):
    min: Positive = 0.05
    max: Positive = 1.8
    step: Annotated[float, Field(ge=0.0001)] = 0.05

    @model_validator(mode="after")
    def validate_grid(self):
        grid_values(self.min, self.max, self.step, name="frequency")
        return self


class Heading(Model):
    min: Annotated[float, Field(ge=0, le=360)] = 0.0
    max: Annotated[float, Field(ge=0, le=360)] = 360.0
    step: Annotated[float, Field(ge=0.01)] = 30.0

    @model_validator(mode="after")
    def validate_grid(self):
        grid_values(self.min, self.max, self.step, name="heading", max_count=361)
        if any(
            not math.isclose(v * 100, round(v * 100), abs_tol=1e-6)
            for v in (self.min, self.max, self.step)
        ):
            raise ValueError("浪向表输出到 0.01 度；min/max/step 必须按该精度给定")
        return self


class Environment(Model):
    frequency: Frequency = Field(default_factory=Frequency)
    headings: Heading = Field(default_factory=Heading)
    depth: Positive | Literal["INF"] = "INF"
    speed_m_s: Nonnegative = 0.0
    rho_kg_m3: Positive = 1025.0
    gravity_m_s2: Positive = 9.81


class MorisonMember(Model):
    start: Vector3
    end: Vector3
    diameter: Positive
    cm: Nonnegative = 0.0
    cd: Nonnegative = 0.0
    segments: Annotated[int, Field(gt=0, strict=True)] = 20

    @model_validator(mode="after")
    def nonzero_length(self):
        if self.start == self.end:
            raise ValueError("Morison 杆件端点不能相同")
        return self


class Spectrum(Model):
    hs: Positive
    tp: Positive
    gamma: Positive = 1.0
    heading: Annotated[float, Field(ge=0, le=360)] = 0.0


class Mechanics(Model):
    model: Literal["uniform_box_demo", "explicit", "components"] = "uniform_box_demo"
    mass_kg: Positive | None = None
    cog_m: Vector3 | None = None
    gyradius_m: Radii6 | None = None
    roll_damping_pct: Nonnegative | None = None
    restraint: Literal["free", "moored", "tension_leg"] = "free"
    stiffness_matrix: list[list[float]] | None = None
    linear_damping_matrix: list[list[float]] | None = None
    hydrostatics_method: Literal["hull", "waterplane"] = "hull"
    components: list[BoxMassComponent] = Field(default_factory=list)
    morison: list[MorisonMember] = Field(default_factory=list)
    wave_amplitude_m: Positive | None = None
    spectrum: Spectrum | None = None
    vertical_external_force_n: float = Field(
        default=0.0, description="Net static external vertical force, upward positive"
    )
    equilibrium_relative_tolerance: Annotated[float, Field(gt=0, le=0.05)] = 0.01
    cog_xy_tolerance_m: Annotated[float, Field(gt=0, le=0.5)] = 0.05
    source_note: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def validate_mechanics(self):
        if self.model == "explicit":
            if (
                self.mass_kg is None
                or self.cog_m is None
                or self.gyradius_m is None
                or not self.source_note.strip()
            ):
                raise ValueError(
                    "显式质量模型请提供 mass_kg、cog_m、gyradius_m 和 source_note（课程假定或装载资料）"
                )
            if self.roll_damping_pct is None:
                raise ValueError("请显式给出 roll_damping_pct；无附加阻尼时填 0")
            validate_gyradius(self.gyradius_m)
        elif self.model == "components":
            if (
                not self.components
                or not self.source_note.strip()
                or self.roll_damping_pct is None
            ):
                raise ValueError(
                    "分量质量模型须提供 components、source_note 和 roll_damping_pct"
                )
            if self.cog_m is not None or self.gyradius_m is not None:
                raise ValueError("分量质量模型的重心和惯性由分量积分求得")
            if not math.isclose(
                sum(c.mass_fraction for c in self.components), 1, abs_tol=1e-10
            ):
                raise ValueError("质量分量比例之和必须为 1")
        elif (
            any(x is not None for x in (self.mass_kg, self.cog_m, self.gyradius_m))
            or self.vertical_external_force_n != 0
        ):
            raise ValueError(
                "uniform_box_demo 不接受质量/重心/惯性/外力覆盖；请使用 explicit"
            )
        if self.model != "components" and self.components:
            raise ValueError("components 仅用于分量质量模型")
        if self.linear_damping_matrix is not None:
            validate_passive_matrix(self.linear_damping_matrix)
        if self.stiffness_matrix is not None:
            if len(self.stiffness_matrix) != 6 or any(
                len(row) != 6 for row in self.stiffness_matrix
            ):
                raise ValueError("stiffness_matrix 必须为 6x6")
        if self.model == "uniform_box_demo" and any(m.cm > 0 for m in self.morison):
            raise ValueError(
                "带实体 Morison 杆件的模型请使用 explicit，并给出组合结构的质量参数"
            )
        if self.restraint != "free" and self.stiffness_matrix is None:
            raise ValueError("系泊/TLP 模型必须显式提供附加刚度矩阵")
        if self.wave_amplitude_m is not None and self.spectrum is not None:
            raise ValueError("规则波与随机海况线性化只能选一项")
        if (
            any(m.cd > 0 for m in self.morison)
            and self.wave_amplitude_m is None
            and self.spectrum is None
        ):
            raise ValueError("有 Cd 的 Morison 杆件须提供 wave_amplitude_m 或 spectrum")
        return self


class CaseConfig(Model):
    project: str = "barge100"
    object_type: Literal["ship", "floating_structure"] = "ship"
    geometry: Annotated[
        Barge | ImportedMesh | Semisub | CurvedHull | SectionHull | ColumnSemi,
        Field(discriminator="type"),
    ] = Field(default_factory=Barge)
    environment: Environment = Field(default_factory=Environment)
    mechanics: Mechanics = Field(default_factory=Mechanics)
    output_dofs: list[Literal["surge", "sway", "heave", "roll", "pitch", "yaw"]] = (
        Field(default_factory=lambda: list(DOFS), min_length=1)
    )
    output_point_m: Vector3 | None = None
    reference_form: (
        Literal["container_kcs_style", "tanker_kvlcc2_style", "semisub_oc4_style"]
        | None
    ) = None
    recommended_max_panels: Annotated[int, Field(gt=0, strict=True)] = 3000
    waterplane_estimate_factor: Annotated[float, Field(ge=1)] = 1.2
    nproc: Annotated[int, Field(ge=1, le=64, strict=True)] = 4
    module_timeout_s: Annotated[float, Field(gt=0, le=86400)] = 1800.0

    @model_validator(mode="after")
    def validate_case(self):
        identifier(self.project)
        if self.reference_form:
            if self.reference_form == "semisub_oc4_style" and not isinstance(
                self.geometry, ColumnSemi
            ):
                raise ValueError("OC4参照构型须使用 column_semisub 几何")
            if self.reference_form != "semisub_oc4_style":
                expected = (
                    "container"
                    if self.reference_form == "container_kcs_style"
                    else "tanker"
                )
                if (
                    not isinstance(self.geometry, SectionHull)
                    or self.geometry.family != expected
                ):
                    raise ValueError("船舶参照构型须与剖面船型族一致")
        if len(set(self.output_dofs)) != len(self.output_dofs):
            raise ValueError("输出自由度不能重复")
        if (
            isinstance(self.geometry, ImportedMesh)
            and self.mechanics.model != "explicit"
        ):
            raise ValueError("导入网格不能从湿表面猜测质量分布；须用 explicit 力学模型")
        if (
            isinstance(
                self.geometry, (Barge, Semisub, CurvedHull, SectionHull, ColumnSemi)
            )
            and self.environment.depth != "INF"
            and self.environment.depth <= self.geometry.draft
        ):
            raise ValueError("水深必须大于吃水")
        if (
            isinstance(self.geometry, (Semisub, CurvedHull, SectionHull, ColumnSemi))
            and self.mechanics.model == "uniform_box_demo"
        ):
            raise ValueError(
                "参数化平台和曲面船体须提供 explicit 或 components 质量模型"
            )
        if self.object_type == "floating_structure" and self.environment.depth == "INF":
            raise ValueError("本项目浮式结构物工况要求显式给定有限水深")
        return self
