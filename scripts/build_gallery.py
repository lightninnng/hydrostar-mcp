"""Build an offline results page with embedded numerical data and local media."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    data = json.loads((ROOT / "docs/data/showcase.json").read_text(encoding="utf-8"))
    if len(data["cases"]) != 3:
        raise ValueError("The gallery requires three verified cases")
    for model in data["cases"]:
        folder = ROOT / "examples/animations" / model["key"]
        field = json.loads((folder / "field.json").read_text(encoding="utf-8"))
        render = json.loads((folder / "render.json").read_text(encoding="utf-8"))
        verification = json.loads(
            (folder / "verification.json").read_text(encoding="utf-8")
        )
        model["animation"] = dict(
            omega_rad_s=field["omega_rad_s"],
            heading_deg=field["heading_deg"],
            wave_amplitude_m=field["wave_amplitude_m"],
            depth_m=field["depth_m"],
            period_s=render["period_s"],
            motion_gain=render["motion_gain"],
            frames=render["frames"],
            source_case_id=verification["source_case_id"],
            field_points=verification["point_count"],
            wave_reference_xy_m=field["wave_reference_xy_m"],
        )
    for model in data["cases"]:
        folder = ROOT / "examples/pressures" / model["key"]
        verification = json.loads(
            (folder / "verification.json").read_text(encoding="utf-8")
        )
        render = json.loads((folder / "render.json").read_text(encoding="utf-8"))
        if set(verification["pressure_gates"].values()) != {"passed"}:
            raise ValueError("Pressure validation must pass before building the report")
        model["pressure"] = {
            k: verification[k]
            for k in [
                "panel_count",
                "incident_complex_max_error",
                "hydrostatic_motion_complex_max_error",
                "offset_complex_change_over_global_peak",
                "pressure_colour_limit_kpa",
            ]
        }
        model["pressure"].update(
            motion_gain=render["motion_gain"],
            source_case_id=verification["source_case_id"],
        )
    (ROOT / "docs/data/showcase.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
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
