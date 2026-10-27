"""Recompute sampled mesh-strategy comparisons from portable native response data."""

from __future__ import annotations

import cmath
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.visualization import _scientific_style
from hydrostar_mcp.workflow import file_hash, save_json

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
        scope="Sampled panel-layout sensitivity at seven frequencies and four headings, with fixed mass, CG, inertia, restoring settings, damping and environment. Two ring grids; target-specific spatial convergence, peak-frequency and benchmark evidence remain to be established.",
        baseline_to_structured=cases,
        spar_ring_pair=dict(
            reference_case_id=coarse_native["source_case_id"],
            candidate_case_id=fine_native["source_case_id"],
            reference_wetted_panels=coarse_native["hslec"]["hull_panels"],
            candidate_wetted_panels=fine_native["hslec"]["hull_panels"],
            reference_summary="sensitivity/cad_spar_coarse/verification.json",
            reference_summary_sha256=file_hash(COARSE / "verification.json"),
            reference_responses_sha256=file_hash(COARSE / "motions.json"),
            metrics=response_difference(
                read(COARSE / "motions.json"), read(BASE / "cad_spar/motions.json")
            ),
        ),
    )


def export_comparison():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = comparison_data()
    _scientific_style(plt)
    baseline = read(BASE / "mesh-baseline-v0.4.0.json")["cases"]["cad_spar"]
    coarse, fine = read(COARSE / "motions.json"), read(BASE / "cad_spar/motions.json")
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.1))
    sources = [
        (
            baseline["motions"],
            f"v0.4 triangles ({baseline['panels']:,})",
            "#7A838C",
            "--",
            "s",
        ),
        (coarse, "Ring bands (6,800)", "#0072B2", "-", "o"),
        (fine, "Ring bands (9,312)", "#D55E00", "-.", "^"),
    ]
    for i, (dof, ax) in enumerate(zip(core.DOFS, axes.flat)):
        for motions, label, colour, style, marker in sources:
            r = motions[dof]
            j = r["headings"].index(60.0)
            ax.plot(
                r["omega"],
                [row[j] for row in r["amplitude"]],
                label=label,
                color=colour,
                linestyle=style,
                marker=marker,
                linewidth=1.4,
                markersize=4,
            )
        ax.set_title(f"({chr(97 + i)}) {dof.capitalize()}", loc="left", fontsize=11)
        ax.set_xlabel("Wave frequency (rad/s)")
        ax.set_ylabel("RAO (" + fine[dof]["unit"] + ")")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.25)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, 0.055),
        frameon=False,
    )
    fig.suptitle(
        "Spar: sampled sensitivity to native panel layout", fontsize=14, y=0.98
    )
    fig.text(
        0.5,
        0.025,
        "Heading 60°. Native samples connected by lines. Mass, CG, inertia, damping and environment held fixed.",
        ha="center",
        fontsize=9,
        color="#526278",
    )
    fig.tight_layout(rect=(0.015, 0.11, 0.995, 0.94), h_pad=1.4, w_pad=1.6)
    assets = ROOT / "docs/assets"
    for suffix in ("png", "pdf"):
        fig.savefig(assets / ("cad_spar_mesh_comparison." + suffix), dpi=300)
    plt.close(fig)
    data["figures"] = {
        "cad_spar_mesh_comparison." + ext: file_hash(
            assets / ("cad_spar_mesh_comparison." + ext)
        )
        for ext in ("png", "pdf")
    }
    save_json(BASE / "mesh-comparison.json", data)
    index = read(BASE / "index.json")
    index["mesh_comparison"] = dict(
        path="examples/geometry/mesh-comparison.json",
        sha256=file_hash(BASE / "mesh-comparison.json"),
    )
    index["figures"].update(data["figures"])
    save_json(BASE / "index.json", index)
    save_json(ROOT / "docs/data/geometry.json", index)
    print("Mesh comparison: two ring grids, fixed physical parameters", flush=True)


if __name__ == "__main__":
    export_comparison()
