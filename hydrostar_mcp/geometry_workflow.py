"""Isolated, reproducible source-data -> accepted wetted HST bundles."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from .geometry_sources import FORMATS, GeometryRequest, format_catalog
from . import core
from .workflow import file_hash, save_json


def _run_kernel(command, folder, environment, timeout):
    """Bound the worker lifetime, including Windows Python launcher descendants."""
    flags = (
        {"creationflags": subprocess.CREATE_NO_WINDOW}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with (folder / "kernel.log").open("wb") as output:
        process = subprocess.Popen(
            command,
            cwd=folder,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            **flags,
        )
        job = None
        try:
            if os.name == "nt":
                job = core._WindowsJob(process)
            return process.wait(timeout=timeout)
        finally:
            if process.poll() is None:
                core._stop_tree(process, job)
            if job is not None:
                job.close()


class GeometryService:
    def __init__(self, root, source_root):
        self.root = Path(root).resolve()
        self.source_root = Path(source_root).resolve()

    def source(self, value):
        path = (self.source_root / value).resolve()
        if (
            not (
                path.is_relative_to(self.source_root) or path.is_relative_to(self.root)
            )
            or not path.is_file()
        ):
            raise ValueError("几何资料须为输入根目录内的现有文件")
        if path.suffix.lower() not in FORMATS:
            raise ValueError("资料格式请采用 " + ", ".join(FORMATS))
        if path.stat().st_size > 100 * 1024**2:
            raise ValueError("单份几何资料上限为 100 MiB；请先简化或拆分资料")
        return path

    def inspect(self, value):
        source = self.source(value)
        result = dict(
            path=str(source),
            format=FORMATS[source.suffix.lower()],
            bytes=source.stat().st_size,
            sha256=file_hash(source),
            routes=format_catalog(),
            optional_dependencies={
                name: importlib.util.find_spec(name) is not None
                for name in ("gmsh", "ezdxf", "meshio", "shapely", "pypdfium2", "PIL")
            },
        )
        if source.suffix.lower() == ".csv":
            import csv

            with source.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
            result["table"] = dict(
                columns=reader.fieldnames,
                rows=len(rows),
                station_count=len({row.get("station") for row in rows}),
            )
        return result

    def build(self, request):
        request = (
            request
            if isinstance(request, GeometryRequest)
            else GeometryRequest.model_validate(request)
        )
        source = self.source(request.path)
        source_sha = file_hash(source)
        folder = self.root / (request.project + "-" + uuid.uuid4().hex[:16])
        folder.mkdir(parents=True)
        snapshot = folder / ("source" + source.suffix.lower())
        shutil.copyfile(source, snapshot)
        if file_hash(snapshot) != source_sha or file_hash(source) != source_sha:
            raise ValueError("源资料在复制期间发生变化，请重新导入")
        if source.suffix.lower() == ".json":
            evidence = json.loads(snapshot.read_text(encoding="utf-8-sig")).get(
                "digitization_evidence"
            )
            if evidence:
                name = evidence.get("source_file", "")
                drawing = (source.parent / name).resolve()
                if (
                    Path(name).name != name
                    or not (
                        drawing.is_relative_to(self.source_root)
                        or drawing.is_relative_to(self.root)
                    )
                    or not drawing.is_file()
                    or FORMATS.get(drawing.suffix.lower()) != "drawing"
                    or file_hash(drawing) != evidence.get("source_sha256")
                ):
                    raise ValueError(
                        "描线 JSON 须与匹配 SHA-256 的原图纸文件放在同一输入目录"
                    )
                drawing_snapshot = folder / ("drawing-source" + drawing.suffix.lower())
                shutil.copyfile(drawing, drawing_snapshot)
                if file_hash(drawing_snapshot) != evidence["source_sha256"]:
                    raise ValueError("原图纸在复制期间发生变化，请重新导入")
        save_json(folder / "request.json", request.model_dump())
        environment = os.environ.copy()
        environment["XDG_CACHE_HOME"] = str(folder / "cache")
        environment["MPLCONFIGDIR"] = str(folder / "cache" / "matplotlib")
        package_root = str(Path(__file__).resolve().parent.parent)
        environment["PYTHONPATH"] = (
            package_root + os.pathsep + environment.get("PYTHONPATH", "")
        )
        try:
            returncode = _run_kernel(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "hydrostar_mcp.geometry_worker",
                    str(folder),
                ],
                folder,
                environment,
                request.timeout_s,
            )
        except subprocess.TimeoutExpired:
            return dict(
                status="failed",
                directory=str(folder),
                error=dict(code="GEOMETRY_TIMEOUT", detail="几何转换达到本次时间上限"),
            )
        report_path = folder / "geometry-report.json"
        if not report_path.is_file():
            return dict(
                status="failed",
                directory=str(folder),
                error=dict(
                    code="GEOMETRY_KERNEL_FAILED", detail="见独立几何进程 kernel.log"
                ),
            )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report["status"] == "geometry_accepted" and returncode != 0:
            raise ValueError("几何进程终态与验收报告不一致")
        report["directory"] = str(folder)
        report["source_sha256"] = source_sha
        if report["status"] == "geometry_accepted":
            hst = folder / "model.hst"
            report["case_geometry"] = dict(
                type="hst",
                path=str(hst),
                source_manifest=str(report_path),
                expected_volume_m3=report["reference"].get("cad_volume_m3")
                or request.expected_volume_m3,
                volume_relative_tolerance=request.volume_tolerance_relative,
            )
            report["input_root_contains_bundle"] = hst.is_relative_to(self.source_root)
        return report


def verify_bundle(manifest, hst):
    manifest, hst = Path(manifest).resolve(), Path(hst).resolve()
    report = json.loads(manifest.read_text(encoding="utf-8"))
    if (
        manifest.parent != hst.parent
        or hst.name != "model.hst"
        or report.get("schema") != "hydrostar-geometry-bundle-1"
        or report.get("status") != "geometry_accepted"
        or report.get("quality", {}).get("passed") is not True
    ):
        raise ValueError("几何源资料清单应与 HST 位于同一已验收数据包中")
    files = report["files"]
    if "model.hst" not in files or "request.json" not in files:
        raise ValueError("几何数据包缺少输入或湿表面")
    for name, expected in files.items():
        path = (manifest.parent / name).resolve()
        if not path.is_relative_to(manifest.parent) or file_hash(path) != expected:
            raise ValueError("几何数据包文件或 SHA-256 已变化：" + name)
    return report
