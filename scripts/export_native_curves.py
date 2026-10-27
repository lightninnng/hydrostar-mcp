"""Batch-export scientific curves using the HydroStar manual's Gnuplot route."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.workflow import file_hash, save_json

CASES = {
    "container": ("examples/results/container_kcs_style", "Container hull"),
    "tanker": ("examples/results/tanker_kvlcc2_style", "Full-form tanker"),
    "platform": ("examples/results/semisub_oc4_style", "Column semisubmersible"),
    "vessel": ("examples/vessel", "Curved station hull"),
}
COLOURS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#4C5966"]


def gp_string(value):
    return "'" + str(value).replace("\\", "/").replace("'", "\\'") + "'"


def heading_tag(heading):
    return f"{heading:g}".replace(".", "-")


def plot_commands(title, headings, native, kind, font_scale=1.0):
    lines = [
        "reset",
        "set encoding utf8",
        "set border linewidth 0.8 linecolor rgb '#34424E'",
        "set tics out nomirror scale 0.4",
        "set grid back linewidth 0.5 linecolor rgb '#E0E5E9'",
        "set format x '%g'",
        "set format y '%.3g'",
        "set key off",
        "set samples 100",
        "wrap(x)=x-360.0*floor((x+180.0)/360.0)",
    ]
    multi = len(headings) > 1
    condition = "Selected headings" if multi else f"Heading {headings[0]:g} deg"
    lines.append(
        "set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title "
        + gp_string(title + ": " + condition)
        + f" font 'Times New Roman,{18 * font_scale:g}'"
    )
    for i, dof in enumerate(core.DOFS):
        d = native[dof]
        unit = d["unit"] if kind == "amplitude" else "deg"
        lines.extend(
            [
                "set title "
                + gp_string(f"({chr(97 + i)}) {dof.capitalize()}")
                + f" offset 0,-0.1 font 'Times New Roman,{14 * font_scale:g}'",
                "set xlabel 'Wave frequency (rad/s)' offset 0,0.35",
                "set ylabel "
                + gp_string(
                    ("RAO" if kind == "amplitude" else "Phase") + " (" + unit + ")"
                )
                + " offset 0.5,0",
                "set xrange [" + str(d["omega"][0]) + ":" + str(d["omega"][-1]) + "]",
                "set yrange [0:*]" if kind == "amplitude" else "set yrange [-180:180]",
            ]
        )
        if multi and i == 4:
            lines.append(
                f"set key at screen 0.5,0.045 center horizontal maxrows 1 font 'Times New Roman,{11 * font_scale:g}' samplen 2.2 spacing 1"
            )
        else:
            lines.append("set key off")
        plots = []
        for j, heading in enumerate(headings):
            col = 2 + d["headings"].index(heading)
            using = str(col)
            style = "with lines linewidth 1.7"
            if kind == "phase":
                col += len(d["headings"])
                using = f"(wrap(column({col})))"
                style = "with points pointtype 7 pointsize 0.32"
            plots.append(
                gp_string("data/" + dof + ".rao")
                + f" using 1:{using} {style} dashtype {1 + j % 3} linecolor rgb "
                + gp_string(COLOURS[j % len(COLOURS)])
                + " title "
                + gp_string(f"{heading:g} deg")
            )
        lines.append("plot " + (", " + chr(92) + "\n").join(plots))
    lines.append("unset multiplot")
    return lines


def export_case(key, executable):
    relative, title = CASES[key]
    source = ROOT / relative
    config = json.loads((source / "config.json").read_text(encoding="utf-8"))
    summary_path = source / ("summary.json" if key != "vessel" else "verification.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if set(summary["quality_gates"].values()) != {"passed"}:
        raise ValueError("Accepted native calculation required: " + key)
    folder = ROOT / "examples/visualization/curves" / key
    (folder / "data").mkdir(parents=True, exist_ok=True)
    assets = ROOT / "docs/assets"
    native = {}
    for dof in core.DOFS:
        original = source / "rao" / (dof + ".rao")
        native[dof] = core.read_rao(original)
        shutil.copyfile(original, folder / "data" / original.name)
    heads = native["heave"]["headings"]
    script, outputs = [], {}
    for heading in heads:
        for kind in ("amplitude", "phase"):
            filename = f"{key}-{kind}-{heading_tag(heading)}.svg"
            # Each reset precedes the terminal/output settings in this batch.
            commands = plot_commands(title, [heading], native, kind)
            terminal = "set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'"
            commands[1:1] = [
                terminal,
                "set output " + gp_string(os.path.relpath(assets / filename, folder)),
            ]
            script.extend(commands + ["unset output"])
            outputs[filename] = dict(heading_deg=heading, mode=kind)
    selected = [h for h in (0.0, 60.0, 90.0, 120.0, 180.0) if h in heads]
    for ext, terminal in [
        (
            "png",
            "set terminal pngcairo size 2400,1540 enhanced font 'Times New Roman,23'",
        ),
        (
            "pdf",
            "set terminal pdfcairo size 12in,7.7in enhanced font 'Times New Roman,12'",
        ),
    ]:
        filename = key + "-response." + ext
        commands = plot_commands(
            title, selected, native, "amplitude", 1.65 if ext == "png" else 1.0
        )
        commands[1:1] = [
            terminal,
            "set output " + gp_string(os.path.relpath(assets / filename, folder)),
        ]
        script.extend(commands + ["unset output"])
        outputs[filename] = dict(headings_deg=selected, mode="amplitude")
    batch = folder / "curves.gp"
    batch.write_text("\n".join(script) + "\n", encoding="utf-8")
    env = dict(os.environ)
    env["PATH"] = str(executable.parent) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [str(executable), batch.name],
        cwd=folder,
        env=env,
        capture_output=True,
        timeout=180,
    )
    (folder / "export.log").write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace")[-1500:])
    version = subprocess.check_output(
        [str(executable), "--version"], env=env, text=True
    ).strip()
    for name, item in outputs.items():
        path = assets / name
        if not path.is_file() or path.stat().st_size < 1000:
            raise ValueError("Missing command export: " + name)
        item["sha256"] = file_hash(path)
    record = dict(
        schema="hydrostar-native-curve-export-1",
        renderer=version,
        workflow="HydroStar manual Gnuplot plotting route with batch terminal/output settings",
        status="exported",
        source=relative,
        native_summary_sha256=file_hash(summary_path),
        project=config["project"],
        display_name=title,
        frequency_count=len(native["heave"]["omega"]),
        heading_count=len(heads),
        phase_display="Modulo 360 in [-180,180); native samples shown as points without lines across phase wraps",
        figures=outputs,
        command=["gnuplot", "curves.gp"],
        files={
            p.relative_to(folder).as_posix(): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        },
    )
    save_json(folder / "verification.json", record)
    print(
        key + ": " + str(len(outputs)) + " command-exported scientific figures",
        flush=True,
    )
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gnuplot", default=os.environ.get("GNUPLOT_EXE") or shutil.which("gnuplot")
    )
    parser.add_argument("--case", choices=list(CASES), action="append")
    args = parser.parse_args()
    if not args.gnuplot:
        parser.error(
            "Provide --gnuplot or GNUPLOT_EXE for the installed command renderer"
        )
    for key in args.case or CASES:
        export_case(key, Path(args.gnuplot).resolve())


if __name__ == "__main__":
    main()
