"""Build an offline scientific report with verified native media."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__
from scripts.gallery_data import presentation_data, geometry_section


def main():
    payload = (
        json.dumps(
            presentation_data(),
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
    )
    (ROOT / "docs/index.html").write_text(result, encoding="utf-8")
    print("Built scientific report with four verified configurations")


if __name__ == "__main__":
    main()
