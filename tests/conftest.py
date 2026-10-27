"""Synthetic geometry and a fake solver for orchestration tests, NOT physics validation."""

from pathlib import Path
import re

import pytest

from hydrostar_mcp import core
from hydrostar_mcp.workflow import CaseService

CHECK_LINES = [
    "nb of zero-area panels",
    "nb of panels over free surface",
    "nb of panels at free surface",
    "nb of superpositions",
    "nb of inconsistences",
    "nb of neighbor-absences",
    "nb of symmetry problem",
]
CHECK_LOG = "\n".join(name + " = 0" for name in CHECK_LINES)


def box_mesh(path, symmetry=1, free_surface=0, indexed=False):
    """A hand-defined 10x4x2 wet rectangular box with outward normals."""
    xmin = 0 if symmetry == 2 else -5
    ymin = 0 if symmetry else -2
    nodes = [
        (xmin, ymin, -2),
        (xmin, 2, -2),
        (xmin, 2, 0),
        (xmin, ymin, 0),
        (5, ymin, -2),
        (5, 2, -2),
        (5, 2, 0),
        (5, ymin, 0),
    ]
    panels = [(1, 2, 6, 5), (2, 3, 7, 6), (5, 6, 7, 8)]
    if symmetry != 2:
        panels.append((1, 4, 3, 2))
    if not symmetry:
        panels.append((1, 5, 8, 4))
    rows = [
        "NBBODY 1",
        f"SYMMETRY 1 {symmetry}",
        f"NUMPANEL 1 1 {len(panels)}",
        f"ZFSURFACE {free_surface}",
        "COORDINATES TYPE 0",
    ]
    rows += [f"{i} {x} {y} {z + free_surface}" for i, (x, y, z) in enumerate(nodes, 1)]
    rows += ["ENDCOORDINATES", f"PANEL TYPE {int(indexed)}"]
    rows += [
        (f"{i} " if indexed else "") + " ".join(map(str, p))
        for i, p in enumerate(panels, 1)
    ]
    rows += ["ENDPANEL", "ENDFILE"]
    Path(path).write_text("\n".join(rows) + "\n", encoding="utf-8")
    return Path(path)


def mesh_from_mri(mri, target):
    """Test-only bilinear mesher; production still exclusively uses hsmsh."""
    nodes, patches = {}, []
    for line in Path(mri).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "NODE":
            nodes[int(parts[1])] = tuple(map(float, parts[2:5]))
        if parts[0] == "PATCH":
            patches.append((list(map(int, parts[3:7])), int(parts[8]), int(parts[12])))
    coords, panels = [], []
    for ids, na, nb in patches:
        a, b, c, d = [nodes[i] for i in ids]
        grid = {}
        for j in range(nb + 1):
            v = j / nb
            for i in range(na + 1):
                u = i / na
                point = tuple(
                    (1 - u) * (1 - v) * a[k]
                    + u * (1 - v) * b[k]
                    + u * v * c[k]
                    + (1 - u) * v * d[k]
                    for k in range(3)
                )
                coords.append(point)
                grid[i, j] = len(coords)
        for j in range(nb):
            for i in range(na):
                panels.append(
                    (grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1])
                )
    rows = [
        "NBBODY 1",
        "SYMMETRY 1 1",
        f"NUMPANEL 1 1 {len(panels)}",
        "ZFSURFACE 0",
        "COORDINATES TYPE 0",
    ]
    rows += [f"{i} {x:.12g} {y:.12g} {z:.12g}" for i, (x, y, z) in enumerate(coords, 1)]
    rows += (
        ["ENDCOORDINATES", "PANEL TYPE 0"]
        + [" ".join(map(str, p)) for p in panels]
        + ["ENDPANEL", "ENDFILE"]
    )
    Path(target).write_text("\n".join(rows) + "\n", encoding="utf-8")


class FakeSolver:
    def __init__(self):
        self.calls = []
        self.fail_module = None
        self.fail_code = "PROCESS_FAILED"
        self.check_log = CHECK_LOG
        self.waterplane = 24
        self.omit_rao = None
        self.hslec_log = None
        self.hsmcn_log = None

    def __call__(self, module, args, cwd, **kwargs):
        self.calls.append(module)
        cwd = Path(cwd)
        log = "synthetic test solver output"
        rc = 0
        error = None
        if module == self.fail_module:
            rc = 1
            error = self.fail_code
            log = "synthetic intentional failure"
        elif module == "hsmsh":
            mesh_from_mri(cwd / args[0], cwd / "PRO.hst")
        elif module == "hslec":
            hyd = core.hydrostatics(cwd / args[0])
            log = (
                f"Nb of bodies to be analysed 1\nNb symmetry of hull geometry {hyd['sym']}\n"
                f"Nb panels on hulls {hyd['n_panels']}\nNb panels on the waterplanes {self.waterplane}\n"
            )
            if self.hslec_log is not None:
                log = self.hslec_log
        elif module == "hschk":
            log = self.check_log
        elif module == "hsmcn" and self.hsmcn_log is not None:
            log = self.hsmcn_log
        elif module == "hsrao":
            rdf = (cwd / (args[1] + ".rdf")).read_text()

            def value(key):
                return float(re.search(r"(?m)^" + key + r" (.+)$", rdf)[1])

            omega = core.grid_values(value("WMIN"), value("WMAX"), value("WSTP"))
            heads = core.grid_values(value("HMIN"), value("HMAX"), value("HSTP"))
            (cwd / "rao").mkdir()
            for instruction in (cwd / args[0]).read_text().splitlines():
                if not instruction.strip():
                    continue
                name = instruction.split("FILE ")[1].split()[0]
                if name == self.omit_rao:
                    continue
                unit = (
                    "deg/m"
                    if instruction.split()[0] in ("GROLL", "GPITCH", "GYAW")
                    else "m/m"
                )
                rows = [
                    f"#UNIT : {unit}",
                    f"#NBHEADING {len(heads)}",
                    "#HEADING " + " ".join(map(str, heads)),
                ]
                rows += [
                    " ".join(
                        map(
                            str,
                            [w]
                            + [0.5 + w / 100 + h / 10000 for h in heads]
                            + [0] * len(heads),
                        )
                    )
                    for w in omega
                ]
                (cwd / "rao" / name).write_text(
                    "\n".join(rows + ["#ENDFILE"]) + "\n", encoding="utf-8"
                )
        destination = kwargs.get("log_path")
        if destination:
            Path(destination).parent.mkdir(exist_ok=True, parents=True)
            Path(destination).write_text(log, encoding="utf-8")
        return core.RunResult(
            module,
            rc,
            log,
            0.001,
            [module, *args],
            error or core.log_error(log),
            str(destination) if destination else None,
        )


@pytest.fixture
def solver(monkeypatch):
    fake = FakeSolver()
    monkeypatch.setattr(core, "run", fake)
    return fake


@pytest.fixture
def service(tmp_path):
    instance = CaseService(root=tmp_path / "runs", source_root=tmp_path)
    yield instance
    instance.close()
