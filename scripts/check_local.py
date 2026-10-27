"""Export portable examples offline; optionally execute one local native solve."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import CaseService, save_json

EXAMPLES = (
    "barge100",
    "barge_explicit",
    "semisub",
    "curved_hull",
    "container_kcs_style",
    "tanker_kvlcc2_style",
    "semisub_oc4_style",
    "imported_mesh",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--solver",
        action="store_true",
        help="Also execute the installed HydroStar solver on the box baseline",
    )
    args = parser.parse_args()
    out = ROOT / "output/validation"
    summary = dict(timestamp=datetime.now(timezone.utc).isoformat(), input_exports={})
    service = CaseService(root=out / "local_checks", source_root=ROOT)
    try:
        save_json(out / "config.schema.json", CaseConfig.model_json_schema())
        for name in EXAMPLES:
            cfg = CaseConfig.model_validate_json(
                (ROOT / "examples" / (name + ".json")).read_text(encoding="utf-8")
            )
            report = service.generate(cfg)
            summary["input_exports"][name] = dict(
                status=report["status"],
                case_id=report.get("case_id"),
                error=report.get("error"),
            )
        if args.solver:
            cfg = CaseConfig.model_validate_json(
                (ROOT / "examples/barge100.json").read_text(encoding="utf-8")
            )
            report = service.prepare(cfg)
            if report["status"] == "prepared":
                service.start(report["case_id"])
                service.jobs[report["case_id"]][0].result(timeout=1800)
                report = service.status(report["case_id"])
            summary["native_solve"] = dict(
                status=report["status"],
                case_id=report.get("case_id"),
                quality_gates=report.get("quality_gates"),
                error=report.get("error"),
            )
        save_json(out / "local_verification.json", summary)
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        statuses = [r["status"] for r in summary["input_exports"].values()]
        if "native_solve" in summary:
            statuses.append(summary["native_solve"]["status"])
        return (
            1 if "failed" in statuses else 2 if "needs_confirmation" in statuses else 0
        )
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
