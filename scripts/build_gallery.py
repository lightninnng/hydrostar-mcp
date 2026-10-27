"""Build a self-contained results page with no network or solver dependency."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    data = json.loads((ROOT / "docs/data/showcase.json").read_text(encoding="utf-8"))
    if len(data["cases"]) != 3:
        raise ValueError("The gallery requires three verified cases")
    payload = (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    template = (ROOT / "scripts/templates/gallery.html").read_text(encoding="utf-8")
    (ROOT / "docs/index.html").write_text(
        template.replace("__SHOWCASE_DATA__", payload), encoding="utf-8"
    )
    print(ROOT / "docs/index.html")


if __name__ == "__main__":
    main()
