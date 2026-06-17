"""Optional plotting and post-processing helpers for CUFSM Octave results."""

from __future__ import annotations

from pathlib import Path

from .result import CufsmResult


FAMILY_LABELS = {
    1: "global",
    2: "distortional",
    3: "local",
    4: "other",
}


def plot_signature_curve(
    result: CufsmResult,
    *,
    ax=None,
    show_minimum: bool = True,
    show_local_minima: bool = True,
    show_family_minima: bool = True,
    log_x: bool = True,
    title: str | None = None,
):
    """Plot the signature curve and return the matplotlib axis."""

    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots()

    curve = result.signature_curve
    if not curve:
        raise ValueError("result does not contain a signature_curve table.")

    lengths = [row[0] for row in curve]
    eigenvalues = [row[1] for row in curve]
    ax.plot(lengths, eigenvalues, marker=".", linewidth=1, label="signature curve")
    if log_x:
        ax.set_xscale("log")
    ax.set_xlabel("Length")
    ax.set_ylabel("Lowest eigenvalue")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)

    if show_minimum and result.overall_minimum:
        length, eigenvalue = result.overall_minimum
        ax.plot(
            [length],
            [eigenvalue],
            marker="o",
            linestyle="none",
            label="overall minimum",
        )

    if show_local_minima:
        local_minima = result.critical_points.get("local_minima", [])
        if local_minima:
            ax.plot(
                [row[0] for row in local_minima],
                [row[1] for row in local_minima],
                marker="s",
                linestyle="none",
                label="local minima",
            )

    if show_family_minima:
        for row in result.family_minima:
            family_id, length, eigenvalue = int(row[0]), row[1], row[2]
            label = f"{FAMILY_LABELS.get(family_id, 'family')} minimum"
            ax.plot([length], [eigenvalue], marker="^", linestyle="none", label=label)

    if title:
        ax.set_title(title)

    handles, labels = ax.get_legend_handles_labels()
    if labels:
        unique = dict(zip(labels, handles))
        ax.legend(unique.values(), unique.keys())

    return ax


def plot_signature_curve_file(result_path: str | Path, **kwargs):
    """Read a CUFSM result JSON file, plot its signature curve, and return the axis."""

    result = CufsmResult.from_file(result_path)
    return plot_signature_curve(result, **kwargs)


def save_signature_curve_plot(
    result: CufsmResult | str | Path,
    output_path: str | Path,
    *,
    dpi: int = 200,
    **kwargs,
) -> Path:
    """Save a signature-curve plot from a result object or result JSON path."""

    import matplotlib.pyplot as plt

    if isinstance(result, CufsmResult):
        cufsm_result = result
    else:
        cufsm_result = CufsmResult.from_file(result)

    ax = plot_signature_curve(cufsm_result, **kwargs)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ax.figure.tight_layout()
    ax.figure.savefig(output, dpi=dpi)
    plt.close(ax.figure)
    return output.resolve()
