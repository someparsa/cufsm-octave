# Development TODO

This file tracks planned work for CUFSM Octave CLI. Priorities may change as
the input and output contracts are defined.

## CLI Interface

- [ ] Replace source-file configuration with documented command-line options.
- [ ] Add a stable model input format, initially JSON, TOML, or CSV.
- [ ] Allow the output path and filename to be selected by the user.
- [ ] Add clear exit codes and concise error messages for invalid input.
- [ ] Add `--help`, `--version`, and analysis-summary commands.
- [ ] Support quiet, normal, and diagnostic logging modes.

## Analysis

- [ ] Validate results against equivalent official CUFSM MATLAB analyses.
- [ ] Add configurable half-wavelength ranges and sampling strategies.
- [ ] Add selection of the number of eigenmodes to retain or report.
- [ ] Support general boundary-condition analyses through the CLI.
- [ ] Define CLI input schemas for springs and multipoint constraints.
- [ ] Evaluate cFSM modal classification support in headless operation.
- [ ] Evaluate vibration and fcFSM workflows separately.

## Output And Visualisation

- [ ] Add a machine-readable result format such as JSON or CSV.
- [ ] Make mode-shape export optional rather than part of default output.
- [ ] Record units and model metadata explicitly in every result file.
- [ ] Add Python-based signature-curve plotting as an optional tool.
- [ ] Add Python-based cross-section and selected mode-shape visualisation.

## Quality

- [ ] Add automated regression tests for signature-curve values.
- [ ] Test supported Octave versions on Linux, macOS, and Windows/WSL.
- [ ] Add continuous integration for headless Octave execution.
- [ ] Audit remaining MATLAB-specific syntax and APIs.
- [ ] Review numerical warnings, convergence handling, and invalid models.
- [ ] Add input validation for materials, nodes, elements, and references.
- [ ] Document numerical tolerances and expected platform variation.

## Public Release

- [ ] Add a citation file for this development and retain upstream citation.
- [ ] Define versioning and release procedures.
- [ ] Add contribution and issue-reporting guidance.
- [ ] Complete a dependency and attribution audit before the first release.
- [ ] Prepare a minimal reproducible example and expected output fixture.

