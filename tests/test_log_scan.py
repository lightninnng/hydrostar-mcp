import sys

from hydrostar_mcp import core


def test_equilibrium_diagnostic_in_the_middle_of_a_long_log(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "hstar_bin", lambda _: sys.executable)
    code = "print('x'*70000);print('Warning the ship is not balanced');print('x'*70000)"
    result = core.run("hsmcn", ["-c", code], tmp_path, timeout=5)
    assert result.error_code == "SOLVER_EQUILIBRIUM_FAILED"
    assert not result.ok
