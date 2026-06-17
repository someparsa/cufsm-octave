"""Subprocess runner for CUFSM Octave JSON analyses."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

from .io import REPO_ROOT, load_input, validate_input
from .result import CufsmResult


class CufsmRunError(RuntimeError):
    """Raised when the Octave runner exits with a non-zero status."""


def run_cufsm(
    input_path: str | Path,
    *,
    repo_root: str | Path = REPO_ROOT,
    octave_cli: str = "octave-cli",
    validate: bool = True,
    extra_args: Sequence[str] = (),
) -> CufsmResult:
    """Run ``cufsm_json.m`` for *input_path* and return a result wrapper."""

    root = Path(repo_root).resolve()
    input_file = Path(input_path)
    if not input_file.is_absolute():
        input_file = root / input_file
    if validate:
        validate_input(load_input(input_file))

    input_data = load_input(input_file)
    output_path = _output_path_from_input(input_data, root)
    command = [
        octave_cli,
        "--quiet",
        str(root / "cufsm_json.m"),
        str(input_file),
        *extra_args,
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise CufsmRunError(
            "CUFSM Octave run failed with exit code "
            f"{completed.returncode}.\nSTDOUT:\n{completed.stdout}\nSTDERR:\n"
            f"{completed.stderr}"
        )
    return CufsmResult.from_file(output_path)


def _output_path_from_input(data: dict, repo_root: Path) -> Path:
    output = data.get("output", {})
    path = output.get("path", "cufsm-results.json")
    output_path = Path(path)
    if output_path.is_absolute():
        return output_path
    return repo_root / output_path
