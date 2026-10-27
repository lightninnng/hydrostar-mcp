"""Three-level barge response-sensitivity study for teaching and simplified analysis."""

from __future__ import annotations

import argparse
import cmath
import copy
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import CaseService, save_json


def compare_rao(candidate, reference):
    """Compare complex RAOs on an identical grid; phase wrapping is handled naturally."""
    for key in ("omega", "headings", "unit"):
        if candidate[key] != reference[key]:
            raise ValueError(f"响应对照需要一致的 {key}")

    def values(result):
        if len(result["amplitude"]) != len(result["omega"]) or len(
            result["phase"]
        ) != len(result["omega"]):
            raise ValueError("响应矩阵行数应与频率数一致")
        for amps, phases in zip(result["amplitude"], result["phase"]):
            if len(amps) != len(result["headings"]) or len(phases) != len(
                result["headings"]
            ):
                raise ValueError("响应矩阵列数应与浪向数一致")
            if any(not math.isfinite(v) for v in [*amps, *phases]) or any(
                v < 0 for v in amps
            ):
                raise ValueError("请提供有限数值及非负幅值")
        return [
            cmath.rect(a, math.radians(p))
            for amps, phases in zip(result["amplitude"], result["phase"])
            for a, p in zip(amps, phases)
        ]

    a, b = values(candidate), values(reference)
    if not a or len(a) != len(b):
        raise ValueError("请提供完整且同形状的响应矩阵")
    scale = max(abs(v) for v in b)
    difference = max(abs(x - y) for x, y in zip(a, b))

    def peak(result):
        amplitude, i, j = max(
            (v, i, j)
            for i, row in enumerate(result["amplitude"])
            for j, v in enumerate(row)
        )
        return amplitude, result["omega"][i], result["headings"][j]

    old, new = peak(candidate), peak(reference)
    return dict(
        complex_max_difference=difference,
        complex_relative_pct=100 * difference / scale if scale > 1e-12 else None,
        peak_amplitude_change_pct=100 * abs(old[0] - new[0]) / new[0]
        if new[0] > 1e-12
        else None,
        peak_omega_shift=abs(old[1] - new[1]),
        candidate_peak=dict(amplitude=old[0], omega=old[1], heading=old[2]),
        reference_peak=dict(amplitude=new[0], omega=new[1], heading=new[2]),
        unit=reference["unit"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true", help="Execute the three planned cases in sequence"
    )
    parser.add_argument(
        "--target-pct",
        type=float,
        default=5.0,
        help="Response-sensitivity observation target, not a hard execution gate",
    )
    args = parser.parse_args()
    if not math.isfinite(args.target_pct) or args.target_pct <= 0:
        parser.error("target-pct must be positive and finite")
    base = json.loads((ROOT / "examples/barge100.json").read_text(encoding="utf-8"))
    service = CaseService(root=ROOT / "output/validation/mesh_study_runs")
    configs = {}
    for label, nl, nb, nt in [
        ("coarse", 32, 7, 3),
        ("medium", 40, 9, 4),
        ("fine", 48, 10, 4),
    ]:
        data = copy.deepcopy(base)
        data["project"] = "mesh_" + label
        data["geometry"].update(n_length=nl, n_half_beam=nb, n_draft=nt)
        data["environment"]["frequency"]["max"] = 1.4
        configs[label] = CaseConfig.model_validate(data)
    result = dict(
        status="planned",
        purpose="same physical model, three mesh levels, 0.05..1.4 rad/s",
        observation_target_pct=args.target_pct,
        plans={},
        cases={},
    )
    destination = ROOT / "output/validation/mesh_study.json"
    try:
        result["plans"] = {label: service.plan(cfg) for label, cfg in configs.items()}
        if not args.run:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        arrays = {}
        for label, cfg in configs.items():
            report = service.prepare(cfg)
            if report["status"] == "prepared":
                service.start(report["case_id"])
                future, _ = service.jobs[report["case_id"]]
                future.result(timeout=600)
                report = service.status(report["case_id"])
            if report["status"] != "completed":
                result.update(status=report["status"], review=report)
                save_json(destination, result)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 2 if report["status"] == "needs_confirmation" else 1
            result["cases"][label] = {
                k: report[k]
                for k in (
                    "case_id",
                    "directory",
                    "quality_gates",
                    "hslec",
                    "hydrostatics",
                    "results",
                )
            }
            names = list(cfg.output_dofs) + (
                ["heave_at_point"] if cfg.output_point_m is not None else []
            )
            arrays[label] = {
                name: service.result(report["case_id"], name) for name in names
            }
            print(
                f"{label}: completed ({report['hslec']['hull_panels']} half-hull panels)",
                flush=True,
            )
        result["comparisons"] = {}
        for first, second in [("coarse", "medium"), ("medium", "fine")]:
            result["comparisons"][first + "_to_" + second] = {
                name: compare_rao(arrays[first][name], arrays[second][name])
                for name in arrays[first]
            }
        result["medium_to_fine_target_met"] = all(
            v["complex_relative_pct"] is not None
            and v["complex_relative_pct"] <= args.target_pct
            for v in result["comparisons"]["medium_to_fine"].values()
        )
        result["status"] = "completed"
        save_json(destination, result)
        print(
            json.dumps(
                {k: v for k, v in result.items() if k not in ("plans", "cases")},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        service.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
