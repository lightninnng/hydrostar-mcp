"""Strict reader for native complex difference-frequency load QTFs."""

from __future__ import annotations

import math
from pathlib import Path
import re

from .core import NUMBER, number, read_hst


def read_difference_qtf(path):
    return parse_difference_qtf(Path(path).read_text(encoding="utf-8"))


def parse_difference_qtf(text):
    metadata, headings, differences, blocks = {}, [], [], {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            upper = line.upper()
            if re.match(r"#HEADING\s*=", upper):
                current = number(line.split("=", 1)[1])
                if current in blocks:
                    raise ValueError("Duplicate native QTF heading block")
                blocks[current] = []
            elif re.match(r"#HEADING\s+", upper):
                headings = [number(v) for v in line.split()[1:]]
            elif re.match(r"#DIFF\s+", upper):
                differences = [number(v) for v in line.split()[1:]]
            elif upper.startswith("#QTFTYPE"):
                metadata["type"] = line.split(maxsplit=1)[1].strip('" ')
            elif upper.startswith("#CPLXTYPE"):
                metadata["complex_type"] = int(line.split()[1])
            elif upper.startswith("#QTFMODE"):
                metadata["mode"] = line.split()[1].lower()
            elif upper.startswith("#DIRECTION"):
                metadata["direction"] = int(re.findall(NUMBER, line)[-1])
            elif upper.startswith("#NBHEADING"):
                metadata["heading_count"] = int(line.split()[1])
            elif upper.startswith("#COORD"):
                metadata["reference_point_m"] = [number(v) for v in line.split()[1:]]
            continue
        if current is None or not differences:
            raise ValueError("Native QTF axes and heading must precede values")
        values = [number(v) for v in line.split()]
        if len(values) != 1 + 2 * len(differences):
            raise ValueError("Incomplete native QTF row")
        blocks[current].append(
            (values[0], [values[i : i + 2] for i in range(1, len(values), 2)])
        )
    if metadata.get("type") != "2NDLOAD" or metadata.get("mode") != "diff":
        raise ValueError(
            "A native difference-frequency second-order load file is required"
        )
    if metadata.get("complex_type") != 0:
        raise ValueError("Native QTF must use explicit real and imaginary components")
    if metadata.get("direction") not in range(1, 7):
        raise ValueError("Native QTF load direction is missing")
    if (
        not headings
        or len(headings) != metadata.get("heading_count")
        or len(set(headings)) != len(headings)
        or set(blocks) != set(headings)
        or not differences
        or differences[0] < 0
        or any(b <= a for a, b in zip(differences, differences[1:]))
    ):
        raise ValueError(
            "Native QTF heading or difference-frequency coverage is incomplete"
        )
    omega = [row[0] for row in blocks[headings[0]]]
    if not omega or omega[0] <= 0 or any(b <= a for a, b in zip(omega, omega[1:])):
        raise ValueError("Native QTF wave frequencies must be positive and ordered")
    for heading in headings:
        if [row[0] for row in blocks[heading]] != omega:
            raise ValueError("Native QTF heading blocks use different frequency grids")
    return dict(
        **metadata,
        headings_deg=headings,
        omega1_rad_s=omega,
        difference_rad_s=differences,
        values=[[[pair for pair in row[1]] for row in blocks[h]] for h in headings],
        complex_convention="Native CPLXTYPE 0: real, imaginary",
        pair_convention="omega2 = omega1 + difference",
    )


def supported_pairs(data):
    """Mark pairs actually covered by the native wave-frequency grid."""
    omega = data["omega1_rad_s"]
    return [
        [
            any(math.isclose(w + d, other, abs_tol=1e-6) for other in omega)
            for d in data["difference_rad_s"]
        ]
        for w in omega
    ]


def read_integration_mesh(path):
    """Read the actual NFREESURFACE connectivity without changing panel types."""
    path = Path(path)
    nodes, _, meta = read_hst(path)
    bounds, all_panels, section, kind, automatic_id = None, {}, False, 0, 0
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        key = tokens[0].upper()
        if key == "NFREESURFACE":
            bounds = list(map(int, tokens[1:]))
        elif key in ("PANEL", "PANELS"):
            kind = int(tokens[-1])
            section = True
        elif key in ("ENDPANEL", "ENDPANELS"):
            section = False
        elif key == "ENDFILE":
            break
        elif section:
            automatic_id += 1
            panel_id = int(tokens[0]) if kind else automatic_id
            all_panels[panel_id] = list(dict.fromkeys(map(int, tokens[kind:])))
    if not bounds or len(bounds) != 3 or bounds[0] != bounds[2] - bounds[1] + 1:
        raise ValueError("Explicit exterior integration-panel bounds required")
    faces = []
    for i in range(bounds[1], bounds[2] + 1):
        if i not in all_panels or len(all_panels[i]) not in (3, 4):
            raise ValueError("Exterior integration connectivity is incomplete")
        faces.append(all_panels[i])
    used = sorted({i for face in faces for i in face})
    if any(i not in nodes or abs(nodes[i][2]) > 1e-8 for i in used):
        raise ValueError("Integration vertices must lie on the mean free surface")
    index = {tag: i for i, tag in enumerate(used)}
    return dict(
        vertices=[list(nodes[i]) for i in used],
        faces=[[index[i] for i in face] for face in faces],
        symmetry=int(meta["SYMMETRY_BODY"][0][1]),
    )


def harmonic_value(real, imaginary, difference_rad_s, time_s):
    """Phase-resolve a native complex coefficient under the positive-time basis.

    This is Re[Q exp(i*Delta*t)], in coefficient units. Actual bichromatic
    loads additionally require the native amplitude and ordered-pair convention.
    """
    real, imaginary, difference, time = map(
        number, (real, imaginary, difference_rad_s, time_s)
    )
    if difference < 0:
        raise ValueError("Difference frequency must be nonnegative")
    phase = difference * time
    return real * math.cos(phase) - imaginary * math.sin(phase)
