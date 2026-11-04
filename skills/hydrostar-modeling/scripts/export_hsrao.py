"""Export original HSRAO tables/macros with Gnuplot file terminals; stdlib only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gp_string(value):
    return "'" + str(value).replace("\\", "/").replace("'", "\\'") + "'"


def read_table(path):
    """Read the original amplitude/phase columns, retaining native units."""
    heads, omega, amplitude, phase, unit = [], [], [], [], None
    count, ended = None, False
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if re.match(r"#HEADING(?:\s|$)", line, re.I):
                if heads or omega:
                    raise ValueError("Repeated HEADING record")
                heads = [float(v) for v in line.split()[1:]]
            elif line.upper().startswith("#NBHEADING"):
                count = int(line.split()[-1])
            elif re.match(r"#UNIT\s*:", line, re.I):
                unit = line.split(":", 1)[1].strip()
            elif line.upper().startswith("#ENDFILE"):
                ended = True
            continue
        values = [float(v.replace("D", "E").replace("d", "e")) for v in line.split()]
        if ended or not heads or len(values) != 1 + 2 * len(heads):
            raise ValueError("Incomplete native amplitude/phase row")
        if not all(math.isfinite(v) for v in values) or values[0] <= 0:
            raise ValueError("Invalid native frequency/value")
        if omega and values[0] <= omega[-1]:
            raise ValueError("Native frequencies must increase")
        if min(values[1 : 1 + len(heads)]) < 0:
            raise ValueError("Negative native amplitude")
        omega.append(values[0])
        amplitude.append(values[1 : 1 + len(heads)])
        phase.append(values[1 + len(heads) :])
    if (
        not ended
        or not omega
        or not unit
        or len(heads) != len(set(heads))
        or not all(math.isfinite(h) for h in heads)
    ):
        raise ValueError("Missing native data/end marker/unit or duplicate heading")
    if count is not None and count != len(heads):
        raise ValueError("NBHEADING differs from native columns")
    return dict(
        omega=omega, headings=heads, amplitude=amplitude, phase=phase, unit=unit
    )


def parse_macro(path):
    """Parse the inspected HSRAO grammar; never execute a supplied macro."""
    blocks = re.split(
        r"(?m)^set terminal windows\s*$", Path(path).read_text(encoding="utf-8-sig")
    )
    result = {}
    row_pattern = re.compile(
        r"'rao/(?P<file>[A-Za-z0-9_.-]+)'\s+u 1:\s*(?P<column>\d+)\s+t '\s*(?P<heading>[-+\d.]+)\s*'\s+w lp\s*(?:,\\)?"
    )
    for block in blocks:
        if not block.strip():
            continue
        title = re.search(r"(?m)^set title '([A-Za-z0-9_.-]+)'\s*$", block)
        if not title:
            raise ValueError("Unrecognized HSRAO macro title")
        name = title[1]
        entries = []
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line in ("set grid", "plot \\", "pause -1"):
                continue
            if re.fullmatch(r"set (?:title|xlabel|ylabel) '[^'\r\n]*'", line):
                continue
            match = row_pattern.fullmatch(line)
            if not match or match["file"] != name:
                raise ValueError("Unsupported macro statement: " + line)
            entries.append(
                dict(heading=float(match["heading"]), column=int(match["column"]))
            )
        if not entries or name in result:
            raise ValueError("Missing or duplicate native plot series")
        result[name] = entries
    if not result:
        raise ValueError("Empty native macro")
    return result


def native_column(macro, filename, table, heading):
    """Validate macro columns, and use header columns for other stored headings."""
    if heading not in table["headings"]:
        raise ValueError(f"Uncomputed heading {heading}: {filename}")
    if macro and filename not in macro:
        raise ValueError("File is absent from supplied native macro: " + filename)
    expected = 2 + table["headings"].index(heading)
    for entry in macro.get(filename, []):
        if entry["heading"] not in table["headings"]:
            raise ValueError("Macro heading is absent from native data")
        if entry["column"] != 2 + table["headings"].index(entry["heading"]):
            raise ValueError("Macro column differs from native heading table")
        if entry["heading"] == heading and entry["column"] != expected:
            raise ValueError("Macro/data column mismatch")
    return expected


def verify_csv(path, table):
    """Prove every exported frequency, heading, amplitude, phase and unit."""
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len(table["omega"]) * len(table["headings"]):
        raise ValueError("CSV row count differs from native table")
    for n, row in enumerate(rows):
        i, j = divmod(n, len(table["headings"]))
        actual = tuple(
            float(row[k])
            for k in ("omega_rad_s", "heading_deg", "amplitude", "phase_deg")
        )
        expected = (
            table["omega"][i],
            table["headings"][j],
            table["amplitude"][i][j],
            table["phase"][i][j],
        )
        if actual != expected or row["amplitude_unit"] != table["unit"]:
            raise ValueError("CSV differs from native amplitude/phase table")
    return len(rows)


def export(source, output, executable, filenames, macro_path=None, headings=None):
    source, output, executable = (
        Path(source).resolve(),
        Path(output).resolve(),
        Path(executable).resolve(),
    )
    if (
        output == source
        or source.is_relative_to(output)
        or output.is_relative_to(source)
    ):
        raise ValueError("Select a separate export directory")
    output.mkdir(parents=True, exist_ok=True)
    (output / "data").mkdir(exist_ok=True)
    native = parse_macro(macro_path) if macro_path else {}
    if macro_path:
        shutil.copyfile(macro_path, output / "native.gnu")
    tables, originals, commands, figures, data_checks = {}, {}, [], {}, {}
    for name in filenames:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:rao|dat)", name, re.I):
            raise ValueError("Use a native RAO/DAT basename")
        path = source / name
        table = read_table(path)
        tables[name], originals[name] = table, file_hash(path)
        shutil.copyfile(path, output / "data" / name)
        selected = table["headings"] if headings is None else headings
        if not selected or len(selected) != len(set(selected)):
            raise ValueError("Select distinct computed headings")
        columns = [native_column(native, name, table, h) for h in selected]
        stem = Path(name).stem
        with (output / (stem + ".csv")).open(
            "w", encoding="utf-8-sig", newline=""
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow(
                [
                    "omega_rad_s",
                    "heading_deg",
                    "amplitude",
                    "phase_deg",
                    "amplitude_unit",
                ]
            )
            for i, omega in enumerate(table["omega"]):
                for j, heading in enumerate(table["headings"]):
                    writer.writerow(
                        [
                            format(v, ".17g")
                            for v in (
                                omega,
                                heading,
                                table["amplitude"][i][j],
                                table["phase"][i][j],
                            )
                        ]
                        + [table["unit"]]
                    )
        data_checks[name] = dict(
            rows=verify_csv(output / (stem + ".csv"), table),
            csv_round_trip="exact frequency/heading/amplitude/phase/unit match",
            unit=table["unit"],
            native_sha256=originals[name],
        )
        for suffix, terminal in (
            ("png", "pngcairo size 3600,2400 enhanced font 'Arial,32' linewidth 2.5"),
            ("pdf", "pdfcairo size 12in,8in enhanced font 'Arial,12'"),
            (
                "svg",
                "svg size 1800,1200 enhanced font 'Arial,16' background rgb 'white'",
            ),
        ):
            target = stem + "." + suffix
            plots = [
                gp_string("data/" + name)
                + f" using 1:{column} with linespoints pointsize 0.45 title "
                + gp_string(f"{heading:g} deg")
                for heading, column in zip(selected, columns)
            ]
            commands.extend(
                [
                    "reset",
                    "set encoding utf8",
                    "set terminal " + terminal,
                    "set output " + gp_string(target),
                    "set grid",
                    "set key outside right center",
                    "set title " + gp_string(name),
                    "set xlabel 'Wave frequency (rad/s)'",
                    "set ylabel " + gp_string("Amplitude (" + table["unit"] + ")"),
                    "set yrange [0:*]",
                    "plot " + (", \\\n").join(plots),
                    "unset output",
                ]
            )
            figures[target] = dict(
                headings_deg=selected, mode="amplitude", unit=table["unit"]
            )
    batch = output / "export.gnu"
    batch.write_text("\n".join(commands) + "\n", encoding="utf-8", newline="\n")
    env = dict(os.environ)
    env["PATH"] = str(executable.parent) + os.pathsep + env.get("PATH", "")
    run = subprocess.run(
        [str(executable), batch.name],
        cwd=output,
        env=env,
        capture_output=True,
        timeout=180,
    )
    (output / "export.log").write_bytes(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(run.stderr.decode("utf-8", "replace"))
    for name, record in figures.items():
        if (output / name).stat().st_size < 1000:
            raise ValueError("Incomplete figure: " + name)
        record["sha256"] = file_hash(output / name)
    if any(file_hash(source / name) != digest for name, digest in originals.items()):
        raise ValueError("Source data changed during export")
    record = dict(
        schema="hydrostar-direct-curve-export-1",
        status="exported",
        visual_review="pending",
        method="HSRAO-generated macro column mapping"
        if native
        else "Original native RAO header column mapping; no macro supplied",
        macro_sha256=file_hash(macro_path) if macro_path else None,
        column_policy="Stored headings only; headings omitted from the generated macro use their original RAO header column without interpolation",
        renderer=subprocess.check_output(
            [str(executable), "--version"], env=env, text=True
        ).strip(),
        command=[executable.name, "export.gnu"],
        data_checks=data_checks,
        figures=figures,
        files={
            p.relative_to(output).as_posix(): file_hash(p)
            for p in output.rglob("*")
            if p.is_file() and p.name != "manifest.json"
        },
    )
    (output / "manifest.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Directory containing original HSRAO .rao/.dat files",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gnuplot", type=Path, required=True)
    parser.add_argument("--macro", type=Path, help="Original HSRAO-generated .gnu file")
    parser.add_argument(
        "--files",
        nargs="+",
        default=[
            "surge.rao",
            "sway.rao",
            "heave.rao",
            "roll.rao",
            "pitch.rao",
            "yaw.rao",
        ],
    )
    parser.add_argument("--headings", nargs="+", type=float)
    args = parser.parse_args()
    result = export(
        args.source, args.output, args.gnuplot, args.files, args.macro, args.headings
    )
    print(
        json.dumps(
            dict(
                status=result["status"],
                figures=len(result["figures"]),
                data=result["data_checks"],
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
