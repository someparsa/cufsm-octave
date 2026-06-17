"""Result accessors for CUFSM Octave JSON output."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import load_json


@dataclass(frozen=True)
class CufsmResult:
    """Convenience wrapper around a CUFSM JSON result object."""

    data: dict[str, Any]
    path: Path | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "CufsmResult":
        result_path = Path(path)
        return cls(load_json(result_path), result_path.resolve())

    @property
    def signature_curve(self) -> list[list[float]]:
        return self.data.get("signature_curve", [])

    @property
    def critical_points(self) -> dict[str, Any]:
        return self.data.get("critical_points", {})

    @property
    def overall_minimum(self) -> list[float] | None:
        return self.critical_points.get("overall_minimum")

    @property
    def family_minima(self) -> list[list[float]]:
        return self.critical_points.get("family_minima", [])

    @property
    def mode_participation(self) -> dict[str, Any]:
        return self.data.get("mode_participation", {})

    @property
    def member_length_modes(self) -> list[list[float]]:
        return self.mode_participation.get("member_lengths", [])

    @property
    def signature_minima_modes(self) -> list[list[float]]:
        return self.mode_participation.get("signature_minima", [])

    def signature_curve_dataframe(self):
        """Return the signature curve as a pandas DataFrame."""

        import pandas as pd

        return pd.DataFrame(
            self.signature_curve,
            columns=["length", "lowest_eigenvalue"],
        )

    def lowest_modes_dataframe(self):
        """Return lowest-mode participation as a pandas DataFrame."""

        import pandas as pd

        columns = self.mode_participation.get("table_columns", [])
        return pd.DataFrame(
            self.mode_participation.get("lowest_modes", []),
            columns=columns,
        )

    def participation_points_dataframe(self, key: str):
        """Return member-length or signature-minima participation as a DataFrame."""

        import pandas as pd

        columns = self.mode_participation.get("participation_point_columns", [])
        return pd.DataFrame(
            self.mode_participation.get(key, []),
            columns=columns,
        )
