"""Check native-derived figures, complex field archives and the budgeted vessel."""

from __future__ import annotations

import cmath
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.geometry_workflow import verify_bundle
from hydrostar_mcp.pressure import verify_pressure_physics, wet_panel_samples
from hydrostar_mcp.visualization import whole_mesh
from hydrostar_mcp.workflow import file_hash
from scripts.export_native_curves import CASES


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_complex_radiation(
    total, incident, diffraction, unit_velocity_sum, tolerance
):
    difference = abs((total - incident - diffraction) - unit_velocity_sum)
    require(difference <= tolerance, "Full-complex radiation and motion do not agree")
    return difference


def value(raw, omega, heading):
    i, j = raw["omega"].index(omega), raw["headings"].index(heading)
    return raw["amplitude"][i][j] * cmath.exp(1j * math.radians(raw["phase"][i][j]))


def files_match(folder, record):
    names = {
        p.relative_to(folder).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and p.name != "verification.json"
    }
    require(
        names == set(record["files"]),
        "Unindexed native media file in " + str(folder.relative_to(ROOT)),
    )
    for name, expected in record["files"].items():
        p = (folder / name).resolve()
        require(
            p.is_relative_to(folder.resolve()) and file_hash(p) == expected,
            "Native media hash: " + name,
        )


def check_vessel():
    folder = ROOT / "examples/vessel"
    v = read(folder / "verification.json")
    files_match(folder, v)
    require(
        set(v["quality_gates"].values()) == {"passed"} and len(v["quality_gates"]) == 6,
        "Vessel native gates",
    )
    g = verify_bundle(
        folder / "geometry/geometry-report.json", folder / "geometry/model.hst"
    )
    require(
        file_hash(folder / "inputs/vessel.hst")
        == file_hash(folder / "geometry/model.hst"),
        "Vessel solved geometry",
    )
    require(g["status"] == "geometry_accepted", "Vessel geometry acceptance")
    cfg = read(folder / "config.json")
    mesh = v["hslec"]
    total = (mesh["hull_panels"] + mesh["waterplane_panels"]) * 2 ** mesh["symmetry"]
    require(
        cfg["recommended_max_panels"] == 3000 and total == 2873 and total <= 3000,
        "Vessel full-equivalent budget",
    )
    require(
        v["hschk"]["pass"]
        and all(x == 0 for k, x in v["hschk"].items() if k != "pass"),
        "Vessel topology",
    )
    require(
        v["solver_mechanics"]["balanced"]
        and min(v["solver_mechanics"]["gm_roll_pitch_m"]) > 0,
        "Vessel equilibrium/stability",
    )
    require(not v["engineering_acceptance"]["ready"], "Vessel intended-use evidence")
    motions = read(folder / "motions.json")
    n = 0
    for dof in core.DOFS:
        raw = core.read_rao(folder / "rao" / (dof + ".rao"))
        require(
            all(
                raw[k] == motions[dof][k]
                for k in ("omega", "headings", "amplitude", "phase", "unit")
            ),
            "Vessel native response arrays",
        )
        require(
            len(raw["omega"]) == 231 and len(raw["headings"]) == 13,
            "Vessel frequency/heading coverage",
        )
        n += len(raw["omega"]) * len(raw["headings"]) * 2
    delivery = read(folder / "delivery.json")
    for item in ("input_files", "output_files"):
        for name, entry in delivery[item].items():
            require(
                entry["status"] == "validated"
                and file_hash(folder / name) == entry["sha256"],
                "Vessel native file delivery",
            )
    return n


def check_curves(key):
    folder = ROOT / "examples/visualization/curves" / key
    record = read(folder / "verification.json")
    files_match(folder, record)
    source = ROOT / CASES[key][0]
    summary = source / (
        "summary.json" if (source / "summary.json").exists() else "verification.json"
    )
    require(
        file_hash(summary) == record["native_summary_sha256"],
        "Curve source summary changed",
    )
    require(
        record["renderer"].startswith("gnuplot ") and record["status"] == "verified",
        "Gnuplot export/review state",
    )
    for dof in core.DOFS:
        require(
            file_hash(folder / "data" / (dof + ".rao"))
            == file_hash(source / "rao" / (dof + ".rao")),
            "Gnuplot original response source",
        )
    require(len(record["figures"]) == 28, "Complete curve exports")
    for name, entry in record["figures"].items():
        require(
            file_hash(ROOT / "docs/assets" / name) == entry["sha256"],
            "Native curve figure changed",
        )


def check_fields(key):
    folder = ROOT / "examples/visualization/fields" / key
    v = read(folder / "verification.json")
    files_match(folder, v)
    c = read(folder / "condition.json")
    waves = read(folder / "waves.json")
    require(
        v["status"] == "numerically_verified"
        and set(v["gates"].values()) == {"passed"},
        "Native field gates",
    )
    require(
        v["gates"].get("native_complex_wave") == "passed",
        "Independent full-complex field gate",
    )
    require(
        v["hsprv_crosscheck"]["raw_total_used_for_display"] is False,
        "Accepted field routing",
    )
    require(
        c["motion_gain"] == 6
        and c["wave_height_gain"] == 6
        and c["pressure_geometry_gain"] == 1,
        "Explicit display gains",
    )
    source = ROOT / v["source_package"]
    source_cfg = read(source / "config.json")
    actual_hst = next((folder / "inputs").glob("*.hst"))
    require(
        file_hash(actual_hst) == v["source_mesh_sha256"],
        "Displayed native mesh source",
    )
    require(
        whole_mesh(actual_hst)
        == whole_mesh(source / "inputs" / (source_cfg["project"] + ".hst")),
        "Field companion geometry must match the response sweep",
    )
    # Retain the original export, including diagnostics, without trusting it as
    # proof of a correct complex radiation reconstruction.
    with ZipFile(folder / "native.zip") as archive:
        require(
            set(archive.namelist()) == set(v["native_files"]),
            "Native PVD dataset completeness",
        )
        for name, h in v["native_files"].items():
            require(
                hashlib.sha256(archive.read(name)).hexdigest() == h,
                "Native animation member hash",
            )
    raw_files = {}
    with gzip.open(folder / "wave-raos.jsonl.gz", "rt", encoding="ascii") as archive:
        for line in archive:
            item = json.loads(line)
            name, content = item["name"], item["content"]
            require(
                name not in raw_files and name in v["wave_validation"]["raw_files"],
                "Wave native record identity",
            )
            require(
                hashlib.sha256(content.encode("utf-8")).hexdigest()
                == v["wave_validation"]["raw_files"][name],
                "Wave native record bytes",
            )
            raw_files[name] = core.read_rao_text(content, path=name)
    require(
        set(raw_files) == set(v["wave_validation"]["raw_files"]),
        "All original complex wave records",
    )
    omega, heading = c["omega_rad_s"], c["heading_deg"]
    for i in range(len(waves["points_m"])):
        for field, code in [
            ("total", "total"),
            ("incident", "inc"),
            ("diffraction", "dif"),
        ]:
            raw = raw_files[f"verified_{code}_{i + 1:04d}.rao"]
            require(
                raw["omega"] == [omega]
                and raw["headings"] == [heading]
                and raw["unit"] in ("m", "m/m"),
                "Wave source condition/unit",
            )
            require(
                abs(value(raw, omega, heading) - complex(*waves[field][i])) < 1e-12,
                "Wave array differs from native output",
            )
    q = []
    parent = read(source / "motions.json")
    for j, dof in enumerate(core.DOFS):
        single = core.read_rao(folder / "motions" / (dof + ".rao"))
        z = value(single, omega, heading)
        require(
            abs(z - value(parent[dof], omega, heading)) / (1 + abs(z)) < 1e-5,
            "Field companion differs from response sweep",
        )
        q.append(z * (math.pi / 180 if j >= 3 else 1))
    for name in raw_files:
        if name.startswith("verified_rad1_"):
            point = int(name.split("_")[-1].split(".")[0])
            i = point - 1
            expected = sum(
                1j
                * omega
                * q[j]
                * value(
                    raw_files[f"verified_rad{j + 1}_{point:04d}.rao"], omega, heading
                )
                for j in range(6)
            )
            validate_complex_radiation(
                *(complex(*waves[k][i]) for k in ("total", "incident", "diffraction")),
                expected,
                5e-5,
            )
    pressure_path = ROOT / c["pressure_file"]
    require(
        file_hash(pressure_path) == c["pressure_file_sha256"], "Panel pressure source"
    )
    pressure = read(pressure_path)
    check = verify_pressure_physics(pressure)
    require(
        check["incident_complex_max_error"] < 3e-5
        and check["hydrostatic_motion_complex_max_error"] < 3e-5
        and check["offset_complex_change_over_global_peak"] <= 0.02,
        "Body pressure physics and sampling",
    )
    n = len(pressure["mesh"]["faces"])
    if key == "vessel":
        native_mesh = wet_panel_samples(ROOT / "examples/vessel/inputs/vessel.hst")
        require(
            native_mesh["faces"] == pressure["mesh"]["faces"]
            and native_mesh["vertices"] == pressure["mesh"]["vertices"],
            "Vessel native panel pressure geometry",
        )
        pv = read(folder / "pressure-verification.json")
        seen = set()
        with gzip.open(
            folder / "pressure-raos.jsonl.gz", "rt", encoding="ascii"
        ) as archive:
            for line in archive:
                item = json.loads(line)
                name, content = item["name"], item["content"]
                require(
                    name not in seen
                    and hashlib.sha256(content.encode("utf-8")).hexdigest()
                    == pv["native_file_sha256"][name],
                    "Vessel native pressure archive",
                )
                kind, index = name.removesuffix(".rao").split("_")[1:]
                field = {
                    "following": "following_head",
                    "eulerian": "eulerian_head",
                    "incident": "incident_head",
                }[kind]
                require(
                    abs(
                        value(core.read_rao_text(content, path=name), omega, heading)
                        - complex(*pressure[field][int(index) - 1])
                    )
                    < 1e-12,
                    "Vessel pressure array differs from native output",
                )
                seen.add(name)
        require(
            seen == set(pv["native_file_sha256"]) and len(seen) == 5 * n,
            "Vessel native pressure record coverage",
        )
    render = read(folder / "render.json")
    require(
        render["renderer"] == "ParaView 6.2" and render["status"] == "verified",
        "ParaView export/review state",
    )
    require(
        render["renderer_script_sha256"]
        == file_hash(ROOT / "scripts/render_native_views.py"),
        "Actual ParaView rendering script",
    )
    require(
        render["encoder_script_sha256"]
        == file_hash(ROOT / "scripts/encode_native_media.py"),
        "Actual GIF encoder",
    )
    require(render["visual_review"]["status"] == "passed", "Actual visual review")
    require(
        len(set(render["native_frame_sha256"].values())) == 40,
        "Dynamic native frame sequence",
    )
    require(
        set(render["native_view_pixel_sha256"])
        == {"Pressure", "Total", "Scattered", "Diffraction", "Radiation"},
        "All dynamic viewports checked",
    )
    require(
        all(
            len(x) == 40 and len(set(x)) >= 20
            for x in render["native_view_pixel_sha256"].values()
        ),
        "Native field pixel variation",
    )
    for group, media in render["media"].items():
        require(
            file_hash(ROOT / media["gif"]) == media["sha256"]
            and file_hash(ROOT / media["still"]) == media["still_sha256"],
            "Native image/GIF hashes",
        )
        for name, h in media["checkpoints"].items():
            require(file_hash(ROOT / name) == h, "Native phase checkpoint")
        with Image.open(ROOT / media["gif"]) as gif:
            require(
                gif.n_frames == 40 and gif.size == (media["width"], 810),
                "Native GIF geometry/frame coverage",
            )
            image_hashes = [set() for _ in range(media["width"] // 720)]
            for i in range(40):
                gif.seek(i)
                require(gif.info["duration"] == 100, "Native GIF playback time")
                rgb = gif.convert("RGB")
                for j, seen in enumerate(image_hashes):
                    seen.add(
                        hashlib.sha256(
                            rgb.crop((j * 720, 105, (j + 1) * 720, 780)).tobytes()
                        ).hexdigest()
                    )
            require(
                all(len(seen) >= 20 for seen in image_hashes),
                "GIF field pixels must evolve independently of text captions",
            )
    return len(raw_files), n


def check_native_media():
    values = check_vessel()
    records = 0
    panels = 0
    for key in CASES:
        check_curves(key)
        r, n = check_fields(key)
        records += r
        panels += n
    return dict(
        budgeted_vessel_response_values=values,
        native_curve_figures=112,
        native_complex_field_records=records,
        native_visualized_pressure_panels=panels,
        native_gifs=12,
    )


if __name__ == "__main__":
    print(json.dumps(check_native_media(), indent=2))
