"""Index native geometry/curve exports and assemble original PDF pages."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__
from hydrostar_mcp.workflow import file_hash, save_json

LABELS = {
    "lofted_vessel": ("曲线站位船体", "Vessel reconstructed from curved sections"),
    "moonpool_caisson": (
        "带贯通月池的多边形浮体",
        "Polygonal caisson with a through moonpool",
    ),
    "cad_spar": ("带升沉板的曲面 Spar", "Curved CAD spar with a finite heave plate"),
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assemble_pdf(pages, target):
    """Copy native PDF page objects without an additional image conversion."""
    import pypdfium2 as pdfium

    combined = pdfium.PdfDocument.new()
    try:
        for page in pages:
            path = ROOT / "output/validation/native-geometry-export" / page["file"]
            if file_hash(path) != page["sha256"]:
                raise ValueError("Native PDF page changed: " + page["file"])
            source = pdfium.PdfDocument(str(path))
            try:
                combined.import_pages(source)
            finally:
                source.close()
        combined.save(str(target))
    finally:
        combined.close()
    return dict(
        sha256=file_hash(target),
        pages=len(pages),
        method="Unmodified ParaView GL2PS pages assembled with PDFium; native raster geometry and vector text paths preserved",
        geometry_encoding="native raster render; not vector geometry",
    )


def export(gnuplot=None):
    assets = ROOT / "docs/assets"
    views_path = ROOT / "examples/geometry/native-mesh-views.json"
    views = read(views_path)
    if views["output_sha256"] != file_hash(assets / "geometry-source-cases.png"):
        raise ValueError("Native ParaView overview changed")
    native_cases = {case["key"]: case for case in views["cases"]}
    views["pdf_outputs"] = {}
    overview_pages = []
    cases = []
    for key, labels in LABELS.items():
        folder = ROOT / "examples/geometry" / key
        report = read(folder / "geometry/geometry-report.json")
        native = read(folder / "verification.json")
        if report["status"] != "geometry_accepted" or set(
            native["quality_gates"].values()
        ) != {"passed"}:
            raise ValueError("Accepted geometry and native results required: " + key)
        motions = read(folder / "motions.json")
        curves = read(folder / "visualization/verification.json")
        if curves["motions_sha256"] != file_hash(folder / "motions.json"):
            raise ValueError("Native Gnuplot curve source changed: " + key)
        for name, item in curves["figures"].items():
            if item["sha256"] != file_hash(assets / name):
                raise ValueError("Native Gnuplot figure changed: " + name)
        figure = native_cases[key]["geometry_figures"]
        if file_hash(ROOT / figure["png"]) != figure["png_sha256"]:
            raise ValueError("Native mesh figure changed: " + key)
        pdf_name = key + "_geometry.pdf"
        views["pdf_outputs"][pdf_name] = assemble_pdf(
            figure["pdf_pages"], assets / pdf_name
        )
        overview_pages.append(figure["pdf_pages"][0])
        cfg = read(folder / "config.json")
        native["publication_version"] = __version__
        native["files"] = {
            p.relative_to(folder).as_posix(): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p != folder / "verification.json"
        }
        save_json(folder / "verification.json", native)
        cases.append(
            dict(
                key=key,
                label=labels[0],
                label_en=labels[1],
                geometry_figure="assets/" + key + "_geometry.png",
                rao_figure="assets/" + key + "_rao.png",
                volume_m3=report["hydrostatics"]["volume"],
                cad_volume_m3=report["reference"]["cad_volume_m3"],
                volume_relative_error=report["fidelity"]["cad_volume_relative_error"],
                cb_distance_m=report["fidelity"]["cad_cb_distance_m"],
                panels=report["quality"]["panels"],
                panel_layout=report["request"]["panel_layout"],
                panel_quality=report["quality"]["panel_quality"],
                waterplane_panels=native["hslec"]["waterplane_panels"],
                full_equivalent_total=native["resource_policy"][
                    "full_equivalent_total"
                ],
                quality_gates=native["quality_gates"],
                frequency_count=len(motions["heave"]["omega"]),
                heading_count=len(motions["heave"]["headings"]),
                frequency_grid=cfg["environment"]["frequency"],
                summary="examples/geometry/" + key + "/verification.json",
                summary_sha256=file_hash(folder / "verification.json"),
                source_case_id=native["source_case_id"],
                geometry_renderer="HSprv native PVD -> ParaView direct orthographic PNG and high-resolution native-view PDF",
                curve_renderer="HSRAO macro/native RAO columns -> Gnuplot direct file terminals",
            )
        )
    views["pdf_outputs"]["geometry-source-cases.pdf"] = assemble_pdf(
        overview_pages, assets / "geometry-source-cases.pdf"
    )
    save_json(views_path, views)
    payload = dict(
        schema="hydrostar-general-geometry-study-1",
        publication_version=__version__,
        source_origin="Original scalar construction in geometry_source_study.py; no external meshes",
        cases=cases,
        native_mesh_views=dict(
            path="examples/geometry/native-mesh-views.json",
            sha256=file_hash(views_path),
        ),
        figures={
            p.name: file_hash(p)
            for p in assets.iterdir()
            if p.name in {"geometry-source-cases.png", "geometry-source-cases.pdf"}
            or any(p.name.startswith(k + "_") for k in LABELS)
        },
    )
    save_json(ROOT / "examples/geometry/index.json", payload)
    save_json(ROOT / "docs/data/geometry.json", payload)
    from scripts.export_mesh_comparison import export_comparison

    export_comparison(gnuplot)
    print("Published native geometry cases:", len(cases))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gnuplot")
    export(parser.parse_args().gnuplot)
