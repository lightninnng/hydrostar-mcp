"""Native local frequency and mesh checks around the semisub's narrow modes."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.models import CaseConfig  # noqa: E402
from hydrostar_mcp.workflow import CaseService, save_json, digest  # noqa: E402
from scripts.mesh_study import compare_rao  # noqa: E402
from scripts.frequency_study import peak, sampled  # noqa: E402


def main():
    destination = ROOT / "output/validation/peak_study.json"
    study = json.loads(
        (ROOT / "output/validation/parametric_study.json").read_text(encoding="utf-8")
    )
    state = (
        json.loads(destination.read_text(encoding="utf-8"))
        if destination.exists()
        else dict(cases={})
    )
    service = CaseService(root=ROOT / "output/validation/parametric_runs")
    arrays = {}
    try:
        for label in ("fine", "medium", "refined"):
            original = study["semisub"]["cases"][
                "fine" if label == "refined" else label
            ]
            data = json.loads(
                (Path(original["directory"]) / "config.json").read_text(
                    encoding="utf-8"
                )
            )
            data["project"] = "own_semisub_peak_" + label
            if label == "refined":
                data["geometry"]["target_panel_m"] = 1.25
            data["environment"]["frequency"] = dict(min=0.08, max=0.36, step=0.001)
            cfg = CaseConfig.model_validate(data)
            prior = state["cases"].get(label, {})
            report = (
                service.status(prior["case_id"])
                if prior.get("config_digest") == digest(cfg.model_dump(mode="json"))
                else None
            )
            if report is None or report["status"] != "completed":
                print(label + ": preparing peak-band mesh", flush=True)
                report = service.prepare(cfg)
                if report["status"] == "prepared":
                    print(label + ": solving 0.08..0.36, step 0.001 rad/s", flush=True)
                    service.start(report["case_id"])
                    service.jobs[report["case_id"]][0].result(timeout=1800)
                    report = service.status(report["case_id"])
            if report["status"] != "completed":
                state["review"] = report
                save_json(destination, state)
                print(
                    json.dumps(
                        report.get("error", report["status"]), ensure_ascii=False
                    ),
                    flush=True,
                )
                return 1
            state["cases"][label] = dict(
                case_id=report["case_id"],
                directory=report["directory"],
                config_digest=digest(cfg.model_dump(mode="json")),
                quality_gates=report["quality_gates"],
            )
            arrays[label] = {
                d: service.result(report["case_id"], d) for d in cfg.output_dofs
            }
            save_json(destination, state)
            print(label + ": completed", flush=True)
        state["initial_mesh_comparison"] = {
            d: compare_rao(arrays["medium"][d], arrays["fine"][d])
            for d in arrays["fine"]
        }
        state["mesh_comparison"] = {
            d: compare_rao(arrays["refined"][d], arrays["fine"][d])
            for d in arrays["fine"]
        }
        state["mesh_comparison_basis"] = dict(
            candidate_spacing_m=1.25,
            reference_spacing_m=1.0,
            initial_candidate_spacing_m=1.5,
            frequency_step_rad_s=0.001,
            reason="Original 1.5 m medium mesh exceeded 5% in the narrow resonance band; add a finer candidate and retain both comparisons.",
        )
        state["frequency_comparison"] = {}
        for dof, a in arrays["fine"].items():
            fine = peak(a)
            sub = peak(sampled(a, 0.002))
            shifted = peak(sampled(a, 0.002, 0.001))
            state["frequency_comparison"][dof] = dict(
                step_001_peak=fine,
                step_002_peak=sub,
                step_002_offset_peak=shifted,
                peak_change_pct=100
                * max(
                    abs(fine["amplitude"] - sub["amplitude"]),
                    abs(fine["amplitude"] - shifted["amplitude"]),
                )
                / max(fine["amplitude"], 1e-12),
            )
        state["status"] = "completed"
        state["mesh_target_met"] = all(
            v["complex_relative_pct"] <= 5 for v in state["mesh_comparison"].values()
        )
        state["frequency_target_met"] = all(
            v["peak_change_pct"] <= 5 for v in state["frequency_comparison"].values()
        )
        save_json(destination, state)
        print(
            json.dumps(
                {
                    k: state[k]
                    for k in ("status", "mesh_target_met", "frequency_target_met")
                }
            ),
            flush=True,
        )
        return 0
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
