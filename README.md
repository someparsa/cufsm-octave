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

CUFSM Octave CLI is intended to run from the command line using GNU Octave. MATLAB is not required for the current command-line example workflow.

You will need:

- GNU Octave
- Git, if you want to clone the repository from GitHub
- A terminal, such as PowerShell, Command Prompt, macOS Terminal, Linux Terminal, or WSL

## Installing GNU Octave

### Windows

On Windows, you can either install GNU Octave directly or use Windows Subsystem for Linux.

#### Option 1: GNU Octave Installer (GUI)

Download and install GNU Octave from:

https://octave.org/download

After installation, open PowerShell or Command Prompt and check that Octave is available:

```powershell
octave-cli --version
```

If the command is not recognised, restart the terminal or add the Octave installation folder to your system PATH.

#### Option 2: Windows Subsystem for Linux

If you use Ubuntu or Debian through WSL, install Octave inside WSL:

```bash
sudo apt update
sudo apt install octave git
```

Then check the installation:

```bash
octave-cli --version
```

#### Option 3: Windows PowerShell

On Windows, GNU Octave can be installed directly from PowerShell using `winget`, the Windows Package Manager.

```powershell
winget install -e --id GNU.Octave
```

After installation, close and reopen PowerShell, then check that Octave is available:

```powershell
octave-cli --version
```

Next, clone the repository and enter the project folder:

```powershell
git clone https://github.com/someparsa/cufsm-octave.git
cd cufsm-octave
```

Run the example:

```powershell
octave-cli --quiet cufsm-octave-example.m
```

After the run is complete, the output report will be written to:

```text
cufsm-results.txt
```

If `octave-cli` is not recognised after installation, restart PowerShell or check that the Octave installation directory has been added to your system `PATH`.

### macOS

On macOS, the easiest installation method is usually through Homebrew:

```bash
brew update
brew install octave
```

Then check that Octave is available:

```bash
octave-cli --version
```

If you do not use Homebrew, follow the macOS installation instructions from:

https://octave.org/download

### Ubuntu / Debian Linux

On Ubuntu or Debian, install Octave and Git using apt:

```bash
sudo apt update
sudo apt install octave git
```

Then check the installation:

```bash
octave-cli --version
```

## Getting the Repository

Clone the repository using Git:

```bash
git clone https://github.com/someparsa/cufsm-octave.git
cd cufsm-octave
```

Alternatively, download the repository as a ZIP file from GitHub, extract it, and open a terminal inside the extracted `cufsm-octave` folder.

## Running the Example

From inside the repository folder, run:

```bash
octave-cli --quiet cufsm-octave-example.m
```

This runs the example model included with the repository.

The current example defines a lipped channel under uniform compression. It uses simply supported loaded edges and evaluates a logarithmically spaced range of half-wavelengths. The lowest buckling eigenvalue at each half-wavelength is used to construct the signature curve.

After the example runs, a text report is written to:

```text
cufsm-results.txt
```

The report includes the model data, analysis settings, eigenvalue results, signature-curve results, and critical points.


## Running A JSON Input

The repository also includes a JSON-driven runner intended for repeatable CLI, automation, and AI-agent workflows:

```bash
octave-cli --quiet cufsm_json.m examples/lipped-channel.json
```

This reads the named-field JSON model, converts it to the CUFSM matrix inputs, runs the same headless signature-curve analysis, and writes the configured result files:

```text
cufsm-results.json
cufsm-results-from-json.txt
```

The JSON input maps directly to the existing CUFSM variables:

| JSON field | CUFSM variable | Meaning |
| --- | --- | --- |
| `model.materials` | `prop` | Material rows: `material_id`, `Ex`, `Ey`, `nu_x`, `nu_y`, `G` |
| `model.nodes` | `node` | Node rows: `node_id`, `x`, `z`, restraints, stress |
| `model.elements` | `elem` | Element rows: `element_id`, end nodes, thickness, material |
| `model.springs` | `springs` | Optional spring definitions |
| `model.constraints` | `constraints` | Optional multipoint constraints |
| `loading` | `node(:,8)` | Direct stress table or generated stresses from actions |
| `analysis.lengths` | `lengths` | Explicit, linear, or logarithmic length set |
| `analysis.boundary_condition` | `BC` | `S-S`, `C-C`, `S-C`, `C-F`, or `C-G` |
| `analysis.longitudinal_terms` | `m_all` | Longitudinal terms per length |
| `analysis.cfsm` | `GBTcon` | cFSM mode inclusion and basis settings |
| `analysis.eigenmodes` | `neigs` | Number of eigenvalues requested |
| `analysis.vectorized` | `ifVec` | Vectorized solver flag |

The first supported analysis type is:

```json
"analysis": {
  "type": "signature_curve"
}
```

The first supported loading modes are:

```json
"loading": {
  "type": "stress_table"
}
```

and:

```json
"loading": {
  "type": "generated_from_actions",
  "fy": 50.0,
  "unsymmetric": false,
  "actions": {
    "P_factor": 1.0,
    "Mxx_factor": 0.0,
    "Mzz_factor": 0.0,
    "M11_factor": 0.0,
    "M22_factor": 0.0
  }
}
```

The generated-action mode computes section properties, yield reference actions, and nodal stresses before analysis. This mirrors the loading workflow in `cufsm-octave-example.m`.

## Running the Example from Windows Using WSL

If the repository is stored on your Windows drive and you want to run the example through WSL, use a command like this from PowerShell:

```powershell
wsl bash -lc "cd /mnt/c/path/to/cufsm-octave && octave-cli --quiet cufsm-octave-example.m"
```

Replace `/mnt/c/path/to/cufsm-octave` with the actual WSL path to your repository folder.

For example, if the repository is located at:

```text
C:\Users\YourName\Downloads\cufsm-octave
```

then the WSL path will usually be:

```bash
/mnt/c/Users/YourName/Downloads/cufsm-octave
```

The output file will be created in the repository folder as:

```text
cufsm-results.txt
```

## Notes

The original example model is defined directly inside:

```text
cufsm-octave-example.m
```

Users can modify this file to change the section geometry, material properties, loading, boundary conditions, and half-wavelength range.

For machine-readable workflows, prefer copying and editing:

```text
examples/lipped-channel.json
```

The JSON format is intentionally explicit and named-field based so that humans, scripts, and LLM agents can generate and validate inputs without relying on positional matrix columns.

A draft validation schema is included at `schema/input-v1.schema.json`.

## Example Model

The current example defines a lipped channel under uniform compression. It uses simply supported loaded edges (`S-S`) and evaluates 100 logarithmically spaced half-wavelengths from 1 to 1000. The first, or lowest, buckling eigenvalue at each half-wavelength forms the reported signature curve.

The same model is available both as `cufsm-octave-example.m` and as `examples/lipped-channel.json`.

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
