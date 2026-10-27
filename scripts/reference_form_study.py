"""Generate and verify the three source-informed basic configurations."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.reference_forms import FORMS, catalog, make_case  # noqa: E402
from hydrostar_mcp.workflow import CaseService, save_json, digest  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    out = ROOT / "output/validation"
    dest = out / "reference_form_study.json"
    state = (
        json.loads(dest.read_text(encoding="utf-8"))
        if dest.exists()
        else dict(cases={})
    )
    state["sources"] = catalog()
    save_json(ROOT / "docs/references/basic-form-catalog.json", catalog())
    service = CaseService(root=out / "reference_form_runs")
    try:
        for name in FORMS:
            cfg = make_case(name)
            plan = service.plan(cfg)
            save_json(ROOT / "examples" / (name + ".json"), cfg.model_dump(mode="json"))
            print(
                json.dumps(
                    dict(
                        form=name,
                        planning=plan["status"],
                        warnings=plan["warnings"],
                        scalar_comparison=plan["reference_model"]["scalar_comparison"],
                    ),
                    ensure_ascii=False,
                ),
                flush=True,
            )
            if not args.run:
                continue
            old = state["cases"].get(name, {})
            report = (
                service.status(old["case_id"])
                if old.get("config_digest") == digest(cfg.model_dump(mode="json"))
                else None
            )
            if report is None or report["status"] != "completed":
                print(name + ": native preparation", flush=True)
                report = service.prepare(cfg)
                if report["status"] == "prepared":
                    print(name + ": topology passed; solving", flush=True)
                    service.start(report["case_id"])
                    service.jobs[report["case_id"]][0].result(timeout=1800)
                    report = service.status(report["case_id"])
            if report["status"] != "completed":
                state["review"] = report
                save_json(dest, state)
                print(
                    json.dumps(
                        dict(
                            form=name,
                            status=report["status"],
                            error=report.get("error"),
                            case_id=report.get("case_id"),
                        ),
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                return 1
            state["cases"][name] = dict(
                case_id=report["case_id"],
                directory=report["directory"],
                config_digest=digest(cfg.model_dump(mode="json")),
                quality_gates=report["quality_gates"],
                hslec=report["hslec"],
                hschk=report["hschk"],
                solver_mechanics=report["solver_mechanics"],
                reference_model=report["reference_model"],
                validation_level="source-informed geometry and native execution checked; benchmark line-form and response validation remain explicit acceptance items",
            )
            save_json(dest, state)
            print(name + ": completed", flush=True)
        state["status"] = "completed" if args.run else "planned"
        state.pop("review", None)
        save_json(dest, state)
        return 0
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
