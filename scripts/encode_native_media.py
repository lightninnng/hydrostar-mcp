"""Apply scientific captions and encode actual ParaView PNG frames as GIFs."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.workflow import file_hash, save_json

TITLES = [
    "Dynamic surface pressure",
    "Total wave elevation",
    "Scattered wave elevation",
    "Diffraction (fixed body)",
    "Motion-induced radiation",
]
GROUPS = dict(coupled=[0, 1, 2], wave=[1, 2], components=[3, 4])
VARIABLES = ["Pressure", "Total", "Scattered", "Diffraction", "Radiation"]


def viewport_pixel_hashes(paths):
    hashes = {name: [] for name in VARIABLES}
    for path in paths:
        with Image.open(path) as image:
            if image.size != (3600, 680):
                raise ValueError("Unexpected native viewport layout")
            rgb = image.convert("RGB")
            for i, name in enumerate(VARIABLES):
                viewport = rgb.crop((i * 720, 0, (i + 1) * 720, 680))
                hashes[name].append(hashlib.sha256(viewport.tobytes()).hexdigest())
    return hashes


def require_field_variation(hashes, minimum_unique=20):
    for name, values in hashes.items():
        if len(set(values)) < minimum_unique:
            raise ValueError(
                "Native viewport did not refresh across physical phases: " + name
            )


def font(size):
    for name in ("C:/Windows/Fonts/times.ttf", "DejaVuSerif.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    raise RuntimeError("Provide a readable scientific serif font")


def compose(native, condition, frame, indices):
    width, height = 720 * len(indices), 810
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title, sub, small = font(30), font(23), font(21)
    time = frame * condition["period_s"] / condition["frames"]
    draw.text((25, 9), condition["label"], font=title, fill="#172832")
    clock = f"t = {time:.3f} s    t/T = {frame / condition['frames']:.3f}"
    draw.text(
        (width - 25 - draw.textlength(clock, font=sub), 15),
        clock,
        font=sub,
        fill="#34454F",
    )
    line = (
        f"A = {condition['wave_amplitude_m']:.2f} m    "
        f"Heading = {condition['heading_deg']:g} deg    "
        f"Frequency = {condition['omega_rad_s']:g} rad/s    "
        f"Depth = {condition['depth_m']:g} m"
    )
    draw.text((25, 49), line, font=small, fill="#34454F")
    for position, index in enumerate(indices):
        image.paste(
            native.crop((index * 720, 0, (index + 1) * 720, 680)), (position * 720, 105)
        )
        draw.text(
            (position * 720 + 22, 79),
            f"({chr(97 + position)}) " + TITLES[index],
            font=sub,
            fill="#172832",
        )
    note = (
        f"HSPRS / ParaView    Colour values: physical units    "
        f"Wave height x{condition['wave_height_gain']:g}; motion x{condition['motion_gain']:g}    Pressure geometry x1"
    )
    draw.text((25, 782), note, font=font(18), fill="#47565F")
    return image


def encode(key):
    package = ROOT / "examples/visualization/fields" / key
    condition = json.loads((package / "condition.json").read_text(encoding="utf-8"))
    frames = ROOT / "tmp" / ("pv-" + key)
    render = json.loads((frames / "render.json").read_text(encoding="utf-8"))
    count = condition["frames"]
    if render["frames"] != count or render["panels"] != [
        "Pressure",
        "Total",
        "Scattered",
        "Diffraction",
        "Radiation",
    ]:
        raise ValueError("A complete native ParaView sequence is required")
    paths = [frames / f"frame{i:02d}.png" for i in range(count)]
    pixel_hashes = viewport_pixel_hashes(paths)
    require_field_variation(pixel_hashes)
    assets, media = ROOT / "docs/assets", {}
    for name, indices in GROUPS.items():
        images = []
        for i, path in enumerate(paths):
            with Image.open(path) as original:
                if original.size != (3600, 680):
                    raise ValueError("Unexpected ParaView frame geometry")
                images.append(compose(original.convert("RGB"), condition, i, indices))
        stem = key + "-" + name
        images[0].save(assets / (stem + "-frame.png"))
        for index in (10, 20, 30):
            images[index].save(assets / (stem + f"-frame{index:02d}.png"))
        # One cycle-wide palette keeps signed pressure/wave colours stable.
        samples = Image.new("RGB", (images[0].width, images[0].height * 4), "white")
        for j, i in enumerate((0, 10, 20, 30)):
            samples.paste(images[i], (0, j * images[0].height))
        palette = samples.quantize(
            colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
        )
        encoded = [
            im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images
        ]
        duration = round(1000 / condition["playback_fps"])
        destination = assets / (stem + ".gif")
        encoded[0].save(
            destination,
            save_all=True,
            append_images=encoded[1:],
            duration=duration,
            loop=0,
            optimize=False,
            disposal=2,
        )
        with Image.open(destination) as gif:
            if gif.n_frames != count:
                raise ValueError("Incomplete encoded cycle")
        media[name] = dict(
            gif="docs/assets/" + destination.name,
            sha256=file_hash(destination),
            still="docs/assets/" + stem + "-frame.png",
            still_sha256=file_hash(assets / (stem + "-frame.png")),
            width=images[0].width,
            height=images[0].height,
            frames=count,
            duration_ms=duration,
            loop_seconds=count * duration / 1000,
            checkpoints={
                f"docs/assets/{stem}-frame{i:02d}.png": file_hash(
                    assets / (stem + f"-frame{i:02d}.png")
                )
                for i in (10, 20, 30)
            },
        )
        print(key + ": encoded " + name + " from ParaView frames", flush=True)
    record = dict(
        **render,
        status="exported",
        encoder="Pillow " + Image.__version__,
        method="Unchanged native ParaView viewports, scientific text layout and one fixed cycle-wide GIF palette",
        physical_period_s=condition["period_s"],
        playback_fps=condition["playback_fps"],
        note="Playback speed differs from physical time; each frame states t and t/T",
        native_frame_sha256={p.name: file_hash(p) for p in paths},
        native_view_pixel_sha256=pixel_hashes,
        renderer_script_sha256=file_hash(ROOT / "scripts/render_native_views.py"),
        encoder_script_sha256=file_hash(Path(__file__)),
        media=media,
        command=[
            "pvpython",
            "--force-offscreen-rendering",
            "scripts/render_native_views.py",
            "examples/visualization/fields/" + key,
            "--output",
            "tmp/pv-" + key,
        ],
    )
    save_json(package / "render.json", record)
    verification = json.loads(
        (package / "verification.json").read_text(encoding="utf-8")
    )
    verification["files"] = {
        p.relative_to(package).as_posix(): file_hash(p)
        for p in package.rglob("*")
        if p.is_file() and p.name != "verification.json"
    }
    save_json(package / "verification.json", verification)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case", choices=["vessel", "container", "tanker", "platform"], action="append"
    )
    args = parser.parse_args()
    for key in args.case or ["vessel", "container", "tanker", "platform"]:
        encode(key)
