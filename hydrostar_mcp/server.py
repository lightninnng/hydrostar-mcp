"""Local stdio MCP server. stdout is reserved for the MCP protocol."""

from __future__ import annotations

import atexit
import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .models import CaseConfig
from .workflow import CaseService
from .reference_forms import catalog, make_case
from .geometry_sources import GeometryRequest, format_catalog
from .geometry_workflow import GeometryService

service = CaseService()
atexit.register(service.close)
mcp = FastMCP(
    "hydrostar",
    instructions=(
        "HydroStar local automation: plan_case -> prepare_case -> start_case -> case_status -> read_rao. "
        "Present needs_confirmation warnings with the concrete plan, then use its token after human agreement. "
        "Use explicit mass parameters and provenance for imported meshes. "
        "For CAD, station tables, DXF curves, surface meshes or drawings, use inspect_geometry_source and build_geometry. "
        "Use the returned case_geometry with explicit mechanics; retain source_manifest through prepare_case. "
        "Drawing inputs require metric calibration, independent checkpoints and reviewed tracing before meshing. "
        "Use list_reference_forms and make_reference_case to choose a source-informed basic configuration. "
        "Carry reference_model and engineering_acceptance with results; execution gates and engineering-purpose evidence are distinct acceptance stages. "
        "Review quality_gates and compare response sensitivity for the intended study level. Full logs are available at the returned local paths."
    ),
)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def inspect_environment() -> dict[str, Any]:
    """Locate solver executables and supported capabilities; does not claim license availability."""
    return service.environment()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def inspect_geometry_source(path: str | None = None) -> dict[str, Any]:
    """Read supported source routes or inspect a source inside HS_SOURCE_ROOT."""
    if path is None:
        return format_catalog()
    return GeometryService(service.root / "geometry", service.source_root).inspect(path)


@mcp.tool()
async def build_geometry(request: GeometryRequest) -> dict[str, Any]:
    """Build an independently checked, provenance-preserving wetted HST bundle.

    CAD and section data use an isolated OpenCASCADE/Gmsh process. Drawing inputs
    produce a metric tracing workspace. Use case_geometry from accepted output
    in prepare_case, with explicit mass, CG, inertia and the desired wave conditions.
    """
    return await asyncio.to_thread(
        GeometryService(service.root / "geometry", service.source_root).build, request
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def list_reference_forms() -> dict[str, Any]:
    """Read built-in source-informed hull families, feature allocation and citations."""
    return catalog()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def make_reference_case(form_id: str, project: str | None = None) -> dict[str, Any]:
    """Create a reviewable typed recipe from public scalar references, without writes.

    Returns source comparison and a full plan. Generate/prepare the returned
    config using the normal gates; benchmark equivalence is evaluated separately.
    """
    cfg = make_case(form_id, project)
    return service.plan(cfg)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def plan_case(config: CaseConfig) -> dict[str, Any]:
    """Validate semantic input, estimate panel counts and screen wavelength before writing files."""
    return service.plan(config)


@mcp.tool()
def generate_inputs(
    config: CaseConfig, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Export reviewable parametric MRI/HST (or imported HST), RDF, MCN and RAO.

    This works without a HydroStar license. The generated status means input
    export only; use prepare_case before attempting any calculation.
    """
    return service.generate(config, confirmation_token)


@mcp.tool()
def prepare_case(
    config: CaseConfig, confirmation_token: str | None = None
) -> dict[str, Any]:
    """Generate geometry/RDF/MCN/RAO and check a fresh mesh before the motion solve.

    If planning requires confirmation, call again with that plan's token only
    after human agreement. Measured mesh warnings require another review before start_case.
    """
    return service.prepare(config, confirmation_token)


@mcp.tool()
def start_case(case_id: str, confirmation_token: str | None = None) -> dict[str, Any]:
    """Start a previously prepared case asynchronously. Poll case_status for results.

    Supply the measured-mesh confirmation token only after human review when requested.
    Input modification invalidates preparation. Each case may be solved once.
    """
    return service.start(case_id, confirmation_token)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def case_status(case_id: str) -> dict[str, Any]:
    """Read persisted state, step timings, log paths, mesh checks and result summaries."""
    return service.status(case_id)


@mcp.tool()
def cancel_case(case_id: str) -> dict[str, Any]:
    """Request cancellation of this service's queued or active job and its solver process tree."""
    return service.cancel(case_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def read_rao(case_id: str, dof: str = "heave") -> dict[str, Any]:
    """Read complete validated RAO arrays, original amplitude unit and phase values (degrees)."""
    return service.result(case_id, dof)


def main():
    try:
        mcp.run(transport="stdio")
    finally:
        service.close()


if __name__ == "__main__":
    main()
