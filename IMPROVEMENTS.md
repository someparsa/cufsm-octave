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

## Development Attribution

The CLI-oriented changes documented here are developed by:

**Parsa Yazdi**  
University of Waikato

The underlying CUFSM numerical methods and source originate from the official
[CUFSM repository](https://github.com/thinwalled/cufsm-git).

