"""Check the portable publication package without a solver installation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__, core
from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.reference_forms import FORMS
from hydrostar_mcp.second_order import (
    read_difference_qtf,
    read_integration_mesh,
    supported_pairs,
)
from hydrostar_mcp.visualization import whole_mesh
from scripts.gallery_data import RESULT_VIEWER_RECORD, presentation_data
from scripts.prepare_hyview_platform import compare_responses

GATES = {
    "semantic_input",
    "static_equilibrium",
    "mesh_geometry",
    "mesh_topology",
    "module_execution",
    "rao_integrity",
}
COUNTERS = {
    "zero_area",
    "over_free_surface",
    "at_free_surface",
    "superposition",
    "inconsistence",
    "neighbor_absence",
    "symmetry_problem",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def public_files():
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return sorted(set(result.stdout.decode("utf-8").strip("\0").split("\0")))


def check_files(files):
    personal = re.compile(r"[A-Za-z]:[/\\]Users[/\\][^/\\\s\"']+", re.I)
    credential = re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"
    )
    forbidden = ("output/", "prototype/", "tmp/", "examples/wind_turbine/", ".env")
    text_types = {
        ".py",
        ".md",
        ".json",
        ".html",
        ".toml",
        ".yml",
        ".yaml",
        ".hst",
        ".rdf",
        ".spc",
        ".mcn",
        ".prs",
        ".rao",
        ".prv",
        ".gp",
        ".svg",
        ".qtf",
        ".dft",
        ".log",
    }
    for name in files:
        path = ROOT / name
        require(path.is_file(), "Missing public file: " + name)
        require(
            not name.startswith(forbidden), "Private artifact in publication: " + name
        )
        require(
            path.suffix.lower() not in {".exe", ".dll", ".dat", ".key", ".lic"},
            "Vendor or credential file: " + name,
        )
        if path.suffix.lower() in {".png", ".jpg", ".pdf", ".gif"}:
            reviewed_geometry = re.fullmatch(
                r"examples/geometry/(lofted_vessel|moonpool_caisson|cad_spar|sensitivity/cad_spar_coarse)/geometry/geometry-qa\.png",
                name,
            )
            require(
                name.startswith("docs/assets/")
                or reviewed_geometry
                or name == "examples/vessel/geometry/geometry-qa.png",
                "Unreviewed binary asset: " + name,
            )
        if path.suffix in text_types or path.name in {
            "LICENSE",
            ".gitignore",
            "MANIFEST.in",
        }:
            content = path.read_text(encoding="utf-8")
            require(not personal.search(content), "Personal machine path in " + name)
            require(not credential.search(content), "Credential pattern in " + name)
            require("\ufffd" not in content, "Invalid text encoding in " + name)


def check_links(files):
    published = set(files)
    count = 0
    for name in files:
        if not name.endswith(".md"):
            continue
        text = (ROOT / name).read_text(encoding="utf-8")
        # Code examples use fenced blocks and are not document links.
        text = re.sub(r"(?ms)^([~\x60])\1{2,}.*?^\1{3,}\s*$", "", text)
        for target in re.findall(r"!?\[[^\]]*\]\(([^)\s]+)\)", text):
            if urlsplit(target).scheme or target.startswith("#"):
                continue
            value = unquote(target.split("#", 1)[0])
            destination = ((ROOT / name).parent / value).resolve()
            require(destination.is_relative_to(ROOT), "Link leaves repository: " + name)
            rel = destination.relative_to(ROOT).as_posix()
            require(
                rel in published
                or (
                    destination.is_dir() and any(f.startswith(rel + "/") for f in files)
                ),
                f"Unpublished local link: {name} -> {target}",
            )
            count += 1
    return count


def check_result_viewer_exports(document):
    from PIL import Image

    record = read_json(ROOT / RESULT_VIEWER_RECORD)
    expected = {
        "platform_rao": ("StarViewer", "save_figure_svg", "svg"),
        "platform_qtf_fz": ("StarViewer", "save_figure_svg", "svg"),
        "platform_wave": ("HyView", "native_recording_frame", "png"),
        "platform_pressure": ("HyView", "native_recording_frame", "png"),
    }
    entries = {entry["key"]: entry for entry in record["figures"]}
    require(
        entries.keys() == expected.keys()
        and len(record["figures"]) == len(document.result_viewers) == len(expected)
        and set(document.result_viewers) == set(expected),
        "Each bundled-viewer result needs one gallery figure",
    )
    readmes = [
        (ROOT / name).read_text(encoding="utf-8")
        for name in ("README.md", "README.en.md")
    ]
    case = record["hyview_case"]
    for key, entry in entries.items():
        viewer, method, fmt = expected[key]
        source = f"docs/assets/{key}_{viewer.lower()}.{fmt}"
        web_path = source.removeprefix("docs/")
        require(
            entry["status"] == "verified"
            and entry["origin"] == "hydrostar_bundled_viewer"
            and (entry["viewer"], entry["export_method"], entry["format"])
            == expected[key]
            and entry["image"] == source
            and sha256(ROOT / source) == entry["sha256"]
            and sum(img.get("src") == web_path for img in document.images) == 1
            and web_path in document.links
            and all(f"]({source})" in readme for readme in readmes),
            "Bundled-viewer result or public references differ: " + key,
        )
        if fmt == "svg":
            svg = ElementTree.parse(ROOT / source).getroot()
            namespace = "{http://www.w3.org/2000/svg}"
            require(
                svg.tag == namespace + "svg"
                and [float(x) for x in svg.attrib["viewBox"].split()[2:]]
                == entry["size"]
                and svg.find(f".//{namespace}path") is not None
                and not any(
                    e.tag.rsplit("}", 1)[-1] in ("image", "foreignObject", "script")
                    for e in svg.iter()
                ),
                "StarViewer curve export must be a pure vector image: " + key,
            )
            for path, digest in entry["sources_sha256"].items():
                require(
                    sha256(ROOT / path) == digest,
                    "Viewer curve source changed: " + path,
                )
        else:
            with Image.open(ROOT / source) as png:
                require(
                    png.format == "PNG" and list(png.size) == entry["size"],
                    "Invalid HyView still",
                )
                png.verify()
            recording = entry["original_recording"]
            require(
                0 <= recording["frame_index_zero_based"] < recording["frame_count"]
                and recording["physical_time_s"] is None
                and recording["physical_phase_deg"] is None
                and entry["field_card"] in case["published_evidence_sha256"],
                "HyView frame provenance or HSPRS card missing",
            )
    rao = entries["platform_rao"]
    require(
        len(rao["sources_sha256"]) == 6, "The bundled RAO uses all six motion files"
    )
    for path in rao["sources_sha256"]:
        data = core.read_rao(ROOT / path)
        settings = rao["settings"]
        require(
            settings["heading_deg"] in data["headings"]
            and settings["frequency_count"] == len(data["omega"])
            and settings["omega_rad_s"] == [data["omega"][0], data["omega"][-1]],
            "Bundled RAO range or heading differs from the original",
        )
    qtf = entries["platform_qtf_fz"]
    data = read_difference_qtf(ROOT / next(iter(qtf["sources_sha256"])))
    invalid = [
        w + d / 2
        for w, row in zip(data["omega1_rad_s"], supported_pairs(data), strict=True)
        for d, valid in zip(data["difference_rad_s"], row, strict=True)
        if not valid
    ]
    require(
        data["direction"] == 3
        and data["headings_deg"] == [qtf["settings"]["heading_deg"]]
        and data["difference_rad_s"] == qtf["settings"]["difference_omega_rad_s"]
        and qtf["settings"]["visible_mean_omega_rad_s_approx"][1] < min(invalid),
        "The QTF view must use vertical loads and exclude invalid pairs",
    )
    for key in ("primary_sources_sha256", "published_evidence_sha256"):
        for path, digest in case[key].items():
            require(
                sha256(ROOT / path) == digest, "HyView case evidence changed: " + path
            )
    report_path = ROOT / case["native_run_verification"]
    report = read_json(report_path)
    errors = compare_responses(report_path.parent / "rao")
    recorded_errors = report["response_max_complex_delta_over_reference_peak"]
    require(
        report["hslec"]["symmetry"] == 0
        and report["hslec"]["hull_panels"] == case["wet_panels"]
        and report["hslec"]["waterplane_panels"] == case["waterplane_panels"]
        and case["wet_panels"] + case["waterplane_panels"]
        == report["total_panels"]
        == case["full_total_panels"]
        <= 3000
        and errors.keys() == recorded_errors.keys()
        and all(
            math.isclose(error, recorded_errors[dof], rel_tol=1e-8, abs_tol=1e-13)
            for dof, error in errors.items()
        ),
        "Full HyView case budget and comparison with its symmetric reference",
    )
    return len(entries)


def check_gallery_media():
    class Media(HTMLParser):
        def __init__(self):
            super().__init__()
            self.cases, self.images, self.links = [], [], []
            self.geometry_cases, self.viewer_cases, self.result_viewers = [], [], []

        def handle_starttag(self, tag, attributes):
            attrs = dict(attributes)
            if tag == "section" and "data-result-case" in attrs:
                self.cases.append(attrs["data-result-case"])
            if tag == "article" and "data-geometry-case" in attrs:
                self.geometry_cases.append(attrs["data-geometry-case"])
            if (
                tag == "figure"
                and attrs.get("data-image-origin") == "hydrostar-bundled-viewer"
            ):
                if "data-viewer-case" in attrs:
                    self.viewer_cases.append(attrs["data-viewer-case"])
                if "data-result-viewer" in attrs:
                    self.result_viewers.append(attrs["data-result-viewer"])
            if tag == "img":
                self.images.append(attrs)
            if tag == "a":
                self.links.append(attrs.get("href", ""))

    document = Media()
    document.feed((ROOT / "docs/index.html").read_text(encoding="utf-8"))
    cases = {"vessel", "platform", "container", "tanker"}
    require(
        set(document.cases) == cases and len(document.cases) == 4,
        "Four visible result chapters required",
    )
    previews = {
        item["preview"].removeprefix("docs/")
        for item in read_json(ROOT / "examples/visualization/readme-media.json")[
            "media"
        ]
    }
    qtf_animations = read_json(ROOT / "examples/second-order/platform/animation.json")
    previews.update(
        item["gif"].removeprefix("docs/") for item in qtf_animations["media"].values()
    )
    animated = [image for image in document.images if "data-animation" in image]
    require(
        {image["data-animation"] for image in animated} == previews
        and len(animated) == 10,
        "Gallery and bilingual README dynamic media differ",
    )
    sources = [image.get("src", "") for image in document.images]
    require(
        "assets/readme-meshes.png" in sources, "ParaView companion mesh plate required"
    )
    geometry = read_json(ROOT / "docs/data/geometry.json")["cases"]
    require(
        set(document.geometry_cases) == {case["key"] for case in geometry}
        and len(document.geometry_cases) == len(geometry)
        and "#geometry-heading" in document.links,
        "Complex geometry chapters and navigation required",
    )
    geometry_figures = ["assets/geometry-source-cases.png"] + [
        case[field] for case in geometry for field in ("geometry_figure", "rao_figure")
    ]
    for source in geometry_figures:
        require(source in sources, "Complex geometry figure missing: " + source)
        for name in ("README.md", "README.en.md"):
            require(
                f"](docs/{source})" in (ROOT / name).read_text(encoding="utf-8"),
                "Complex geometry figure missing in " + name + ": " + source,
            )
    from PIL import Image

    viewer_figures = read_json(ROOT / "examples/visualization/viewer-exports.json")[
        "figures"
    ]
    expected = {
        case["key"]: (case["package"], case["wet_panels"], case["total_panels"])
        for case in presentation_data()["cases"]
    }
    expected.update(
        {
            case["key"]: (
                f"examples/geometry/{case['key']}",
                case["panels"],
                case["full_equivalent_total"],
            )
            for case in geometry
        }
    )
    second_order = "examples/second-order/platform"
    expected["platform_exterior"] = (
        second_order,
        expected["platform"][1],
        read_json(ROOT / second_order / "verification.json")["main_total_panels"],
    )
    require(
        len(viewer_figures) == len(document.viewer_cases) == len(expected)
        and {entry["case"] for entry in viewer_figures} == set(expected)
        and set(document.viewer_cases) == set(expected),
        "Each public mesh needs one bundled-viewer export and one gallery entry",
    )
    require(
        len({entry["image_sha256"] for entry in viewer_figures}) == len(expected),
        "Bundled-viewer images must be distinct",
    )
    for entry in viewer_figures:
        key = entry["case"]
        package, wet, total = expected[key]
        project = (
            "platform2"
            if key == "platform_exterior"
            else read_json(ROOT / package / "config.json")["project"]
        )
        solved_hst = f"{package}/inputs/{project}.hst"
        _, stored_faces, mesh_meta = core.read_hst(ROOT / solved_hst)
        symmetry = int(mesh_meta["SYMMETRY_BODY"][0][1])
        exterior = (
            len(read_integration_mesh(ROOT / solved_hst)["faces"]) * 2**symmetry
            if key == "platform_exterior"
            else 0
        )
        require(
            entry["origin"] == "hydrostar_bundled_viewer"
            and entry["viewer"] == "Visu5D"
            and entry["status"] == "verified"
            and entry["wet_panels"] == wet == len(stored_faces) * 2**symmetry
            and entry.get("exterior_panels", 0) == exterior
            and entry["full_equivalent_total"] == total <= 3000
            and entry.get("symmetry_display", "as_stored")
            == ("viewer_mirror" if symmetry else "as_stored"),
            "Bundled-viewer origin and mesh acceptance: " + key,
        )
        require(
            entry["solved_hst"] == solved_hst
            and sha256(ROOT / entry["source"])
            == entry["source_sha256"]
            == sha256(ROOT / solved_hst),
            "Bundled-viewer source must be the solved mesh: " + key,
        )
        source = entry["image"]
        require(
            source == f"docs/assets/{key}_visu5d.jpg"
            and sha256(ROOT / source) == entry["image_sha256"],
            "Bundled-viewer export path and hash: " + key,
        )
        with Image.open(ROOT / source) as exported:
            require(
                exported.format == entry["format"] == "JPEG"
                and exported.size == (entry["width"], entry["height"]),
                "Bundled-viewer export format and size",
            )
            exported.verify()
        require(
            sources.count(source.removeprefix("docs/")) == 1
            and source.removeprefix("docs/") in document.links,
            "Bundled-viewer image missing from gallery",
        )
        for name in ("README.md", "README.en.md"):
            require(
                f"]({source})" in (ROOT / name).read_text(encoding="utf-8"),
                "Bundled-viewer image missing from " + name,
            )
    for key in cases:
        require(
            f"assets/{key}-response.png" in sources,
            "Native response overview missing: " + key,
        )
    for target in (
        sources + [image["data-animation"] for image in animated] + document.links
    ):
        if not target or target.startswith("#") or urlsplit(target).scheme:
            continue
        path = (ROOT / "docs" / unquote(urlsplit(target).path)).resolve()
        require(
            path.is_relative_to(ROOT / "docs") and path.is_file(),
            "Missing gallery asset: " + target,
        )
    return dict(
        gallery_result_chapters=4,
        gallery_dynamic_views=10,
        gallery_geometry_chapters=len(geometry),
        gallery_bundled_viewer_exports=len(viewer_figures),
        gallery_bundled_result_exports=check_result_viewer_exports(document),
    )


def check_results():
    base = ROOT / "examples/results"
    index = read_json(base / "index.json")
    require(index["case_count"] == len(FORMS), "Example count changed")
    require({c["form_id"] for c in index["cases"]} == set(FORMS), "Example IDs changed")
    showcase = read_json(ROOT / "docs/data/showcase.json")
    gallery = {c["key"]: c for c in showcase["cases"]}
    require(set(gallery) == set(FORMS), "Gallery example IDs changed")
    total_values = 0
    for entry in index["cases"]:
        key = entry["form_id"]
        summary_path = base / entry["path"]
        require(sha256(summary_path) == entry["summary_sha256"], key + ": summary hash")
        folder = summary_path.parent
        summary = read_json(summary_path)
        cfg_json = read_json(folder / "config.json")
        cfg = CaseConfig.model_validate(cfg_json)
        require(summary["form_id"] == key, key + ": wrong summary ID")
        require(
            summary["publication_version"] == __version__, key + ": publication version"
        )
        require(set(summary["quality_gates"]) == GATES, key + ": incomplete gates")
        require(
            set(summary["quality_gates"].values()) == {"passed"}, key + ": gate failed"
        )
        require(
            set(summary["topology"]) == COUNTERS | {"pass"}, key + ": topology counters"
        )
        require(
            summary["topology"]["pass"]
            and all(summary["topology"][c] == 0 for c in COUNTERS),
            key + ": topology failed",
        )
        require(summary["solver_mechanics"]["balanced"], key + ": native balance")
        require(
            all(g > 0 for g in summary["solver_mechanics"]["gm_roll_pitch_m"]),
            key + ": GM",
        )
        require(
            not summary["reference_model"]["engineering_acceptance"]["ready"],
            key + ": engineering evidence classification",
        )
        require(
            summary["provenance"]["external_mesh_files"] == [],
            key + ": geometry origin",
        )
        require(
            all(s["ok"] and s["rc"] == 0 for s in summary["steps"]),
            key + ": native module status",
        )
        actual = {
            p.relative_to(folder).as_posix()
            for p in folder.rglob("*")
            if p.is_file() and p.name != "summary.json"
        }
        require(actual == set(summary["files"]), key + ": unindexed files")
        for name, expected in summary["files"].items():
            file_path = (folder / name).resolve()
            require(
                file_path.is_relative_to(folder.resolve()), key + ": invalid file path"
            )
            require(sha256(file_path) == expected, key + ": hash mismatch " + name)
        hst = folder / "inputs" / (cfg.project + ".hst")
        hyd = core.hydrostatics(hst)
        require(
            math.isclose(
                hyd["volume"], summary["hydrostatics"]["volume"], rel_tol=1e-10
            ),
            key + ": volume",
        )
        require(
            hyd["n_panels"] == summary["mesh"]["hull_panels"], key + ": panel count"
        )
        motions = read_json(folder / "motions.json")
        require(set(motions) == set(core.DOFS), key + ": DOFs")
        for dof in core.DOFS:
            native = core.read_rao(folder / "rao" / (dof + ".rao"))
            exported = motions[dof]
            require(
                exported == {k: native[k] for k in exported},
                key + ": raw/JSON mismatch " + dof,
            )
            require(
                set(exported) == {"omega", "headings", "amplitude", "phase", "unit"},
                key + ": array fields",
            )
            require(
                native["unit"] == ("m/m" if dof in core.DOFS[:3] else "deg/m"),
                key + ": units",
            )
            for grid_name, grid in [
                ("omega", cfg.environment.frequency),
                ("headings", cfg.environment.headings),
            ]:
                expected = core.grid_values(grid.min, grid.max, grid.step)
                require(len(native[grid_name]) == len(expected), key + ": grid length")
                require(
                    all(
                        math.isclose(a, b, abs_tol=1e-6)
                        for a, b in zip(native[grid_name], expected)
                    ),
                    key + ": grid values",
                )
            require(
                len(native["omega"]) == summary["frequency_count"],
                key + ": frequency count",
            )
            require(
                len(native["headings"]) == summary["heading_count"],
                key + ": heading count",
            )
            for field in ("amplitude", "phase"):
                require(
                    all(math.isfinite(v) for row in native[field] for v in row),
                    key + ": finite arrays",
                )
                total_values += sum(map(len, native[field]))
        model = gallery[key]
        require(model["responses"] == motions, key + ": gallery responses")
        require(
            model["summary"] == summary and model["config"] == cfg_json,
            key + ": gallery metadata",
        )
        vertices, faces = whole_mesh(hst)
        require(model["faces"] == faces, key + ": gallery mesh")
        require(
            model["vertices"] == [[round(v, 6) for v in p] for p in vertices],
            key + ": gallery vertices",
        )
    html = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="data">(.*?)</script>', html, re.S
    )
    from scripts.gallery_data import presentation_data

    require(
        match is not None and json.loads(match[1]) == presentation_data(),
        "Embedded gallery dataset",
    )
    require(
        not re.search(r"\b[0-9a-f]{64}\b|source_case_id", html),
        "Audit identifiers must stay in the data packages",
    )
    require("__SHOWCASE_DATA__" not in html, "Unbuilt gallery")
    node = shutil.which("node")
    if node:
        for script in re.findall(r"<script>(.*?)</script>", html, re.S):
            syntax = subprocess.run(
                [node, "--check"],
                input=script,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=20,
            )
            require(
                syntax.returncode == 0,
                "Gallery JavaScript syntax: " + syntax.stderr[-1000:],
            )
    require(
        not re.search(r"<script[^>]+src=|\bfetch\s*\(", html),
        "Gallery must work offline",
    )
    for stem in ["reference-geometry"] + [key + "_rao" for key in FORMS]:
        for suffix in (".png", ".pdf"):
            require(
                (ROOT / "docs/assets" / (stem + suffix)).stat().st_size > 1000,
                "Missing figure " + stem + suffix,
            )
    return dict(native_cases=len(FORMS), response_values=total_values)


def main():
    try:
        files = public_files()
        check_files(files)
        links = check_links(files)
        results = check_results()
        from scripts.check_wavefields import check_wavefields

        results.update(check_wavefields())
        from scripts.check_pressures import check_pressures

        results.update(check_pressures())
        from scripts.check_geometry import check_geometry

        results.update(check_geometry())
        from scripts.check_native_media import check_native_media

        results.update(check_native_media())
        from scripts.export_readme_media import check as check_readme_media

        results.update(check_readme_media())
        from scripts.check_second_order import check_second_order

        results.update(check_second_order())
        results.update(check_gallery_media())
        print(
            json.dumps(
                dict(
                    status="passed",
                    version=__version__,
                    public_files=len(files),
                    local_links=links,
                    **results,
                ),
                indent=2,
            )
        )
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print("Publication check failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
