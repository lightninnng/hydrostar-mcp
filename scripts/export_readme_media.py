"""Create compact README previews from the accepted ParaView GIF exports.

Every preview keeps all forty physical phases, their timing, units and legends.
The full-resolution source remains the image's click-through target in README.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
KEYS = ("vessel", "platform", "container", "tanker")
GROUPS = dict(
    coupled=("Pressure", "Total", "Scattered"), components=("Diffraction", "Radiation")
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_variation(path, fields, scale):
    unique = {name: set() for name in fields}
    with Image.open(path) as gif:
        for i in range(gif.n_frames):
            gif.seek(i)
            rgb = gif.convert("RGB")
            for j, name in enumerate(fields):
                # Exclude the changing clock, captions and colour bars.
                box = tuple(
                    round(v * scale) for v in (720 * j + 8, 110, 720 * (j + 1) - 8, 650)
                )
                unique[name].add(hashlib.sha256(rgb.crop(box).tobytes()).hexdigest())
    counts = {name: len(values) for name, values in unique.items()}
    if min(counts.values()) != 40:
        raise ValueError("All forty physical phases must change in every viewport")
    return counts


def export():
    media = []
    for key in KEYS:
        folder = ROOT / "examples/visualization/fields" / key
        render = read(folder / "render.json")
        verification = read(folder / "verification.json")
        if set(verification["gates"].values()) != {"passed"}:
            raise ValueError("Accepted native field data required: " + key)
        for group, fields in GROUPS.items():
            entry = render["media"][group]
            source = ROOT / entry["gif"]
            if digest(source) != entry["sha256"]:
                raise ValueError("Native export changed: " + source.name)
            width = 1200 if group == "coupled" else 1000
            scale = width / entry["width"]
            size = (width, round(entry["height"] * scale))
            frames, durations = [], []
            with Image.open(source) as gif:
                if gif.n_frames != 40 or gif.info.get("loop") != 0:
                    raise ValueError("Complete repeating source cycle required")
                palette = gif.getpalette()
                fixed = Image.new("P", (1, 1))
                fixed.putpalette(palette)
                for i in range(gif.n_frames):
                    gif.seek(i)
                    durations.append(gif.info["duration"])
                    image = gif.convert("RGB").resize(size, Image.Resampling.LANCZOS)
                    frames.append(
                        image.quantize(palette=fixed, dither=Image.Dither.NONE)
                    )
            target = ROOT / "docs/assets" / f"readme-{key}-{group}.gif"
            frames[0].save(
                target,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                disposal=2,
                optimize=True,
            )
            with Image.open(target) as gif:
                if gif.n_frames != 40 or gif.info.get("loop") != 0:
                    raise ValueError("Preview lost a physical phase")
                actual_duration = []
                for i in range(gif.n_frames):
                    gif.seek(i)
                    actual_duration.append(gif.info["duration"])
                if actual_duration != durations:
                    raise ValueError("Preview timing differs from native export")
            variation = pixel_variation(target, fields, scale)
            media.append(
                dict(
                    preview=target.relative_to(ROOT).as_posix(),
                    preview_sha256=digest(target),
                    preview_bytes=target.stat().st_size,
                    width=size[0],
                    height=size[1],
                    source=source.relative_to(ROOT).as_posix(),
                    source_sha256=digest(source),
                    source_bytes=source.stat().st_size,
                    frames=40,
                    duration_ms=durations,
                    unique_physical_viewports=variation,
                )
            )
            print(target.name, f"{target.stat().st_size / 1024**2:.2f} MiB", flush=True)
    record = dict(
        encoder="Pillow " + Image.__version__,
        method="Lanczos resize of accepted ParaView GIFs, original fixed palette, all phases and timing retained",
        units_and_gains="Native legends and captions retained; click through to full resolution",
        script_sha256=digest(Path(__file__)),
        media=media,
    )
    (ROOT / "examples/visualization/readme-media.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )


def check():
    meshes = read(ROOT / "examples/visualization/readme-meshes.json")
    if digest(ROOT / meshes["output"]) != meshes["output_sha256"]:
        raise ValueError("README mesh plate changed")
    if (
        digest(ROOT / "scripts/render_readme_meshes.py")
        != meshes["renderer_script_sha256"]
    ):
        raise ValueError("README mesh renderer changed")
    for case in meshes["cases"]:
        for field in ("source", "acceptance"):
            if digest(ROOT / case[field]) != case[field + "_sha256"]:
                raise ValueError("README mesh acceptance source changed")
    record = read(ROOT / "examples/visualization/readme-media.json")
    if digest(Path(__file__)) != record["script_sha256"]:
        raise ValueError("README encoder changed")
    for item in record["media"]:
        for field in ("preview", "source"):
            if digest(ROOT / item[field]) != item[field + "_sha256"]:
                raise ValueError("README media source changed")
        group = Path(item["preview"]).stem.rsplit("-", 1)[1]
        if (
            pixel_variation(
                ROOT / item["preview"],
                GROUPS[group],
                item["width"] / (2160 if group == "coupled" else 1440),
            )
            != item["unique_physical_viewports"]
        ):
            raise ValueError("README physical pixel check changed")
    expected = {item["preview"] for item in record["media"]}
    for name in ("README.md", "README.en.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        if any(path not in text for path in expected):
            raise ValueError("Bilingual README gallery is incomplete: " + name)
    return dict(
        readme_mesh_views=len(meshes["cases"]),
        readme_dynamic_previews=len(record["media"]),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing exports and bilingual coverage",
    )
    if parser.parse_args().check:
        print(json.dumps(check(), indent=2))
    else:
        export()
