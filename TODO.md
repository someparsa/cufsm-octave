# Development TODO

Completed items reflect the current repository. Unchecked items are the next
maintenance and development work.

## Octave Backend

- [x] Preserve the CUFSM numerical backend under headless GNU Octave.
- [x] Support configurable geometry, loading, half-wavelengths, boundary
  conditions, springs, constraints, and eigenmodes.
- [x] Add versioned machine-readable JSON input and output formats.
- [ ] Refactor the JSON runner into smaller, separately testable functions.
- [ ] Add lightweight compatibility checks against known CUFSM runner outputs.

## Command-Line Interface

- [x] Document the JSON runner command and input-file workflow.
- [x] Allow users to select input files, output formats, and output locations.
- [x] Keep the signature-curve workflow usable without graphics.
- [ ] Standardize validation errors, exit codes, and logging levels.
- [ ] Add optional command-line flags without duplicating engineering settings
  already stored in JSON.

## Python Integration

- [x] Provide an initial Python interface for loading inputs, running Octave, and reading results.
- [x] Generate JSON inputs from common section templates.
- [x] Export signature curves and mode data through Python-friendly accessors.
- [x] Add optional Python plotting for signature curves.
- [x] Add Python examples for batch runs and simple grid-search optimization.
- [ ] Add automated tests for Python validation, templates, runners, and result
  accessors.
- [ ] Add optional Python plotting for cross-sections and mode shapes.
- [ ] Support development of graphical applications in Python without coupling
  the numerical backend to a specific GUI framework.
- [ ] Package the Octave backend and Python tools as one installable workflow.

## MCP Interface

- [x] Add a hosted beta MCP server around the existing CUFSM workflow.
- [x] Add validated parametric inputs for supported section templates.
- [x] Return structured analysis results and static plot images.
- [x] Isolate calculations and enforce per-request timeouts.
- [x] Document server updates, health checks, smoke tests, and rollback.
- [ ] Add automated tests for MCP schemas, defaults, tool calls, timeouts, and
  cleanup.
- [ ] Publish an explicit MCP server version and compatibility policy.
- [ ] Track provider-neutral systemd and reverse-proxy configuration examples.
- [ ] Define monitoring, rate-limiting, and access-control requirements for the
  hosted beta service.

## Public Development

- [ ] Add cross-platform compatibility checks for Octave and Python integration.
- [x] Document the backend and CLI contracts for external developers.
- [x] Add project versioning and citation guidance.
- [ ] Add contribution and release-process guidance.
- [ ] Publish trusted reference cases for numerical regression checks.
