# CUFSM-Octave

CUFSM-Octave is an Octave-oriented adaptation of the original CUFSM MATLAB codebase. CUFSM, the Constrained and Unconstrained Finite Strip Method software, provides elastic buckling analysis of thin-walled member cross-sections using the finite strip method. This version aims to make selected CUFSM capabilities easier to use in GNU Octave, command-line environments, automated workflows, and reproducible research pipelines.

This repository is based on the original open-source CUFSM project and retains selected computational components of the original implementation. The focus of this adaptation is not to replace the official CUFSM distribution, but to provide a streamlined variant suitable for Octave-compatible, script-based, and CLI-focused use.

## Project Background

The original CUFSM software was developed as a MATLAB-based tool for elastic buckling analysis of thin-walled structural members. It includes both constrained and unconstrained finite strip method formulations and supports analyses such as signature curve generation and general boundary condition modelling. CUFSM has been widely used in cold-formed steel research, structural stability studies, and engineering education.

The original CUFSM project is available at:

* https://github.com/thinwalled/cufsm-git
* https://www.ce.jhu.edu/cufsm

This repository builds on that work by adapting selected parts of the codebase for use in GNU Octave and command-line workflows.

## Purpose of This Adaptation

The purpose of this project is to support a more accessible and scriptable version of selected CUFSM functionality. MATLAB remains a powerful and widely used platform, but access to MATLAB may be limited for some users, especially in open-source, Linux-based, remote-server, or automated research environments. GNU Octave provides a free and open-source environment with broad compatibility with MATLAB syntax, making it a practical platform for adapting numerical engineering codes.

This adaptation is therefore intended to support:

* command-line execution of finite strip analyses;
* Octave-compatible workflows;
* batch analysis and automated parametric studies;
* integration with optimisation, scripting, and research pipelines;
* easier deployment on Linux systems and remote servers;
* reproducible computational studies using open-source tools.

## Scope of Development

This version focuses mainly on the computational and analysis-related components of CUFSM. Graphical interface components, MATLAB-app-specific files, icons, templates, and GUI utilities may be removed, simplified, or reorganised where they are not required for command-line execution.

The development approach is intentionally conservative. Where possible, original function names, file structures, and numerical logic are retained to preserve traceability to the upstream CUFSM codebase. Changes are introduced only where needed to improve Octave compatibility, simplify CLI-based use, or support automated workflows.

## Relationship to the Original CUFSM Project

This repository is a derivative adaptation of the original CUFSM project. It does not aim to replace the official CUFSM distribution. Users who require the complete MATLAB GUI, official standalone applications, or the full original feature set should refer to the official CUFSM repository and project website.

This version is intended for users who want to run selected CUFSM-style analyses in Octave or in script-based workflows. Future updates from the original CUFSM project may be reviewed and selectively incorporated when compatible with the CLI-oriented direction of this repository.

## Acknowledgement and Citation

This repository is an Octave-oriented adaptation of the original CUFSM codebase. CUFSM, the Constrained and Unconstrained Finite Strip Method software, was developed for elastic buckling analysis of thin-walled member cross-sections and has made a significant contribution to thin-walled member stability analysis, cold-formed steel research, structural stability studies, and engineering education.

This work acknowledges the original CUFSM authors and contributors. The original CUFSM project remains the primary reference for the underlying finite strip method implementation, the computational approach, and the software's historical development.

The original CUFSM software is distributed under the MIT License. This repository retains the original licence notices and documents additional modifications made for Octave-oriented and command-line workflows.

If you use this adapted version, please cite this repository where appropriate and also cite the original CUFSM software and related academic papers. Citation information is provided in the `CITATION.cff` file.

## Note on Language Classification

Although GitHub may classify this repository as MATLAB due to the use of `.m` source files, this project is developed as an Octave-oriented adaptation. GNU Octave uses MATLAB-compatible `.m` files, so the repository language statistics may not fully reflect the intended execution environment.

# CUFSM (Copy from the Original Rep)

This is the GitHub repository for the cross-section elastic buckling analysis tool CUFSM, written in MATLAB.

## Description

CUFSM is the Constrained and Unconstrained Finite Strip Method and provides elastic buckling for member cross-sections as utilised by structural engineers. The method employs the finite strip method, a variant of the finite element method. The implementation allows for general end boundary conditions via series approximations or provides signature curve analysis aligned with classical buckling solutions under idealised end conditions.

## Installation

The latest version of the software is available for download on [the latest release page](https://github.com/thinwalled/cufsm-git/releases). The software is provided as both (1) the MATLAB source code and (2) compiled standalone applications. For researchers, students, or anyone with access to MATLAB, it is highly recommended to use the source code directly in MATLAB; this is much more stable and manageable.

Note: installation of the standalone version (PC or Mac) will also require downloading libraries from MATLAB (MathWorks). In addition, be patient at boot-up of the standalone version; it takes a few moments for the code to load.

Note: installing the MATLAB app version will place a cufsm icon in the MATLAB app toolbar and allow users to use the GUI without knowing the underlying file structures, etc. Anyone using cufsm for research, or in batch mode, should use the source files. Open cufsm5.m, set your directory to the installation location, and then run cufsm5 from the command line in MATLAB to start the GUI.

## License

Software is open source and distributed under [MIT license](https://github.com/thinwalled/cufsm-git/blob/main/LICENSE).

## Help and Support

For assistance with the package, please raise an issue on the GitHub Issues page. Please use the appropriate labels to indicate the specific functionality you are inquiring about.

## Additional Information

The websites [www.ce.jhu.edu/cufsm](www.ce.jhu.edu/cufsm) and [www.ce.jhu.edu/bschafer](www.ce.jhu.edu/bschafer) provide more information on the software.
