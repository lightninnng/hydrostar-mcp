"""Run and compare a single-frequency native companion for the detailed vessel."""

import cmath
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import CaseService, file_hash, save_json


def main():
    cfg = json.loads((ROOT / "examples/vessel/config.json").read_text(encoding="utf-8"))
    cfg["project"] = "vessel_view"
    cfg["environment"]["frequency"] = dict(min=0.65, max=0.65, step=0.005)
    cfg["environment"]["headings"] = dict(min=60, max=60, step=30)
    cfg["nproc"] = 1
    service = CaseService(ROOT / "output/validation/course-wave-native", ROOT)
    pointer = ROOT / "output/validation/course-vessel-wave-native.json"
    try:
        if pointer.exists():
            saved = json.loads(pointer.read_text(encoding="utf-8"))
            report = service.status(saved["case_id"])
            if report["config"] != CaseConfig.model_validate(cfg).model_dump(
                mode="json"
            ):
                raise ValueError("Existing companion parameters differ")
        else:
            report = service.prepare(CaseConfig.model_validate(cfg))
            save_json(pointer, report)
        if report["status"] == "prepared":
            service.start(report["case_id"])
            service.jobs[report["case_id"]][0].result(timeout=1800)
            report = service.status(report["case_id"])
        if report["status"] != "completed" or set(report["quality_gates"].values()) != {
            "passed"
        }:
            raise ValueError("Companion native gates failed: " + report["status"])
        directory = Path(report["directory"])
        if file_hash(directory / "vessel_view.hst") != file_hash(
            ROOT / "examples/vessel/inputs/vessel.hst"
        ):
            raise ValueError("The companion mesh differs from the detailed sweep")
        errors = {}
        for dof in core.DOFS:
            original = core.read_rao(ROOT / "examples/vessel/rao" / (dof + ".rao"))
            new = service.result(report["case_id"], dof)
            i, j = original["omega"].index(0.65), original["headings"].index(60.0)
            a = original["amplitude"][i][j] * cmath.exp(
                1j * math.radians(original["phase"][i][j])
            )
            b = new["amplitude"][0][0] * cmath.exp(
                1j * math.radians(new["phase"][0][0])
            )
            errors[dof] = abs(a - b) / (1 + abs(a))
        if max(errors.values()) > 1e-5:
            raise ValueError(
                "Single-frequency complex responses differ: " + str(errors)
            )
        save_json(pointer, report)
        save_json(
            ROOT / "output/validation/course-vessel-wave-comparison.json",
            dict(
                status="passed",
                frequency_rad_s=0.65,
                heading_deg=60,
                compared="Single-frequency native companion against the accepted 231-frequency sweep; identical HST, mass, CG, inertia, restoring, damping and environment",
                normalized_complex_errors=errors,
                limit=1e-5,
                definition="abs(H_single-H_sweep)/(1+abs(H_sweep)); native output unit for each DOF",
                parent_mesh_sha256=file_hash(
                    ROOT / "examples/vessel/inputs/vessel.hst"
                ),
                parent_verification_sha256=file_hash(
                    ROOT / "examples/vessel/verification.json"
                ),
            ),
        )
        print(
            "Single-frequency native companion passed; maximum normalized complex difference "
            + str(max(errors.values())),
            flush=True,
        )
    finally:
        service.close()


if __name__ == "__main__":
    main()
