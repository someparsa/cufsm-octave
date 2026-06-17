"""Read a CUFSM result JSON file and plot the signature curve.

Usage:
    python examples/postprocess_signature_curve.py \
        examples/lipped-channel-results.json \
        examples/lipped-channel-signature-curve.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from cufsm_octave.plotting import save_signature_curve_plot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot a CUFSM signature curve from a result JSON file."
    )
    parser.add_argument(
        "result_json",
        nargs="?",
        default="examples/lipped-channel-results.json",
        help="Path to the CUFSM result JSON file.",
    )
    parser.add_argument(
        "output_png",
        nargs="?",
        default="examples/lipped-channel-signature-curve.png",
        help="Path for the output PNG image.",
    )
    args = parser.parse_args()

    output = save_signature_curve_plot(
        args.result_json,
        args.output_png,
        title="CUFSM signature curve",
    )
    print(f"Signature curve plot written to {output}")


if __name__ == "__main__":
    main()
