# Third-party software and reference data

The MIT license covers this project's original code, documentation, generated
meshes, figures, and published example result files. It does not relicense the
third-party software or original reference datasets cited below.

## HydroStar

HydroStar / Hstar4Experts is commercial software from Bureau Veritas. A separate
installation and valid authorization are required to execute its solver modules.
This repository contains automation code and generated examples; solver binaries,
license files, vendor manuals, training materials, and installed vendor meshes
are outside the distribution. Product names belong to their respective owners.

## Reference configurations

- [SIMMAN2014 KCS](https://simman2014.dk/ship-data/moeri-container-ship/geometry-and-conditions-moeri-container-ship/)
  and [KVLCC2](https://simman2014.dk/ship-data/moeri-kvlcc2-tanker/geometry-and-conditions-moeri-kvlcc2-tanker/):
  published particulars and test conditions inform the sectional hull recipes.
  The generated hulls are project reconstructions, with explicit shape assumptions.
  Original IGES, offsets, drawings, and experimental datasets retain their source
  terms and attribution; they are linked rather than bundled here.
- [OpenFAST r-test](https://github.com/OpenFAST/r-test), commit
  `dd5feaaaa500ba7283140107806300d551cff0a7`: OC4 DeepCwind scalar dimensions,
  mass properties and hydrodynamic coefficients inform the column-platform recipe.
  This repository generates its own mesh and records its proxy loading and
  restraint assumptions. Original OpenFAST input files and hydrodynamic databases
  retain their upstream terms and are linked rather than redistributed.
- [OpenFAST HydroDyn modeling considerations](https://openfast.readthedocs.io/en/main/source/user/hydrodyn/modeling_considerations.html)
  informs the documented separation of potential-flow, member drag, buoyancy,
  ballast, and additional stiffness/damping terms.

See [reference configurations](docs/reference-forms.md) and the machine-readable
[source index](docs/references/sources.json) for URLs, versions, and verification
metadata. Python dependencies keep their own licenses.

## Visualization software

The published command exports use separately installed
[Gnuplot](http://www.gnuplot.info/) and [ParaView](https://www.paraview.org/),
following the HydroStar manual's plotting and companion-viewer workflows.
Their executables and dependency runtimes are outside this distribution.
The repository includes original plotting/rendering scripts, version records,
generated native field data and scientific figures. Each software installation
retains its own upstream terms.

## Optional geometry software

The geometry extra uses separately installed software under its upstream terms:
[Gmsh](https://gmsh.info/) (GPLv2 or later, with OpenCASCADE CAD support),
[ezdxf](https://ezdxf.readthedocs.io/) and [meshio](https://github.com/nschloe/meshio)
(MIT), Shapely and SciPy (BSD), Matplotlib, Pillow, and
[pypdfium2](https://pypdfium2.readthedocs.io/) (BSD/Apache and dependency notices).
This project's wheel contains its original adapter code and tracing HTML; it
does not bundle those kernels, their binaries or the HydroStar solver.
Redistributing a combined installation requires following each dependency's
license. The original general-geometry examples are constructed from the scalars
in geometry_source_study.py and include no external reference meshes.
