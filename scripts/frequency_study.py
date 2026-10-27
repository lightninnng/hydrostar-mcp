"""Resolve in-band RAO maxima on a 0.005 rad/s grid using the finest wet mesh."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.models import CaseConfig  # noqa: E402
from hydrostar_mcp.workflow import CaseService, save_json, digest  # noqa: E402


def peak(a):
    value, i, j = max(
        (v, i, j) for i, row in enumerate(a["amplitude"]) for j, v in enumerate(row)
    )
    return dict(
        amplitude=value, omega=a["omega"][i], heading=a["headings"][j], unit=a["unit"]
    )


def sampled(a, step, offset=0.0):
    ids = [
        i
        for i, w in enumerate(a["omega"])
        if w >= a["omega"][0] + offset - 1e-8
        and abs(
            (w - a["omega"][0] - offset) / step
            - round((w - a["omega"][0] - offset) / step)
        )
        < 1e-6
    ]
    # Keep the same physical frequency band for both interleaved subsets.
    ids = sorted({0, len(a["omega"]) - 1, *ids})
    return dict(
        **{k: a[k] for k in ("headings", "unit")},
        omega=[a["omega"][i] for i in ids],
        amplitude=[a["amplitude"][i] for i in ids],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind", choices=["semisub", "curved_hull", "all"], default="all"
    )
    args = parser.parse_args()
    source = json.loads(
        (ROOT / "output/validation/parametric_study.json").read_text(encoding="utf-8")
    )
    dest = ROOT / "output/validation/frequency_study.json"
    result = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {}
    service = CaseService(root=ROOT / "output/validation/parametric_runs")
    try:
        for kind in ["semisub", "curved_hull"] if args.kind == "all" else [args.kind]:
            original = source[kind]["cases"]["fine"]
            data = json.loads(
                (Path(original["directory"]) / "config.json").read_text(
                    encoding="utf-8"
                )
            )
            data["project"] = "own_" + kind + "_frequency"
            data["environment"]["frequency"]["step"] = 0.005
            cfg = CaseConfig.model_validate(data)
            state = result.get(kind, {})
            report = (
                service.status(state["case_id"])
                if state.get("config_digest") == digest(cfg.model_dump(mode="json"))
                else None
            )
            if report is None or report["status"] != "completed":
                print(f"{kind}: preparing 0.005 rad/s grid", flush=True)
                report = service.prepare(cfg)
                if report["status"] == "prepared":
                    print(f"{kind}: solving refined frequencies", flush=True)
                    service.start(report["case_id"])
                    service.jobs[report["case_id"]][0].result(timeout=1800)
                    report = service.status(report["case_id"])
            if report["status"] != "completed":
                save_json(dest, dict(**result, review=report))
                print(
                    json.dumps(
                        report.get("error", report["status"]), ensure_ascii=False
                    ),
                    flush=True,
                )
                return 1
            comparisons = {}
            for dof in cfg.output_dofs:
                response = service.result(report["case_id"], dof)
                old = peak(service.result(original["case_id"], dof))
                new = peak(response)
                final = peak(sampled(response, 0.01))
                shifted = peak(sampled(response, 0.01, 0.005))
                comparisons[dof] = dict(
                    original_step_025_peak=old,
                    step_010_peak=final,
                    step_010_offset_peak=shifted,
                    step_005_peak=new,
                    peak_change_025_to_005_pct=100
                    * abs(old["amplitude"] - new["amplitude"])
                    / max(new["amplitude"], 1e-12),
                    peak_change_010_to_005_pct=100
                    * max(
                        abs(final["amplitude"] - new["amplitude"]),
                        abs(shifted["amplitude"] - new["amplitude"]),
                    )
                    / max(new["amplitude"], 1e-12),
                    omega_shift_010_to_005=abs(final["omega"] - new["omega"]),
                )
            result[kind] = dict(
                status="completed",
                case_id=report["case_id"],
                directory=report["directory"],
                config_digest=digest(cfg.model_dump(mode="json")),
                quality_gates=report["quality_gates"],
                comparisons=comparisons,
                step_010_to_005_peak_target_met=all(
                    v["peak_change_010_to_005_pct"] <= 5 for v in comparisons.values()
                ),
                basis="Same inputs and finest wet mesh. Compare both interleaved 0.01 subsets of the 0.005 solve with endpoints retained. Maxima refer to the requested frequency band and discrete headings.",
            )
            save_json(dest, result)
            print(
                json.dumps(
                    dict(
                        kind=kind,
                        target_met=result[kind]["step_010_to_005_peak_target_met"],
                        peak_changes={
                            d: v["peak_change_010_to_005_pct"]
                            for d, v in comparisons.items()
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
