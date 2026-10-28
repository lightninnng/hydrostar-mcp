import pytest

from hydrostar_mcp.second_order import parse_difference_qtf, supported_pairs


NATIVE = """#QTFTYPE "2NDLOAD"
#CPLXTYPE 0
#QTFMODE Diff
#DIRECTION " 1
#COORD 0 0 -9.959
#NBHEADING 1
#HEADING 60
#DIFF 0 0.05
#Heading = 60
0.50 434.43 0 525.85 -2134.9
0.55 644.92 0 0 0
"""


def test_native_complex_qtf_retains_phase_and_masks_uncomputed_edge():
    data = parse_difference_qtf(NATIVE)
    assert data["values"][0][0][1] == [525.85, -2134.9]
    assert supported_pairs(data) == [[True, True], [True, False]]


@pytest.mark.parametrize(
    "broken",
    [
        NATIVE.replace("434.43 0", "434.43"),
        NATIVE.replace("#NBHEADING 1", "#NBHEADING 2"),
        NATIVE.replace("#CPLXTYPE 0", "#CPLXTYPE 1"),
        NATIVE.replace("434.43", "NaN"),
        NATIVE.replace("#DIFF 0 0.05", "#DIFF 0.05 0"),
    ],
)
def test_partial_or_ambiguous_qtf_is_rejected(broken):
    with pytest.raises(ValueError):
        parse_difference_qtf(broken)


def test_actual_integration_connectivity_excludes_wet_panels_and_retains_quads(
    tmp_path,
):
    from hydrostar_mcp.second_order import read_integration_mesh

    path = tmp_path / "mesh.hst"
    path.write_text(
        """PROJECT demo
NBBODY 1
SYMMETRY 1 1
NUMPANEL 1 1 1
NFREESURFACE 2 2 3
COORDINATES TYPE 0
1 0 0 -1
2 1 0 -1
3 1 1 -1
4 0 1 -1
5 0 0 0
6 1 0 0
7 1 1 0
8 0 1 0
9 2 0 0
ENDCOORDINATES
PANEL TYPE 0
1 2 3 4
8 7 6 5
6 7 9 9
ENDPANEL
ENDFILE
""",
        encoding="ascii",
    )
    mesh = read_integration_mesh(path)
    assert mesh["symmetry"] == 1
    assert [len(face) for face in mesh["faces"]] == [4, 3]
    assert all(point[2] == 0 for point in mesh["vertices"])
    path.write_text(
        path.read_text().replace("NFREESURFACE 2 2 3", "NFREESURFACE 3 2 4")
    )
    with pytest.raises(ValueError, match="incomplete"):
        read_integration_mesh(path)
