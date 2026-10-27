"""Verify published harmonic fields against every archived native field-point RAO."""

from __future__ import annotations

import cmath
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check_wavefields():
    from hydrostar_mcp import core
    from hydrostar_mcp.animation import inside_or_near, wave_number
    from hydrostar_mcp.models import CaseConfig
    from PIL import Image

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    base = ROOT / "examples/animations"
    index = load(base / "index.json")
    expected = {"container_kcs_style", "tanker_kvlcc2_style", "semisub_oc4_style"}
    require(
        {c["form_id"] for c in index["cases"]} == expected,
        "Incomplete native animation cases",
    )
    count = 0
    for entry in index["cases"]:
        key = entry["form_id"]
        folder = base / key
        verification = load(folder / "verification.json")
        require(
            sha(folder / "verification.json") == entry["verification_sha256"],
            key + ": verification hash",
        )
        require(
            set(verification["quality_gates"].values()) == {"passed"},
            key + ": numerical gates",
        )
        require(
            set(verification["field_gates"].values()) == {"passed"},
            key + ": field gates",
        )
        require(
            all(s["ok"] and s["rc"] == 0 for s in verification["field_steps"]),
            key + ": native steps",
        )
        actual = {
            p.relative_to(folder).as_posix()
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        }
        require(actual == set(verification["files"]), key + ": unindexed field files")
        for name, expected_hash in verification["files"].items():
            path = (folder / name).resolve()
            require(path.is_relative_to(folder.resolve()), key + ": unsafe file path")
            require(sha(path) == expected_hash, key + ": file hash " + name)
        cfg = CaseConfig.model_validate(load(folder / "config.json"))
        field = load(folder / "field.json")
        grid = field["grid"]
        omega, heading = field["omega_rad_s"], field["heading_deg"]
        require(
            cfg.environment.frequency.min == cfg.environment.frequency.max == omega,
            key + ": frequency",
        )
        require(
            cfg.environment.headings.min == cfg.environment.headings.max == heading,
            key + ": heading",
        )
        require(cfg.environment.depth == field["depth_m"], key + ": water depth")
        require(
            field["phase_convention"] == "real(H*exp(+i*omega*t)); phase lead",
            key + ": phase convention",
        )
        require(
            verification["coefficients"]
            == {
                "incident": 1.0,
                "diffraction_radiation": 1.0,
                "hydrostatic_motion": 0.0,
            },
            key + ": absolute field definition",
        )
        points = grid["points"]
        require(len(points) == verification["point_count"], key + ": point count")
        require(
            len(set(tuple(i) for i in grid["indices"])) == len(points),
            key + ": duplicate grid index",
        )
        require(
            len(field["total"]) == len(field["incident"]) == len(points),
            key + ": array sizes",
        )
        require(
            all(
                math.isfinite(v)
                for kind in ("total", "incident")
                for pair in field[kind]
                for v in pair
            ),
            key + ": finite complex fields",
        )
        k = wave_number(omega, field["depth_m"], field["gravity_m_s2"])
        beta = math.radians(heading)
        ref = field["wave_reference_xy_m"]
        maximum = 0.0
        for n, ((identifier, x, y, z), (iy, ix)) in enumerate(
            zip(points, grid["indices"])
        ):
            require(
                identifier == n + 1 and abs(z) < 1e-10, key + ": point IDs/free surface"
            )
            require(
                grid["x"][ix] == x and grid["y"][iy] == y, key + ": coordinates/grid"
            )
            require(
                not any(
                    inside_or_near((x, y), p, grid["clearance_m"])
                    for p in grid["waterlines"]
                ),
                key + ": interior/near-waterline point",
            )
            expected_value = cmath.exp(
                -1j
                * k
                * ((x - ref[0]) * math.cos(beta) + (y - ref[1]) * math.sin(beta))
            )
            maximum = max(maximum, abs(complex(*field["incident"][n]) - expected_value))
        require(maximum < 2e-5, key + ": analytical complex phase")
        require(
            abs(maximum - verification["incident_complex_max_error"]) < 1e-12,
            key + ": reported incident error",
        )
        seen = set()
        with gzip.open(
            folder / "native-field-raos.jsonl.gz", "rt", encoding="ascii"
        ) as stream:
            for line in stream:
                record = json.loads(line)
                name = record["name"]
                content = record["content"]
                require(
                    name not in seen and name in verification["native_file_sha256"],
                    key + ": native record name",
                )
                seen.add(name)
                require(
                    hashlib.sha256(content.encode("utf-8")).hexdigest()
                    == verification["native_file_sha256"][name],
                    key + ": raw native hash",
                )
                raw = core.read_rao_text(content, name)
                kind = "incident" if name.startswith("field_incident_") else "total"
                point_index = int(name.removesuffix(".rao").rsplit("_", 1)[1]) - 1
                require(
                    raw["omega"] == [omega] and raw["headings"] == [heading],
                    key + ": native grids",
                )
                require(
                    raw["unit"] in ({"m/m"} if kind == "total" else {"m", "m/m"}),
                    key + ": native unit",
                )
                value = cmath.rect(
                    raw["amplitude"][0][0], math.radians(raw["phase"][0][0])
                )
                require(
                    abs(value - complex(*field[kind][point_index])) < 1e-12,
                    key + ": raw/export complex value",
                )
        require(
            seen == set(verification["native_file_sha256"])
            and len(seen) == 2 * len(points),
            key + ": native record completeness",
        )
        gif = ROOT / "docs/assets" / (key + "_wave.gif")
        require(sha(gif) == entry["gif_sha256"], key + ": GIF hash")
        settings = load(folder / "render.json")
        with Image.open(gif) as image:
            require(
                image.n_frames == settings["frames"]
                and image.size == tuple(settings["size_px"]),
                key + ": GIF frame count/size",
            )
            require(
                image.info.get("loop") == 0
                and image.info.get("duration") == settings["duration_ms"],
                key + ": GIF loop/timing",
            )
            image.seek(0)
            first = (
                image.convert("RGB")
                .crop(
                    (
                        int(image.width * 0.62),
                        int(image.height * 0.3),
                        int(image.width * 0.9),
                        int(image.height * 0.65),
                    )
                )
                .tobytes()
            )
            image.seek(image.n_frames // 4)
            quarter = (
                image.convert("RGB")
                .crop(
                    (
                        int(image.width * 0.62),
                        int(image.height * 0.3),
                        int(image.width * 0.9),
                        int(image.height * 0.65),
                    )
                )
                .tobytes()
            )
            require(first != quarter, key + ": GIF must contain actual changing frames")
        count += len(points)
    return dict(
        native_wavefield_cases=len(index["cases"]),
        exterior_field_points=count,
        native_field_records=count * 2,
    )


if __name__ == "__main__":
    print(json.dumps(check_wavefields(), indent=2))
