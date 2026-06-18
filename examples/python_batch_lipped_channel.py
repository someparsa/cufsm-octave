"""Batch-run lipped-channel examples through the CUFSM Octave JSON workflow.

This example sweeps lip length and thickness, writes one JSON input per case,
runs each case, and writes a CSV summary. If matplotlib is installed, it also
writes a signature-curve comparison plot.

Usage:
    python examples/python_batch_lipped_channel.py
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from cufsm_octave import logspace_lengths, run_section_input, signature_analysis  # noqa: E402
from cufsm_octave.plotting import FAMILY_LABELS  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "examples" / "batch-results"
MEMBER_LENGTH = 120.0


@dataclass(frozen=True)
class BatchCase:
    case_id: str
    lip: float
    thickness: float


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = make_cases()
    rows = []
    result_paths = []

    for case in cases:
        result = run_case(case)
        result_paths.append(result.path)
        rows.append(summarize_case(case, result))
        print(
            f"{case.case_id}: lip={case.lip}, thickness={case.thickness}, "
            f"overall_minimum={result.overall_minimum}"
        )

    summary_path = OUTPUT_DIR / "batch-summary.csv"
    write_summary_csv(summary_path, rows)
    print(f"Batch summary written to {summary_path}")

    plot_path = OUTPUT_DIR / "signature-curve-comparison.png"
    if write_comparison_plot(result_paths, plot_path):
        print(f"Comparison plot written to {plot_path}")
    else:
        print("matplotlib is not installed; skipped comparison plot.")


def make_cases() -> list[BatchCase]:
    lips = [0.5, 0.75, 1.0, 1.25]
    thicknesses = [0.075, 0.1, 0.125]
    cases = []
    for thickness in thicknesses:
        for lip in lips:
            case_id = f"t{thickness:.3f}_lip{lip:.2f}".replace(".", "p")
            cases.append(BatchCase(case_id=case_id, lip=lip, thickness=thickness))
    return cases


def run_case(case: BatchCase):
    analysis = signature_analysis(
        boundary_condition="S-S",
        lengths=logspace_lengths(1.0, 1000.0, 60, member_lengths=[MEMBER_LENGTH]),
        eigenmodes=6,
    )
    return run_section_input(
        OUTPUT_DIR / f"{case.case_id}.json",
        "lipped-channel",
        depth=9.0,
        flange=5.0,
        lip=case.lip,
        thickness=case.thickness,
        max_segment_length=2.5,
        fy=50.0,
        analysis=analysis,
        output_path=str(OUTPUT_DIR / f"{case.case_id}-results.json"),
        text_output_path=str(OUTPUT_DIR / f"{case.case_id}-results.txt"),
        metadata={
            "name": case.case_id,
            "description": "Batch lipped-channel sweep case.",
            "lip": case.lip,
            "thickness": case.thickness,
        },
    )


def summarize_case(case: BatchCase, result) -> dict[str, object]:
    overall_length, overall_factor = result.overall_minimum
    member_mode = first_member_length_mode(result)
    return {
        "case_id": case.case_id,
        "lip": case.lip,
        "thickness": case.thickness,
        "overall_minimum_length": overall_length,
        "overall_minimum_factor": overall_factor,
        "member_length": member_mode.get("requested_length", ""),
        "member_length_factor": member_mode.get("eigenvalue", ""),
        "member_length_dominant_family": member_mode.get("dominant_family", ""),
        "result_json": str(result.path),
    }


def first_member_length_mode(result) -> dict[str, object]:
    rows = result.member_length_modes
    if not rows:
        return {}
    row = rows[0]
    family_id = int(row[9])
    return {
        "requested_length": row[0],
        "eigenvalue": row[4],
        "dominant_family": FAMILY_LABELS.get(family_id, "unknown"),
    }


def write_summary_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "case_id",
        "lip",
        "thickness",
        "overall_minimum_length",
        "overall_minimum_factor",
        "member_length",
        "member_length_factor",
        "member_length_dominant_family",
        "result_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_comparison_plot(result_paths: list[Path], output_path: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    from cufsm_octave import CufsmResult

    _, ax = plt.subplots()
    for path in result_paths:
        result = CufsmResult.from_file(path)
        curve = result.signature_curve
        label = path.name.replace("-results.json", "")
        ax.plot([row[0] for row in curve], [row[1] for row in curve], label=label)

    ax.set_xscale("log")
    ax.set_xlabel("Length")
    ax.set_ylabel("Lowest eigenvalue")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    ax.legend(fontsize="small", ncols=2)
    ax.figure.tight_layout()
    ax.figure.savefig(output_path, dpi=200)
    plt.close(ax.figure)
    return True


if __name__ == "__main__":
    main()
