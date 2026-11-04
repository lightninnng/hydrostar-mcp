"""Direct exports must retain native columns and reject invented/misread data."""

import csv
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/hydrostar-modeling/scripts"))
from export_hsrao import native_column, parse_macro, read_table, verify_csv
from hydrostar_mcp import core
from scripts.export_native_curves import CASES, GEOMETRY_CASES


@pytest.mark.parametrize("key", list(CASES) + list(GEOMETRY_CASES))
def test_original_macros_and_standalone_reader_match_published_native_data(key):
    geometry = key in GEOMETRY_CASES
    source = ROOT / (GEOMETRY_CASES if geometry else CASES)[key][0]
    folder = (
        source / "visualization"
        if geometry
        else ROOT / "examples/visualization/curves" / key
    )
    macro = parse_macro(folder / "native.gnu")
    for dof in core.DOFS:
        name = dof + ".rao"
        table = read_table(source / "rao" / name)
        parsed = core.read_rao(source / "rao" / name)
        assert table == {k: parsed[k] for k in table}
        assert [
            native_column(macro, name, table, h) for h in table["headings"]
        ] == list(range(2, 2 + len(table["headings"])))
        with pytest.raises(ValueError, match="Uncomputed heading"):
            native_column(macro, name, table, 17.5)


def test_wrong_macro_column_and_arbitrary_macro_command_are_rejected(tmp_path):
    path = ROOT / "examples/geometry/cad_spar/visualization/native.gnu"
    macro = parse_macro(path)
    table = read_table(ROOT / "examples/geometry/cad_spar/rao/pitch.rao")
    macro["pitch.rao"][0]["column"] += 1
    with pytest.raises(ValueError, match="Macro column differs"):
        native_column(macro, "pitch.rao", table, 60)
    unsafe = tmp_path / "unsafe.gnu"
    unsafe.write_text(
        path.read_text(encoding="utf-8") + "\nsystem 'arbitrary command'\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unsupported macro statement"):
        parse_macro(unsafe)


def test_csv_numeric_corruption_is_rejected(tmp_path):
    table = read_table(ROOT / "examples/geometry/cad_spar/rao/pitch.rao")
    path = tmp_path / "pitch.csv"
    rows = [
        [w, h, table["amplitude"][i][j], table["phase"][i][j], table["unit"]]
        for i, w in enumerate(table["omega"])
        for j, h in enumerate(table["headings"])
    ]

    def write():
        with path.open("w", encoding="utf-8", newline="") as stream:
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
            writer.writerows(rows)

    write()
    assert verify_csv(path, table) == 28
    rows[4][2] += 0.01
    write()
    with pytest.raises(ValueError, match="CSV differs"):
        verify_csv(path, table)
