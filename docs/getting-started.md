# Getting Started

This guide shows the shortest path from a fresh checkout to running CUFSM Octave CLI.

## Requirements

- GNU Octave with `octave-cli` available on the command line.
- Git, if cloning from GitHub.
- A terminal: PowerShell, Command Prompt, Windows Terminal, macOS Terminal, Linux shell, or WSL.

Check Octave with:

```bash
octave-cli --version
```

## Install GNU Octave

### Windows Installer

Download GNU Octave from:

https://octave.org/download

After installation, open a new PowerShell or Command Prompt window and run:

```powershell
octave-cli --version
```

If the command is not found, restart the terminal or add the Octave installation directory to `PATH`.

### Windows PowerShell With winget

```powershell
winget install -e --id GNU.Octave
```

Then open a new terminal and check:

```powershell
octave-cli --version
```

### Windows Subsystem For Linux

For Ubuntu or Debian in WSL:

```bash
sudo apt update
sudo apt install octave git
```

### macOS

Using Homebrew:

```bash
brew update
brew install octave
```

### Ubuntu / Debian Linux

```bash
sudo apt update
sudo apt install octave git
```

## Get The Repository

```bash
git clone https://github.com/someparsa/cufsm-octave.git
cd cufsm-octave
```

## Run The JSON Example

The JSON workflow is the preferred workflow for repeatable analysis:

```bash
octave-cli --quiet cufsm_json.m examples/lipped-channel.json
```

It writes:

```text
examples/lipped-channel-results.json
examples/lipped-channel-results.txt
```

The JSON result is the machine-readable result. The text report is easier to inspect manually.

## Run The Legacy Script Example

The older hardcoded example is still available:

```bash
octave-cli --quiet cufsm-octave-example.m
```

It writes:

```text
cufsm-results.txt
```

Use this mostly as a reference for the original hardcoded Octave workflow. Prefer the JSON runner for new work.

## Running From WSL Against A Windows Folder

If the repository is stored on a Windows drive and you run Octave through WSL, use a command like:

```powershell
wsl bash -lc "cd /mnt/c/path/to/cufsm-octave && octave-cli --quiet cufsm_json.m examples/lipped-channel.json"
```

Replace `/mnt/c/path/to/cufsm-octave` with the actual WSL path.
