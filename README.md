# CUFSM Octave CLI

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20635623.svg)](https://doi.org/10.5281/zenodo.20635623)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Octave](https://img.shields.io/badge/GNU%20Octave-compatible-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Status](https://img.shields.io/badge/status-development-orange)

**Octave-oriented adaptation by Parsa Yazdi**

CUFSM Octave CLI is a command-line-oriented adaptation of [CUFSM](https://github.com/thinwalled/cufsm-git), the constrained and unconstrained finite strip method software for elastic buckling analysis of thin-walled member cross-sections.

This repository adapts CUFSM numerical routines for headless execution with GNU Octave. The main workflow runs signature-curve analyses from JSON input files and writes machine-readable JSON results plus text reports.

## Current Capabilities

- Runs CUFSM signature-curve analysis from `octave-cli`.
- Supports reproducible JSON input for model, loading, analysis, and output settings.
- Includes Python helpers for generating JSON inputs from common section templates.
- Includes Python post-processing helpers for reading result JSON and plotting signature curves.
- Supports generated loading from reference actions or direct stress-table loading.
- Inserts declared member lengths into the solved length set.
- Reports signature curves, critical points, classified minima, and cFSM mode participation.
- Writes JSON and text outputs suitable for automation and manual review.
- Retains the broader CUFSM numerical source as a basis for continued CLI development.

## Quick Start

Install GNU Octave, then clone and enter the repository:

```bash
git clone https://github.com/someparsa/cufsm-octave.git
cd cufsm-octave
```

Check Octave:

```bash
octave-cli --version
```

Run the JSON example:

```bash
octave-cli --quiet cufsm_json.m examples/lipped-channel.json
```

The example writes:

```text
examples/lipped-channel-results.json
examples/lipped-channel-results.txt
```

The older hardcoded example is also available:

```bash
octave-cli --quiet cufsm-octave-example.m
```

It writes:

```text
cufsm-results.txt
```

## Documentation

| Topic | Document |
| --- | --- |
| Installation and first run | [docs/getting-started.md](docs/getting-started.md) |
| JSON input fields | [docs/json-input-format.md](docs/json-input-format.md) |
| JSON and text output fields | [docs/json-output-format.md](docs/json-output-format.md) |
| Example walkthrough | [docs/examples.md](docs/examples.md) |
| Signature-curve and mode-family background | [docs/theory-and-cufsm-background.md](docs/theory-and-cufsm-background.md) |
| Compatibility and regression scope | [docs/compatibility-and-regression.md](docs/compatibility-and-regression.md) |
| Python tooling | [docs/python-tooling.md](docs/python-tooling.md) |
| Development direction | [docs/development-roadmap.md](docs/development-roadmap.md) |
| Backend code map | [docs/backend-code-map.md](docs/backend-code-map.md) |

The JSON schema is tracked at [schema/input-v1.schema.json](schema/input-v1.schema.json).

## JSON Workflow Summary

The preferred runner is:

```bash
octave-cli --quiet cufsm_json.m path/to/input.json
```

The input JSON is the source of truth for model and analysis settings. The CLI should remain thin and should not duplicate engineering options that belong in the JSON file.

Key input sections:

| JSON section | Purpose |
| --- | --- |
| `model` | Materials, nodes, elements, springs, and constraints. |
| `loading` | Stress-table loading or generated stresses from actions. |
| `analysis` | Signature-curve settings, boundary condition, lengths, member lengths, eigenmodes, mesh refinement, and cFSM settings. |
| `output` | JSON and text output paths. |

Mode-family participation uses numeric dominant-family codes:

| Code | Buckling mode family |
| --- | --- |
| `1` | Global |
| `2` | Distortional |
| `3` | Local |
| `4` | Other |

Important output fields:

| JSON output key | Meaning |
| --- | --- |
| `signature_curve` | Lowest eigenvalue at each analyzed length. |
| `critical_points.local_minima_classified` | Detected local minima with cFSM participation and dominant family. |
| `critical_points.family_minima` | Lowest detected minimum for each dominant family that appears. |
| `mode_participation.lowest_modes` | Lowest-mode participation at every analyzed length. |
| `mode_participation.member_lengths` | All solved eigenmodes at declared member lengths. |
| `mode_participation.signature_minima` | All solved eigenmodes at detected signature-curve minima. |

## Example Model

The included JSON example defines a lipped channel under generated uniform compression. It uses simply supported loaded edges and evaluates a logarithmically spaced signature curve with an inserted member length:

```json
"lengths": {
  "type": "logspace",
  "min": 1.0,
  "max": 1000.0,
  "count": 100,
  "member_lengths": [120.0]
}
```

See [docs/examples.md](docs/examples.md) for details.

## Project Status

This repository is under active development. The JSON workflow executes successfully with GNU Octave, and current development focuses on the headless runner contract, JSON/Python interoperability, examples, and compatibility checks against known CUFSM workflows.

See [TODO.md](TODO.md), [IMPROVEMENTS.md](IMPROVEMENTS.md), and [docs/development-roadmap.md](docs/development-roadmap.md).

## Upstream Project

The finite strip implementation and core engineering methods originate from the official [thinwalled/cufsm-git](https://github.com/thinwalled/cufsm-git) repository. CUFSM was developed by Benjamin W. Schafer and contributors.

This repository is an independent CLI-oriented development project. It is not a replacement for the official CUFSM distribution, GUI, documentation, or compiled applications.

## Authorship And Attribution

CLI-oriented development and maintenance:

**Parsa Yazdi**  
University of Waikato

Original CUFSM development and contributors are documented by the upstream project and its citation metadata:

- [Official CUFSM repository](https://github.com/thinwalled/cufsm-git)
- [Official CUFSM releases](https://github.com/thinwalled/cufsm-git/releases)

Users publishing research based on this software should cite the official CUFSM project and the relevant finite strip method literature identified by the upstream repository.

## License

This project is distributed under the MIT License, consistent with the upstream CUFSM project. See [LICENSE](LICENSE).
