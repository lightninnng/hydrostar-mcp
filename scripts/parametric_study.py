"""Original parameterized models, documented mass assumptions, native mesh studies."""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.geometry import build, combine_box_masses  # noqa: E402
from hydrostar_mcp.models import Semisub, CurvedHull, CaseConfig  # noqa: E402
from hydrostar_mcp.workflow import CaseService, save_json, digest  # noqa: E402
from scripts.mesh_study import compare_rao  # noqa: E402


def diagonal(values):
    return [
        [value if i == j else 0.0 for j in range(6)] for i, value in enumerate(values)
    ]


def example(kind):
    """All dimensions/fractions are independently selected teaching assumptions."""
    geometry = (Semisub() if kind == "semisub" else CurvedHull()).model_dump()
    mesh = build(geometry)
    reference = mesh.reference
    mass = 1025.0 * reference["volume_m3"]
    components = []

    def component(name, fraction, size, center):
        components.append(
            dict(name=name, mass_fraction=fraction, size_m=size, center_m=center)
        )

    if kind == "semisub":
        for y in (-12.0, 12.0):
            component(f"pontoon_{y:+g}", 0.30, [36.0, 6.0, 4.0], [0.0, y, -12.0])
            for x in (-12.0, 12.0):
                component(
                    f"column_{x:+g}_{y:+g}", 0.0625, [4.0, 4.0, 16.0], [x, y, -2.0]
                )
        for x in (-12.0, 12.0):
            component(f"crossbeam_{x:+g}", 0.05, [4.0, 18.0, 2.0], [x, 0.0, -13.0])
        component("effective_deck", 0.05, [32.0, 32.0, 2.0], [0.0, 0.0, 7.0])
        stiffness = [50000.0, 50000.0, 0.0, 0.0, 0.0, 8000000.0]
        note = "本项目自行选定教学假设：浮筒/压载60%，四立柱25%，横梁10%，有效甲板5%；各分量按均匀有效长方体和平行轴定理求惯性。总质量按解析排水量平衡，K11=K22=50kN/m，K66=8MN·m/rad，无静态预载。"
    else:
        L, B, T = geometry["length"], geometry["beam"], geometry["draft"]
        component(
            "hull_and_ballast",
            0.60,
            [0.8 * L, 0.8 * B, 0.45 * T],
            [0.0, 0.0, -0.65 * T],
        )
        component("deck_and_equipment", 0.25, [0.6 * L, 0.6 * B, 2.0], [0.0, 0.0, 1.0])
        for x in (-0.2 * L, 0.2 * L):
            component(
                f"machinery_{x:+g}",
                0.075,
                [0.18 * L, 0.5 * B, 0.5 * T],
                [x, 0.0, -0.4 * T],
            )
        stiffness = [0.0] * 6
        note = "本项目自行选定教学假设：船壳/压载60%，甲板设备25%，艏艉机器各7.5%；均匀有效分量和平行轴定理求惯性，总质量按解析排水量固定；曲面为下半椭球解析船型，零航速、自由浮态。"
    mass_model = combine_box_masses(mass, components)
    gm = [
        reference["cb_m"][2] + i / reference["volume_m3"] - mass_model["cog_m"][2]
        for i in reference["waterplane_inertia_m4"]
    ]
    c = [*stiffness]
    c[2] += 1025 * 9.81 * reference["waterplane_area_m2"]
    c[3] += mass * 9.81 * gm[0]
    c[4] += mass * 9.81 * gm[1]
    generalized_mass = [mass] * 3 + [
        mass_model["inertia_kg_m2"][i][i] for i in range(3)
    ]
    damping = [0.10 * math.sqrt(m * k) for m, k in zip(generalized_mass, c)]
    cfg = dict(
        project="own_" + kind,
        object_type="floating_structure" if kind == "semisub" else "ship",
        geometry=geometry,
        environment=dict(
            depth=80.0,
            frequency=dict(min=0.05, max=1.4 if kind == "semisub" else 1.8, step=0.025),
        ),
        mechanics=dict(
            model="components",
            mass_kg=mass,
            components=components,
            roll_damping_pct=0.0,
            restraint="moored" if kind == "semisub" else "free",
            stiffness_matrix=diagonal(stiffness),
            linear_damping_matrix=diagonal(damping),
            source_note=note
            + " 附加线性阻尼取各自由度干质量、未耦合静刚度参考临界值的5%，矩阵固定用于全部网格；辐射阻尼另由求解器计算。",
        ),
        waterplane_estimate_factor=1.1 if kind == "semisub" else 1.2,
    )
    return CaseConfig.model_validate(cfg), dict(
        reference=reference,
        mass_model=mass_model,
        reference_gm_m=gm,
        damping_reference=dict(
            zeta=0.05,
            mass_diagonal=generalized_mass,
            stiffness_diagonal=c,
            damping_diagonal=damping,
            basis="2*zeta*sqrt(M_dry*C_uncoupled); radiation added separately; course assumption",
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--kind", choices=["semisub", "curved_hull", "all"], default="all"
    )
    args = parser.parse_args()
    service = CaseService(root=ROOT / "output/validation/parametric_runs")
    dest = ROOT / "output/validation/parametric_study.json"
    result = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {}
    try:
        for kind in ["semisub", "curved_hull"] if args.kind == "all" else [args.kind]:
            base, assumptions = example(kind)
            save_json(
                ROOT / "examples" / (kind + ".json"), base.model_dump(mode="json")
            )
            state = result.setdefault(kind, {})
            state.update(assumptions=assumptions, observation_target_pct=5.0)
            state.setdefault("cases", {})
            configs = {}
            for index, label in enumerate(("coarse", "medium", "fine")):
                data = copy.deepcopy(base.model_dump(mode="json"))
                data["project"] = "own_" + kind + "_" + label
                if kind == "semisub":
                    data["geometry"]["target_panel_m"] = (2.0, 1.5, 1.0)[index]
                else:
                    data["geometry"].update(
                        zip(
                            ("n_length", "n_section"),
                            ((48, 8), (56, 12), (64, 16))[index],
                        )
                    )
                configs[label] = CaseConfig.model_validate(data)
            state["plans"] = {k: service.plan(v) for k, v in configs.items()}
            save_json(dest, result)
            if not args.run:
                print(
                    json.dumps(
                        {
                            kind: {
                                k: dict(
                                    status=p["status"],
                                    budget=p["budget"],
                                    warnings=p["warnings"],
                                )
                                for k, p in state["plans"].items()
                            }
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                continue
            arrays = {}
            for label, cfg in configs.items():
                prior = state["cases"].get(label)
                report = (
                    service.status(prior["case_id"])
                    if prior
                    and prior.get("config_digest")
                    == digest(cfg.model_dump(mode="json"))
                    else None
                )
                if report is None or report["status"] != "completed":
                    print(f"{kind}/{label}: preparing", flush=True)
                    report = service.prepare(cfg)
                    if report["status"] == "prepared":
                        print(
                            f"{kind}/{label}: native topology passed; solving",
                            flush=True,
                        )
                        service.start(report["case_id"])
                        service.jobs[report["case_id"]][0].result(timeout=1800)
                        report = service.status(report["case_id"])
                if report["status"] != "completed":
                    state.update(status=report["status"], review=report)
                    save_json(dest, result)
                    print(
                        json.dumps(
                            dict(
                                kind=kind,
                                label=label,
                                status=report["status"],
                                error=report.get("error"),
                                warnings=report.get("plan", {}).get("warnings"),
                                case_id=report.get("case_id"),
                            ),
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )
                    return 1
                state["cases"][label] = dict(
                    case_id=report["case_id"],
                    directory=report["directory"],
                    config_digest=digest(cfg.model_dump(mode="json")),
                    quality_gates=report["quality_gates"],
                    hslec=report["hslec"],
                    hydrostatics=report["hydrostatics"],
                    solver_mechanics=report.get("solver_mechanics"),
                )
                arrays[label] = {
                    d: service.result(report["case_id"], d) for d in cfg.output_dofs
                }
                save_json(dest, result)
                print(
                    f"{kind}/{label}: completed, {report['hslec']['hull_panels']} half-hull + {report['hslec']['waterplane_panels']} waterplane",
                    flush=True,
                )
            state["comparisons"] = {
                a + "_to_" + b: {
                    d: compare_rao(arrays[a][d], arrays[b][d]) for d in base.output_dofs
                }
                for a, b in (("coarse", "medium"), ("medium", "fine"))
            }
            state["medium_to_fine_target_met"] = all(
                v["complex_relative_pct"] is not None
                and v["complex_relative_pct"] <= 5.0
                for v in state["comparisons"]["medium_to_fine"].values()
            )
            state["status"] = "completed"
            state.pop("review", None)
            save_json(dest, result)
            print(
                json.dumps(
                    dict(
                        kind=kind,
                        medium_to_fine_target_met=state["medium_to_fine_target_met"],
                        relative_pct={
                            d: v["complex_relative_pct"]
                            for d, v in state["comparisons"]["medium_to_fine"].items()
                        },
                    )
                ),
                flush=True,
            )
        return 0
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
