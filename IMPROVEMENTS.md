# Major Improvements

This document records significant changes made while adapting CUFSM for an
Octave-based command-line workflow.

## 2026-06-11

### Cross-Platform Execution

- Replaced machine-specific installation paths with paths resolved relative
  to `cufsm-octave-example.m`.
- Used `fullfile` so path construction works across Windows, Linux, and macOS.
- Verified execution through GNU Octave under WSL.

### Headless CLI Operation

- Removed figure generation and graphical post-processing from the example.
- Removed the plotting directory from the example's runtime path.
- Removed the solver's GUI progress window dependency.
- Preserved the numerical signature-curve workflow without requiring a
  graphics toolkit.

### MATLAB And Octave Compatibility

- Updated the `eigs` call to use an options structure accepted by MATLAB and
  GNU Octave.
- Replaced scalar uses of `&` and `|` with explicit short-circuit operators
  `&&` and `||` in the exercised analysis path.
- Normalised legacy source comments that contained invalid UTF-8 bytes.
- Achieved a warning-free run of the current example under Octave.

### CLI Reporting

- Replaced the full workspace dump with `cufsm-results.txt`.
- Added model, analysis-setting, and signature-curve sections.
- Added detection and reporting of local signature-curve minima.
- Added reporting of the overall minimum eigenvalue and half-wavelength.
- Excluded large mode-shape matrices from the default report.

### Source Readability

- Reorganised the example into focused environment, model, loading,
  configuration, solution, and reporting sections.
- Replaced tutorial-style and GUI-oriented commentary with concise comments
  describing data schemas and engineering assumptions.

## 2026-06-17 to 2026-06-18

### JSON Runner

- Added the versioned JSON input schema and the `cufsm_json.m` command-line
  entry point.
- Made geometry, material, loading, boundary conditions, length sweeps,
  springs, constraints, eigenmodes, mesh refinement, and cFSM settings
  configurable through JSON.
- Added machine-readable JSON results and optional text reports with section
  properties, signature curves, classified minima, and mode participation.
- Added generated-action and direct stress-table loading workflows.

### Python Integration

- Added Python helpers for input validation, JSON generation, Octave execution,
  result access, and optional signature-curve plotting.
- Added parametric templates for unlipped and lipped channels, Z sections,
  sigma sections, and stiffened-web channels.
- Added batch-analysis, grid-search optimization, and result-post-processing
  examples.
- Added optional JSON Schema validation, pandas accessors, and matplotlib
  plotting dependencies.

## 2026-09-03 to 2026-09-07

### MCP Interface

- Added a beta hosted MCP interface that uses the existing Python, JSON, and
  GNU Octave workflow rather than duplicating the solver.
- Added validated parametric section inputs with usable defaults for analysis
  and plotting requests.
- Added structured analysis results and static cross-section, signature-curve,
  and mode-participation plots.
- Isolated each calculation in a temporary workspace and added configurable
  timeouts and cleanup of worker processes.

### Deployment And Maintenance

- Added a container image definition containing Python, GNU Octave, and the
  MCP runtime dependencies.
- Documented safe server updates, dependency installation, service restarts,
  health checks, end-to-end smoke tests, and rollback.
- Replaced deployment-specific identifiers in the MCP maintenance guide with
  reusable placeholders.
- Added beta MCP connection instructions to the main README.

## Development Attribution

The CLI-oriented changes documented here are developed by:

**Parsa Yazdi**  
University of Waikato

The underlying CUFSM numerical methods and source originate from the official
[CUFSM repository](https://github.com/thinwalled/cufsm-git).

