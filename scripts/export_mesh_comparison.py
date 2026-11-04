"""Recompute sampled mesh-strategy comparisons from portable native response data."""

from __future__ import annotations

import cmath
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/hydrostar-modeling/scripts"))
from hydrostar_mcp import core
from hydrostar_mcp.workflow import file_hash, save_json
from export_hsrao import native_column, parse_macro

BASE = ROOT / "examples/geometry"
COARSE = BASE / "sensitivity/cad_spar_coarse"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def physical_parameters(mechanics):
    return {k: v for k, v in mechanics.items() if k != "source_note"}


def response_difference(reference, candidate):
    """All headings/frequencies; normalize by the reference peak for each DOF."""
    result = {}
    for dof in core.DOFS:
        a, b = reference[dof], candidate[dof]
        if any(a[k] != b[k] for k in ("omega", "headings", "unit")):
            raise ValueError("Comparison response grids/units differ: " + dof)
        za = [
            cmath.rect(amp, math.radians(phase))
            for amps, phases in zip(a["amplitude"], a["phase"])
            for amp, phase in zip(amps, phases)
        ]
        zb = [
            cmath.rect(amp, math.radians(phase))
            for amps, phases in zip(b["amplitude"], b["phase"])
            for amp, phase in zip(amps, phases)
        ]
        peak = max(map(abs, za))
        if peak <= 0 or len(za) != len(zb):
            raise ValueError("Comparison response peak/shape invalid: " + dof)
        phase_difference = [
            abs(math.degrees(cmath.phase(y / x)))
            for x, y in zip(za, zb)
            if min(abs(x), abs(y)) >= 0.05 * peak
        ]
        result[dof] = dict(
            max_complex_difference_over_reference_peak=max(
                abs(y - x) for x, y in zip(za, zb)
            )
            / peak,
            max_amplitude_difference_over_reference_peak=max(
                abs(abs(y) - abs(x)) for x, y in zip(za, zb)
            )
            / peak,
            max_phase_difference_deg_above_5pct_peak=max(
                phase_difference, default=None
            ),
            reference_peak=peak,
            unit=a["unit"],
            sample_count=len(za),
        )
    return result


def comparison_data():
    baseline_path = BASE / "mesh-baseline-v0.4.0.json"
    baseline = read(baseline_path)
    cases = {}
    for key, old in baseline["cases"].items():
        folder = BASE / key
        cfg, summary = read(folder / "config.json"), read(folder / "verification.json")
        if physical_parameters(old["mechanics"]) != physical_parameters(
            cfg["mechanics"]
        ):
            raise ValueError(
                key + ": physical parameters changed during mesh comparison"
            )
        if old["environment"] != cfg["environment"]:
            raise ValueError(key + ": comparison environment changed")
        cases[key] = dict(
            baseline_case_id=old["case_id"],
            baseline_mesh_sha256=old["mesh_sha256"],
            baseline_wetted_panels=old["panels"],
            candidate_case_id=summary["source_case_id"],
            candidate_mesh_sha256=file_hash(folder / "geometry/model.hst"),
            candidate_wetted_panels=summary["hslec"]["hull_panels"],
            candidate_full_equivalent_total=summary["resource_policy"][
                "full_equivalent_total"
            ],
            native_summary_sha256=file_hash(folder / "verification.json"),
            responses_sha256=file_hash(folder / "motions.json"),
            mechanics_fixed=True,
            environment_fixed=True,
            metrics=response_difference(old["motions"], read(folder / "motions.json")),
        )
    coarse_cfg = read(COARSE / "config.json")
    fine_cfg = read(BASE / "cad_spar/config.json")
    if (
        physical_parameters(coarse_cfg["mechanics"])
        != physical_parameters(fine_cfg["mechanics"])
        or coarse_cfg["environment"] != fine_cfg["environment"]
    ):
        raise ValueError("Spar ring study requires fixed mechanics and environment")
    coarse_native = read(COARSE / "verification.json")
    fine_native = read(BASE / "cad_spar/verification.json")
    return dict(
        schema="hydrostar-sampled-mesh-comparison-1",
        baseline_release="v0.4.0",
        baseline_sha256=file_hash(baseline_path),
        normalization="Maximum complex response difference across all sampled frequencies/headings, divided by the reference peak of that DOF.",
        phase_convention="Complex RAO = amplitude * exp(i * phase_deg * pi / 180).",
        scope="Sampled panel-layout sensitivity at seven frequencies and four headings, with fixed mass, CG, inertia, restoring settings, damping and environment. The v0.4 baseline is historical numerical evidence. Current cases and both nearby Spar grids are within 3000 total panels; the Spar pair measures local sensitivity and does not establish spatial convergence.",
        baseline_to_structured=cases,
        spar_ring_pair=dict(
            reference_case_id=coarse_native["source_case_id"],
            candidate_case_id=fine_native["source_case_id"],
            reference_wetted_panels=coarse_native["hslec"]["hull_panels"],
            candidate_wetted_panels=fine_native["hslec"]["hull_panels"],
            reference_full_equivalent_total=coarse_native["resource_policy"][
                "full_equivalent_total"
            ],
            candidate_full_equivalent_total=fine_native["resource_policy"][
                "full_equivalent_total"
            ],
            reference_summary="sensitivity/cad_spar_coarse/verification.json",
            reference_summary_sha256=file_hash(COARSE / "verification.json"),
            reference_responses_sha256=file_hash(COARSE / "motions.json"),
            metrics=response_difference(
                read(COARSE / "motions.json"), read(BASE / "cad_spar/motions.json")
            ),
        ),
    )


def export_comparison(executable=None):
    executable = executable or os.environ.get("GNUPLOT_EXE") or shutil.which("gnuplot")
    if not executable:
        raise ValueError(
            "Provide --gnuplot or GNUPLOT_EXE for the native curve renderer"
        )
    executable = Path(executable).resolve()
    data = comparison_data()
    folder = BASE / "sensitivity/visualization"
    (folder / "data").mkdir(parents=True, exist_ok=True)
    sources = [
        (
            "coarse",
            COARSE,
            data["spar_ring_pair"]["reference_full_equivalent_total"],
            "#0072B2",
        ),
        (
            "fine",
            BASE / "cad_spar",
            data["spar_ring_pair"]["candidate_full_equivalent_total"],
            "#D55E00",
        ),
    ]
    native = {}
    macros = {label: parse_macro(folder / (label + ".gnu")) for label, *_ in sources}
    for label, source, *_ in sources:
        (folder / "data" / label).mkdir(exist_ok=True)
        native[label] = {}
        for dof in core.DOFS:
            path = source / "rao" / (dof + ".rao")
            native[label][dof] = core.read_rao(path)
            shutil.copyfile(path, folder / "data" / label / path.name)
    from scripts.export_native_curves import gp_string

    commands = []
    assets = ROOT / "docs/assets"
    for suffix, terminal, scale in (
        ("png", "pngcairo size 2400,1540 enhanced font 'Times New Roman,23'", 1.65),
        ("pdf", "pdfcairo size 12in,7.7in enhanced font 'Times New Roman,12'", 1),
        ("svg", "svg size 1400,900 enhanced font 'Times New Roman,15'", 1),
    ):
        commands.extend(
            [
                "reset",
                "set encoding utf8",
                "set terminal " + terminal,
                "set output "
                + gp_string(
                    os.path.relpath(
                        assets / ("cad_spar_mesh_comparison." + suffix), folder
                    )
                ),
                "set border linewidth 0.8",
                "set grid back linecolor rgb '#E0E5E9'",
                "set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Spar: local sensitivity within 3,000 total panels; heading 60 deg'",
            ]
        )
        for i, dof in enumerate(core.DOFS):
            commands.extend(
                [
                    "set title " + gp_string(f"({chr(97 + i)}) {dof.capitalize()}"),
                    "set xlabel 'Wave frequency (rad/s)'",
                    "set ylabel "
                    + gp_string("RAO (" + native["fine"][dof]["unit"] + ")"),
                    "set yrange [0:*]",
                    f"set key at screen 0.5,0.045 center horizontal font 'Times New Roman,{11 * scale:g}'"
                    if i == 4
                    else "set key off",
                ]
            )
            plots = []
            for j, (label, source, total, colour) in enumerate(sources):
                column = native_column(
                    macros[label], dof + ".rao", native[label][dof], 60.0
                )
                plots.append(
                    gp_string("data/" + label + "/" + dof + ".rao")
                    + f" using 1:{column} with linespoints pointtype {7 + j * 2} pointsize 0.5 linewidth 1.7 dashtype {j + 1} linecolor rgb "
                    + gp_string(colour)
                    + " title "
                    + gp_string(f"Ring bands ({total:,} total)")
                )
            commands.append("plot " + (", \\\n").join(plots))
        commands.extend(["unset multiplot", "unset output"])
    batch = folder / "comparison.gp"
    batch.write_text("\n".join(commands) + "\n", encoding="utf-8", newline="\n")
    env = dict(os.environ)
    env["PATH"] = str(executable.parent) + os.pathsep + env.get("PATH", "")
    run = subprocess.run(
        [str(executable), batch.name],
        cwd=folder,
        env=env,
        capture_output=True,
        timeout=180,
    )
    (folder / "export.log").write_bytes(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(run.stderr.decode("utf-8", "replace"))
    data["figures"] = {
        "cad_spar_mesh_comparison." + ext: file_hash(
            assets / ("cad_spar_mesh_comparison." + ext)
        )
        for ext in ("png", "pdf", "svg")
    }
    receipt = dict(
        renderer=subprocess.check_output(
            [str(executable), "--version"], env=env, text=True
        ).strip(),
        method="Original HSRAO macros and native response files -> Gnuplot file terminals; fixed physical parameters",
        status="exported",
        figures=data["figures"],
        files={
            p.relative_to(folder).as_posix(): file_hash(p)
            for p in folder.rglob("*")
            if p.is_file() and p.name != "verification.json"
        },
    )
    save_json(folder / "verification.json", receipt)
    save_json(BASE / "mesh-comparison.json", data)
    index = read(BASE / "index.json")
    index["mesh_comparison"] = dict(
        path="examples/geometry/mesh-comparison.json",
        sha256=file_hash(BASE / "mesh-comparison.json"),
        visualization="examples/geometry/sensitivity/visualization/verification.json",
        visualization_sha256=file_hash(folder / "verification.json"),
    )
    index["figures"].update(data["figures"])
    save_json(BASE / "index.json", index)
    save_json(ROOT / "docs/data/geometry.json", index)
    print("Mesh comparison: two ring grids, fixed physical parameters", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gnuplot")
    export_comparison(parser.parse_args().gnuplot)
