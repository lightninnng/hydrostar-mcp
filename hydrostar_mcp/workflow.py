"""Prepare -> inspect/confirm -> asynchronous solve -> validated results.

Every case has a new directory. Inputs and results are hash checked; a module
failure always stops the dependency chain. Reports survive MCP disconnection.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
from threading import Event, RLock
import time
import uuid

from . import __version__, core
from . import geometry as parametric
from .models import (
    Barge,
    CaseConfig,
    ImportedMesh,
    Semisub,
    CurvedHull,
    SectionHull,
    ColumnSemi,
)
from .reference_forms import source_comparison

PARAMETRIC_TYPES = (Semisub, CurvedHull, SectionHull, ColumnSemi)

REPO_ROOT = Path(__file__).resolve().parent.parent


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return (
            hashlib.file_digest(stream, "sha256").hexdigest()
            if hasattr(hashlib, "file_digest")
            else hashlib.sha256(stream.read()).hexdigest()
        )


def save_json(path, data):
    path = Path(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        for attempt in range(8):
            try:
                temp.replace(path)
                break
            except PermissionError:
                # Windows readers can briefly hold a handle across atomic replacement.
                if attempt == 7:
                    raise
                time.sleep(0.01 * 2 ** min(attempt, 4))
    finally:
        temp.unlink(missing_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def owner_is_alive(pid):
    """Check a persisted owner's PID without sending any Windows process signal."""
    if not isinstance(pid, int) or pid < 1:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
        if not handle:
            return (
                ctypes.get_last_error() != 87
            )  # Access denied is not evidence of death.
        try:
            return kernel.WaitForSingleObject(handle, 0) == 0x102
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class CaseService:
    def __init__(self, root=None, source_root=None):
        self.root = Path(
            root or os.environ.get("HS_WORKSPACE", REPO_ROOT / "runs")
        ).resolve()
        self.source_root = Path(
            source_root or os.environ.get("HS_SOURCE_ROOT", REPO_ROOT)
        ).resolve()
        installation = Path(core.hstar_root()).resolve()
        if self.root == installation or installation in self.root.parents:
            raise ValueError("工作目录不得位于 HydroStar 安装目录")
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hydrostar")
        self.lock = RLock()
        self.jobs = {}

    def source_path(self, name):
        path = (self.source_root / name).resolve()
        generated = (
            path.is_relative_to(self.root / "geometry") and path.name == "model.hst"
        )
        if generated and path.is_file():
            from .geometry_workflow import verify_bundle

            verify_bundle(path.parent / "geometry-report.json", path)
        if (
            not (path.is_relative_to(self.source_root) or generated)
            or path.suffix.lower() != ".hst"
            or not path.is_file()
        ):
            raise ValueError("导入文件必须是 HS_SOURCE_ROOT 内存在的 .hst 文件")
        return path

    def _geometry_bundle(self, geometry):
        from .geometry_workflow import verify_bundle

        manifest = (self.source_root / geometry.source_manifest).resolve()
        if not (
            manifest.is_relative_to(self.source_root)
            or manifest.is_relative_to(self.root / "geometry")
        ):
            raise ValueError("几何源清单位于允许的输入或几何生成目录之外")
        return manifest, verify_bundle(manifest, self.source_path(geometry.path))

    def case_path(self, case_id):
        if not isinstance(case_id, str) or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]{0,47}-[0-9a-f]{16}", case_id
        ):
            raise ValueError("无效 case_id")
        path = (self.root / case_id).resolve()
        if path.parent != self.root:
            raise ValueError("case_id 越出工作区")
        return path

    def environment(self):
        modules = {}
        for module in core.MODULES:
            try:
                modules[module] = core.hstar_bin(module)
            except FileNotFoundError:
                modules[module] = None
        return dict(
            version=__version__,
            hstar_root=core.hstar_root(),
            modules=modules,
            workspace=str(self.root),
            source_root=str(self.source_root),
            license_status="unknown_until_module_execution",
            capabilities=[
                "parameterized_half_barge",
                "original_parameterized_semisub_and_curved_hull",
                "component_mass_and_passive_linear_damping",
                "source_informed_section_hulls_and_column_semisub",
                "reference_scalar_comparison_and_engineering_acceptance",
                "single_body_hst_import",
                "unit_aware_cad_sections_dxf_mesh_and_calibrated_drawing_sources",
                "input_generation",
                "mesh_validation",
                "linear_6dof_rao",
                "structured_morison_and_stiffness",
            ],
            scope_notes=[
                "Single-body linear frequency-domain motion, driven through CLI modules",
                "Parameterized baselines, source-informed sectional hulls/column semisub, or supported HST import",
                "Zero static external load in executable cases; preload balance can be planned",
                "Mesh wavelength screening followed by response-sensitivity comparisons",
            ],
        )

    def plan(self, config):
        cfg = (
            config
            if isinstance(config, CaseConfig)
            else CaseConfig.model_validate(config)
        )
        geometry, env = cfg.geometry, cfg.environment
        if isinstance(geometry, Barge):
            budget = core.budget_barge(
                geometry.length,
                geometry.beam,
                geometry.draft,
                geometry.n_length,
                geometry.n_half_beam,
                geometry.n_draft,
                depth=env.depth,
                gravity=env.gravity_m_s2,
            )
            hyd = dict(
                volume=geometry.length * geometry.beam * geometry.draft,
                cb=(0, 0, -geometry.draft / 2),
                max_edge=budget["max_edge"],
                wetted_area=budget["s_wet"],
                n_panels=budget["half"],
                sym=1,
            )
        else:
            if isinstance(geometry, ImportedMesh):
                hyd = core.hydrostatics(self.source_path(geometry.path))
                self._mesh_environment(hyd, cfg)
            else:
                mesh = parametric.build(
                    geometry.model_dump(), env.rho_kg_m3, env.gravity_m_s2
                )
                hyd = mesh.hydrostatics()
                quality = parametric.mesh_quality(mesh)
                if not quality["passed"]:
                    raise ValueError(f"参数化网格拓扑/平面性检查失败: {quality}")
            budget = dict(
                full=hyd["n_panels"] * 2 ** hyd["sym"],
                half=hyd["n_panels"],
                max_edge=hyd["max_edge"],
                max_aspect_ratio=hyd["max_aspect_ratio"],
                omega_max=core.wave_limit(hyd["max_edge"], env.depth, env.gravity_m_s2),
            )
        # Geometry's submerged volume determines equilibrium, not the mass distribution.
        mechanics = self._mechanics(
            cfg,
            hyd,
            mesh.reference if isinstance(geometry, PARAMETRIC_TYPES) else None,
        )
        advice = core.assess_budget(
            budget, cfg.recommended_max_panels, cfg.waterplane_estimate_factor
        )
        warnings = self._warnings(
            cfg,
            budget["max_edge"],
            advice["n_effective_estimate"],
            budget.get("max_aspect_ratio", 1),
        )
        payload = dict(
            config=cfg.model_dump(mode="json"),
            budget=budget,
            mechanics=mechanics,
            panel_advice=advice,
            warnings=warnings,
            geometry_source_hash=file_hash(self.source_path(geometry.path))
            if isinstance(geometry, ImportedMesh)
            else None,
            geometry_source_manifest_sha256=file_hash(
                self._geometry_bundle(geometry)[0]
            )
            if isinstance(geometry, ImportedMesh) and geometry.source_manifest
            else None,
            heading_convention="Wave propagation angle from +x; with bow +x, 0 deg following / 180 deg head seas",
        )
        if isinstance(geometry, PARAMETRIC_TYPES):
            payload.update(
                geometry_reference=mesh.reference,
                geometry_provenance=mesh.provenance,
                independent_mesh_quality=quality,
            )
            payload["reference_model"] = source_comparison(cfg, hyd)
        return dict(
            status="needs_confirmation" if warnings else "planned",
            **payload,
            confirmation_token=digest(payload) if warnings else None,
            note="Planning is read-only; waterplane count is an estimate until hslec succeeds",
        )

    def _warnings(self, cfg, edge, count, aspect):
        warnings = []
        if count > cfg.recommended_max_panels:
            warnings.append(
                dict(
                    code="PANEL_RECOMMENDATION_EXCEEDED",
                    count=count,
                    recommended=cfg.recommended_max_panels,
                    action="Review cost, revise discretization or explicitly confirm; recommendation is not a hard limit",
                )
            )
        omega = core.wave_limit(
            edge, cfg.environment.depth, cfg.environment.gravity_m_s2
        )
        if cfg.environment.frequency.max > omega * (1 + 1e-6):
            warnings.append(
                dict(
                    code="FREQUENCY_ABOVE_MESH_SCREENING_LIMIT",
                    requested=cfg.environment.frequency.max,
                    screening_omega_max=omega,
                    max_edge_m=edge,
                    action="Refine the mesh or revise the frequency interval; confirmation records use outside this screening criterion",
                )
            )
        if aspect > 5:
            warnings.append(
                dict(
                    code="HIGH_PANEL_ASPECT_RATIO",
                    max_aspect_ratio=aspect,
                    action="Review local mesh shape; threshold 5 is advisory, not a HydroStar acceptance rule",
                )
            )
        return warnings

    def _mesh_environment(self, hyd, cfg):
        for key, expected in (
            ("rho", cfg.environment.rho_kg_m3),
            ("gravity", cfg.environment.gravity_m_s2),
        ):
            if not math.isclose(hyd[key], expected, rel_tol=1e-8):
                raise ValueError(f"HST {key}={hyd[key]} 与工况 {expected} 不一致")
        if hyd["free_surface"] != 0:
            raise ValueError("当前输入生成要求 HST 自由面 z=0；请先平移到统一坐标")
        if cfg.environment.depth != "INF":
            nodes, _, _ = core.read_hst(self.source_path(cfg.geometry.path))
            if -min(v[2] for v in nodes.values()) >= cfg.environment.depth:
                raise ValueError("网格接触或穿过海底")

    def _mechanics(self, cfg, hyd, reference=None):
        model, env = cfg.mechanics, cfg.environment
        morison = core.morison_displacement([m.model_dump() for m in model.morison])
        total_volume = hyd["volume"] + morison["volume_m3"]
        if model.model == "uniform_box_demo":
            g = cfg.geometry
            mass = env.rho_kg_m3 * hyd["volume"]
            cog = [0.0, 0.0, -g.draft / 2]
            radii = [
                math.sqrt((g.beam**2 + g.draft**2) / 12),
                math.sqrt((g.length**2 + g.draft**2) / 12),
                math.sqrt((g.length**2 + g.beam**2) / 12),
                0,
                0,
                0,
            ]
            source = (
                "assumed homogeneous submerged rectangular solid; demonstration only"
            )
        elif model.model == "components":
            component_model = parametric.combine_box_masses(
                model.mass_kg or env.rho_kg_m3 * total_volume,
                [c.model_dump() for c in model.components],
            )
            mass, cog, radii = (
                component_model[k] for k in ("mass_kg", "cog_m", "gyradius_m")
            )
            core.validate_gyradius(radii)
            source = "specified_component_geometry_and_inertia: " + model.source_note
        else:
            mass, cog, radii = model.mass_kg, model.cog_m, model.gyradius_m
            source = "specified_input: " + model.source_note
        residual = (
            mass * env.gravity_m_s2
            - env.rho_kg_m3 * total_volume * env.gravity_m_s2
            - model.vertical_external_force_n
        )
        relative = abs(residual) / (env.rho_kg_m3 * total_volume * env.gravity_m_s2)
        if relative > model.equilibrium_relative_tolerance:
            raise ValueError(
                f"静力竖向不平衡 {relative:.3%} 超过 {model.equilibrium_relative_tolerance:.3%}；核对质量、排水量及系泊预张力"
            )
        total_cb = [
            (
                hyd["volume"] * hyd["cb"][k]
                + morison["volume_m3"] * (morison["cb_m"][k] if morison["cb_m"] else 0)
            )
            / total_volume
            for k in range(3)
        ]
        cog_xy_offset = math.dist(cog[:2], total_cb[:2])
        stability = None
        if reference is not None:
            gm = [
                hyd["cb"][2] + i / hyd["volume"] - cog[2]
                for i in reference.get(
                    "mesh_waterplane_inertia_m4", reference["waterplane_inertia_m4"]
                )
            ]
            if min(gm) <= 0:
                raise ValueError(f"参数化课程模型初稳性须为正；横/纵向 GM={gm}")
            stability = dict(
                gm_roll_pitch_m=gm,
                basis="analytic waterplane inertia and integrated mesh buoyancy",
                passed=True,
            )
        if (
            model.vertical_external_force_n == 0
            and cog_xy_offset > model.cog_xy_tolerance_m
        ):
            raise ValueError(
                f"当前平衡姿态中重心与组合浮心的水平偏距 {cog_xy_offset:.4f} m 超过 {model.cog_xy_tolerance_m} m；请调整质量参数或提供平衡后的网格姿态"
            )
        return dict(
            mass_kg=mass,
            cog_m=cog,
            gyradius_m=radii,
            mass_distribution_source=source,
            component_mass_model=component_model
            if model.model == "components"
            else None,
            initial_stability=stability,
            roll_damping_pct=model.roll_damping_pct
            if model.roll_damping_pct is not None
            else 6.0,
            damping_source="specified_input"
            if model.roll_damping_pct is not None
            else "6% empirical demonstration assumption",
            displacement_source="wetted mesh/analytic geometry plus physical Morison cylinders",
            mesh_displacement_m3=hyd["volume"],
            morison_displacement=morison,
            total_displacement_m3=total_volume,
            total_cb_m=total_cb,
            equilibrium_relative_error=relative,
            static_vertical_external_force_n=model.vertical_external_force_n,
            static_moment_balance=dict(
                cog_xy_offset_m=cog_xy_offset,
                tolerance_m=model.cog_xy_tolerance_m,
                checked=model.vertical_external_force_n == 0,
                basis="vertical gravity/buoyancy at the supplied equilibrium attitude",
            ),
        )

    def _inputs(self, directory, cfg, mechanics):
        project, env, model = cfg.project, cfg.environment, cfg.mechanics
        freq, heading = env.frequency, env.headings
        core.write_rdf(
            directory / (project + ".rdf"),
            wmin=freq.min,
            wmax=freq.max,
            wstp=freq.step,
            hmin=heading.min,
            hmax=heading.max,
            hstp=heading.step,
            depth=env.depth,
            speeds=((1, env.speed_m_s),),
        )
        core.write_mcn(
            directory / (project + ".mcn"),
            mass=mechanics["mass_kg"],
            cog=mechanics["cog_m"],
            gyradius=mechanics["gyradius_m"],
            roll_damp_pct=mechanics["roll_damping_pct"],
            rho=env.rho_kg_m3,
            gravity=env.gravity_m_s2,
            stiffness_matrix=model.stiffness_matrix,
            linear_damping_matrix=model.linear_damping_matrix,
            waterplane_hydrostatics=model.hydrostatics_method == "waterplane",
            morison=[m.model_dump() for m in model.morison],
            wave_amplitude=model.wave_amplitude_m,
            spectrum=model.spectrum.model_dump() if model.spectrum else None,
        )
        core.write_rao(
            directory / (project + ".rao"), dofs=cfg.output_dofs, ref=cfg.output_point_m
        )

    def _record(self, directory, report):
        report["updated_at"] = now()
        save_json(directory / "report.json", report)

    def _fail(self, directory, report, code, detail):
        for gate, status in report.get("quality_gates", {}).items():
            if status == "pending":
                report["quality_gates"][gate] = "not_run"
        report.update(
            status="cancelled" if code == "CANCELLED" else "failed",
            error=dict(code=code, detail=detail),
        )
        self._record(directory, report)
        return report

    def _step(self, directory, report, module, args, cfg, cancel=None):
        report["current_module"] = module
        self._record(directory, report)
        result = core.run(
            module,
            args,
            directory,
            nproc=cfg.nproc if module == "hsrdf" else 1,
            timeout=min(cfg.module_timeout_s, 60)
            if module in ("hsmsh", "hslec", "hschk")
            else cfg.module_timeout_s,
            log_path=directory / "logs" / (module + ".log"),
            cancel=cancel,
        )
        if module == "hsmcn":
            report["solver_mechanics"] = core.parse_hsmcn(result.log)
            gm = report["solver_mechanics"]["gm_roll_pitch_m"]
            if result.ok and gm and min(gm) <= 0:
                result.error_code = "INITIAL_STABILITY_FAILED"
                result.log += "\n课程与简化分析门禁：求解器横/纵向 GM 应为正。"
            if not result.ok:
                report["solver_mechanics"]["balanced"] = (
                    False if result.error_code == "SOLVER_EQUILIBRIUM_FAILED" else None
                )
        step = dict(
            module=module,
            ok=result.ok,
            rc=result.rc,
            seconds=round(result.seconds, 3),
            command=result.cmd,
            log=result.log_path,
            error_code=result.error_code,
        )
        report["steps"].append(step)
        self._record(directory, report)
        if not result.ok:
            report.setdefault("quality_gates", {})["module_execution"] = "failed"
            if result.error_code in (
                "SOLVER_EQUILIBRIUM_FAILED",
                "INITIAL_STABILITY_FAILED",
            ):
                report["quality_gates"]["static_equilibrium"] = "failed"
            self._fail(
                directory,
                report,
                result.error_code or "PROCESS_FAILED",
                result.log[-3000:],
            )
        return result

    def generate(self, config, confirmation_token=None):
        """Export reviewable inputs without executing any HydroStar binary."""
        cfg = (
            config
            if isinstance(config, CaseConfig)
            else CaseConfig.model_validate(config)
        )
        plan = self.plan(cfg)
        if (
            cfg.mechanics.vertical_external_force_n != 0
            or cfg.mechanics.restraint == "tension_leg"
        ):
            raise ValueError(
                "静态预载目前用于规划平衡核对；生成流程需先接入并验证 HydroStar 预载输入卡片。当前可生成零静态外载的自由/系泊模型。"
            )
        if plan["warnings"] and confirmation_token != plan["confirmation_token"]:
            return dict(
                status="needs_confirmation",
                stage="before_generation",
                plan=plan,
                confirmation_token=plan["confirmation_token"],
                detail="请审阅具体输入和警告；修改参数重试，或在用户确认后传回此 token",
            )
        case_id = cfg.project + "-" + uuid.uuid4().hex[:16]
        directory = self.case_path(case_id)
        directory.mkdir(parents=True, exist_ok=False)
        report = dict(
            case_id=case_id,
            project=cfg.project,
            directory=str(directory),
            status="generating",
            created_at=now(),
            version=__version__,
            steps=[],
            config=cfg.model_dump(mode="json"),
            plan=plan,
            quality_gates=dict(
                semantic_input="passed",
                static_equilibrium="passed",
                mesh_geometry="pending",
                mesh_topology="pending",
                module_execution="pending",
                rao_integrity="pending",
            ),
        )
        save_json(directory / "config.json", report["config"])
        self._record(directory, report)
        try:
            self._inputs(directory, cfg, plan["mechanics"])
            if isinstance(cfg.geometry, Barge):
                geom = cfg.geometry
                core.write_mri_barge(
                    directory / (cfg.project + ".mri"),
                    geom.length,
                    geom.beam,
                    geom.draft,
                    geom.n_length,
                    geom.n_half_beam,
                    geom.n_draft,
                    project=cfg.project,
                )
            elif isinstance(cfg.geometry, ImportedMesh):
                target = directory / (cfg.project + ".hst")
                shutil.copyfile(self.source_path(cfg.geometry.path), target)
                if file_hash(target) != plan["geometry_source_hash"]:
                    raise ValueError("导入网格在规划后发生变化，请重新规划")
                if cfg.geometry.source_manifest:
                    manifest, bundle = self._geometry_bundle(cfg.geometry)
                    if file_hash(manifest) != plan["geometry_source_manifest_sha256"]:
                        raise ValueError("几何源清单在规划后发生变化")
                    shutil.copyfile(
                        manifest, directory / "geometry-source--manifest.json"
                    )
                    for name, expected in bundle["files"].items():
                        if Path(name).name != name:
                            raise ValueError("几何源数据包采用平铺文件清单")
                        archived = directory / ("geometry-source--" + name)
                        shutil.copyfile(manifest.parent / name, archived)
                        if file_hash(archived) != expected:
                            raise ValueError("几何源文件在归档期间发生变化")
                    report["geometry_source_validation"] = {
                        k: bundle[k]
                        for k in (
                            "schema",
                            "quality",
                            "fidelity",
                            "geometry_gates",
                            "reference",
                        )
                    }
            else:
                mesh = parametric.build(
                    cfg.geometry.model_dump(),
                    cfg.environment.rho_kg_m3,
                    cfg.environment.gravity_m_s2,
                )
                mesh.write(directory / (cfg.project + ".hst"), cfg.project)
                source_archive = directory / "geometry-generator.py"
                shutil.copyfile(Path(parametric.__file__), source_archive)
                if file_hash(source_archive) != mesh.provenance["generator_sha256"]:
                    raise ValueError("生成器源码在生成过程中发生变化；请重新生成")
                for name, expected_hash in mesh.provenance.get(
                    "additional_generator_sources", {}
                ).items():
                    if name != "forms_geometry.py":
                        raise ValueError("未知生成器源码快照")
                    archived = directory / name
                    shutil.copyfile(Path(parametric.__file__).with_name(name), archived)
                    if file_hash(archived) != expected_hash:
                        raise ValueError("附加生成器源码在生成过程中变化")
                report["geometry_reference"] = mesh.reference
                report["geometry_provenance"] = mesh.provenance
                report["reference_model"] = plan.get("reference_model")
                report["independent_mesh_quality"] = parametric.mesh_quality(mesh)
                save_json(
                    directory / "geometry.json",
                    dict(
                        parameters=cfg.geometry.model_dump(),
                        reference=mesh.reference,
                        provenance=mesh.provenance,
                        quality=report["independent_mesh_quality"],
                    ),
                )
            report["input_hashes"] = {
                p.name: file_hash(p)
                for p in [
                    directory / "config.json",
                    *directory.glob("geometry.json"),
                    *directory.glob("geometry-generator.py"),
                    *directory.glob("forms_geometry.py"),
                    *directory.glob("geometry-source--*"),
                    *sorted(directory.glob(cfg.project + ".*")),
                ]
            }
            report["status"] = "generated"
            report["validation"] = (
                "semantic checks only; hslec/hschk and solver have not run"
            )
            self._record(directory, report)
            return report
        except Exception as exc:
            return self._fail(directory, report, "INPUT_GENERATION_FAILED", str(exc))

    def prepare(self, config, confirmation_token=None):
        cfg = (
            config
            if isinstance(config, CaseConfig)
            else CaseConfig.model_validate(config)
        )
        report = self.generate(cfg, confirmation_token)
        if report["status"] != "generated":
            return report
        directory = self.case_path(report["case_id"])
        report["status"] = "preparing"
        report.pop("input_hashes", None)
        plan = report["plan"]
        self._record(directory, report)
        try:
            target = directory / (cfg.project + ".hst")
            if isinstance(cfg.geometry, Barge):
                r = self._step(directory, report, "hsmsh", [cfg.project + ".mri"], cfg)
                if not r.ok:
                    return report
                generated = directory / "PRO.hst"
                if not generated.is_file() or not generated.stat().st_size:
                    return self._fail(
                        directory,
                        report,
                        "MISSING_ARTIFACT",
                        "hsmsh 未生成新的 PRO.hst",
                    )
                generated.rename(target)
                # hsmsh otherwise writes default 1025/9.81 implicitly. Make constants explicit.
                mesh_text = target.read_text(encoding="utf-8")
                mesh_text = re.sub(r"(?im)^(?:RHO|GRAVITY)\s+[^\r\n]*", "", mesh_text)
                mesh_text = re.sub(
                    r"(?im)^ENDFILE\s*$",
                    f"RHO {cfg.environment.rho_kg_m3:.12g}\nGRAVITY {cfg.environment.gravity_m_s2:.12g}\nENDFILE",
                    mesh_text,
                )
                target.write_text(mesh_text, encoding="utf-8", newline="\n")
            hyd = core.hydrostatics(target)
            report["hydrostatics"] = hyd
            if isinstance(cfg.geometry, Barge):
                geom = cfg.geometry
                expected = geom.length * geom.beam * geom.draft
                expected_area = plan["budget"]["s_wet"]
                discrepancies = dict(
                    volume_relative=abs(hyd["volume"] - expected) / expected,
                    wetted_area_relative=abs(hyd["wetted_area"] - expected_area)
                    / expected_area,
                    cb_distance_m=math.dist(hyd["cb"], [0, 0, -geom.draft / 2]),
                )
                report["fidelity"] = discrepancies
                if max(discrepancies.values()) > 0.001:
                    report["quality_gates"]["mesh_geometry"] = "failed"
                    return self._fail(
                        directory,
                        report,
                        "GEOMETRY_FIDELITY_FAILED",
                        str(discrepancies),
                    )
                if hyd["n_panels"] != plan["budget"]["half"] or hyd["sym"] != 1:
                    return self._fail(
                        directory,
                        report,
                        "MESH_COUNT_MISMATCH",
                        "实际面板数/对称性与参数化预算不一致",
                    )
            elif isinstance(cfg.geometry, PARAMETRIC_TYPES):
                ref = report["geometry_reference"]
                tol_cb = (
                    1e-6
                    if isinstance(cfg.geometry, Semisub)
                    else 0.005 * cfg.geometry.draft
                )
                tolerances = ref.get("mesh_tolerances", {})
                tol_cb = tolerances.get("cb_distance_m", tol_cb)
                tol_volume = tolerances.get("volume_relative", 1e-8)
                discrepancy = dict(
                    volume_relative=abs(hyd["volume"] / ref["volume_m3"] - 1),
                    cb_distance_m=math.dist(hyd["cb"], ref["cb_m"]),
                    cb_tolerance_m=tol_cb,
                    volume_tolerance_relative=tol_volume,
                )
                if "wetted_area_m2" in ref:
                    discrepancy["wetted_area_relative"] = abs(
                        hyd["wetted_area"] / ref["wetted_area_m2"] - 1
                    )
                report["fidelity"] = discrepancy
                if (
                    discrepancy["volume_relative"] > tol_volume
                    or discrepancy["cb_distance_m"] > tol_cb
                    or discrepancy.get("wetted_area_relative", 0) > 1e-8
                ):
                    report["quality_gates"]["mesh_geometry"] = "failed"
                    return self._fail(
                        directory, report, "GEOMETRY_FIDELITY_FAILED", str(discrepancy)
                    )
                if not report["independent_mesh_quality"]["passed"]:
                    report["quality_gates"]["mesh_topology"] = "failed"
                    return self._fail(
                        directory, report, "MESH_REJECTED", "独立边关联/平面性检查失败"
                    )
            elif cfg.geometry.expected_volume_m3 is not None:
                delta = (
                    abs(hyd["volume"] - cfg.geometry.expected_volume_m3)
                    / cfg.geometry.expected_volume_m3
                )
                if delta > cfg.geometry.volume_relative_tolerance:
                    return self._fail(
                        directory,
                        report,
                        "GEOMETRY_FIDELITY_FAILED",
                        f"排水量偏差 {delta:.3%}",
                    )
            mechanics = self._mechanics(cfg, hyd, report.get("geometry_reference"))
            report["mechanics"] = mechanics
            report["quality_gates"]["mesh_geometry"] = "passed"
            self._inputs(directory, cfg, mechanics)
            r = self._step(directory, report, "hslec", [target.name, cfg.project], cfg)
            if not r.ok:
                return report
            measured = core.parse_hslec(r.log)
            report["hslec"] = measured
            has_exterior = bool(
                re.search(
                    r"(?mi)^\s*(?:NFREESURFACE|AUTOMATIC_SURF)\b",
                    target.read_text(encoding="utf-8-sig"),
                )
            )
            if (has_exterior and not measured.get("exterior_free_surface_panels")) or (
                "exterior_free_surface_panels" in measured
                and measured["exterior_free_surface_panels"] is None
            ):
                return self._fail(
                    directory,
                    report,
                    "INCOMPLETE_MESH_REPORT",
                    "外部自由面须有完整的 hslec 面元统计，并计入全体总面元预算",
                )
            if any(
                measured[k] is None
                for k in ("bodies", "symmetry", "hull_panels", "waterplane_panels")
            ):
                return self._fail(
                    directory,
                    report,
                    "INCOMPLETE_MESH_REPORT",
                    "hslec 缺少预算所需统计；不能按零处理",
                )
            if (
                measured["bodies"] != 1
                or measured["symmetry"] != hyd["sym"]
                or measured["hull_panels"] != hyd["n_panels"]
            ):
                return self._fail(
                    directory,
                    report,
                    "MESH_COUNT_MISMATCH",
                    "hslec 与独立解析的网格统计不一致",
                )
            r = self._step(directory, report, "hschk", ["-", cfg.project], cfg)
            if not r.ok:
                return report
            report["hschk"] = core.parse_hschk(r.log)
            if not report["hschk"]["pass"]:
                report["quality_gates"]["mesh_topology"] = "failed"
                return self._fail(
                    directory, report, "MESH_REJECTED", "hschk 七项计数须完整且均为 0"
                )
            report["quality_gates"]["mesh_topology"] = "passed"
            report["validation"] = (
                "semantic checks, independent geometry integration and hslec/hschk passed; solver not yet run"
            )
            effective = (
                measured["hull_panels"]
                + measured["waterplane_panels"]
                + measured.get("exterior_free_surface_panels", 0)
            ) * 2 ** hyd["sym"]
            warnings = self._warnings(
                cfg, hyd["max_edge"], effective, hyd["max_aspect_ratio"]
            )
            report["mesh_screening"] = dict(
                full_equivalent_panels=effective,
                warnings=warnings,
                omega_max=core.wave_limit(
                    hyd["max_edge"], cfg.environment.depth, cfg.environment.gravity_m_s2
                ),
                criterion="lambda >= 8*maximum edge; advisory screening, not an accuracy guarantee",
            )
            inputs = [
                directory / "config.json",
                *directory.glob("geometry.json"),
                *directory.glob("geometry-generator.py"),
                *directory.glob("forms_geometry.py"),
                *directory.glob("geometry-source--*"),
                *sorted(directory.glob(cfg.project + ".*")),
            ]
            report["input_hashes"] = {p.name: file_hash(p) for p in inputs}
            report["confirmation_token"] = (
                digest(dict(inputs=report["input_hashes"], warnings=warnings))
                if warnings
                else None
            )
            report["status"] = "needs_confirmation" if warnings else "prepared"
            report["stage"] = "before_solver"
            report["current_module"] = None
            self._record(directory, report)
            return report
        except Exception as exc:
            return self._fail(directory, report, "PREPARATION_FAILED", str(exc))

    def status(self, case_id):
        path = self.case_path(case_id)
        report = json.loads((path / "report.json").read_text(encoding="utf-8"))
        if report["status"] == "completed":
            # Recheck legacy reports against the current mechanical gate without
            # rewriting their original execution history.
            log_path = path / "logs/hsmcn.log"
            if not log_path.is_file():
                report["status"] = "failed"
                report["error"] = dict(
                    code="MISSING_LOG", detail="请保留 hsmcn 日志以完成力学验收"
                )
            else:
                log = log_path.read_text(encoding="utf-8", errors="replace")
                report["solver_mechanics"] = core.parse_hsmcn(log)
                issue = core.log_error(log)
                if issue:
                    report["original_execution_status"] = "completed"
                    report["status"] = "failed"
                    report["error"] = dict(
                        code=issue,
                        detail="当前质量复核识别到求解器力学告警；原执行记录保留",
                    )
                    if issue == "SOLVER_EQUILIBRIUM_FAILED":
                        report.setdefault("quality_gates", {})["static_equilibrium"] = (
                            "failed"
                        )
        if (
            report["status"] in ("running", "queued")
            and case_id not in self.jobs
            and not owner_is_alive(report.get("owner_pid"))
        ):
            # Don't resume a solve after a server restart or pretend the old job completed.
            report["status"] = "interrupted"
            report["error"] = dict(
                code="SERVER_RESTARTED",
                detail="重新 prepare 生成独立算例；原日志和输入保留",
            )
        return report

    def _verify_inputs(self, directory, report):
        for name, expected in report["input_hashes"].items():
            path = (directory / name).resolve()
            if (
                path.parent != directory
                or not path.is_file()
                or file_hash(path) != expected
            ):
                raise ValueError(f"输入已变化或丢失: {name}；请重新 prepare")

    def start(self, case_id, confirmation_token=None):
        with self.lock:
            report = self.status(case_id)
            if case_id in self.jobs or report["status"] not in (
                "prepared",
                "needs_confirmation",
            ):
                raise ValueError(
                    f"当前状态 {report['status']} 不允许启动；每个算例只求解一次"
                )
            token = report.get("confirmation_token")
            if token and confirmation_token != token:
                return dict(
                    status="needs_confirmation",
                    case_id=case_id,
                    confirmation_token=token,
                    warnings=report["mesh_screening"]["warnings"],
                    stage="before_solver",
                )
            directory = self.case_path(case_id)
            self._verify_inputs(directory, report)
            # Persistent per-case lock also prevents a second MCP process from starting it.
            lock_path = directory / ".solve.lock"
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            report["status"] = "queued"
            report["owner_pid"] = os.getpid()
            report["confirmed_token"] = confirmation_token if token else None
            self._record(directory, report)
            cancel = Event()
            self.jobs[case_id] = (None, cancel)
            try:
                future = self.pool.submit(self._solve, directory, report, cancel)
                self.jobs[case_id] = (future, cancel)
            except Exception:
                self.jobs.pop(case_id, None)
                lock_path.unlink(missing_ok=True)
                raise
            return dict(case_id=case_id, status="queued", directory=str(directory))

    def _solve(self, directory, report, cancel):
        try:
            cfg = CaseConfig.model_validate(report["config"])
            self._verify_inputs(directory, report)
            report["status"] = "running"
            self._record(directory, report)
            for module, extension in (
                ("hsrdf", "rdf"),
                ("hsmcn", "mcn"),
                ("hsrao", "rao"),
            ):
                if cancel.is_set():
                    return self._fail(directory, report, "CANCELLED", "用户取消")
                result = self._step(
                    directory,
                    report,
                    module,
                    [cfg.project + "." + extension, cfg.project],
                    cfg,
                    cancel,
                )
                if not result.ok:
                    return report
            report["quality_gates"]["module_execution"] = "passed"
            # All requested outputs must exist, have complete arrays and match this case.
            expected_omega = core.grid_values(
                cfg.environment.frequency.min,
                cfg.environment.frequency.max,
                cfg.environment.frequency.step,
            )
            expected_heads = core.grid_values(
                cfg.environment.headings.min,
                cfg.environment.headings.max,
                cfg.environment.headings.step,
            )
            names = list(cfg.output_dofs) + (
                ["heave_at_point"] if cfg.output_point_m is not None else []
            )
            report["results"], report["output_hashes"] = {}, {}
            for name in names:
                path = directory / "rao" / (name + ".rao")
                result = core.read_rao(path)
                for actual, expected in (
                    (result["omega"], expected_omega),
                    (result["headings"], expected_heads),
                ):
                    if len(actual) != len(expected) or any(
                        abs(a - b) > 5.1e-5 for a, b in zip(actual, expected)
                    ):
                        raise ValueError(f"{name}: 输出频率或浪向与本次输入不一致")
                peak = max(
                    (
                        (value, i, j)
                        for i, row in enumerate(result["amplitude"])
                        for j, value in enumerate(row)
                    )
                )
                report["results"][name] = dict(
                    n_frequency=len(result["omega"]),
                    n_heading=len(result["headings"]),
                    unit=result["unit"],
                    peak_amplitude=peak[0],
                    peak_omega=result["omega"][peak[1]],
                    peak_heading=result["headings"][peak[2]],
                )
                report["output_hashes"][
                    str(path.relative_to(directory)).replace("\\", "/")
                ] = file_hash(path)
            report["status"] = "completed"
            report["quality_gates"]["rao_integrity"] = "passed"
            report["current_module"] = None
            report["completed_at"] = now()
            self._record(directory, report)
            return report
        except Exception as exc:
            report.setdefault("quality_gates", {})["rao_integrity"] = "failed"
            return self._fail(directory, report, "RESULT_VALIDATION_FAILED", str(exc))
        finally:
            (directory / ".solve.lock").unlink(missing_ok=True)

    def cancel(self, case_id):
        with self.lock:
            if case_id not in self.jobs:
                raise ValueError("当前服务没有这个活动任务")
            future, event = self.jobs[case_id]
            if future is not None and future.done():
                return self.status(case_id)
            event.set()
            return dict(case_id=case_id, status="cancellation_requested")

    def result(self, case_id, dof="heave"):
        if dof not in (*core.DOFS, "heave_at_point"):
            raise ValueError("无效自由度")
        report = self.status(case_id)
        if report["status"] != "completed" or dof not in report.get("results", {}):
            raise ValueError("只有本次完整求解并验证通过的输出才能读取")
        relative = "rao/" + dof + ".rao"
        path = self.case_path(case_id) / relative
        if file_hash(path) != report["output_hashes"].get(relative):
            raise ValueError("结果已改变，拒绝当作本次可信输出")
        return dict(case_id=case_id, dof=dof, **core.read_rao(path))

    def close(self):
        for future, cancel in self.jobs.values():
            cancel.set()
        self.pool.shutdown(wait=True, cancel_futures=False)
