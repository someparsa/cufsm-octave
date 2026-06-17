# Development TODO

## Octave Backend

- [ ] Separate model input, analysis, and result export into reusable functions.
- [ ] Preserve and validate the CUFSM numerical backend under GNU Octave.
- [ ] Add lightweight compatibility checks against known CUFSM runner outputs.
- [ ] Support configurable geometry, loading, half-wavelengths, boundary
  conditions, springs, constraints, and eigenmodes.
- [ ] Add stable machine-readable input and output formats.

## Command-Line Interface

- [ ] Add documented commands and options for running analyses.
- [ ] Provide clear validation errors, exit codes, and logging levels.
- [ ] Allow users to select input files, output formats, and output locations.
- [ ] Keep all analysis workflows fully usable without graphics.

## Python Integration

- [x] Provide an initial Python interface for loading inputs, running Octave, and reading results.
- [x] Generate JSON inputs from common section templates.
- [x] Export signature curves and mode data through Python-friendly accessors.
- [x] Add optional Python plotting for signature curves.
- [ ] Add optional Python plotting for cross-sections and mode shapes.
- [ ] Support development of graphical applications in Python without coupling
  the numerical backend to a specific GUI framework.
- [ ] Evaluate packaging the Octave backend and Python tools as one documented
  workflow.

## Public Development

- [ ] Add cross-platform compatibility checks for Octave and Python integration.
- [ ] Document the backend and CLI contracts for external developers.
- [ ] Add versioning, citation, contribution, and release guidance.
