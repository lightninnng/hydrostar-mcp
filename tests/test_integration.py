import os

import pytest

from hydrostar_mcp.models import CaseConfig
from hydrostar_mcp.workflow import CaseService


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("HS_RUN_INTEGRATION") != "1",
    reason="Set HS_RUN_INTEGRATION=1 to execute the installed HydroStar solver",
)
def test_installed_solver_chain(tmp_path):
    service = CaseService(root=tmp_path / "real_runs")
    try:
        prepared = service.prepare(CaseConfig(module_timeout_s=120))
        if prepared.get("error", {}).get("code") == "LICENSE_UNAVAILABLE":
            pytest.xfail(
                "Real HydroStar license unavailable; no numerical validation performed"
            )
        if prepared["status"] == "needs_confirmation":
            pytest.xfail("Measured mesh requires human review before solver execution")
        assert prepared["status"] == "prepared", prepared
        service.start(prepared["case_id"])
        future, _ = service.jobs[prepared["case_id"]]
        future.result(timeout=360)
        report = service.status(prepared["case_id"])
        if report.get("error", {}).get("code") == "LICENSE_UNAVAILABLE":
            pytest.xfail(
                "Solver-stage license unavailable; no complete numerical validation performed"
            )
        assert report["status"] == "completed", report
        heave = service.result(prepared["case_id"], "heave")
        assert 0.9 < heave["amplitude"][0][0] < 1.1
    finally:
        service.close()
