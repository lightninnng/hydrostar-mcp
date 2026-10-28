import sys

import pytest

from hydrostar_mcp import core


@pytest.mark.parametrize(
    "line",
    [
        "Difference frequency missing  0.5000E-01",
        "*Wave frequence 2=     0.85000 cannot be found.",
        "Wave frequency 2= 0.65 cannot be found.",
    ],
)
def test_missing_second_order_frequency_rejects_partial_results(line):
    assert core.log_error(line) == "MISSING_FREQUENCY"


def test_equilibrium_diagnostic_in_the_middle_of_a_long_log(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    code = "print('x'*70000);print('Warning the ship is not balanced');print('x'*70000)"
    result = core.run("hsmcn", ["-c", code], tmp_path, timeout=5)
    assert result.error_code == "SOLVER_EQUILIBRIUM_FAILED"
    assert not result.ok


def test_native_error_blocks_postprocessing(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    code = "print('ERROR: Error when opening file tmp/hsprv.log.log')"
    result = core.run("hsprv", ["-c", code], tmp_path, timeout=5)
    # A live scan may stop the child while it is exiting normally.
    assert result.error_code == "INPUT_ERROR"
    assert not result.ok
