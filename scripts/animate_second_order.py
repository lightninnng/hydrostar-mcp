"""Export phase-resolved native difference-QTF coefficients through Gnuplot SVG.

These are load-coefficient harmonics. Bichromatic amplitude-pair assembly,
second-order surface pressure and slow-drift motion are separate calculations.
"""

import argparse
import cmath
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp.second_order import harmonic_value
from hydrostar_mcp.workflow import file_hash, save_json
from scripts.export_native_curves import gp_string
from scripts.export_second_order import (
    COMPONENTS,
    PACKAGE,
    convert_native_svg,
    read,
    require,
    review,
)

COUNT = 80
DURATION_MS = 100
WIDTH, HEIGHT = 1800, 1152
MARGINS = (0.07, 0.90, 0.19, 0.82)
SPACING = (0.10, 0.21)
KINDS = ("map", "harmonics")


def plot_boxes(kind):
    left, right, bottom, top = MARGINS
    gapx, gapy = SPACING
    width = (right - left - 2 * gapx) / 3
    height = (top - bottom - gapy) / 2
    result = []
    for i in range(6):
        x = left + (i % 3) * (width + gapx)
        y = top - (i // 3) * (height + gapy) - height
        # Exclude clocks, captions, legends and colour bars from variation checks.
        result.append(
            [
                round(x * WIDTH) + 3,
                round((1 - y - height) * HEIGHT) + 3,
                round((x + width) * WIDTH) - 3,
                round((1 - y) * HEIGHT) - 3,
            ]
        )
    return result


def coefficient_plan():
    evaluated = review(PACKAGE, portable=True)
    data = evaluated["loads"]
    axes = data["fx"]
    omega, differences = axes["omega1_rad_s"], axes["difference_rad_s"]
    positive = [v for v in differences if v > 0]
    base = min(positive)
    selection = dict(omega1_rad_s=0.8, omega2_rad_s=0.9, difference_rad_s=0.1)
    iw, jd = (
        omega.index(selection["omega1_rad_s"]),
        differences.index(selection["difference_rad_s"]),
    )
    mask = evaluated["mask"]
    require(mask[iw][jd], "Selected native frequency pair must be calculated")
    times = dict(
        map=[i * 2 * math.pi / base / COUNT for i in range(COUNT)],
        harmonics=[
            i * 2 * math.pi / selection["difference_rad_s"] / COUNT
            for i in range(COUNT)
        ],
    )
    maximum_mean = maximum_rms = maximum_closure = 0.0
    peaks, selected, selected_values = {}, {}, {}
    for name in COMPONENTS:
        values = data[name]["values"][0]
        peaks[name] = (
            max(
                abs(complex(*pair))
                for row, valid in zip(values, mask)
                for pair, ok in zip(row, valid)
                if ok
            )
            / 1000
        )
        selected[name] = values[iw][jd]
        selected_values[name] = [
            harmonic_value(*selected[name], selection["difference_rad_s"], t) / 1000
            for t in times["harmonics"]
        ]
        for i, row in enumerate(mask):
            for j, ok in enumerate(row):
                if not ok:
                    continue
                real, imaginary = values[i][j]
                difference = differences[j]
                series = [
                    harmonic_value(real, imaginary, difference, t) for t in times["map"]
                ]
                scale = max(1, abs(complex(real, imaginary)))
                expected_mean = real if difference == 0 else 0
                maximum_mean = max(
                    maximum_mean, abs(sum(series) / COUNT - expected_mean) / scale
                )
                if difference > 0:
                    expected_rms = abs(complex(real, imaginary)) / math.sqrt(2)
                    maximum_rms = max(
                        maximum_rms,
                        abs(
                            math.sqrt(sum(v * v for v in series) / COUNT) - expected_rms
                        )
                        / scale,
                    )
                closure = harmonic_value(
                    real, imaginary, difference, 2 * math.pi / base
                )
                maximum_closure = max(maximum_closure, abs(closure - real) / scale)
        # Independent phasor representation checks the imaginary sign.
        for t, value in zip(times["harmonics"], selected_values[name]):
            expected = (
                complex(*selected[name])
                * cmath.exp(1j * selection["difference_rad_s"] * t)
            ).real / 1000
            require(
                abs(value - expected) <= 1e-10 * max(1, abs(expected)),
                "Native coefficient harmonic phase differs",
            )
    require(
        max(maximum_mean, maximum_rms, maximum_closure) < 1e-12,
        "Harmonic mean, RMS or periodic closure gate",
    )
    return dict(
        schema="hydrostar-qtf-harmonic-animation-1",
        scope="Phase-resolved normalized load coefficients from the native complex QTF; positive-time harmonic basis",
        formula="q(t)=Re[Q exp(i*Delta*t)]=Qr*cos(Delta*t)-Qi*sin(Delta*t)",
        normalization="Coefficient units retained; actual bichromatic wave-amplitude and ordered-pair assembly is separate",
        force_unit="kN/m^2",
        moment_unit="kN m/m^2",
        coefficient_gain=1,
        heading_deg=60,
        depth_m=200,
        omega1_rad_s=omega,
        difference_rad_s=differences,
        valid_pair_mask=mask,
        valid_pairs=36,
        selection=selection,
        selected_complex_native=selected,
        selected_values_scaled=selected_values,
        fixed_colour_limits={name: [-peaks[name], peaks[name]] for name in COMPONENTS},
        frames=COUNT,
        frame_duration_ms=DURATION_MS,
        playback_fps=1000 / DURATION_MS,
        times_s=times,
        periods_s=dict(
            map=2 * math.pi / base,
            harmonics=2 * math.pi / selection["difference_rad_s"],
        ),
        numerical_validation=dict(
            max_mean_error_relative=maximum_mean,
            max_rms_error_relative=maximum_rms,
            max_periodic_closure_relative=maximum_closure,
        ),
        phase_reference="HstarManual section 2.2, PDF page 30: positive-time phase-lead convention from v7.00 onward; reconstruction basis explicitly defined here",
        native_viewer_route="StarViewer supports QTF views; HstarManual documents the Gnuplot companion path. These coefficient animations use that native-data plotting route with explicit phase reconstruction.",
        method_boundary="These scalar load-coefficient maps use frequency axes. Surface pressure, spatial wave fields and slow-drift displacement require their own native solutions.",
        yaw_scope="Mz remains a convergence-study component (23.374% own-peak exterior-grid difference)",
        sources={
            f"rao/qtf_{name}.qtf": file_hash(PACKAGE / f"rao/qtf_{name}.qtf")
            for name in COMPONENTS
        },
    )


def gnuplot_script(kind, plan):
    period = plan["periods_s"][kind]
    title = (
        "Difference-frequency QTF: phase-resolved coefficients"
        if kind == "map"
        else "Selected-pair QTF: normalized load harmonics"
    )
    condition = (
        "Heading 60 deg; depth 200 m; q(t) = Re[Q exp(i Delta t)]; coefficient gain 1x"
    )
    if kind == "harmonics":
        pair = plan["selection"]
        condition = f"ω1 = {pair['omega1_rad_s']:.2f}, ω2 = {pair['omega2_rad_s']:.2f}, Δω = {pair['difference_rad_s']:.2f} rad/s; heading 60 deg; depth 200 m; gain 1x"
    lines = [
        "reset",
        "set encoding utf8",
        "if (!exists('OUTDIR')) OUTDIR='frames'",
        "set border linewidth 0.8 linecolor rgb '#34424E'",
        "set tics out nomirror",
        "set format y '%.2g'",
        "set format cb '%.2g'",
        "set key off",
        "set style fill solid 1.0 border rgb '#dce3e7'",
        "set palette defined (-1 '#2166ac',0 '#f7f7f7',1 '#b2182b')",
        f"N={COUNT}",
        f"T={period:.16g}",
        "do for [f=0:N-1] {",
        "t=f*T/N",
        f"set terminal svg size {WIDTH},{HEIGHT} noenhanced font 'Times New Roman,20'",
        f"set output sprintf('%s/{kind}-%03d.svg',OUTDIR,f)",
        f"set label 900 {gp_string(condition)} at screen 0.5,0.93 center font 'Times New Roman,20'",
        "set label 901 sprintf('Physical t = %.2f s; t/T = %.3f; T = %.3f s',t,t/T,T) at screen 0.5,0.885 center font 'Times New Roman,21'",
        "set label 902 'Native HydroStar QTF / Gnuplot; Mz: convergence study' at screen 0.5,0.035 center font 'Times New Roman,19'",
        "set multiplot layout 2,3 rowsfirst margins 0.07,0.90,0.19,0.82 spacing 0.10,0.21 title "
        + gp_string(title)
        + " font 'Times New Roman,27'",
    ]
    selected = plan["selection"]
    for i, name in enumerate(COMPONENTS):
        unit = "kN/m²" if name[0] == "f" else "kN m/m²"
        label = name[0].upper() + name[1] + (" (research)" if name == "mz" else "")
        lines.extend(
            [
                "set title " + gp_string(f"({chr(97 + i)}) {label} ({unit})"),
                "unset arrow",
            ]
        )
        if kind == "map":
            width = (MARGINS[1] - MARGINS[0] - 2 * SPACING[0]) / 3
            height = (MARGINS[3] - MARGINS[2] - SPACING[1]) / 2
            x = MARGINS[0] + (i % 3) * (width + SPACING[0]) + width + 0.009
            y = MARGINS[3] - (i // 3) * (height + SPACING[1]) - height
            limit = plan["fixed_colour_limits"][name][1]
            lines.extend(
                [
                    "unset grid",
                    "set xlabel 'Wave frequency ω1 (rad/s)'",
                    "set ylabel 'Δω (rad/s)'" if i % 3 == 0 else "set ylabel ''",
                    "set xrange [0.475:1.125]",
                    "set yrange [-0.025:0.125]",
                    "set xtics (0.5,0.7,0.9,1.1)",
                    "set ytics (0,0.05,0.10)",
                    "set format cb '%.0f'" if limit >= 10 else "set format cb '%.1f'",
                    f"set cbrange [{-limit:.12g}:{limit:.12g}]",
                    f"set cbtics ({-limit:.12g},0,{limit:.12g})",
                    f"set colorbox vertical user origin {x:.6f},{y:.6f} size 0.009,{height:.6f}",
                ]
            )
            curves = []
            for j, difference in enumerate(plan["difference_rad_s"]):
                col = 2 + 2 * j
                value = f"(column({col})*cos({difference:g}*t)-column({col + 1})*sin({difference:g}*t))/1000"
                curves.append(
                    gp_string(f"rao/qtf_{name}.qtf")
                    + f" using (($1>={0.5 - 1e-6:.6f} && $1<={1.1 - difference + 1e-6:.6f}) ? $1 : 1/0):({difference:g}):($1-0.025):($1+0.025):({difference - 0.025:g}):({difference + 0.025:g}):({value}) with boxxyerrorbars fillcolor palette notitle"
                )
            lines.append("plot " + (", " + chr(92) + "\n").join(curves))
        else:
            real, imaginary = plan["selected_complex_native"][name]
            d = selected["difference_rad_s"]
            limit = abs(complex(real, imaginary)) / 1000 * 1.16
            lines.extend(
                [
                    "unset colorbox",
                    "set grid back linewidth 0.5 linecolor rgb '#e0e5e9'",
                    "set xlabel 'Physical time (s)'",
                    "set ylabel 'Harmonic coefficient'",
                    f"set xrange [{-0.02 * period:.9g}:{1.02 * period:.9g}]",
                    f"set yrange [{-limit:.12g}:{limit:.12g}]",
                    "set xtics autofreq",
                    "set ytics autofreq",
                    "set samples 401",
                    f"h(x)=({real:.16g}*cos({d:g}*x)-{imaginary:.16g}*sin({d:g}*x))/1000",
                    f"set arrow 1 from t,{-limit:.12g} to t,{limit:.12g} nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'",
                    "plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle",
                ]
            )
        if i == 0:
            lines.extend(["unset label 900", "unset label 901", "unset label 902"])
    lines += [
        "unset multiplot",
        "unset output",
        "unset label 900",
        "unset label 901",
        "unset label 902",
        "}",
    ]
    return "\n".join(lines) + "\n"


def variation(path, boxes, expected_rgb=None):
    hashes = [set() for _ in boxes]
    with Image.open(path) as gif:
        require(gif.n_frames == COUNT, "Every harmonic phase must be retained")
        require(gif.size == (WIDTH, HEIGHT), "Harmonic GIF dimensions")
        for i in range(gif.n_frames):
            gif.seek(i)
            require(gif.info.get("duration") == DURATION_MS, "Harmonic GIF timing")
            rgb = gif.convert("RGB")
            if expected_rgb is not None:
                require(
                    hashlib.sha256(rgb.tobytes()).hexdigest() == expected_rgb[i],
                    "GIF palette pixels differ from their native frames",
                )
            for box, unique in zip(boxes, hashes):
                unique.add(hashlib.sha256(rgb.crop(box).tobytes()).hexdigest())
    counts = [len(x) for x in hashes]
    require(
        min(counts) >= COUNT // 2,
        "Every load panel must vary independently of the clock",
    )
    return counts


def same_values(actual, expected):
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(same_values(actual[k], v) for k, v in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(same_values(a, b) for a, b in zip(actual, expected))
        )
    if isinstance(expected, float):
        return isinstance(actual, (int, float)) and math.isclose(
            actual, expected, rel_tol=1e-12, abs_tol=1e-12
        )
    return actual == expected


def check_animations(*, require_visual=True):
    record = read(PACKAGE / "animation.json")
    require(record["schema"] == "hydrostar-qtf-harmonic-animation-1", "Harmonic schema")
    if require_visual:
        require(
            record["visual_review"] == "verified",
            "Harmonic media need actual visual review",
        )
    require(
        record["generator_script_sha256"] == file_hash(Path(__file__)),
        "Harmonic generator changed",
    )
    require(
        record["harmonic_module_sha256"]
        == file_hash(ROOT / "hydrostar_mcp/second_order.py"),
        "Harmonic reconstruction source changed",
    )
    current = coefficient_plan()
    for key in (
        "sources",
        "selection",
        "selected_complex_native",
        "selected_values_scaled",
        "valid_pair_mask",
        "times_s",
        "fixed_colour_limits",
        "frames",
        "periods_s",
        "formula",
        "force_unit",
        "moment_unit",
        "coefficient_gain",
    ):
        require(
            same_values(record[key], current[key]),
            "Harmonic native source or phase data changed: " + key,
        )
    for name, expected in record["plot_scripts"].items():
        require(
            file_hash(PACKAGE / name) == expected, "Harmonic native plot script changed"
        )
    for kind, item in record["media"].items():
        path = ROOT / item["gif"]
        require(file_hash(path) == item["sha256"], "Harmonic GIF changed")
        require(
            file_hash(ROOT / item["still"]) == item["still_sha256"],
            "Harmonic still changed",
        )
        require(
            variation(path, plot_boxes(kind), item["decoded_frame_rgb_sha256"])
            == item["panel_unique_phases"],
            "Harmonic field variation changed",
        )
    return dict(
        second_order_gifs=2,
        second_order_animation_phases=COUNT,
        yaw_animation_scope="convergence_study",
    )


def export(gnuplot):
    plan = coefficient_plan()
    work = ROOT / "output/validation/second-order/animation"
    work.mkdir(parents=True, exist_ok=True)
    native = work / "native"
    native.mkdir(exist_ok=True)
    env = dict(
        os.environ, PATH=str(gnuplot.parent) + os.pathsep + os.environ.get("PATH", "")
    )
    scripts = {}
    for kind in KINDS:
        path = PACKAGE / "plots" / f"animate_{kind}.gp"
        path.write_text(gnuplot_script(kind, plan), encoding="utf-8", newline="\n")
        scripts[path.relative_to(PACKAGE).as_posix()] = file_hash(path)
        command = [
            str(gnuplot),
            "-e",
            "OUTDIR=" + gp_string(os.path.relpath(native, PACKAGE)),
            path.relative_to(PACKAGE).as_posix(),
        ]
        result = subprocess.run(
            command, cwd=PACKAGE, env=env, capture_output=True, timeout=180
        )
        (work / (kind + "-gnuplot.log")).write_bytes(result.stdout + result.stderr)
        require(
            result.returncode == 0, result.stderr.decode("utf-8", "replace")[-1500:]
        )
    media = {}
    conversion = None
    for kind in KINDS:
        frames = []
        for i in range(COUNT):
            path = native / f"{kind}-{i:03d}.svg"
            require(path.exists(), "Native Gnuplot frame missing")
            conversion = convert_native_svg(path)
            frame = (
                Image.open(path.with_suffix(".png"))
                .convert("RGB")
                .resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            )
            frames.append(frame)
            if i % 20 == 0:
                print(f"{kind}: converted {i + 1}/{COUNT} native phases", flush=True)
        still = ROOT / "docs/assets" / f"platform-second-order-{kind}-frame.png"
        frames[0].save(still)
        palette = frames[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        indexed = [
            im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames
        ]
        expected_rgb = [
            hashlib.sha256(im.convert("RGB").tobytes()).hexdigest() for im in indexed
        ]
        target = ROOT / "docs/assets" / f"platform-second-order-{kind}.gif"
        indexed[0].save(
            target,
            save_all=True,
            append_images=indexed[1:],
            duration=DURATION_MS,
            loop=0,
            disposal=1,
            optimize=True,
        )
        media[kind] = dict(
            gif=target.relative_to(ROOT).as_posix(),
            sha256=file_hash(target),
            still=still.relative_to(ROOT).as_posix(),
            still_sha256=file_hash(still),
            panel_unique_phases=variation(target, plot_boxes(kind), expected_rgb),
            decoded_frame_rgb_sha256=expected_rgb,
        )
    plan.update(
        visual_review="pending",
        media=media,
        plot_scripts=scripts,
        generator_script_sha256=file_hash(Path(__file__)),
        harmonic_module_sha256=file_hash(ROOT / "hydrostar_mcp/second_order.py"),
        renderer=subprocess.check_output(
            [str(gnuplot), "--version"], env=env, text=True
        ).strip(),
        conversion=conversion,
        encoding=dict(
            global_palette_colours=256,
            dither="none",
            loop=0,
            disposal=1,
            optimize=True,
            decoded_pixels_match_palette_frames=True,
            frame_duration_ms=DURATION_MS,
        ),
        native_frame_sha256={
            path.name: file_hash(path) for path in native.glob("*.svg")
        },
        frame_source="Gnuplot native SVG frames, converted to PDF/PNG and encoded without changing coefficients",
    )
    save_json(PACKAGE / "animation.json", plan)
    print("Exported two native-QTF coefficient animations", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gnuplot", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--accept-review",
        action="store_true",
        help="Record actual inspection of native frames and both final GIFs",
    )
    args = parser.parse_args()
    if args.accept_review:
        check_animations(require_visual=False)
        record = read(PACKAGE / "animation.json")
        record["visual_review"] = "verified"
        save_json(PACKAGE / "animation.json", record)
        print(json.dumps(check_animations(), indent=2))
    elif args.check:
        print(json.dumps(check_animations(), indent=2))
    else:
        require(args.gnuplot is not None, "Provide --gnuplot for native rendering")
        export(args.gnuplot.resolve())
