# CUFSM Octave CLI

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20635623.svg)](https://doi.org/10.5281/zenodo.20635623)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Octave](https://img.shields.io/badge/GNU%20Octave-compatible-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Status](https://img.shields.io/badge/status-development-orange)

**Octave-oriented adaptation by Parsa Yazdi**

CUFSM Octave CLI is a command-line-oriented adaptation of [CUFSM](https://github.com/thinwalled/cufsm-git), the constrained and unconstrained finite strip method software for elastic buckling analysis of thin-walled member cross-sections.

This project adapts the CUFSM numerical routines for headless execution with GNU Octave, enabling users to run signature-curve analyses from the command line without relying on the MATLAB graphical interface or plotting system. By removing GUI-dependent steps and supporting reproducible CLI-based workflows across Linux and Windows, CUFSM Octave CLI enables faster and more efficient execution, automation, testing, integration, and future multi-platform development.

## Upstream Project

The finite strip implementation and core engineering methods originate from the official [thinwalled/cufsm-git](https://github.com/thinwalled/cufsm-git) repository. CUFSM was developed by Benjamin W. Schafer and contributors.

This repository is an independent, CLI-oriented development project. It is not a replacement for the official CUFSM distribution, GUI, documentation, or compiled applications.

## Current Capabilities

- Runs a CUFSM signature-curve analysis from `octave-cli`.
- Uses paths relative to the project directory on Linux, macOS, and Windows.
- Supports headless operation without figures, plotters, or GUI progress bars.
- Calculates elastic buckling eigenvalues over a logarithmic range of half-wavelengths.
- Writes a compact text report containing:
  - material properties;
  - refined node geometry, restraints, and stresses;
  - element connectivity and thickness;
  - analysis settings;
  - the lowest eigenvalue at every half-wavelength;
  - local minima and the overall minimum.
- Retains the broader CUFSM numerical source as a basis for continued CLI development.

## Requirements

- GNU Octave with `octave-cli` available on the command line.
- A shell environment capable of running Octave.
- WSL may be used when working from Windows.

No graphical toolkit is required for the current CLI workflow.

## Running The Example

From Linux, macOS, or WSL:

```bash
cd /path/to/cufsm-octave
octave-cli --quiet cufsm-octave-example.m
```

Example from Windows PowerShell through WSL:

```powershell
wsl bash -lc "cd /mnt/c/path/to/cufsm-octave && octave-cli --quiet cufsm-octave-example.m"
```

The analysis writes `cufsm-results.txt` in the project directory.

## Example Model

The current example defines a lipped channel under uniform compression. It uses simply supported loaded edges (`S-S`) and evaluates 100 logarithmically spaced half-wavelengths from 1 to 1000. The first, or lowest, buckling eigenvalue at each half-wavelength forms the reported signature curve.

The model is currently defined directly in `cufsm-octave-example.m`. A future CLI interface is intended to accept model and analysis parameters without requiring edits to the source file.

## Output

The text report is divided into four sections:

1. `MODEL`
2. `ANALYSIS SETTINGS`
3. `SIGNATURE CURVE`
4. `CRITICAL POINTS`

The signature curve is emitted as comma-separated pairs:

```text
half_wavelength,lowest_eigenvalue
1,...
1.07226722201,...
...
```

Large mode-shape matrices are intentionally excluded from the default report. They may be exposed later through an optional machine-readable output mode.

## Project Status

This repository is under active development. The present example executes successfully with GNU Octave in a headless WSL environment, but it is not yet a general-purpose packaged CLI. Numerical validation, automated tests, stable input schemas, and additional analysis modes remain development priorities.

See [TODO.md](TODO.md) for planned work and [IMPROVEMENTS.md](IMPROVEMENTS.md) for completed major changes.

## Plotting

The original CUFSM plotting routines are retained for compatibility and reference but are not loaded by the CLI example. Future visualisation can be implemented separately, including through Python tools that consume the reported signature-curve data.

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
