"""JSON input/output helpers for CUFSM Octave workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "schema" / "input-v1.schema.json"


class InputValidationError(ValueError):
    """Raised when a CUFSM JSON input fails lightweight Python validation."""


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from *path*."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise InputValidationError("CUFSM JSON files must contain a top-level object.")
    return data


def load_input(path: str | Path, *, validate: bool = False) -> dict[str, Any]:
    """Load a CUFSM input JSON file, optionally validating it."""

    data = load_json(path)
    if validate:
        validate_input(data)
    return data


def write_input(data: dict[str, Any], path: str | Path, *, indent: int = 2) -> Path:
    """Write a CUFSM input object to *path* and return the resolved path."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent)
        handle.write("\n")
    return output_path.resolve()


def validate_input(
    data: dict[str, Any],
    *,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> None:
    """Validate a CUFSM input object.

    If ``jsonschema`` is installed, the repository schema is used. Otherwise a
    small set of structural checks catches the most common interface mistakes.
    """

    try:
        import jsonschema
    except ImportError:
        _validate_input_lightweight(data)
        return

    schema = load_json(schema_path)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = path or "<root>"
        raise InputValidationError(f"{location}: {exc.message}") from exc

    _validate_input_lightweight(data)


def _validate_input_lightweight(data: dict[str, Any]) -> None:
    _require(data, "version", "top-level input")
    _require(data, "model", "top-level input")
    _require(data, "analysis", "top-level input")

    model = _require_mapping(data["model"], "model")
    materials = _require_list(model, "materials", "model")
    nodes = _require_list(model, "nodes", "model")
    elements = _require_list(model, "elements", "model")

    material_ids = _unique_ids(materials, "model.materials")
    node_ids = _unique_ids(nodes, "model.nodes")
    _unique_ids(elements, "model.elements")

    for element in elements:
        element_id = element.get("id", "<missing>")
        if element.get("node_i") not in node_ids:
            raise InputValidationError(
                f"model.elements id {element_id} references missing node_i."
            )
        if element.get("node_j") not in node_ids:
            raise InputValidationError(
                f"model.elements id {element_id} references missing node_j."
            )
        if element.get("material_id") not in material_ids:
            raise InputValidationError(
                f"model.elements id {element_id} references missing material_id."
            )
        if element.get("thickness", 0) <= 0:
            raise InputValidationError(
                f"model.elements id {element_id} has non-positive thickness."
            )

    analysis = _require_mapping(data["analysis"], "analysis")
    boundary_condition = analysis.get("boundary_condition")
    valid_boundary_conditions = {"S-S", "C-C", "S-C", "C-F", "C-G"}
    if boundary_condition not in valid_boundary_conditions:
        raise InputValidationError(
            f"analysis.boundary_condition must be one of "
            f"{sorted(valid_boundary_conditions)}."
        )

    lengths = _require_mapping(analysis.get("lengths"), "analysis.lengths")
    length_type = lengths.get("type")
    if length_type in {"logspace", "linspace"}:
        if lengths.get("min", 0) <= 0 or lengths.get("max", 0) <= 0:
            raise InputValidationError("analysis.lengths min and max must be positive.")
        if lengths.get("count", 0) < 1:
            raise InputValidationError("analysis.lengths count must be at least 1.")
    elif length_type == "explicit":
        values = _require_list(lengths, "values", "analysis.lengths")
        if any(value <= 0 for value in values):
            raise InputValidationError("analysis.lengths.values must be positive.")
    else:
        raise InputValidationError(
            "analysis.lengths.type must be logspace, linspace, or explicit."
        )

    loading = data.get("loading", {"type": "stress_table"})
    loading_type = loading.get("type") if isinstance(loading, dict) else None
    if loading_type not in {"stress_table", "generated_from_actions"}:
        raise InputValidationError(
            "loading.type must be stress_table or generated_from_actions."
        )


def _require(mapping: dict[str, Any], key: str, location: str) -> Any:
    if key not in mapping:
        raise InputValidationError(f"{location} is missing required field {key}.")
    return mapping[key]


def _require_mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputValidationError(f"{location} must be an object.")
    return value


def _require_list(mapping: dict[str, Any], key: str, location: str) -> list[Any]:
    values = mapping.get(key)
    if not isinstance(values, list) or not values:
        raise InputValidationError(f"{location}.{key} must be a non-empty array.")
    return values


def _unique_ids(items: list[Any], location: str) -> set[Any]:
    ids: list[Any] = []
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            raise InputValidationError(f"{location} entries must contain id.")
        ids.append(item["id"])
    unique_ids = set(ids)
    if len(unique_ids) != len(ids):
        raise InputValidationError(f"{location} contains duplicate ids.")
    return unique_ids
