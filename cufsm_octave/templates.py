"""Template builders for CUFSM Octave JSON inputs."""

from __future__ import annotations

from math import ceil, hypot
from pathlib import Path
from typing import Any, Iterable, Sequence

from .io import write_input
from .result import CufsmResult
from .runner import run_cufsm


Point = tuple[float, float]


def steel_material(
    *,
    material_id: int = 100,
    ex: float = 29500.0,
    ey: float = 29500.0,
    nu_x: float = 0.3,
    nu_y: float = 0.3,
    g: float = 11346.15,
) -> dict[str, float | int]:
    """Return an isotropic steel-like material record."""

    return {
        "id": material_id,
        "Ex": ex,
        "Ey": ey,
        "nu_x": nu_x,
        "nu_y": nu_y,
        "G": g,
    }


def generated_action_loading(
    *,
    fy: float,
    p_factor: float = 1.0,
    mxx_factor: float = 0.0,
    mzz_factor: float = 0.0,
    m11_factor: float = 0.0,
    m22_factor: float = 0.0,
    unsymmetric: bool = False,
    actions: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Return a generated loading block based on reference actions."""

    loading_actions = {
        "P_factor": p_factor,
        "Mxx_factor": mxx_factor,
        "Mzz_factor": mzz_factor,
        "M11_factor": m11_factor,
        "M22_factor": m22_factor,
    }
    if actions:
        loading_actions.update(actions)
    return {
        "type": "generated_from_actions",
        "fy": fy,
        "unsymmetric": unsymmetric,
        "actions": loading_actions,
    }


def stress_table_loading() -> dict[str, str]:
    """Return a loading block that uses stresses stored on the node table."""

    return {"type": "stress_table"}


def logspace_lengths(
    minimum: float,
    maximum: float,
    count: int,
    *,
    member_lengths: Sequence[float] = (),
) -> dict[str, Any]:
    """Return a logarithmically spaced length definition."""

    return {
        "type": "logspace",
        "min": minimum,
        "max": maximum,
        "count": count,
        "member_lengths": list(member_lengths),
    }


def linspace_lengths(
    minimum: float,
    maximum: float,
    count: int,
    *,
    member_lengths: Sequence[float] = (),
) -> dict[str, Any]:
    """Return a linearly spaced length definition."""

    return {
        "type": "linspace",
        "min": minimum,
        "max": maximum,
        "count": count,
        "member_lengths": list(member_lengths),
    }


def explicit_lengths(
    values: Sequence[float],
    *,
    member_lengths: Sequence[float] = (),
) -> dict[str, Any]:
    """Return an explicit length definition."""

    return {
        "type": "explicit",
        "values": list(values),
        "member_lengths": list(member_lengths),
    }


def signature_analysis(
    *,
    boundary_condition: str = "S-S",
    lengths: dict[str, Any] | None = None,
    longitudinal_terms: Sequence[int] = (1,),
    eigenmodes: int = 10,
    vectorized: bool = False,
    doubler: bool = False,
    cfsm: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a signature-curve analysis block."""

    return {
        "type": "signature_curve",
        "boundary_condition": boundary_condition,
        "lengths": lengths or logspace_lengths(1.0, 1000.0, 100),
        "longitudinal_terms": {"default": list(longitudinal_terms)},
        "eigenmodes": eigenmodes,
        "vectorized": vectorized,
        "mesh_refinement": {"doubler": doubler},
        "cfsm": cfsm or cfsm_defaults(),
    }


def cfsm_defaults() -> dict[str, Any]:
    """Return cFSM settings matching the current JSON example defaults."""

    return {
        "ospace": 1,
        "couple": 1,
        "orth": 2,
        "norm": 1,
        "local": [],
        "distortional": [],
        "global": [],
        "other": [],
    }


def model_from_centerline(
    points: Sequence[Point],
    *,
    thickness: float,
    material: dict[str, Any] | None = None,
    material_id: int = 100,
    max_segment_length: float | None = None,
    stress: float = 0.0,
) -> dict[str, Any]:
    """Build CUFSM model tables from an ordered open-section centerline."""

    if len(points) < 2:
        raise ValueError("At least two centerline points are required.")
    if thickness <= 0:
        raise ValueError("thickness must be positive.")

    material_record = material or steel_material(material_id=material_id)
    material_id = int(material_record["id"])
    refined_points = _subdivide_polyline(points, max_segment_length)

    nodes = [
        {
            "id": index,
            "x": x,
            "z": z,
            "dof_x": 1,
            "dof_z": 1,
            "dof_y": 1,
            "dof_rotation": 1,
            "stress": stress,
        }
        for index, (x, z) in enumerate(refined_points, start=1)
    ]
    elements = [
        {
            "id": index,
            "node_i": index,
            "node_j": index + 1,
            "thickness": thickness,
            "material_id": material_id,
        }
        for index in range(1, len(refined_points))
    ]
    return {
        "materials": [material_record],
        "nodes": nodes,
        "elements": elements,
        "springs": [],
        "constraints": [],
    }


def build_section_model(
    section_type: str,
    *,
    depth: float,
    thickness: float,
    flange: float | None = None,
    lip: float = 0.0,
    top_flange: float | None = None,
    bottom_flange: float | None = None,
    web_stiffener_depth: float | None = None,
    material: dict[str, Any] | None = None,
    material_id: int = 100,
    max_segment_length: float | None = None,
    stress: float = 0.0,
) -> dict[str, Any]:
    """Build a model for a named thin-walled section family."""

    points = section_centerline(
        section_type,
        depth=depth,
        flange=flange,
        lip=lip,
        top_flange=top_flange,
        bottom_flange=bottom_flange,
        web_stiffener_depth=web_stiffener_depth,
    )
    return model_from_centerline(
        points,
        thickness=thickness,
        material=material,
        material_id=material_id,
        max_segment_length=max_segment_length,
        stress=stress,
    )


def section_centerline(
    section_type: str,
    *,
    depth: float,
    flange: float | None = None,
    lip: float = 0.0,
    top_flange: float | None = None,
    bottom_flange: float | None = None,
    web_stiffener_depth: float | None = None,
) -> list[Point]:
    """Return ordered centerline points for a labeled section family."""

    section = section_type.lower().replace("_", "-")
    if depth <= 0:
        raise ValueError("depth must be positive.")
    if lip < 0:
        raise ValueError("lip must be non-negative.")

    flange_value = _resolve_flange(flange, top_flange, bottom_flange)
    top = top_flange if top_flange is not None else flange_value
    bottom = bottom_flange if bottom_flange is not None else flange_value
    if top <= 0 or bottom <= 0:
        raise ValueError("flange dimensions must be positive.")

    if section in {"unlipped-channel", "channel", "c"}:
        return [(bottom, 0.0), (0.0, 0.0), (0.0, depth), (top, depth)]

    if section in {"lipped-channel", "lipped-c"}:
        if lip <= 0:
            raise ValueError("lipped-channel requires lip > 0.")
        return [
            (bottom, lip),
            (bottom, 0.0),
            (0.0, 0.0),
            (0.0, depth),
            (top, depth),
            (top, depth - lip),
        ]

    if section in {"z", "z-section", "zed"}:
        return [(-bottom, 0.0), (0.0, 0.0), (0.0, depth), (top, depth)]

    if section in {"sigma", "sigma-section"}:
        if lip <= 0:
            raise ValueError("sigma-section requires lip > 0.")
        stiffener = _default_stiffener_depth(web_stiffener_depth, top, bottom)
        return [
            (bottom, lip),
            (bottom, 0.0),
            (0.0, 0.0),
            (0.0, 0.35 * depth),
            (stiffener, 0.45 * depth),
            (stiffener, 0.55 * depth),
            (0.0, 0.65 * depth),
            (0.0, depth),
            (top, depth),
            (top, depth - lip),
        ]

    if section in {"stiffened-web", "stiffened-web-channel"}:
        stiffener = _default_stiffener_depth(web_stiffener_depth, top, bottom)
        return [
            (bottom, 0.0),
            (0.0, 0.0),
            (0.0, 0.35 * depth),
            (stiffener, 0.5 * depth),
            (0.0, 0.65 * depth),
            (0.0, depth),
            (top, depth),
        ]

    valid = [
        "unlipped-channel",
        "lipped-channel",
        "z-section",
        "sigma-section",
        "stiffened-web-channel",
    ]
    raise ValueError(f"Unsupported section_type {section_type!r}. Use one of {valid}.")


def build_section_input(
    section_type: str,
    *,
    depth: float,
    thickness: float,
    flange: float | None = None,
    lip: float = 0.0,
    top_flange: float | None = None,
    bottom_flange: float | None = None,
    web_stiffener_depth: float | None = None,
    max_segment_length: float | None = None,
    material: dict[str, Any] | None = None,
    fy: float = 50.0,
    loading: dict[str, Any] | None = None,
    analysis: dict[str, Any] | None = None,
    output_path: str | None = None,
    text_output_path: str | None = None,
    units: str = "kip_in",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a full CUFSM JSON input for a named section template."""

    model = build_section_model(
        section_type,
        depth=depth,
        thickness=thickness,
        flange=flange,
        lip=lip,
        top_flange=top_flange,
        bottom_flange=bottom_flange,
        web_stiffener_depth=web_stiffener_depth,
        material=material,
        max_segment_length=max_segment_length,
    )
    output = {}
    if output_path:
        output["path"] = output_path
    if text_output_path:
        output["text_path"] = text_output_path

    return {
        "version": "1.0",
        "metadata": metadata
        or {
            "name": f"{section_type}-template",
            "description": f"Generated {section_type} section input.",
        },
        "units": {"system": units},
        "model": model,
        "loading": loading or generated_action_loading(fy=fy),
        "analysis": analysis or signature_analysis(),
        "output": output,
    }


def write_section_input(
    path: str | Path,
    section_type: str,
    **kwargs: Any,
) -> Path:
    """Build and write a named section input JSON file."""

    data = build_section_input(section_type, **kwargs)
    return write_input(data, path)


def run_section_input(
    path: str | Path,
    section_type: str,
    **kwargs: Any,
) -> CufsmResult:
    """Build a named section input JSON file, run Octave, and return results."""

    input_path = write_section_input(path, section_type, **kwargs)
    return run_cufsm(input_path)


def _subdivide_polyline(
    points: Sequence[Point],
    max_segment_length: float | None,
) -> list[Point]:
    if max_segment_length is not None and max_segment_length <= 0:
        raise ValueError("max_segment_length must be positive when provided.")

    refined: list[Point] = []
    for start, end in zip(points[:-1], points[1:]):
        x1, z1 = start
        x2, z2 = end
        if not refined:
            refined.append((float(x1), float(z1)))
        length = hypot(x2 - x1, z2 - z1)
        divisions = 1
        if max_segment_length:
            divisions = max(1, int(ceil(length / max_segment_length)))
        for step in range(1, divisions + 1):
            ratio = step / divisions
            refined.append((x1 + (x2 - x1) * ratio, z1 + (z2 - z1) * ratio))
    return _deduplicate_consecutive(refined)


def _deduplicate_consecutive(points: Iterable[Point]) -> list[Point]:
    cleaned: list[Point] = []
    for point in points:
        if not cleaned or point != cleaned[-1]:
            cleaned.append(point)
    return cleaned


def _resolve_flange(
    flange: float | None,
    top_flange: float | None,
    bottom_flange: float | None,
) -> float:
    if flange is not None:
        return flange
    if top_flange is not None:
        return top_flange
    if bottom_flange is not None:
        return bottom_flange
    raise ValueError("Provide flange, top_flange, or bottom_flange.")


def _default_stiffener_depth(
    web_stiffener_depth: float | None,
    top_flange: float,
    bottom_flange: float,
) -> float:
    if web_stiffener_depth is not None:
        if web_stiffener_depth <= 0:
            raise ValueError("web_stiffener_depth must be positive.")
        return web_stiffener_depth
    return 0.25 * min(top_flange, bottom_flange)
