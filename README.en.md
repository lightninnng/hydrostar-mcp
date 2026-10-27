# HydroStar MCP

[简体中文](README.md)　**English**

[![Tests](https://github.com/lightninnng/hydrostar-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/lightninnng/hydrostar-mcp/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

HydroStar MCP connects parametric geometry, mass properties and restraints to traceable first-order hydrodynamic calculations. It supports graduate coursework, method studies and simplified engineering analysis using HydroStar 8.2.0 on Windows, through a local MCP server or a shared command-line workflow.

Each case has an independent directory containing its inputs, quality checks, native logs, results and SHA-256 records. Public examples include source-informed geometry, six-degree-of-freedom responses, native wave fields and dynamic pressure on the wetted BEM surfaces.

[Open the scientific results report](https://lightninnng.github.io/hydrostar-mcp/)

![Generated meshes used in the native calculations](docs/assets/reference-geometry.png)

## Computed reference configurations

The project generates its own nodes and panels from public scalar references and explicit shape assumptions. The names retain `style` to identify their reference-configuration scope. All three cases were solved with HydroStar 8.2.0 and passed the six execution gates.

| Configuration | Geometry represented | Angular-frequency grid (rad/s) | Half-body wetted and waterplane panels |
| --- | --- | --- | --- |
| [Container hull](examples/results/container_kcs_style) | KCS-informed particulars, parallel middle body, rounded bilges, bulbous bow and transom | 0.05–0.80, step 0.005; 151 frequencies | 727 and 128 |
| [Full-form tanker](examples/results/tanker_kvlcc2_style) | KVLCC2-informed scalars, full middle body, broad flat bottom and tapered ends | 0.05–0.60, step 0.005; 111 frequencies | 660 and 206 |
| [Column semisubmersible](examples/results/semisub_oc4_style) | OC4-informed centre column, three offset columns with enlarged bases, members and ballast | 0.02–1.20, step 0.005; 237 frequencies | 828 and 63 |

Each response dataset contains six DOFs and 13 headings from 0° to 360° in 30° increments. The ship cases use 80 m water depth; the semisubmersible uses 200 m. Density is 1025 kg/m³, gravity is 9.81 m/s², and forward speed is zero.

![Semisubmersible response amplitude operators](docs/assets/semisub_oc4_style_rao.png)

Scientific figures use colourblind-friendly line colours, distinct heading line styles, panel labels and explicit units. Both 300 dpi PNG and vector PDF are provided. [Container responses](docs/assets/container_kcs_style_rao.png) and [tanker responses](docs/assets/tanker_kvlcc2_style_rao.png) use the same format.

The [result packages](examples/results/index.json) contain generated HST/RDF/MCN/RAO inputs, original RAO files, complete amplitude/phase arrays, provenance and per-file hashes. For a specific engineering application, review the target geometry, loading, restraints, damping and benchmark responses. The current evidence status is retained explicitly as `engineering_acceptance.ready=false`.

Native mesh, load and parameter files are formal deliverables. The [native-file delivery requirements](docs/native-delivery.md) describe .hst, .rdf, .mcn, .rao and the .spc inputs used for spectral analysis, including dependencies, execution order and verification status. The modelling skill applies the same requirements; figures retain their own actual calculation provenance.

## Synchronized surface pressure, waves and motion

![Semisubmersible surface pressure, wave elevation and rigid-body motion](docs/assets/semisub_oc4_style_coupled.gif)

The left view shows the body-following first-order dynamic pressure perturbation on the mean wetted BEM panels. The centre view shows native total wave elevation with the corresponding six-DOF motion. The right view retains the scattered wave elevation, computed as complex total minus complex incident elevation, including diffraction and motion-induced radiation. All three views use the same physical phase and wave reference.

Pressure colours are in kPa and wave colours are in m, at their physical values. The motion and three-dimensional wave height have a stated 6× viewing gain. Colour limits remain fixed throughout each cycle. Equilibrium hydrostatic pressure is stored separately, so signed pressure colours describe perturbations about that equilibrium. Dry structural context and Morison members are identified separately from the coloured BEM surfaces.

| Configuration | Frequency (rad/s) | Heading and wave amplitude | Full-body pressure panels |
| --- | --- | --- | --- |
| Container hull | 0.5 | 60°, 0.5 m | 1454 |
| Full-form tanker | 0.4 | 60°, 0.5 m | 1320 |
| Column semisubmersible | 0.8 | 60°, 0.5 m | 1656 |

[Container animation](docs/assets/container_kcs_style_coupled.gif), [tanker animation](docs/assets/tanker_kvlcc2_style_coupled.gif) and [pressure records](examples/pressures/index.json) are available for download. The native pressure calculation is checked against the finite-depth incident solution, the body-motion hydrostatic identity, and an outward-normal sampling sensitivity check. All native point records are archived with individual SHA-256 hashes.

The separate [wave-field dataset](examples/animations/index.json) retains total and scattered elevation. Scattered elevation is computed as total minus incident in the complex domain, preserving diffraction and radiation phase relationships.

The [online report](https://lightninnng.github.io/hydrostar-mcp/) provides model selection, a rotatable solved mesh, synchronized animations, heading selection, amplitude/phase plots and raw-sample inspection. Opening [docs/index.html](docs/index.html) after cloning also works offline, using its embedded numerical data and local media files.

## General geometry from source data

Panel topology follows the structure. Coaxial columns use equal-angle ring bands and radial shoulders; smooth hulls use matched station and section bands; polygonal bodies and through openings use conforming blocks. Native quadrilaterals retain their connectivity in the HST file. Shape, warpage, neighbouring size transitions and geometric fidelity are checked together. The [panel meshing method](docs/panel-meshing.md) records these choices and their applicable conditions as project guidance.

**New models use a default budget of 3,000 full-equivalent total panels, including wetted and waterplane panels after symmetry expansion.** Optimize the layout within that budget; increases require explicit case-specific review and authorization. The existing dense studies retain their authorized configurations as research references. The [HydroStar modelling skill](skills/hydrostar-modeling/SKILL.md) and AGENTS.md apply the same rule.

The optional geometry workflow accepts CSV/JSON sections, closed station curves in DXF, external displacement solids in STEP/IGES/BREP, and oriented surface meshes in STL/OBJ/PLY/HST. Explicit units, a right-handed frame and the mean waterline are recorded. Polygon corners are retained; interpolating splines and smooth longitudinal lofts represent curved forms. Image and PDF inputs produce a calibrated tracing workspace with independent metric checkpoints.

![Original complex geometries used for native calculations](docs/assets/geometry-source-cases.png)

The [general geometry examples](examples/geometry/index.json) contain an original vessel reconstructed from curved sections, a polygonal caisson with a through moonpool, and a millimetre STEP spar with a connected finite-thickness heave plate. Each package retains original source data, the accepted wetted mesh, CAD/mesh displacement and buoyancy-centre comparisons, topology and intersection checks, native inputs and complete six-DOF arrays. Their seven frequencies and four headings verify the geometry-to-solver chain; response-peak studies require separate grid refinement.

| Retained reference | Wetted quads / triangles | Full-equivalent total including waterplane | CAD volume difference |
| --- | --- | --- | --- |
| Curved station hull | 9811 / 7 | 14962 | 0.100% |
| Through-moonpool caisson | 728 / 0 | 1108 | Less than 0.001% |
| Ring-band Spar and heave plate | 9312 / 0 | 9955 | 0.195% |

These meshes retain their existing density. Comparisons hold the v0.4.0 baseline mass, CG, inertia, restoring settings, damping and environment fixed. The [two-ring-grid Spar study](examples/geometry/mesh-comparison.json) preserves native files for 6,800 and 9,312 wetted panels. Across the sampled grid, the maximum complex heave difference divided by the coarser-grid heave peak is 3.70%. This records sampled sensitivity; target-specific spatial convergence, peak-frequency and reference-response evidence remains to be established.

Install with `python -m pip install -e ".[geometry]"`. Use `geometry-inspect` and `geometry-build`, or MCP tools `inspect_geometry_source` and `build_geometry`. The returned `case_geometry` feeds `prepare_case` with explicit mechanics and environment. Source hashes are checked when preparing and starting a case. The default CAD/mesh volume tolerance is 0.5%; the buoyancy-centre tolerance is max(0.002 m, 0.0005 × maximum wetted dimension).

Geometry acceptance precedes all six native execution gates. A source mesh without an independent displacement reference retains `source_reference_pending` for fidelity. The [geometry guide](docs/geometry-sources.md) explains inputs, reconstruction assumptions and structure-specific scope. The drawing route has automated backend checks for rendering, calibration, independent dimensions and traced data; manual verification of the interactive tracing interface remains pending.

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
python -m hydrostar_mcp plan examples/semisub_oc4_style.json
python -m hydrostar_mcp prepare examples/semisub_oc4_style.json
~~~

Use the `case_id` returned by `prepare`:

~~~powershell
$caseId = '<case_id returned by prepare>'
python -m hydrostar_mcp start $caseId
python -m hydrostar_mcp result $caseId --dof heave
python -m hydrostar_mcp plot $caseId
~~~

`generate` exports reviewable inputs. `prepare` builds or imports a new mesh and performs preparation checks. `start` runs radiation/diffraction, mechanics and RAO construction. The CLI waits for completion; MCP `start_case` returns asynchronously. `plot` writes a six-DOF PNG and PDF.

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
