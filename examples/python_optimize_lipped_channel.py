"""Grid-search optimization example using the CUFSM Octave JSON workflow.

This example varies lipped-channel flange width and lip length, runs each case,
and selects the case with the largest lowest-mode eigenvalue at the requested
member length. It uses only the Python standard library plus this package.

Usage:
    python examples/python_optimize_lipped_channel.py
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from cufsm_octave import logspace_lengths, run_section_input, signature_analysis  # noqa: E402
from cufsm_octave.plotting import FAMILY_LABELS, save_signature_curve_plot  # noqa: E402


OUTPUT_DIR = REPO_ROOT / "examples" / "optimization-results"
MEMBER_LENGTH = 120.0


@dataclass(frozen=True)
class OptimizationCase:
    case_id: str
    flange: float
    lip: float


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for case in make_cases():
        result = run_case(case)
        row = summarize_case(case, result)
        rows.append(row)
        print(
            f"{case.case_id}: flange={case.flange}, lip={case.lip}, "
            f"objective={row['objective_member_length_factor']}"
        )

    best = max(rows, key=lambda row: row["objective_member_length_factor"])
    summary_path = OUTPUT_DIR / "optimization-summary.csv"
    write_summary_csv(summary_path, rows)
    copy_best_files(best)
    maybe_plot_best(best)

    print(f"Optimization summary written to {summary_path}")
    print(
        "Best case: "
        f"{best['case_id']} with member-length factor "
        f"{best['objective_member_length_factor']}"
    )


def make_cases() -> list[OptimizationCase]:
    flanges = [4.0, 4.5, 5.0, 5.5, 6.0]
    lips = [0.5, 0.75, 1.0, 1.25, 1.5]
    cases = []
    for flange in flanges:
        for lip in lips:
            if lip >= flange:
                continue
            case_id = f"flange{flange:.2f}_lip{lip:.2f}".replace(".", "p")
            cases.append(OptimizationCase(case_id=case_id, flange=flange, lip=lip))
    return cases


def run_case(case: OptimizationCase):
    analysis = signature_analysis(
        boundary_condition="S-S",
        lengths=logspace_lengths(1.0, 1000.0, 60, member_lengths=[MEMBER_LENGTH]),
        eigenmodes=6,
    )
    return run_section_input(
        OUTPUT_DIR / f"{case.case_id}.json",
        "lipped-channel",
        depth=9.0,
        flange=case.flange,
        lip=case.lip,
        thickness=0.1,
        max_segment_length=2.5,
        fy=50.0,
        analysis=analysis,
        output_path=str(OUTPUT_DIR / f"{case.case_id}-results.json"),
        text_output_path=str(OUTPUT_DIR / f"{case.case_id}-results.txt"),
        metadata={
            "name": case.case_id,
            "description": "Grid-search lipped-channel optimization case.",
            "flange": case.flange,
            "lip": case.lip,
            "objective": "maximize lowest eigenvalue at member length 120.0",
        },
    )


def summarize_case(case: OptimizationCase, result) -> dict[str, object]:
    member_mode = first_member_length_mode(result)
    overall_length, overall_factor = result.overall_minimum
    return {
        "case_id": case.case_id,
        "flange": case.flange,
        "lip": case.lip,
        "objective_member_length_factor": member_mode["eigenvalue"],
        "member_length": member_mode["requested_length"],
        "member_length_dominant_family": member_mode["dominant_family"],
        "overall_minimum_length": overall_length,
        "overall_minimum_factor": overall_factor,
        "input_json": str(OUTPUT_DIR / f"{case.case_id}.json"),
        "result_json": str(result.path),
    }


def first_member_length_mode(result) -> dict[str, object]:
    rows = result.member_length_modes
    if not rows:
        raise RuntimeError("Result does not contain member-length mode participation.")
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
        "flange",
        "lip",
        "objective_member_length_factor",
        "member_length",
        "member_length_dominant_family",
        "overall_minimum_length",
        "overall_minimum_factor",
        "input_json",
        "result_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def copy_best_files(best: dict[str, object]) -> None:
    shutil.copyfile(best["input_json"], OUTPUT_DIR / "best-case.json")
    shutil.copyfile(best["result_json"], OUTPUT_DIR / "best-case-results.json")


def maybe_plot_best(best: dict[str, object]) -> None:
    try:
        save_signature_curve_plot(
            best["result_json"],
            OUTPUT_DIR / "best-signature-curve.png",
            title=f"Best case: {best['case_id']}",
        )
    except ImportError:
        print("matplotlib is not installed; skipped best-case plot.")


if __name__ == "__main__":
    main()
