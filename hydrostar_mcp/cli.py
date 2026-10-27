"""JSON CLI using the same validation and workflow as MCP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

from .models import CaseConfig
from .workflow import CaseService
from .reference_forms import catalog, make_case


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="HydroStar 输入生成、校验与计算")
    parser.add_argument("--workspace", help="运行文件根目录，默认项目内 runs")
    parser.add_argument(
        "--source-root", help="几何源资料和 HST 的允许输入根目录，默认项目目录"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("environment")
    commands.add_parser("schema")
    commands.add_parser("forms")
    commands.add_parser("geometry-formats")
    inspect_geometry = commands.add_parser("geometry-inspect")
    inspect_geometry.add_argument("path")
    geometry_build = commands.add_parser("geometry-build")
    geometry_build.add_argument("request", type=Path)
    reference = commands.add_parser("reference")
    reference.add_argument("form_id")
    reference.add_argument("--project")
    plot = commands.add_parser("plot")
    plot.add_argument("case_id")
    plot.add_argument("--output", type=Path)
    for name in ("plan", "generate", "prepare"):
        command = commands.add_parser(name)
        command.add_argument("config", type=Path)
        if name != "plan":
            command.add_argument("--confirmation-token")
    start = commands.add_parser("start")
    start.add_argument("case_id")
    start.add_argument("--confirmation-token")
    start.add_argument("--poll-seconds", type=float, default=0.5)
    for name in ("status", "result"):
        command = commands.add_parser(name)
        command.add_argument("case_id")
        if name == "result":
            command.add_argument("--dof", default="heave")
    args = parser.parse_args(argv)
    service = None
    try:
        if args.command == "schema":
            result = CaseConfig.model_json_schema()
        elif args.command == "forms":
            result = catalog()
        else:
            service = CaseService(args.workspace, args.source_root)
            if args.command == "environment":
                result = service.environment()
            elif args.command == "geometry-formats":
                from .geometry_sources import format_catalog

                result = format_catalog()
            elif args.command in ("geometry-inspect", "geometry-build"):
                from .geometry_workflow import GeometryService

                geometry_service = GeometryService(
                    service.root / "geometry", service.source_root
                )
                if args.command == "geometry-inspect":
                    result = geometry_service.inspect(args.path)
                else:
                    from .geometry_sources import GeometryRequest

                    result = geometry_service.build(
                        GeometryRequest.model_validate_json(
                            args.request.read_text(encoding="utf-8-sig")
                        )
                    )
            elif args.command == "reference":
                result = service.plan(make_case(args.form_id, args.project))
            elif args.command == "plot":
                from .visualization import plot_case

                result = plot_case(service, args.case_id, args.output)
            elif args.command in ("plan", "generate", "prepare"):
                config = CaseConfig.model_validate_json(
                    args.config.read_text(encoding="utf-8-sig")
                )
                if args.command == "plan":
                    result = service.plan(config)
                else:
                    result = (
                        service.generate
                        if args.command == "generate"
                        else service.prepare
                    )(config, args.confirmation_token)
            elif args.command == "start":
                if args.poll_seconds <= 0:
                    raise ValueError("poll-seconds 必须大于 0")
                result = service.start(args.case_id, args.confirmation_token)
                while result["status"] in ("queued", "running"):
                    time.sleep(min(args.poll_seconds, 5))
                    result = service.status(args.case_id)
            elif args.command == "status":
                result = service.status(args.case_id)
            else:
                result = service.result(args.case_id, args.dof)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return (
            1
            if result.get("status") in ("failed", "cancelled", "interrupted")
            else 2
            if result.get("status") == "needs_confirmation"
            else 0
        )
    except (ValueError, OSError) as exc:
        print(
            json.dumps(
                dict(
                    status="failed", error=dict(code="INVALID_REQUEST", detail=str(exc))
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    finally:
        if service is not None:
            service.close()


if __name__ == "__main__":
    raise SystemExit(main())
