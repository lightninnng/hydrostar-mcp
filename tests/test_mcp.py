import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parent.parent


def test_real_stdio_builds_a_frozen_geometry_bundle(tmp_path):
    pytest.importorskip("shapely")
    pytest.importorskip("matplotlib")
    from conftest import box_mesh

    source = box_mesh(tmp_path / "own.hst", symmetry=0)

    async def check():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hydrostar_mcp.server"],
            cwd=str(REPO),
            env={
                **os.environ,
                "HS_WORKSPACE": str(tmp_path / "runs"),
                "HS_SOURCE_ROOT": str(tmp_path),
            },
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                build = asyncio.create_task(
                    client.call_tool(
                        "build_geometry",
                        {
                            "request": {
                                "project": "geometry_mcp",
                                "path": str(source),
                                "units": "m",
                                "expected_volume_m3": 80,
                                "timeout_s": 60,
                                "panel_quality": {"max_neighbor_size_ratio": 3.0},
                                "source_note": "Original closed wet box for actual MCP geometry transport",
                            }
                        },
                    )
                )
                await asyncio.sleep(0.1)
                tools = await asyncio.wait_for(client.list_tools(), timeout=10)
                assert any(t.name == "build_geometry" for t in tools.tools)
                result = await asyncio.wait_for(build, timeout=90)
                assert not result.isError
                report = result.structuredContent
                assert report["status"] == "geometry_accepted", report
                assert report["quality"]["passed"]
                assert report["quality"]["quadrilaterals"] == 5
                assert report["quality"]["triangles"] == 0
                assert report["hydrostatics"]["volume"] == pytest.approx(80)
                assert Path(report["case_geometry"]["source_manifest"]).is_file()

    asyncio.run(check())


def test_real_stdio_handshake_schema_planning_and_input_export(tmp_path):
    """Real MCP transport and SDK, without substituting a fake MCP server."""

    async def check():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hydrostar_mcp.server"],
            cwd=str(REPO),
            env={
                **os.environ,
                "HS_WORKSPACE": str(tmp_path / "runs"),
                "HS_SOURCE_ROOT": str(REPO),
            },
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                tools = await client.list_tools()
                expected = {
                    "inspect_environment",
                    "plan_case",
                    "generate_inputs",
                    "prepare_case",
                    "start_case",
                    "case_status",
                    "cancel_case",
                    "read_rao",
                    "list_reference_forms",
                    "make_reference_case",
                    "inspect_geometry_source",
                    "build_geometry",
                }
                assert {t.name for t in tools.tools} == expected
                routes = await client.call_tool("inspect_geometry_source", {})
                assert not routes.isError
                assert routes.structuredContent["formats"][".step"] == "cad_solid"
                plan_tool = next(t for t in tools.tools if t.name == "plan_case")
                assert "CaseConfig" in json.dumps(plan_tool.inputSchema)
                plan = await client.call_tool("plan_case", {"config": {}})
                assert not plan.isError
                assert plan.structuredContent["status"] == "planned"
                assert plan.structuredContent["budget"]["max_edge"] < 2.1
                forms = await client.call_tool("list_reference_forms", {})
                assert not forms.isError
                assert len(forms.structuredContent["forms"]) == 3
                reference = await client.call_tool(
                    "make_reference_case", {"form_id": "container_kcs_style"}
                )
                assert not reference.isError
                assert (
                    reference.structuredContent["config"]["geometry"]["type"]
                    == "section_hull"
                )
                assert not reference.structuredContent["reference_model"][
                    "engineering_acceptance"
                ]["ready"]
                generated = await client.call_tool("generate_inputs", {"config": {}})
                assert not generated.isError
                report = generated.structuredContent
                assert report["status"] == "generated"
                assert Path(report["directory"]).is_relative_to(tmp_path)
                assert Path(report["directory"], "barge100.mri").is_file()
                invalid = await client.call_tool(
                    "plan_case", {"config": {"project": "../escape"}}
                )
                assert invalid.isError
                for name in ("semisub", "curved_hull"):
                    config = json.loads(
                        (REPO / "examples" / (name + ".json")).read_text(
                            encoding="utf-8"
                        )
                    )
                    generated = await client.call_tool(
                        "generate_inputs", {"config": config}
                    )
                    assert not generated.isError
                    report = generated.structuredContent
                    assert report["status"] == "generated"
                    assert report["geometry_provenance"]["external_mesh_files"] == []
                    assert Path(
                        report["directory"], config["project"] + ".hst"
                    ).is_file()

    asyncio.run(check())


def test_cli_emits_valid_json_and_can_export_without_license(tmp_path):
    command = [
        sys.executable,
        "-m",
        "hydrostar_mcp",
        "--workspace",
        str(tmp_path / "runs"),
        "generate",
        str(REPO / "examples/barge100.json"),
    ]
    result = subprocess.run(command, cwd=REPO, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    report = json.loads(result.stdout.decode("utf-8"))
    assert report["status"] == "generated"
    assert report["steps"] == []
