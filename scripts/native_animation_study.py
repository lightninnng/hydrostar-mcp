"""Generate native HSprv field animations in isolated, reproducible workspaces."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import core
from hydrostar_mcp.visualization import whole_mesh
from hydrostar_mcp.workflow import file_hash, save_json

SETTINGS = {
    "container": ("container_kcs_style", 0.5, 60.0),
    "tanker": ("tanker_kvlcc2_style", 0.4, 60.0),
    "platform": ("semisub_oc4_style", 0.8, 60.0),
    "vessel": (None, 0.65, 60.0),
}


def run_one(key, frames=40):
    source_key, omega, heading = SETTINGS[key]
    if source_key is None:
        source_record = json.loads(
            (ROOT / "output/validation/course-vessel-wave-native.json").read_text(
                encoding="utf-8"
            )
        )
    else:
        source_record = json.loads(
            (ROOT / "output/validation/wavefield_study.json").read_text(
                encoding="utf-8"
            )
        )["cases"][source_key]
    source = Path(source_record["directory"])
    native = json.loads((source / "report.json").read_text(encoding="utf-8"))
    if native["status"] != "completed" or set(native["quality_gates"].values()) != {
        "passed"
    }:
        raise ValueError("A completed native case is required")
    folder = (
        ROOT
        / "output/validation/native-views"
        / ("vessel-wave" if key == "vessel" else key)
    )
    project = native["project"]
    if not folder.exists():
        folder.mkdir(parents=True)
        for p in source.iterdir():
            if p.is_file():
                shutil.copyfile(p, folder / p.name)
        for name in ("bin", "hdf"):
            if (source / name).is_dir():
                shutil.copytree(source / name, folder / name)
    else:
        old = json.loads((folder / "source.json").read_text(encoding="utf-8"))
        if old["source_case_id"] != native["case_id"]:
            raise ValueError("Native-view workspace belongs to a different calculation")
    cfg = native["config"]
    period = 2 * math.pi / omega
    source_info = dict(
        source_case_id=native["case_id"],
        project=project,
        mesh_sha256=file_hash(source / (project + ".hst")),
        omega_rad_s=omega,
        heading_deg=heading,
        wave_amplitude_m=0.5,
        depth_m=cfg["environment"]["depth"],
        gravity_m_s2=cfg["environment"]["gravity_m_s2"],
        rho_kg_m3=cfg["environment"]["rho_kg_m3"],
        period_s=period,
        frames=frames,
    )
    if (folder / "native-export.json").exists():
        previous = json.loads(
            (folder / "native-export.json").read_text(encoding="utf-8")
        )
        same = all(previous.get(k) == v for k, v in source_info.items())
        cards = [
            p
            for p in folder.glob("*.prv")
            if file_hash(p) == previous.get("input_sha256")
        ]
        intact = all(
            (folder / p).is_file() and file_hash(folder / p) == h
            for p, h in previous.get("native_files", {}).items()
        )
        if same and cards and intact and previous.get("ok"):
            print(key + ": reusing verified HSprv output", flush=True)
            return previous
        raise ValueError(
            "Existing animation export differs; select a new workspace or diagnose its input/files"
        )
    save_json(folder / "source.json", source_info)
    vertices, _ = whole_mesh(source / (project + ".hst"))
    lo = [min(p[k] for p in vertices) for k in (0, 1)]
    hi = [max(p[k] for p in vertices) for k in (0, 1)]
    span = max(hi[k] - lo[k] for k in (0, 1))
    center = [(lo[k] + hi[k]) / 2 for k in (0, 1)]
    half = [span * 0.9, span * (0.6 if (hi[0] - lo[0]) / (hi[1] - lo[1]) > 3 else 0.9)]
    grid = "".join(
        f"{axis}MIN {center[k] - half[k]:.12g}\n{axis}MAX {center[k] + half[k]:.12g}\n{axis}STP {2 * half[k] / 60:.12g}\n"
        for k, axis in enumerate(("X", "Y"))
    )
    card = (
        grid + f"TMIN 0\nTMAX {period:.12g}\nTSTP {period / frames:.12g}\n"
        f"AIRY 0.5 {heading:.12g} {omega:.12g}\nDIFWAVE\nSHIP\nNB_PROC 1\nENDFILE\n"
    )
    (folder / "tmp").mkdir(exist_ok=True)
    path = folder / "animation.prv"
    path.write_text(card, encoding="ascii")
    print(key + ": HSprv native field and motion export", flush=True)
    result = core.run(
        "hsprv",
        [path.name, project],
        folder,
        timeout=1200,
        log_path=folder / "logs/hsprv.log",
    )
    if not result.ok:
        raise ValueError(str(result.error_code) + " " + result.log[-1200:])
    files = {
        p.relative_to(folder).as_posix(): file_hash(p)
        for p in (folder / "Anim").rglob("*")
        if p.is_file()
    }
    if not files or not any(p.endswith(".pvd") for p in files):
        raise ValueError("HSprv did not produce its native animation index")
    record = dict(
        **source_info,
        ok=True,
        rc=result.rc,
        seconds=result.seconds,
        input_file=path.name,
        input_sha256=file_hash(path),
        native_files=files,
    )
    save_json(folder / "native-export.json", record)
    print(key + ": " + str(len(files)) + " native animation files", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=list(SETTINGS), action="append")
    parser.add_argument("--frames", type=int, default=40)
    args = parser.parse_args()
    if not 16 <= args.frames <= 120:
        parser.error("frames must be between 16 and 120")
    for key in args.case or SETTINGS:
        run_one(key, args.frames)


if __name__ == "__main__":
    main()
