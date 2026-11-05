"""Re-run the accepted platform wet mesh with symmetry explicit for HyView."""

import argparse
import cmath
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hydrostar_mcp import core
from hydrostar_mcp.workflow import file_hash, save_json

SOURCE = ROOT / "examples/second-order/platform"
HYVIEW_SETTINGS = ROOT / "examples/visualization/hyview-platform/hyview/parameters.json"
PROJECT = "platform_hyview"
DOFS = ("surge", "sway", "heave", "roll", "pitch", "yaw")


def expand(source, destination):
    nodes, panels, meta = core.read_hst(source)
    if meta["SYMMETRY_BODY"] != [[1, 1]]:
        raise ValueError("The reference HST must be a single port/starboard half mesh")
    ids, faces = {}, []
    for sign in (1, -1):
        for panel in panels:
            distinct = list(dict.fromkeys(panel))
            if sign == -1:
                distinct[1:] = reversed(distinct[1:])
            face = []
            for index in distinct:
                x, y, z = nodes[index]
                point = (x, sign * y if y else 0.0, z)
                face.append(ids.setdefault(point, len(ids) + 1))
            faces.append(face + face[-1:] * (4 - len(face)))
    header = (
        f"PROJECT {PROJECT}\nUSER NATIVE_VIEWER\nNBBODY 1\nSYMMETRY 1 0\n"
        f"NUMPANEL 1 1 {len(faces)}\nZFSURFACE {meta['ZFSURFACE'][0][0]:g}\n"
        f"RHO {meta['RHO'][0][0]:g}\nGRAVITY {meta['GRAVITY'][0][0]:g}\n"
    )
    lines = [header + "COORDINATES TYPE 0"]
    lines += [
        f"{index} " + " ".join(f"{value:.15g}" for value in point)
        for point, index in ids.items()
    ]
    lines += ["ENDCOORDINATES", "PANEL TYPE 0"]
    lines += [" ".join(map(str, face)) for face in faces]
    destination.write_text(
        "\n".join(lines + ["ENDPANEL", "ENDFILE", ""]), "ascii", newline="\n"
    )
    reference, expanded = map(core.hydrostatics, (source, destination))
    for key in ("volume", "wetted_area"):
        if not math.isclose(reference[key], expanded[key], rel_tol=1e-10):
            raise ValueError(f"Symmetry expansion changed {key}")
    if math.dist(reference["cb"], expanded["cb"]) > 1e-9:
        raise ValueError("Symmetry expansion changed the buoyancy centre")
    return expanded


def compare_responses(folder):
    def coefficients(response):
        return [
            cmath.rect(amp[0], math.radians(phase[0]))
            for amp, phase in zip(response["amplitude"], response["phase"], strict=True)
        ]

    errors = {}
    for dof in DOFS:
        name = f"{dof}.rao"
        reference = core.read_rao(SOURCE / "rao" / name)
        actual = core.read_rao(folder / name)
        for key in ("omega", "headings", "unit"):
            if reference[key] != actual[key]:
                raise ValueError(f"{name}: changed {key}")
        a, b = map(coefficients, (reference, actual))
        peak = max(map(abs, a))
        errors[dof] = max(abs(x - y) for x, y in zip(a, b, strict=True)) / peak
    return errors


def prepare(work):
    work.mkdir(parents=True, exist_ok=False)
    original = SOURCE / "inputs"
    cards = {ext: work / f"{PROJECT}.{ext}" for ext in ("hst", "rdf", "mcn", "rao")}
    geometry = expand(original / "platform2.hst", cards["hst"])
    for ext in ("rdf", "mcn"):
        shutil.copyfile(original / f"platform2.{ext}", cards[ext])
    extraction = [f"G{dof.upper()} BODY 1 FILE {dof}.rao" for dof in DOFS]
    cards["rao"].write_text(
        "\n".join(["OUTPUTFOLDER rao", *extraction, "ENDFILE", ""]),
        "ascii",
        newline="\n",
    )
    steps = []
    for module, extension in (
        ("hslec", "hst"),
        ("hschk", None),
        ("hsrdf", "rdf"),
        ("hsmcn", "mcn"),
        ("hsrao", "rao"),
    ):
        args = [cards[extension].name if extension else "-", PROJECT]
        print(module, *args, flush=True)
        log = work / "logs" / f"{module}.log"
        result = core.run(module, args, work, log_path=log)
        if not result.ok:
            raise ValueError(f"{module}: {result.error_code}\n{result.log[-2200:]}")
        steps.append(dict(module=module, args=args, log_sha256=file_hash(log)))
        if module == "hslec":
            mesh = core.parse_hslec(result.log)
            total = sum(mesh[k] for k in ("hull_panels", "waterplane_panels"))
            if (
                mesh["symmetry"] != 0
                or mesh["hull_panels"] != geometry["n_panels"]
                or mesh.get("exterior_free_surface_panels", 0) != 0
                or total > 3000
            ):
                raise ValueError(
                    "Explicit full platform failed the native panel budget"
                )
        elif module == "hschk" and not core.parse_hschk(result.log)["pass"]:
            raise ValueError("Native mesh topology checks failed")
        elif module == "hsmcn" and not core.parse_hsmcn(result.log)["balanced"]:
            raise ValueError("Native motion case is unbalanced")
    errors = compare_responses(work / "rao")
    report = dict(
        project=PROJECT,
        source_hst_sha256=file_hash(original / "platform2.hst"),
        inputs_sha256={p.name: file_hash(p) for p in cards.values()},
        geometry=geometry,
        hslec=mesh,
        total_panels=total,
        steps=steps,
        response_max_complex_delta_over_reference_peak=errors,
        databases_sha256={
            p.name: file_hash(p) for p in sorted((work / "hdf").glob("*.h5"))
        },
    )
    save_json(work / "verification.json", report)
    (work / "hyview").mkdir(exist_ok=True)
    shutil.copyfile(HYVIEW_SETTINGS, work / "hyview/parameters.json")
    print(
        f"{total} panels; maximum relative complex response difference: {max(errors.values()):.4%}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="A new working directory")
    prepare(parser.parse_args().output.resolve())
