# HydroStar MCP

[简体中文](README.md)　**English**

[![Tests](https://github.com/lightninnng/hydrostar-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/lightninnng/hydrostar-mcp/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Build hydrodynamic models from parameters, sections and CAD, then verify panel quality, static equilibrium, native HydroStar execution and six-degree-of-freedom results. The project supports graduate coursework, method studies and simplified engineering analysis with explicit assumptions, through a Windows local MCP server and a shared CLI.

The [online scientific report](https://lightninnng.github.io/hydrostar-mcp/) retains a rotatable solved-mesh view and selectable configurations, headings, amplitude, phase and dynamic fields. See the [quickstart](docs/quickstart.md) for installation and replay, and the [modelling guide](docs/modeling-guide.md) for physical inputs and quality requirements.

## Computed examples

The original curved hull is reconstructed from the project's own station table using corresponding longitudinal and sectional quadrilateral bands. Its wet mesh has 2018 quadrilaterals and 11 end-cap triangles, with 844 waterplane panels: **2873 full-equivalent total panels**. The native sweep covers **231 frequencies and 13 headings** within the default budget. Geometry acceptance and all six execution gates passed.

![Native six-DOF response of the curved station hull](docs/assets/vessel-response.png)

The manual-recommended Gnuplot route reads the original response files and exports high-resolution PNG, vector PDF and heading-selectable SVG. Translation amplitudes are in m/m, rotations in deg/m and phases in degrees. The [curved-hull package](examples/vessel) contains complete values, parameters and native inputs.

| Configuration | Full-equivalent total panels, including waterplane | Frequency range and spacing (rad/s) | Frequencies and headings |
| --- | --- | --- | --- |
| [Original curved hull](examples/vessel) | 2873 | 0.05–1.20, 0.005 | 231 × 13 |
| [Container hull](examples/results/container_kcs_style) | 1710 | 0.05–0.80, 0.005 | 151 × 13 |
| [Full-form tanker](examples/results/tanker_kvlcc2_style) | 1732 | 0.05–0.60, 0.005 | 111 × 13 |
| [Semisubmersible](examples/results/semisub_oc4_style) | 1782 | 0.02–1.20, 0.005 | 237 × 13 |

The three reference configurations use public principal dimensions and explicit shape assumptions. The project generates its own nodes and panels. [Source notes](docs/reference-forms.md) document the dimensional references, reconstruction and physical idealizations.

## Dynamic pressure, waves and motion

![Curved hull pressure, total elevation and scattered elevation](docs/assets/vessel-coupled.gif)

![Semisubmersible pressure, total elevation and scattered elevation](docs/assets/platform-coupled.gif)

The left view shows the body-following first-order pressure perturbation on the mean wetted panels in kPa. The centre shows total elevation and rigid-body motion. The right shows scattered elevation, including diffraction and motion-induced radiation; elevation colours are in metres. Colours retain physical values. Motion and wave height each use a stated 6× viewing gain; pressure geometry uses 1×. Views share the physical phase and fixed cycle-wide colour scales.

The fields come from independently checked native HSPRS complex results. ParaView saves the frames by command, followed by GIF encoding. Checks cover analytical incident waves, full-complex radiation reconstruction, body-following pressure correction and outward-normal sampling sensitivity. Original HSprv exports and version diagnostics are retained, while display records identify the accepted fields. The [diffraction and radiation animation](docs/assets/platform-components.gif), [visualization data](examples/visualization) and [export methods](docs/native-visualization.md) support reproduction. All field views remain selectable in the online report.

## Modelling and native delivery

Panels follow structural features: axial rings for coaxial bodies, station bands for hulls, and conforming blocks for polygons and through openings. Quadrilaterals remain in the solved HST. Acceptance covers angles, warpage, size transitions, CAD volume and buoyancy centre, topology and intersections. **New models default to 3000 full-equivalent total panels, including wet and waterplane panels and symmetry expansion. Budget increases require explicit case-specific authorization.** Previously authorized dense [research references](examples/geometry) retain their configurations.

Sections, curves, DXF, STEP/IGES/BREP and surface meshes share the preprocessing workflow. Images and PDFs use dimensional calibration, reviewed traces and independent check dimensions. Install optional dependencies with `python -m pip install -e ".[geometry]"`; see [source-based modelling](docs/geometry-sources.md) and [panel meshing](docs/panel-meshing.md).

Actual HST, RDF, MCN, RAO, field inputs and task-specific SPC files are formal deliverables, with units, relative paths, execution order, status and provenance. The [delivery requirements](docs/native-delivery.md) and [modelling skill](skills/hydrostar-modeling/SKILL.md) apply the same rules. Verified failures and repairs are retained in the skill's [troubleshooting reference](skills/hydrostar-modeling/references/troubleshooting.md).

## Install and run

Python 3.10+ is required. Planning, input export and viewing the published data work offline. New numerical solves require a separately installed and authorized HydroStar solver and its MPI runtime.

~~~powershell
git clone https://github.com/lightninnng/hydrostar-mcp.git
cd hydrostar-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[plot,test]"

$env:HSTAR_PATH7 = 'C:\path\to\Hstar4Experts\v8.2.0'
python -m hydrostar_mcp environment
python -m hydrostar_mcp forms
python -m hydrostar_mcp plan examples/vessel/config.json
python -m hydrostar_mcp prepare examples/vessel/config.json
~~~

Use the `case_id` returned by `prepare`:

~~~powershell
$caseId = '<case_id returned by prepare>'
python -m hydrostar_mcp start $caseId
python -m hydrostar_mcp result $caseId --dof heave
~~~

`generate` exports reviewable inputs. `prepare` builds or imports a new mesh and performs preparation checks. `start` runs radiation/diffraction, mechanics and RAO construction. The CLI waits for completion; MCP `start_case` returns asynchronously. Routine visualization first follows the [native and manual-recommended routes](docs/native-visualization.md); `plot` provides supplementary PNG/PDF figures.

Set `HS_WORKSPACE` or use the CLI `--workspace` option for another run directory. Set `HS_SOURCE_ROOT` or `--source-root` to control the permitted HST import root.

## Connect an MCP client

Edit the absolute Python, project and solver paths in [mcp-settings.json](examples/mcp-settings.json). The server uses stdio:

~~~powershell
python -m hydrostar_mcp.server
~~~

| Tools | Purpose |
| --- | --- |
| `list_reference_forms` and `make_reference_case` | Inspect reference configurations, sources and typed recipes |
| `inspect_environment` | Locate native solver programs and inspect runtime capabilities |
| `inspect_geometry_source` and `build_geometry` | Inspect source data and build a checked wet surface or metric tracing workspace |
| `plan_case` and `generate_inputs` | Validate a plan and export inputs offline |
| `prepare_case` | Prepare a fresh case and check mesh and equilibrium |
| `start_case`, `case_status` and `cancel_case` | Run, monitor and cancel a case with process-tree cleanup |
| `read_rao` | Read verified arrays, phase values and original units |

## Quality gates and analysis scope

| Hard gate | Acceptance requirement |
| --- | --- |
| `semantic_input` | Valid dimensions, discretization, finite values, units and physically admissible mass/inertia |
| `static_equilibrium` | Total buoyancy includes physical members; vertical error defaults to ≤1%, horizontal CG/CB offset to ≤0.05 m, and native balance checks pass |
| `mesh_geometry` | Valid wetted geometry, normals, panel planarity and known reference quantities |
| `mesh_topology` | All seven required hschk counters are present and zero |
| `module_execution` | Normal completion and acceptable licensing, Fortran, equilibrium and convergence diagnostics |
| `rao_integrity` | Complete requested outputs, matching grids, finite values and valid file hashes |

A failed hard gate stops dependent work. The default execution budget is 3,000 full-equivalent total panels; increasing it requires explicit review for the specific case. Wavelength-to-panel scale and aspect ratio provide additional geometric screening. Exceedances return concrete values and a confirmation token for review.

The models describe one rigid body, small motions and first-order frequency-domain behaviour. Executable cases use zero static external preload. Semisubmersible modelling combines BEM surfaces, Morison members, component mass properties, added stiffness and linearized drag. Model-specific evidence and sensitivity studies establish the intended engineering use.

General geometry adds curved lofts, boolean combinations, through openings and CAD import. Multibody motion, structural flexibility, actual mooring preload equilibrium and moonpool viscous losses require the corresponding physical extensions and validation.

## Reproduce and verify

~~~powershell
python -m pip install -e ".[dev,plot]"
python -m pytest -q -m "not integration" --basetemp .pytest-tmp
python scripts/check_release.py
python scripts/check_local.py
~~~

On a machine with valid solver authorization:

~~~powershell
python scripts/reference_form_study.py --run
python scripts/wavefield_study.py --run
python scripts/pressure_study.py --run
python scripts/export_showcase.py
python scripts/build_gallery.py
~~~

`wavefield_study.py --render` and `pressure_study.py --render` rebuild animations from published numerical data. Geometry and frequency sensitivity scripts are described in the verification guide. Their convergence conclusions apply to their own benchmark configurations.

The detailed guides are currently written in Chinese: [quickstart](docs/quickstart.md), [modelling](docs/modeling-guide.md), [reference forms](docs/reference-forms.md), [surface pressure](docs/surface-pressure.md), [wave fields](docs/wavefields.md), [verification](docs/verification.md) and [architecture](docs/architecture.md).

## License and attribution

Original code and the generated public examples are released under the [MIT license](LICENSE). HydroStar is commercial software from Bureau Veritas, with separate installation and authorization requirements. Public scalar references and upstream rights are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
