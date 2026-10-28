"""Verify and publish the native platform drift/QTF study and scientific plots."""

import argparse
import cmath
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.second_order import read_difference_qtf, supported_pairs
from hydrostar_mcp.visualization import whole_mesh
from hydrostar_mcp.workflow import file_hash, save_json
from scripts.export_native_curves import COLOURS, gp_string

COMPONENTS = ("fx", "fy", "fz", "mx", "my", "mz")
PACKAGE = ROOT / "examples/second-order/platform"
REFERENCE = ROOT / "examples/results/semisub_oc4_style"
LIMITS = dict(
    first_order_complex_error=1e-4,
    diagonal_drift_error=0.002,
    horizontal_drift_near_far_error=0.05,
    force_surface_sensitivity=0.005,
    dominant_moment_surface_sensitivity=0.005,
    characteristic_moment_surface_sensitivity=0.005,
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wet_signature(path):
    nodes, panels, _ = core.read_hst(path)
    return [[nodes[i] for i in p] for p in panels]


def complex_motion(data, i, j):
    return data["amplitude"][i][j] * cmath.exp(1j * math.radians(data["phase"][i][j]))


def review(work, *, portable=False):
    inputs = work / "inputs" if portable else work
    state = read(work / ("execution.json" if portable else "study.json"))
    require(
        state["status"] == "computed", "Completed native second-order study required"
    )
    require(
        len(state["steps"]) == 8
        and all(
            s["ok"] and s["rc"] == 0 and not s["error_code"] for s in state["steps"]
        ),
        "All eight native stages must pass",
    )
    require(
        state["mesh"]["full_equivalent_total_including_exterior"] <= 3000,
        "3000 total-panel budget",
    )
    for name, expected in state["input_hashes"].items():
        require(file_hash(inputs / name) == expected, "Native input changed: " + name)
    for name, expected in state["result_files"].items():
        require(
            file_hash(work / "rao" / name) == expected, "Native result changed: " + name
        )
    for step in state["steps"]:
        log = (work / "logs" / (step["module"] + ".log")).read_text(encoding="utf-8")
        require(core.log_error(log) is None, "Native log diagnostic: " + step["module"])
    hst = inputs / "platform2.hst"
    require(
        wet_signature(hst) == wet_signature(REFERENCE / "inputs/oc4_style.hst"),
        "Accepted wet panels must remain identical",
    )
    require(
        (inputs / "platform2.mcn").read_bytes()
        == (REFERENCE / "inputs/oc4_style.mcn").read_bytes(),
        "Mass, inertia, restoring and damping must remain fixed",
    )
    surface = read(
        work / "geometry/surface.json"
        if portable
        else work.parent / "geometry/platform2.surface.json"
    )
    require(
        surface["output_hst_sha256"] == file_hash(hst),
        "Integration mesh source differs",
    )
    require(
        abs(surface["overlap_m2"]) < 1e-6 and surface["uncovered_or_extra_m2"] < 1e-6,
        "Conforming exterior coverage required",
    )
    q = surface["panel_quality"]
    require(
        q["min_corner_deg"] >= 10
        and q["max_corner_deg"] <= 170
        and q["max_edge_ratio"] <= 8
        and q["max_neighbor_size_ratio"] <= 2
        and q["nonconvex"] == 0,
        "Exterior panel shape gate",
    )
    require(
        surface["quad_fraction"] >= 0.8,
        "Quadrilateral-dominant exterior surface required",
    )
    source = read(REFERENCE / "motions.json")
    motion_errors = {}
    for dof in core.DOFS:
        response = core.read_rao(work / "rao" / (dof + ".rao"))
        reference = source[dof]
        target_heading = reference["headings"].index(60.0)
        actual, expected = [], []
        for i, w in enumerate(response["omega"]):
            k = min(
                range(len(reference["omega"])),
                key=lambda k: abs(reference["omega"][k] - w),
            )
            require(
                abs(reference["omega"][k] - w) < 1e-6, "Reference frequency missing"
            )
            actual.append(complex_motion(response, i, 0))
            expected.append(complex_motion(reference, k, target_heading))
        motion_errors[dof] = max(abs(a - b) for a, b in zip(actual, expected)) / max(
            map(abs, expected)
        )
    require(
        max(motion_errors.values()) <= LIMITS["first_order_complex_error"],
        "First-order complex response comparison",
    )
    loads, drifts, diagonal = {}, {}, {}
    for direction, name in enumerate(COMPONENTS, 1):
        data = read_difference_qtf(work / "rao" / ("qtf_" + name + ".qtf"))
        require(
            data["direction"] == direction
            and data["headings_deg"] == [60.0]
            and data["difference_rad_s"] == [0.0, 0.05, 0.1],
            "QTF axes or load direction differ",
        )
        require(
            data["omega1_rad_s"] == [round(0.5 + 0.05 * i, 6) for i in range(13)],
            "Requested QTF wave-frequency grid incomplete",
        )
        loads[name] = data
        drifts[name] = dict(
            near=read_difference_qtf(work / "rao" / ("drift_" + name + "_near.rao"))
        )
        if name in ("fx", "fy", "mz"):
            drifts[name]["far"] = read_difference_qtf(
                work / "rao" / ("drift_" + name + "_far.rao")
            )
        reference = {
            w: complex(*row[0])
            for w, row in zip(
                drifts[name]["near"]["omega1_rad_s"], drifts[name]["near"]["values"][0]
            )
        }
        scale = max(abs(reference[w]) for w in data["omega1_rad_s"])
        diagonal[name] = max(
            abs(complex(*row[0]) - reference[w])
            for w, row in zip(data["omega1_rad_s"], data["values"][0])
        ) / max(scale, 1)
    require(
        max(diagonal.values()) <= LIMITS["diagonal_drift_error"],
        "QTF diagonal must match native mean drift",
    )
    mask = supported_pairs(loads["fx"])
    expected_pairs = {
        (round(w, 6), round(w + d, 6))
        for w, row in zip(loads["fx"]["omega1_rad_s"], mask)
        for d, valid in zip(loads["fx"]["difference_rad_s"], row)
        if valid
    }
    log = (work / "logs/hsqtf.log").read_text(encoding="utf-8")
    found = {
        (round(float(a), 6), round(float(b), 6))
        for _, a, b in re.findall(
            r"DeltaOmega=\s*("
            + core.NUMBER
            + r")\s+Omega_1,Omega_2=\s*("
            + core.NUMBER
            + r")\s+("
            + core.NUMBER
            + r")",
            log,
        )
    }
    require(
        found == expected_pairs and len(found) == 36,
        "Each valid QTF frequency pair must be recorded by the solver",
    )
    require(
        bool(re.search(r"Fd3out\s*=\s*T", log))
        and bool(re.search(r"Fd3in\s*=\s*T", log)),
        "Free-surface Haskind contributions required",
    )
    near_far = {}
    for name in ("fx", "fy", "mz"):
        a, b = drifts[name]["near"], drifts[name]["far"]
        rows = [i for i, w in enumerate(a["omega1_rad_s"]) if 0.4 <= w <= 1.1]
        av = [complex(*a["values"][0][i][0]) for i in rows]
        bv = [complex(*b["values"][0][i][0]) for i in rows]
        near_far[name] = max(abs(x - y) for x, y in zip(av, bv)) / max(
            1, max(map(abs, bv))
        )
    require(
        max(near_far[k] for k in ("fx", "fy"))
        <= LIMITS["horizontal_drift_near_far_error"],
        "Horizontal near/far mean drift comparison",
    )
    return dict(
        state=state,
        surface=surface,
        loads=loads,
        drifts=drifts,
        mask=mask,
        motion_errors=motion_errors,
        diagonal=diagonal,
        near_far=near_far,
    )


def native_surface_review(work, surface):
    """Independently inspect the solver's actual HSLEC integration cells."""
    import h5py
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    path = work / "hdf/hslec_platform2.h5"
    with h5py.File(path, "r") as database:
        cells = database["PROPZERO"][:]
    shapes = [Polygon(row[12:24].reshape(4, 3)[:, :2]) for row in cells]
    union = unary_union(shapes)
    area = sum(p.area for p in shapes)
    overlap = area - union.area
    normal_error = float(max(abs(cells[:, 6] + 1)))
    require(
        len(cells) == surface["half_domain_panels"], "Native exterior count differs"
    )
    require(
        abs(area - surface["expected_half_area_m2"]) < 1e-6,
        "Native exterior area differs",
    )
    require(
        abs(overlap) < 1e-6 and normal_error < 1e-9,
        "Native exterior coverage or normals failed",
    )
    return dict(
        status="verified",
        source_hst_sha256=file_hash(work / "platform2.hst"),
        native_database="hdf/hslec_platform2.h5",
        native_database_sha256=file_hash(path),
        half_domain_panels=len(cells),
        area_m2=area,
        union_area_m2=union.area,
        overlap_m2=overlap,
        downward_normal_max_error=normal_error,
    )


def publish_case(work, destination, reviewed):
    for subdir in ("inputs", "rao", "logs", "geometry"):
        (destination / subdir).mkdir(parents=True, exist_ok=True)
    for name in reviewed["state"]["input_hashes"]:
        shutil.copyfile(work / name, destination / "inputs" / name)
    for name in reviewed["state"]["result_files"]:
        shutil.copyfile(work / "rao" / name, destination / "rao" / name)
    for path in (work / "logs").glob("*.log"):
        shutil.copyfile(path, destination / "logs" / path.name)
    shutil.copyfile(
        work.parent / "geometry/platform2.surface.json",
        destination / "geometry/surface.json",
    )
    save_json(
        destination / "geometry/native-surface-check.json",
        native_surface_review(work, reviewed["surface"]),
    )
    record = dict(
        **reviewed["state"],
        first_order_complex_error=reviewed["motion_errors"],
        qtf_diagonal_mean_drift_error=reviewed["diagonal"],
        near_far_mean_drift_error=reviewed["near_far"],
    )
    save_json(destination / "execution.json", record)


def plot_commands(kind, scale, totals):
    title = dict(
        drift="Mean second-order drift loads",
        qtf="Full-potential difference-frequency QTF",
        complex="Complex QTF at difference frequency 0.10 rad/s",
        sensitivity="Exterior integration mesh comparison",
    )[kind]
    lines = [
        "reset",
        "set encoding utf8",
        "set border linewidth 0.8 linecolor rgb '#34424E'",
        "set tics out nomirror",
        "set grid back linewidth 0.5 linecolor rgb '#E0E5E9'",
        "set format y '%.3g'",
        "set key off",
        "set multiplot layout 2,3 rowsfirst margins 0.08,0.98,0.20,0.84 spacing 0.085,0.18 title "
        + gp_string("Semisubmersible: " + title + " (60 deg, 200 m depth)")
        + f" font 'Times New Roman,{18 * scale:g}'",
    ]
    for i, name in enumerate(COMPONENTS):
        unit = "kN/m²" if name[0] == "f" else "kN m/m²"
        quantity = (
            "Mean drift"
            if kind == "drift"
            else "QTF magnitude"
            if kind in ("qtf", "sensitivity")
            else "QTF component"
        )
        lines.extend(
            [
                "set title "
                + gp_string(f"({chr(97 + i)}) " + name[0].upper() + name[1])
                + f" font 'Times New Roman,{14 * scale:g}'",
                "set xlabel 'Wave frequency ω1 (rad/s)'",
                "set ylabel " + gp_string(quantity + " (" + unit + ")"),
                "set xrange [0.39:1.11]"
                if kind == "drift"
                else "set xrange [0.49:1.01]",
                "set yrange [*:*]"
                if kind in ("drift", "complex")
                else "set yrange [0:*]",
            ]
        )
        if i == 5:
            lines.append(
                f"set key at screen 0.5,0.055 center horizontal maxrows 2 font 'Times New Roman,{11 * scale:g}' samplen 2.2"
            )
        else:
            lines.append("set key off")
        plots = []
        if kind == "drift":
            for j, method in enumerate(
                ("near", "far") if name in ("fx", "fy", "mz") else ("near",)
            ):
                plots.append(
                    gp_string("rao/drift_" + name + "_" + method + ".rao")
                    + f" using 1:($2/1000) with linespoints pointtype {7 + j} pointsize 0.45 linewidth 1.6 dashtype {j + 1} linecolor rgb "
                    + gp_string(COLOURS[j])
                    + " title "
                    + gp_string("Near field" if method == "near" else "Far field")
                )
        elif kind == "qtf":
            for j, difference in enumerate((0, 0.05, 0.1)):
                col = 2 + 2 * j
                plots.append(
                    gp_string("rao/qtf_" + name + ".qtf")
                    + f" using 1:(sqrt(column({col})**2+column({col + 1})**2)/1000) with linespoints pointtype {7 + j} pointsize 0.55 linewidth 1.7 dashtype {j + 1} linecolor rgb "
                    + gp_string(COLOURS[j])
                    + " title "
                    + gp_string(f"Difference {difference:.2f} rad/s")
                )
        elif kind == "complex":
            for j, col in enumerate((6, 7)):
                plots.append(
                    gp_string("rao/qtf_" + name + ".qtf")
                    + f" using 1:(column({col})/1000) with linespoints pointtype {7 + j} pointsize 0.5 linewidth 1.7 dashtype {j + 1} linecolor rgb "
                    + gp_string(COLOURS[j])
                    + " title "
                    + gp_string("Real" if j == 0 else "Imaginary")
                )
        else:
            for j, prefix in enumerate(("rao/", "sensitivity/coarse/rao/")):
                plots.append(
                    gp_string(prefix + "qtf_" + name + ".qtf")
                    + " using 1:(sqrt($6**2+$7**2)/1000) with linespoints "
                    + f"pointtype {7 + j} pointsize 0.5 linewidth 1.7 dashtype {j + 1} linecolor rgb "
                    + gp_string(COLOURS[j])
                    + " title "
                    + gp_string(f"{totals[j]} total panels")
                )
        lower, upper = (0.4, 1.1) if kind == "drift" else (0.5, 1.0)
        plots = [
            line.replace(
                " using 1:", f" using (($1 >= {lower} && $1 <= {upper}) ? $1 : 1/0):"
            )
            for line in plots
        ]
        lines.append("plot " + (", " + chr(92) + "\n").join(plots))
    return lines + ["unset multiplot"]


def compare_surfaces(main, reference):
    peaks, errors = {}, {}
    for name in COMPONENTS:
        a, b = main["loads"][name], reference["loads"][name]
        av = [
            complex(*a["values"][0][i][j])
            for i, row in enumerate(main["mask"])
            for j, ok in enumerate(row)
            if ok
        ]
        bv = [
            complex(*b["values"][0][i][j])
            for i, row in enumerate(main["mask"])
            for j, ok in enumerate(row)
            if ok
        ]
        peaks[name] = max(map(abs, av))
        errors[name] = max(abs(x - y) for x, y in zip(av, bv))
    vertices, _ = whole_mesh(REFERENCE / "inputs/oc4_style.hst")
    length = max(
        max(p[k] for p in vertices) - min(p[k] for p in vertices) for k in (0, 1)
    )
    force_scale = max(peaks[k] for k in ("fx", "fy", "fz"))
    sensitivity = {
        name: dict(
            absolute_error=errors[name],
            relative_to_own_peak=errors[name] / max(peaks[name], 1),
            relative_to_characteristic_scale=errors[name]
            / force_scale
            / (length if name[0] == "m" else 1),
        )
        for name in COMPONENTS
    }
    require(
        max(sensitivity[k]["relative_to_own_peak"] for k in ("fx", "fy", "fz"))
        <= LIMITS["force_surface_sensitivity"],
        "Force QTF surface sensitivity",
    )
    require(
        max(sensitivity[k]["relative_to_own_peak"] for k in ("mx", "my"))
        <= LIMITS["dominant_moment_surface_sensitivity"],
        "Dominant moment QTF surface sensitivity",
    )
    require(
        max(
            sensitivity[k]["relative_to_characteristic_scale"]
            for k in ("mx", "my", "mz")
        )
        <= LIMITS["characteristic_moment_surface_sensitivity"],
        "Characteristic moment QTF surface sensitivity",
    )
    return sensitivity, force_scale, length


def convert_native_svg(path):
    """Convert the inspected native SVG without the legacy Cairo clipping path."""
    import importlib.metadata
    import pypdfium2 as pdfium
    from reportlab.graphics import renderPDF
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from svglib.svglib import svg2rlg

    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    if (fonts / "times.ttf").exists():
        pdfmetrics.registerFont(TTFont("Times New Roman", str(fonts / "times.ttf")))
    drawing = svg2rlg(str(path))
    require(drawing is not None and drawing.width > 0, "Native SVG cannot be converted")
    scale = 864 / drawing.width
    drawing.scale(scale, scale)
    drawing.width *= scale
    drawing.height *= scale
    target = path.with_suffix(".pdf")
    renderPDF.drawToFile(drawing, str(target))
    document = pdfium.PdfDocument(target)
    page = document[0]
    page.render(scale=2400 / page.get_width()).to_pil().save(path.with_suffix(".png"))
    page.close()
    document.close()
    return dict(
        method="Native Gnuplot SVG to vector PDF with Svglib/ReportLab, raster PNG with PDFium; data and plot geometry retained",
        versions={
            name: importlib.metadata.version(name)
            for name in ("reportlab", "svglib", "pypdfium2")
        },
        pdf_width_inches=12,
        png_width_pixels=2400,
    )


def export(fine, coarse, gnuplot):
    main, reference = review(fine), review(coarse)
    publish_case(fine, PACKAGE, main)
    publish_case(coarse, PACKAGE / "sensitivity/coarse", reference)
    sensitivity, force_scale, length = compare_surfaces(main, reference)
    data = dict(
        heading_deg=60,
        depth_m=200,
        omega1_rad_s=main["loads"]["fx"]["omega1_rad_s"],
        difference_rad_s=[0, 0.05, 0.1],
        valid_pair_mask=main["mask"],
        valid_pair_count=36,
        pair_convention="omega2=omega1+difference",
        complex_convention="Native CPLXTYPE 0: [real, imaginary]",
        force_unit="N/m^2",
        moment_unit="N m/m^2",
        moment_reference_m=main["loads"]["fx"]["reference_point_m"],
        loads={
            name: [
                [pair if ok else None for pair, ok in zip(row, mask)]
                for row, mask in zip(main["loads"][name]["values"][0], main["mask"])
            ]
            for name in COMPONENTS
        },
    )
    save_json(PACKAGE / "qtf.json", data)
    record = dict(
        schema="hydrostar-second-order-study-1",
        status="verified_with_component_limitations",
        component_acceptance={
            name: (
                "convergence_required"
                if name == "mz"
                else "passed_example_sensitivity_gate"
            )
            for name in COMPONENTS
        },
        method=main["state"]["method"],
        native_backend="HydroStar For Experts V8.2.0beta",
        main_total_panels=main["state"]["mesh"][
            "full_equivalent_total_including_exterior"
        ],
        comparison_total_panels=reference["state"]["mesh"][
            "full_equivalent_total_including_exterior"
        ],
        valid_complex_coefficients=216,
        limits=LIMITS,
        first_order_complex_errors=main["motion_errors"],
        diagonal_mean_drift_errors=main["diagonal"],
        near_far_mean_drift_errors=main["near_far"],
        surface_sensitivity=sensitivity,
        characteristic_force_n_per_m2=force_scale,
        characteristic_length_m=length,
        yaw_scope="Mz fails a 0.5% own-peak convergence target and the near/far mean-drift comparison. It is retained as a numerical research result; dedicated yaw-load engineering use requires further convergence evidence.",
        wet_mesh_scope="The accepted wet mesh is fixed; this comparison changes the exterior integration mesh only.",
        source_boundary="examples/results/semisub_oc4_style/inputs/oc4_style.hst",
        source_boundary_sha256=file_hash(REFERENCE / "inputs/oc4_style.hst"),
        visual_review="pending",
    )
    commands, batches, figures = [], [], {}
    for kind in ("drift", "qtf", "complex", "sensitivity"):
        target = ROOT / "docs/assets" / f"platform-second-order-{kind}.svg"
        section = plot_commands(
            kind, 1.65, [record["main_total_panels"], record["comparison_total_panels"]]
        )
        section[1:1] = [
            "set terminal svg size 2400,1540 noenhanced font 'Times New Roman,23'",
            "set output " + gp_string(os.path.relpath(target, PACKAGE)),
        ]
        batch = PACKAGE / "plots" / f"{kind}.gp"
        batch.parent.mkdir(parents=True, exist_ok=True)
        batch.write_text(
            "\n".join(section + ["unset output"]) + "\n", encoding="utf-8", newline="\n"
        )
        batches.append(batch)
        commands.append(["gnuplot", batch.relative_to(PACKAGE).as_posix()])
        figures[target.relative_to(ROOT).as_posix()] = dict(
            kind=kind, role="native_vector"
        )
    # Superseded Cairo batches are private diagnostics; this delivery uses SVG.
    for path in (PACKAGE / "plots").glob("*-*.gp"):
        path.unlink()
    obsolete = PACKAGE / "curves.gp"
    if obsolete.exists():
        obsolete.unlink()
    env = dict(os.environ)
    env["PATH"] = str(gnuplot.parent) + os.pathsep + env.get("PATH", "")
    logs = []
    for batch in batches:
        result = subprocess.run(
            [str(gnuplot), batch.relative_to(PACKAGE).as_posix()],
            cwd=PACKAGE,
            env=env,
            capture_output=True,
            timeout=120,
        )
        logs.extend((result.stdout, result.stderr))
        require(
            result.returncode == 0, result.stderr.decode("utf-8", "replace")[-1200:]
        )
    (PACKAGE / "export.log").write_bytes(b"".join(logs))
    conversion = None
    for name, item in list(figures.items()):
        conversion = convert_native_svg(ROOT / name)
        for ext in ("pdf", "png"):
            derived = str(Path(name).with_suffix("." + ext)).replace(chr(92), "/")
            figures[derived] = dict(
                kind=item["kind"], role="converted_from_native_svg", source=name
            )
    record["conversion"] = conversion
    for name, item in figures.items():
        require(
            (ROOT / name).stat().st_size > 1000, "Missing native curve export: " + name
        )
        item["sha256"] = file_hash(ROOT / name)
    record["figures"] = figures
    record["renderer"] = subprocess.check_output(
        [str(gnuplot), "--version"], env=env, text=True
    ).strip()
    record["export_script_sha256"] = file_hash(Path(__file__))
    record["commands"] = commands
    record["files"] = {
        p.relative_to(PACKAGE).as_posix(): file_hash(p)
        for p in PACKAGE.rglob("*")
        if p.is_file() and p.name != "verification.json"
    }
    save_json(PACKAGE / "verification.json", record)
    print(
        "Verified 216 native complex QTF coefficients and exported twelve scientific figure files",
        flush=True,
    )
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fine", type=Path, required=True)
    parser.add_argument("--coarse", type=Path, required=True)
    parser.add_argument("--gnuplot", type=Path, required=True)
    args = parser.parse_args()
    export(args.fine, args.coarse, args.gnuplot.resolve())
