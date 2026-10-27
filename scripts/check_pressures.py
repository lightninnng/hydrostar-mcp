"""Verify every archived native panel-pressure record and synchronized figure."""

from __future__ import annotations

import cmath
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check_pressures():
    from hydrostar_mcp import core
    from hydrostar_mcp.models import CaseConfig
    from hydrostar_mcp.pressure import (
        wet_panel_samples,
        pressure_points,
        verify_pressure_physics,
    )
    from PIL import Image

    def require(value, message):
        if not value:
            raise ValueError(message)

    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    base = ROOT / "examples/pressures"
    index = load(base / "index.json")
    keys = {"container_kcs_style", "tanker_kvlcc2_style", "semisub_oc4_style"}
    require(
        {r["form_id"] for r in index["cases"]} == keys, "Incomplete pressure case index"
    )
    panel_total = 0
    record_total = 0
    for entry in index["cases"]:
        key = entry["form_id"]
        folder = base / key
        v = load(folder / "verification.json")
        require(
            sha(folder / "verification.json") == entry["verification_sha256"],
            key + ": verification hash",
        )
        require(
            set(v["quality_gates"].values()) == {"passed"}, key + ": execution gates"
        )
        require(
            set(v["pressure_gates"].values()) == {"passed"}, key + ": pressure gates"
        )
        require(
            all(step["ok"] and step["rc"] == 0 for step in v["pressure_steps"]),
            key + ": native processes",
        )
        names = {
            p.relative_to(folder).as_posix()
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        }
        require(names == set(v["files"]), key + ": publication file set")
        for name, expected in v["files"].items():
            path = (folder / name).resolve()
            require(path.is_relative_to(folder.resolve()), key + ": unsafe file path")
            require(sha(path) == expected, key + ": public file hash " + name)
        cfg = CaseConfig.model_validate(load(folder / "config.json"))
        d = load(folder / "pressure.json")
        n = len(d["mesh"]["faces"])
        mesh = wet_panel_samples(folder / "inputs" / (cfg.project + ".hst"))
        require(mesh == d["mesh"], key + ": source mesh/centroids/normals")
        require(
            pressure_points(mesh, d["outward_offset_m"]) == d["points"],
            key + ": pressure collocation geometry",
        )
        require(
            d["pressure_colour_gain"] == 1 and d["display_unit"] == "kPa",
            key + ": physical pressure colour units",
        )
        require(
            d["phase_convention"] == "real(H*exp(+i*omega*t)); phase lead",
            key + ": phase sign",
        )
        require(
            cfg.environment.frequency.min
            == cfg.environment.frequency.max
            == d["omega_rad_s"],
            key + ": frequency",
        )
        require(
            cfg.environment.headings.min
            == cfg.environment.headings.max
            == d["heading_deg"],
            key + ": heading",
        )
        require(
            cfg.environment.depth == d["depth_m"]
            and cfg.mechanics.wave_amplitude_m == d["wave_amplitude_m"],
            key + ": wave parameters",
        )
        metrics = verify_pressure_physics(d)
        for name, value in metrics.items():
            require(
                abs(value - v[name]) < 1e-10,
                key + ": physical verification metric " + name,
            )
        require(
            v["coefficients"]
            == dict(
                incident=1.0, diffraction_radiation=1.0, hydrostatic_motion=1.0, body=1
            ),
            key + ": pressure definition",
        )
        expected_static = [
            -d["rho_kg_m3"] * d["gravity_m_s2"] * c[2] / 1000 for c in mesh["centers"]
        ]
        require(
            expected_static == d["mean_static_pressure_kpa"],
            key + ": separate equilibrium pressure",
        )
        wave_folder = ROOT / "examples/animations" / key
        require(
            sha(wave_folder / "field.json") == d["source_wave_field_sha256"],
            key + ": linked wave field",
        )
        wave = load(wave_folder / "field.json")
        for name in [
            "omega_rad_s",
            "heading_deg",
            "wave_amplitude_m",
            "depth_m",
            "rho_kg_m3",
            "gravity_m_s2",
        ]:
            require(d[name] == wave[name], key + ": pressure/wave physical condition")
        motions = load(folder / "motions.json")
        reference = load(wave_folder / "motions.json")
        for dof in core.DOFS:
            raw = core.read_rao(folder / "rao" / (dof + ".rao"))
            require(
                {k: raw[k] for k in motions[dof]} == motions[dof],
                key + ": native motion RAO",
            )
            require(motions[dof] == reference[dof], key + ": synchronized wave motion")
        seen = set()
        with gzip.open(
            folder / "native-pressure-raos.jsonl.gz", "rt", encoding="ascii"
        ) as archive:
            for line in archive:
                record = json.loads(line)
                name, content = record["name"], record["content"]
                require(
                    name in v["native_file_sha256"] and name not in seen,
                    key + ": native record IDs",
                )
                seen.add(name)
                require(
                    hashlib.sha256(content.encode("utf-8")).hexdigest()
                    == v["native_file_sha256"][name],
                    key + ": native record SHA",
                )
                match = re.fullmatch(
                    r"pressure_(following|incident|eulerian)_(\d+)\.rao", name
                )
                require(match is not None, key + ": native record name")
                kind, point = match[1], int(match[2]) - 1
                field = {
                    "following": "following_head",
                    "incident": "incident_head",
                    "eulerian": "eulerian_head",
                }[kind]
                require(
                    0 <= point < (n if kind == "eulerian" else 2 * n),
                    key + ": native point bounds",
                )
                raw = core.read_rao_text(content, name)
                require(
                    raw["omega"] == [d["omega_rad_s"]]
                    and raw["headings"] == [d["heading_deg"]],
                    key + ": native pressure grids",
                )
                require(
                    raw["unit"] in ({"m", "m/m"} if kind == "incident" else {"m/m"}),
                    key + ": native water-column unit",
                )
                xyz_match = re.search(
                    r"Reference point of body 0:\s*\(([^)]+)\)", content
                )
                xyz = (
                    [float(value) for value in xyz_match[1].split()]
                    if xyz_match
                    else []
                )
                require(
                    len(xyz) == 3
                    and max(abs(a - b) for a, b in zip(xyz, d["points"][point][1:]))
                    <= 0.00051,
                    key + ": native pressure coordinates",
                )
                ref = [
                    float(value)
                    for value in raw["metadata"]["REF.PT INCIDENT WAVE"]
                    .strip("() ")
                    .split()
                ]
                require(
                    ref == d["wave_reference_xy_m"], key + ": native phase reference"
                )
                value = cmath.rect(
                    raw["amplitude"][0][0],
                    __import__("math").radians(raw["phase"][0][0]),
                )
                require(
                    abs(value - complex(*d[field][point])) < 1e-12,
                    key + ": native/exported pressure coefficient",
                )
        require(
            seen == set(v["native_file_sha256"]) and len(seen) == 5 * n,
            key + ": complete pressure archive",
        )
        for path in (folder / "native-samples").glob("*.rao"):
            require(
                sha(path) == v["native_file_sha256"][path.name],
                key + ": native sample record",
            )
        render = load(folder / "render.json")
        require(
            render["pressure_colour_unit"] == "kPa"
            and render["wave_colour_unit"] == "m",
            key + ": displayed units",
        )
        require(
            render["pressure_colour_gain"] == render["wave_colour_gain"] == 1,
            key + ": physical colour gain",
        )
        require(
            render["motion_gain"] == render["wave_height_gain"] == 6,
            key + ": observation gain",
        )
        require(
            abs(
                render["pressure_colour_limit_kpa"]
                - metrics["pressure_colour_limit_kpa"]
            )
            < 1e-10,
            key + ": pressure colour limit",
        )
        require(
            render["views"]
            == [
                "body_following_pressure",
                "total_wave_and_motion",
                "scattered_wave_diffraction_and_radiation",
            ],
            key + ": all three requested views",
        )
        gif = ROOT / "docs/assets" / (key + "_coupled.gif")
        require(sha(gif) == entry["gif_sha256"], key + ": synchronized GIF hash")
        with Image.open(gif) as image:
            require(
                image.size == tuple(render["size_px"])
                and image.n_frames == render["frames"],
                key + ": GIF dimensions/frames",
            )
            require(
                image.info.get("loop") == 0 and image.info.get("duration") == 80,
                key + ": GIF timing",
            )
            box = (
                int(image.width * 0.06),
                int(image.height * 0.3),
                int(image.width * 0.29),
                int(image.height * 0.7),
            )
            image.seek(0)
            first = image.convert("RGB").crop(box).tobytes()
            image.seek(image.n_frames // 4)
            quarter = image.convert("RGB").crop(box).tobytes()
            require(first != quarter, key + ": changing pressure/motion in animation")
        panel_total += n
        record_total += len(seen)
    return dict(
        native_pressure_cases=len(index["cases"]),
        wetted_pressure_panels=panel_total,
        native_pressure_records=record_total,
    )


if __name__ == "__main__":
    print(json.dumps(check_pressures(), indent=2))
