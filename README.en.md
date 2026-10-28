# HydroStar MCP

[简体中文](README.md)　**English**

[![Tests](https://github.com/lightninnng/hydrostar-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/lightninnng/hydrostar-mcp/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Build hydrodynamic models from parameters, sections and CAD, then verify panel quality, static equilibrium, native HydroStar execution and six-degree-of-freedom results. The project supports graduate coursework, method studies and simplified engineering analysis with explicit assumptions, through a Windows local MCP server and a shared CLI.

The [online scientific report](https://lightninnng.github.io/hydrostar-mcp/) retains a rotatable solved-mesh view and selectable configurations, headings, amplitude, phase and dynamic fields. See the [quickstart](docs/quickstart.md) for installation and replay, and the [modelling guide](docs/modeling-guide.md) for physical inputs and quality requirements.

## Configurations and solved meshes

The original curved hull is reconstructed from the project's own station table using corresponding longitudinal and sectional quadrilateral bands. Its wet mesh has 2018 quadrilaterals and 11 end-cap triangles, with 844 waterplane panels: **2873 full-equivalent total panels**. The native sweep covers **231 frequencies and 13 headings** within the default budget. Geometry acceptance and all six execution gates passed.

[![Actual solved wet meshes for the four configurations](docs/assets/readme-meshes.png)](docs/assets/readme-meshes.png)

This plate is exported by ParaView commands from the accepted solved connectivity, retaining quadrilaterals and local triangles. Blue surfaces are the potential-flow wet mesh; grey geometry supplies the platform's dry-structure and slender-member context. Geometry uses a 1× gain, and each view is fitted independently. Total counts include waterplane panels; the plate shows wet surfaces. The online report provides a rotatable view of each model.

| Configuration | Full-equivalent total panels, including waterplane | Frequency range and spacing (rad/s) | Frequencies and headings |
| --- | --- | --- | --- |
| [Original curved hull](examples/vessel) | 2873 | 0.05–1.20, 0.005 | 231 × 13 |
| [Container hull](examples/results/container_kcs_style) | 1710 | 0.05–0.80, 0.005 | 151 × 13 |
| [Full-form tanker](examples/results/tanker_kvlcc2_style) | 1732 | 0.05–0.60, 0.005 | 111 × 13 |
| [Semisubmersible](examples/results/semisub_oc4_style) | 1782 | 0.02–1.20, 0.005 | 237 × 13 |

The three reference configurations use public principal dimensions and explicit shape assumptions. The project generates its own nodes and panels. [Source notes](docs/reference-forms.md) document the dimensional references, reconstruction and physical idealizations.

## Dynamic pressure, waves and motion

All four configurations provide synchronized surface pressure, total elevation and scattered elevation. Incident amplitude is **0.50 m** and heading is **60°**. Each uses the selected frequency, physical period and depth below.

| Configuration | Angular frequency (rad/s) | Physical period (s) | Depth (m) |
| --- | --- | --- | --- |
| Curved station hull | 0.65 | 9.666 | 80 |
| Semisubmersible | 0.80 | 7.854 | 200 |
| Container hull | 0.50 | 12.566 | 80 |
| Full-form tanker | 0.40 | 15.708 | 80 |

The left view shows the body-following first-order pressure perturbation on the mean wetted panels in kPa. The centre shows total elevation and rigid-body motion. The right shows scattered elevation, including diffraction and motion-induced radiation; elevation colours are in metres. Colours retain physical values. Motion and wave height each use a stated 6× viewing gain; pressure geometry uses 1×. Views share the physical phase and fixed cycle-wide colour scales.

**Curved station hull.** The wet-surface pressure cycle is shown alongside total and scattered elevation and the corresponding six-DOF rigid-body motion.

[![Curved hull pressure, total elevation and scattered elevation](docs/assets/readme-vessel-coupled.gif)](docs/assets/vessel-coupled.gif)

**Semisubmersible.** The column arrangement and inter-column wave field appear together, with pressure attached to the actual wet panels.

[![Semisubmersible pressure, total elevation and scattered elevation](docs/assets/readme-platform-coupled.gif)](docs/assets/platform-coupled.gif)

**Container hull.** This reference reconstruction includes a parallel midbody, rounded bilge, bulbous bow and transom. Its animation uses its own computed fields.

[![Container hull pressure, total elevation and scattered elevation](docs/assets/readme-container-coupled.gif)](docs/assets/container-coupled.gif)

**Full-form tanker.** The full midbody and continuously narrowing ends are shown with their computed surface pressure and exterior wave fields.

[![Full-form tanker pressure, total elevation and scattered elevation](docs/assets/readme-tanker-coupled.gif)](docs/assets/tanker-coupled.gif)

Click any preview to open its full-resolution export. Each retains all 40 physical phases and time annotations, playing at 10 frames/s. A playback cycle lasts four seconds; physical time is given by t, t/T and the periods above. Colour limits are stated separately for each panel and configuration.

## Diffraction and radiation fields

These animations decompose the scattered field into fixed-body diffraction and motion-induced radiation. The left view retains the mean body pose; the right shows radiation from that case's six-DOF response. Components are separated in the complex domain and reconstructed at a shared physical phase. Elevation is in metres, with 6× viewing gains for wave height and motion. Each panel retains its colour limits throughout the cycle.

**Curved hull diffraction and radiation.**

[![Curved hull fixed-body diffraction and motion-induced radiation](docs/assets/readme-vessel-components.gif)](docs/assets/vessel-components.gif)

**Semisubmersible diffraction and radiation.**

[![Semisubmersible fixed-body diffraction and motion-induced radiation](docs/assets/readme-platform-components.gif)](docs/assets/platform-components.gif)

**Container hull diffraction and radiation.**

[![Container hull fixed-body diffraction and motion-induced radiation](docs/assets/readme-container-components.gif)](docs/assets/container-components.gif)

**Full-form tanker diffraction and radiation.**

[![Full-form tanker fixed-body diffraction and motion-induced radiation](docs/assets/readme-tanker-components.gif)](docs/assets/tanker-components.gif)

The fields come from independently checked native HSPRS complex results. ParaView saves frames by command, followed by GIF encoding. Checks cover analytical incident waves, full-complex radiation reconstruction, body-following pressure correction and outward-normal sampling sensitivity. Original HSprv exports and version diagnostics are retained, while display records identify the accepted fields. [Visualization data and export records](examples/visualization) and [command reproduction](docs/native-visualization.md) are included. Larger total/scattered wave views are available for the [curved hull](docs/assets/vessel-wave.gif), [semisubmersible](docs/assets/platform-wave.gif), [container hull](docs/assets/container-wave.gif) and [tanker](docs/assets/tanker-wave.gif).

## Six-DOF frequency response

The manual-recommended Gnuplot route reads the original response files and exports the curves by command. Each figure overlays headings of 0°, 60°, 90°, 120° and 180° for surge, sway, heave, roll, pitch and yaw. Angular frequency is in rad/s, translation amplitudes in m/m and rotation amplitudes in deg/m. Each case retains its own loading, damping, depth and frequency range.

**Curved station hull.** The 231-point sweep covers 0.05–1.20 rad/s at 0.005 rad/s spacing, retaining the peaks and troughs in heave, roll, pitch and the other responses.

[![Native six-DOF response of the curved station hull](docs/assets/vessel-response.png)](docs/assets/vessel-response.pdf)

**Semisubmersible.** The 237-point sweep covers 0.02–1.20 rad/s with the published restoring and damping assumptions.

[![Native six-DOF response of the semisubmersible](docs/assets/platform-response.png)](docs/assets/platform-response.pdf)

**Container hull.** The 151-point sweep covers 0.05–0.80 rad/s.

[![Native six-DOF response of the container hull](docs/assets/container-response.png)](docs/assets/container-response.pdf)

**Full-form tanker.** The 111-point sweep covers 0.05–0.60 rad/s.

[![Native six-DOF response of the full-form tanker](docs/assets/tanker-response.png)](docs/assets/tanker-response.pdf)

<details>
<summary>View the curved hull's six-DOF phase at a 60° heading</summary>

Phase is in degrees, wrapped to −180° through 180°. Discrete points retain the native samples across the wrap boundary. Interpret phase jumps together with this convention and the corresponding amplitude.

![Curved hull six-DOF phase at a 60-degree heading](docs/assets/vessel-phase-60.svg)

</details>

Click a response figure for its vector PDF. Full values, SVGs for all 13 headings, physical inputs and native files are in the [curved-hull package](examples/vessel), [three reference result packages](examples/results) and [native curve exports](examples/visualization/curves).

## Second-order mean drift and difference-frequency loads

The semisubmersible has completed native **HSdft → HSamg → HSqtf** calculations, providing mean drift loads and full difference-frequency QTFs including the free-surface integral. Water depth is 200 m, heading is 60°, and difference frequencies are 0, 0.05 and 0.10 rad/s: **36 valid wave-frequency pairs and 216 complex load coefficients**.

![Semisubmersible and structured annular integration mesh](docs/assets/platform-second-order-mesh.png)

The exterior domain uses 72 equal angular divisions and nine graded quadrilateral annuli, with corresponding near-body sectors. The main mesh has **2946 full-equivalent total panels**, including wet surfaces, waterplane, exterior free surface and symmetry expansion; the comparison has 2898. Both native calculations retain the same wet mesh, mass, inertia, restoring and damping.

[![Six-component second-order mean drift loads](docs/assets/platform-second-order-drift.png)](docs/assets/platform-second-order-drift.pdf)

[![Full difference-frequency QTF magnitudes](docs/assets/platform-second-order-qtf.png)](docs/assets/platform-second-order-qtf.pdf)

Force coefficients use kN/m² and moment coefficients use kN m/m². Figures retain the native frequency samples. QTF diagonal terms agree with mean drift within 0.032% of the corresponding peak; horizontal near/far-field drift differs by at most 3.76%. Across the two exterior meshes, complex force differences reach 0.41%, and roll/pitch moments reach 0.083%. **Yaw moment changes by 23.37% of its own peak, with a 128.85% near/far-field mean-drift difference. It remains a numerical research component requiring further convergence before engineering load use.** This comparison fixes the wet mesh and exterior radius; engineering use needs corresponding spatial, domain, frequency and reference-result evidence.

<details>
<summary>Inspect complex QTFs and integration-mesh sensitivity</summary>

[![Real and imaginary QTF at difference frequency 0.10 rad/s](docs/assets/platform-second-order-complex.png)](docs/assets/platform-second-order-complex.pdf)

[![Difference-frequency loads on the two exterior meshes](docs/assets/platform-second-order-sensitivity.png)](docs/assets/platform-second-order-sensitivity.pdf)

</details>

[Methods and replay](docs/second-order.md) describe the integration domain, frequency pairing and acceptance scope. The [native second-order package](examples/second-order/platform) includes HST, RDF, MCN, DFT, QTF and RAO inputs, eight execution logs, complex outputs and a delivery manifest. SPC spectral analysis is not applicable to this regular-wave study. The four configurations' animations above show their respective first-order pressure, waves and motion.

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
python -m pip install -e ".[dev,plot,geometry]"
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

The detailed guides are currently written in Chinese: [quickstart](docs/quickstart.md), [modelling](docs/modeling-guide.md), [reference forms](docs/reference-forms.md), [surface pressure](docs/surface-pressure.md), [wave fields](docs/wavefields.md), [verification](docs/verification.md), [second-order loads](docs/second-order.md) and [architecture](docs/architecture.md).

## License and attribution

Original code and the generated public examples are released under the [MIT license](LICENSE). HydroStar is commercial software from Bureau Veritas, with separate installation and authorization requirements. Public scalar references and upstream rights are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
