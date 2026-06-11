# Development TODO

## Octave Backend

- [ ] Separate model input, analysis, and result export into reusable functions.
- [ ] Preserve and validate the CUFSM numerical backend under GNU Octave.
- [ ] Add regression tests against trusted CUFSM results.
- [ ] Support configurable geometry, loading, half-wavelengths, boundary
  conditions, springs, constraints, and eigenmodes.
- [ ] Add stable machine-readable input and output formats.

## Command-Line Interface

- [ ] Add documented commands and options for running analyses.
- [ ] Provide clear validation errors, exit codes, and logging levels.
- [ ] Allow users to select input files, output formats, and output locations.
- [ ] Keep all analysis workflows fully usable without graphics.

## Python Integration

- [ ] Provide a Python interface for preparing inputs and reading results.
- [ ] Export signature curves and mode data in Python-friendly formats.
- [ ] Add optional Python plotting for signature curves, cross-sections, and
  mode shapes.
- [ ] Support development of graphical applications in Python without coupling
  the numerical backend to a specific GUI framework.
- [ ] Evaluate packaging the Octave backend and Python tools as one documented
  workflow.

## Public Development

- [ ] Add cross-platform automated tests for Octave and Python integration.
- [ ] Document the backend and CLI contracts for external developers.
- [ ] Add versioning, citation, contribution, and release guidance.
