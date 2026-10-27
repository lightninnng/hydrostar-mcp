"""Metric calibration and reviewed section tracing for raster and PDF drawings."""

from __future__ import annotations

import json
from pathlib import Path


def stage_drawing(folder, source, request):
    from PIL import Image, ImageOps
    from .workflow import file_hash

    if source.suffix.lower() == ".pdf":
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(source))
        try:
            if request.pdf_page >= len(document):
                raise ValueError("所选 PDF 页码超出范围；页码从 0 开始")
            page = document[request.pdf_page]
            try:
                scale = min(3.0, 6000 / max(page.get_size()))
                bitmap = page.render(scale=scale)
                try:
                    picture = bitmap.to_pil().convert("RGB")
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            document.close()
    else:
        with Image.open(source) as image:
            if image.width * image.height > 40_000_000:
                raise ValueError("图纸栅格上限为 4000 万像素，请先裁出所需型线区域")
            picture = ImageOps.exif_transpose(image).convert("RGB")
    picture.save(folder / "drawing.png")
    constants = json.dumps(
        dict(
            project=request.project,
            source_file=source.name,
            source_sha256=file_hash(source),
            page=request.pdf_page,
            width=picture.width,
            height=picture.height,
        )
    )
    template = (
        Path(__file__).with_name("drawing_workbench.html").read_text(encoding="utf-8")
    )
    (folder / "digitize.html").write_text(
        template.replace("__DRAWING_DATA__", constants), encoding="utf-8"
    )
    return dict(
        schema="hydrostar-drawing-workspace-1",
        status="digitization_required",
        image="drawing.png",
        workbench="digitize.html",
        source_page=request.pdf_page,
        width_px=picture.width,
        height_px=picture.height,
        next_step="标定至少 3 个已知坐标点，用至少 2 个独立尺寸点复核，再按对应特征顺序描绘剖面并导出米制 JSON",
        quality_requirements=dict(
            calibration_points=3,
            independent_checkpoints=2,
            explicit_uncertainty_m=True,
            closed_ordered_sections=True,
        ),
    )
