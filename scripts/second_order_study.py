"""Compute a full difference-frequency QTF on the accepted platform wet mesh.

The native free-surface mesh is included in the same 3000-panel total budget.
Use --source for an independently completed first-order platform case directory.
"""

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.workflow import file_hash, save_json
from scripts.second_order_ring_surface import surface_mesh


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(source, surface_size):
    native = read(source / "report.json")
    if native["status"] != "completed" or set(native["quality_gates"].values()) != {
        "passed"
    }:
        raise ValueError("A completed, accepted first-order case is required")
    if native["config"]["geometry"]["type"] != "column_semisub":
        raise ValueError("This study is the explicitly configured platform example")
    project = "platform2"
    work = (
        ROOT
        / "output/validation/second-order"
        / ("platform-rings-" + f"{surface_size:g}")
    )
    work.mkdir(parents=True, exist_ok=True)
    original = source / (native["project"] + ".hst")
    generated = work / "geometry" / (project + ".hst")
    metadata = generated.with_suffix(".surface.json")
    surface = read(metadata) if metadata.exists() else None
    if not (
        surface
        and generated.exists()
        and surface["output_hst_sha256"] == file_hash(generated)
        and surface["source_hst_sha256"] == file_hash(original)
        and surface.get("generator_script_sha256")
        == file_hash(ROOT / "scripts/second_order_ring_surface.py")
        and surface.get("quality_utility_sha256")
        == file_hash(ROOT / "scripts/second_order_surface.py")
    ):
        surface = surface_mesh(original, generated, outer_size=surface_size)
    hst = generated.read_text(encoding="ascii")
    # Freeze each accepted integration mesh in its own native workspace.
    # A later geometry refinement keeps the previous database and logs intact.
    work = work / ("native-" + file_hash(generated)[:10])
    work.mkdir(parents=True, exist_ok=True)
    cards = {
        project + ".hst": hst,
        project + ".mcn": (source / (native["project"] + ".mcn"))
        .read_bytes()
        .decode("ascii"),
        project + ".rdf": (
            "FILENAME rd1\nFREQUENCY TYPE 1\n"
            + " ".join(
                f"{value:.6g}"
                for value in [0.05, 0.10] + [0.4 + 0.025 * i for i in range(29)]
            )
            + "\nENDFREQUENCY\n"
            "HEADING TYPE 2\nHMIN 60\nHMAX 60\nHSTP 1\nENDHEADING\n"
            "WATERDEPTH 200\nSPEEDS TYPE 0\n1 0\nENDSPEEDS\nENDFILE\n"
        ),
        "drift.dft": "NFORMULE YES\nFFORMULE YES\nMFORMULE NO\nENDFILE\n",
        "full.qtf": (
            "DIFFREQUENCY 0.00 0.10 0.05\nWAVFREQUENCY 0.50 1.10 0.05\n"
            "TYPEFORMULE NEAR-FIELD\nMODE DIFF\nFSMETHOD QUADPACK\nNBES 30\nENDFILE\n"
        ),
        "results.rao": "OUTPUTFOLDER rao\n"
        + "".join(f"G{name.upper()} BODY 1 FILE {name}.rao\n" for name in core.DOFS)
        + "".join(
            f"DRIFT{component.upper()} BODY 1 FILE drift_{component}_near.rao PRE COS\n"
            for component in ("fx", "fy", "fz", "mx", "my", "mz")
        )
        + "".join(
            f"DRIFT{component.upper()} BODY 1 FILE drift_{component}_far.rao MOM COS\n"
            for component in ("fx", "fy", "mz")
        )
        + "".join(
            f"QTF{component.upper()} BODY 1 FILE qtf_{component}.qtf\n"
            for component in ("fx", "fy", "fz", "mx", "my", "mz")
        )
        + "ENDFILE\n",
    }
    input_hashes = {}
    for name, text in cards.items():
        path = work / name
        payload = text.encode("ascii")
        if path.exists() and path.read_bytes() != payload:
            raise ValueError("Existing study input changed: " + name)
        path.write_bytes(payload)
        input_hashes[name] = file_hash(path)
    before_nodes, before_panels, _ = core.read_hst(original)
    after_nodes, after_panels, _ = core.read_hst(work / (project + ".hst"))
    if [[before_nodes[i] for i in p] for p in before_panels] != [
        [after_nodes[i] for i in p] for p in after_panels
    ]:
        raise ValueError("Second-order study must retain the accepted wet mesh")
    status_path = work / "study.json"
    state = (
        read(status_path)
        if status_path.exists()
        else dict(
            project=project,
            source_project=native["project"],
            source_wet_mesh_sha256=file_hash(original),
            input_hashes=input_hashes,
            free_surface={
                k: v for k, v in surface.items() if k not in ("vertices", "panels")
            },
            method="Full difference-frequency QTF, near-field, including the free-surface Haskind integral with QUADPACK and NBES=30",
            steps=[],
        )
    )
    if state["input_hashes"] != input_hashes:
        raise ValueError("Study input hashes differ")
    completed = {step["name"] for step in state["steps"] if step["ok"]}
    sequence = (
        ("hslec", project + ".hst", "mesh", 0),
        ("hschk", "-", "topology", 0),
        ("hsrdf", project + ".rdf", "first-order", 2),
        ("hsmcn", project + ".mcn", "mechanics", 0),
        ("hsdft", "drift.dft", "mean-drift", 2),
        ("hsamg", "full.qtf", "second-order-potential", 2),
        ("hsqtf", "full.qtf", "full-qtf", 2),
        ("hsrao", "results.rao", "extraction", 0),
    )
    for module, card, name, nproc in sequence:
        if name in completed:
            print(name + ": reusing recorded native stage", flush=True)
            continue
        print(f"platform surface {surface_size:g} m: {module} ({name})", flush=True)
        result = core.run(
            module,
            [card, project],
            work,
            nproc=nproc,
            timeout=1800,
            log_path=work / "logs" / (module + ".log"),
        )
        step = dict(
            name=name,
            module=module,
            input=card,
            ok=result.ok,
            rc=result.rc,
            seconds=result.seconds,
            error_code=result.error_code,
        )
        state["steps"].append(step)
        state["status"] = "running" if result.ok else "failed"
        if result.ok and module == "hslec":
            mesh = core.parse_hslec(result.log)
            match = re.search(r"Nb panels over the free surface\s+(\d+)", result.log)
            if not match:
                raise ValueError("Native free-surface panel count required")
            mesh["exterior_free_surface_panels"] = int(match[1])
            mesh["full_equivalent_total_including_exterior"] = (
                mesh["hull_panels"]
                + mesh["waterplane_panels"]
                + mesh["exterior_free_surface_panels"]
            ) * 2 ** mesh["symmetry"]
            state["mesh"] = mesh
            if mesh["full_equivalent_total_including_exterior"] > 3000:
                state["status"] = "budget_exceeded"
                save_json(status_path, state)
                raise ValueError(
                    "3000 total-panel budget includes the exterior free surface"
                )
        if result.ok and module == "hschk":
            state["topology"] = core.parse_hschk(result.log)
            if not state["topology"]["pass"]:
                raise ValueError("Native topology checks failed")
        if result.ok and module == "hsmcn":
            state["mechanics"] = core.parse_hsmcn(result.log)
            if not state["mechanics"]["balanced"]:
                raise ValueError("Native mechanics balance failed")
        save_json(status_path, state)
        if not result.ok:
            raise ValueError(f"{module}: {result.error_code}\n{result.log[-2200:]}")
    state["status"] = "computed"
    state["result_files"] = {
        path.name: file_hash(path)
        for path in (work / "rao").iterdir()
        if path.suffix in (".rao", ".qtf")
    }
    save_json(status_path, state)
    print("Native second-order calculation completed: " + str(work), flush=True)
    return work


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--surface-size", type=float, choices=(6.5, 7.5), default=6.5)
    args = parser.parse_args()
    source = args.source
    if source is None:
        source = Path(
            read(ROOT / "output/validation/reference_form_study.json")["cases"][
                "semisub_oc4_style"
            ]["directory"]
        )
    run(source.resolve(), args.surface_size)
