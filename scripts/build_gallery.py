"""Build an offline scientific report with verified native media."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__
from scripts.gallery_data import (
    acceptance_table,
    geometry_section,
    overview_table,
    presentation_data,
    result_sections,
    second_order_section,
)


def main():
    dataset = presentation_data()
    payload = (
        json.dumps(
            dataset,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    template = (ROOT / "scripts/templates/gallery.html").read_text(encoding="utf-8")
    result = (
        template.replace("__SHOWCASE_DATA__", payload)
        .replace("__VERSION__", __version__)
        .replace("__GEOMETRY_STUDY__", geometry_section())
        .replace("__RESULT_SECTIONS__", result_sections(dataset))
        .replace("__SECOND_ORDER_SECTION__", second_order_section())
        .replace("__OVERVIEW_ROWS__", overview_table(dataset))
        .replace("__ACCEPTANCE_ROWS__", acceptance_table(dataset))
    )
    (ROOT / "docs/index.html").write_text(result, encoding="utf-8")
    print("Built scientific report with four verified configurations")


if __name__ == "__main__":
    main()
