"""Remote MCP wrapper for the existing cufsm-octave Python interface."""

from __future__ import annotations

from copy import deepcopy
import json
import multiprocessing
import os
import queue
import signal
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp_types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, model_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cufsm_octave import (  # noqa: E402
    CufsmResult,
    build_section_model,
    cfsm_defaults,
    explicit_lengths,
    linspace_lengths,
    logspace_lengths,
    run_cufsm,
    write_input,
)


BoundaryCondition = Literal["S-S", "C-C", "S-C", "C-F", "C-G"]
SectionType = Literal[
    "unlipped-channel",
    "lipped-channel",
    "z-section",
    "sigma-section",
    "stiffened-web-channel",
]

CANONICAL_SCHEMA_PATH = REPO_ROOT / "schema" / "input-v1.schema.json"
with CANONICAL_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
    CANONICAL_SCHEMA = json.load(schema_file)


def _canonical_node(*path: str) -> dict[str, Any]:
    node: Any = CANONICAL_SCHEMA
    for part in path:
        node = node[part]
    if not isinstance(node, dict):
        raise RuntimeError(f"Canonical schema path is not an object: {'.'.join(path)}")
    return node


def _canonical_default(*path: str) -> Any:
    node = _canonical_node(*path)
    if "default" not in node:
        raise RuntimeError(f"Canonical schema path has no default: {'.'.join(path)}")
    return deepcopy(node["default"])


def _canonical_keyword_values(keyword: str) -> tuple[Any, ...]:
    values: list[Any] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if keyword in value:
                values.append(deepcopy(value[keyword]))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(CANONICAL_SCHEMA)
    return tuple(values)


# Every value below is read from an explicit `default` keyword in the
# canonical repository schema. Parametric geometry, material, and reference
# loading have no schema defaults; the MCP-convenience defaults below are not
# canonical schema values, so a caller can still override every one of them.
_DEFAULT_UNIT_SYSTEM = "mm_MPa"
_DEFAULT_SECTION_TYPE: SectionType = "lipped-channel"
_DEFAULT_DEPTH = 195.0
_DEFAULT_FLANGE = 45.0
_DEFAULT_LIP = 15.0
_DEFAULT_THICKNESS = 1.5
_DEFAULT_MATERIAL_ID = 100
_DEFAULT_EX = 200000.0
_DEFAULT_EY = 200000.0
_DEFAULT_NU_X = 0.3
_DEFAULT_NU_Y = 0.3
_DEFAULT_G = _DEFAULT_EX / (2 * (1 + _DEFAULT_NU_X))
_DEFAULT_FY = 350.0
_DEFAULT_P_FACTOR = 1.0
_DEFAULT_BOUNDARY_CONDITION: BoundaryCondition = "S-S"
_DEFAULT_LENGTHS_TYPE = "logspace"
_DEFAULT_LENGTHS_MIN = 10.0
_DEFAULT_LENGTHS_MAX = 10000.0
_DEFAULT_LENGTHS_COUNT = 60

_DEFAULT_SPRINGS = _canonical_default("properties", "model", "properties", "springs")
_DEFAULT_CONSTRAINTS = _canonical_default("properties", "model", "properties", "constraints")
_DEFAULT_EIGENMODES = _canonical_default("properties", "analysis", "properties", "eigenmodes")
_DEFAULT_VECTORIZED = _canonical_default("properties", "analysis", "properties", "vectorized")
_DEFAULT_DOUBLER = _canonical_default(
    "properties", "analysis", "properties", "mesh_refinement", "properties", "doubler"
)
_DEFAULT_UNSYMMETRIC = _canonical_default(
    "$defs", "generatedActionLoading", "properties", "unsymmetric"
)
_DEFAULT_MEMBER_LENGTHS = _canonical_default("$defs", "memberLengths")
_CANONICAL_CONST_VALUES = _canonical_keyword_values("const")

FAMILY_NAMES = {0: "unknown", 1: "global", 2: "distortional", 3: "local", 4: "other"}
READ_ONLY_TOOL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


class StudyMetadata(BaseModel):
    """Study fields corresponding to ``metadata`` in the JSON/web interface."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        description="Optional study name; the section builder supplies its native name when omitted.",
    )
    description: str | None = Field(
        default=None,
        description="Optional study description; the section builder supplies it when omitted.",
    )


class UnitDefinition(BaseModel):
    """Unit convention corresponding to ``units.system``."""

    model_config = ConfigDict(extra="forbid")

    system: str | None = Field(
        default=_DEFAULT_UNIT_SYSTEM,
        description=(
            "Unit convention for dimensional values. The canonical schema "
            "defines no default; this MCP layer defaults to mm_MPa to match "
            "its own geometry/material/loading defaults. Webapp choices also "
            "include in_ksi, mm_N, m_N, and in_lb, with custom values permitted."
        ),
    )


class MaterialDefinition(BaseModel):
    """One material row using the canonical JSON/web material field names."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(
        default=_DEFAULT_MATERIAL_ID,
        description="Material identifier used by generated elements.",
    )
    Ex: float = Field(
        default=_DEFAULT_EX,
        allow_inf_nan=False,
        description="Longitudinal elastic modulus, in the selected unit system.",
    )
    Ey: float = Field(
        default=_DEFAULT_EY,
        allow_inf_nan=False,
        description="Transverse elastic modulus, in the selected unit system.",
    )
    nu_x: float = Field(
        default=_DEFAULT_NU_X,
        allow_inf_nan=False,
        description="Poisson ratio nu_x.",
    )
    nu_y: float = Field(
        default=_DEFAULT_NU_Y,
        allow_inf_nan=False,
        description="Poisson ratio nu_y.",
    )
    G: float = Field(
        default=_DEFAULT_G,
        allow_inf_nan=False,
        description="Shear modulus, in the selected unit system.",
    )


class SectionGeometry(BaseModel):
    """Parametric section-generator fields shown in the webapp Geometry tab."""

    model_config = ConfigDict(extra="forbid")

    section_type: SectionType = Field(
        default=_DEFAULT_SECTION_TYPE,
        description="Section family supported by the public template builder.",
    )
    depth: float = Field(
        default=_DEFAULT_DEPTH,
        gt=0,
        allow_inf_nan=False,
        description="Web depth in the length unit identified by units.system.",
    )
    flange: float = Field(
        default=_DEFAULT_FLANGE,
        gt=0,
        allow_inf_nan=False,
        description="Equal top and bottom flange width in the selected length unit.",
    )
    lip: float = Field(
        default=_DEFAULT_LIP,
        ge=0,
        allow_inf_nan=False,
        description="Lip length; required for lipped-channel and sigma-section.",
    )
    thickness: float = Field(
        default=_DEFAULT_THICKNESS,
        gt=0,
        allow_inf_nan=False,
        description="Section thickness in the selected length unit.",
    )
    max_segment_length: float | None = Field(
        default=None,
        gt=0,
        allow_inf_nan=False,
        description=(
            "Optional maximum centerline segment length. Omission preserves "
            "build_section_model's native unrefined-centerline behavior."
        ),
    )

    @model_validator(mode="after")
    def validate_lip(self) -> "SectionGeometry":
        if self.section_type in {"lipped-channel", "sigma-section"} and self.lip <= 0:
            raise ValueError(f"{self.section_type} requires lip > 0.")
        return self


class SectionDefinition(BaseModel):
    """Webapp-style parametric section plus canonical study/material fields."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = "1.0"
    metadata: StudyMetadata | None = None
    units: UnitDefinition | None = Field(default_factory=UnitDefinition)
    geometry: SectionGeometry = Field(default_factory=SectionGeometry)
    material: MaterialDefinition = Field(default_factory=MaterialDefinition)


class GeneratedActions(BaseModel):
    """Canonical ``loading.actions`` fields from the schema and webapp."""

    model_config = ConfigDict(extra="forbid")

    P: float | None = Field(default=None, allow_inf_nan=False, description="Absolute axial action.")
    Mxx: float | None = Field(default=None, allow_inf_nan=False, description="Absolute moment Mxx.")
    Mzz: float | None = Field(default=None, allow_inf_nan=False, description="Absolute moment Mzz.")
    M11: float | None = Field(default=None, allow_inf_nan=False, description="Absolute principal moment M11.")
    M22: float | None = Field(default=None, allow_inf_nan=False, description="Absolute principal moment M22.")
    P_factor: float | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Factor on the reference axial yield action.",
    )
    Mxx_factor: float | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Factor on the reference Mxx yield action.",
    )
    Mzz_factor: float | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Factor on the reference Mzz yield action.",
    )
    M11_factor: float | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Factor on the reference M11 yield action.",
    )
    M22_factor: float | None = Field(
        default=None,
        allow_inf_nan=False,
        description="Factor on the reference M22 yield action.",
    )


class LoadingDefinition(BaseModel):
    """Generated-action loading used by the parametric section workflow."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["generated_from_actions"] = "generated_from_actions"
    fy: float = Field(
        default=_DEFAULT_FY,
        gt=0,
        allow_inf_nan=False,
        description="Reference yield stress in the selected unit system.",
    )
    unsymmetric: bool = bool(_DEFAULT_UNSYMMETRIC)
    actions: GeneratedActions = Field(
        default_factory=lambda: GeneratedActions(P_factor=_DEFAULT_P_FACTOR)
    )


class GeneratedLengths(BaseModel):
    """Canonical logarithmic or linear signature-curve length sweep."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["logspace", "linspace"]
    min: float = Field(gt=0, allow_inf_nan=False)
    max: float = Field(gt=0, allow_inf_nan=False)
    count: int = Field(ge=1)
    member_lengths: list[Annotated[float, Field(gt=0, allow_inf_nan=False)]] = Field(
        default_factory=lambda: deepcopy(_DEFAULT_MEMBER_LENGTHS),
        json_schema_extra={"default": deepcopy(_DEFAULT_MEMBER_LENGTHS)},
    )


class ExplicitLengths(BaseModel):
    """Canonical explicit signature-curve length list."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["explicit"]
    values: list[Annotated[float, Field(gt=0, allow_inf_nan=False)]] = Field(min_length=1)
    member_lengths: list[Annotated[float, Field(gt=0, allow_inf_nan=False)]] = Field(
        default_factory=lambda: deepcopy(_DEFAULT_MEMBER_LENGTHS),
        json_schema_extra={"default": deepcopy(_DEFAULT_MEMBER_LENGTHS)},
    )


LengthDefinition = Annotated[GeneratedLengths | ExplicitLengths, Field(discriminator="type")]


class LongitudinalTermSet(BaseModel):
    """Longitudinal terms for one length in ``per_length`` order."""

    model_config = ConfigDict(extra="forbid")

    terms: list[Annotated[int, Field(ge=1)]] = Field(min_length=1)


class LongitudinalTerms(BaseModel):
    """Canonical ``analysis.longitudinal_terms`` structure."""

    model_config = ConfigDict(extra="forbid")

    default: list[Annotated[int, Field(ge=1)]] | None = Field(
        default=None,
        min_length=1,
    )
    per_length: list[LongitudinalTermSet] | None = None


class CfsmDefinition(BaseModel):
    """cFSM settings and enums shown in the webapp cFSM tab."""

    model_config = ConfigDict(extra="forbid")

    ospace: Literal[1, 2, 3, 4] | None = None
    couple: Literal[1, 2] | None = None
    orth: Literal[1, 2, 3] | None = None
    norm: Literal[0, 1, 2, 3] | None = None
    local: list[Annotated[int, Field(ge=0)]] | None = None
    distortional: list[Annotated[int, Field(ge=0)]] | None = None
    global_: list[Annotated[int, Field(ge=0)]] | None = Field(
        default=None,
        alias="global",
    )
    other: list[Annotated[int, Field(ge=0)]] | None = None


class MeshRefinement(BaseModel):
    """Canonical ``analysis.mesh_refinement`` structure."""

    model_config = ConfigDict(extra="forbid")

    doubler: bool = bool(_DEFAULT_DOUBLER)


class SignatureCurveAnalysis(BaseModel):
    """Signature-curve settings matching the JSON schema and webapp controls."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["signature_curve"] = "signature_curve"
    boundary_condition: BoundaryCondition = _DEFAULT_BOUNDARY_CONDITION
    lengths: LengthDefinition = Field(
        default_factory=lambda: GeneratedLengths(
            type=_DEFAULT_LENGTHS_TYPE,
            min=_DEFAULT_LENGTHS_MIN,
            max=_DEFAULT_LENGTHS_MAX,
            count=_DEFAULT_LENGTHS_COUNT,
        )
    )
    longitudinal_terms: LongitudinalTerms | None = None
    eigenmodes: int = Field(default=int(_DEFAULT_EIGENMODES), ge=1)
    vectorized: bool = bool(_DEFAULT_VECTORIZED)
    mesh_refinement: MeshRefinement | None = None
    cfsm: CfsmDefinition | None = None

    @model_validator(mode="before")
    @classmethod
    def _fill_partial_lengths(cls, data: Any) -> Any:
        """Repair a ``lengths`` object missing its discriminator/range.

        A caller (or an LLM tool-caller) may supply ``lengths`` with only the
        ``member_lengths`` leaf populated, omitting ``type``/``min``/``max``/
        ``count`` because those have no leaf-level default to copy from. Fill
        the missing pieces with the MCP-convenience length sweep instead of
        failing the discriminated union with a missing-tag error.
        """

        if not isinstance(data, dict):
            return data
        lengths = data.get("lengths")
        if isinstance(lengths, dict) and "type" not in lengths:
            data = dict(data)
            data["lengths"] = {
                "type": _DEFAULT_LENGTHS_TYPE,
                "min": _DEFAULT_LENGTHS_MIN,
                "max": _DEFAULT_LENGTHS_MAX,
                "count": _DEFAULT_LENGTHS_COUNT,
                **lengths,
            }
        return data


server = MCPServer(
    "cufsm-octave",
    instructions=(
        "Run elastic buckling signature-curve analyses with the existing "
        "cufsm-octave GNU Octave solver. Results are dimensionless load factors; "
        "interpret them with the supplied reference loading and units."
    ),
)


@server.tool(annotations=READ_ONLY_TOOL)
def analyze_lipped_channel(
    depth: Annotated[float, Field(gt=0, allow_inf_nan=False)] = _DEFAULT_DEPTH,
    flange: Annotated[float, Field(gt=0, allow_inf_nan=False)] = _DEFAULT_FLANGE,
    lip: Annotated[float, Field(gt=0, allow_inf_nan=False)] = _DEFAULT_LIP,
    thickness: Annotated[float, Field(gt=0, allow_inf_nan=False)] = _DEFAULT_THICKNESS,
    material: MaterialDefinition | None = None,
    analysis: SignatureCurveAnalysis | None = None,
    max_segment_length: Annotated[float | None, Field(gt=0, allow_inf_nan=False)] = None,
    metadata: StudyMetadata | None = None,
    units: UnitDefinition | None = None,
    loading: LoadingDefinition | None = None,
) -> dict[str, Any]:
    """Analyze a parametric lipped channel using the webapp's geometry fields.

    Geometry, material, and analysis fall back to MCP-convenience defaults (a
    typical mm/MPa cold-formed-steel lipped channel and an S-S signature-curve
    sweep) when omitted; these are not canonical schema defaults, so any of
    them can still be overridden. This is the only tool that runs with no
    arguments at all.
    """

    return _tool_call(
        lambda: _execute_section(
            SectionDefinition(
                version="1.0",
                metadata=metadata,
                units=units if units is not None else UnitDefinition(),
                geometry=SectionGeometry(
                    section_type="lipped-channel",
                    depth=depth,
                    flange=flange,
                    lip=lip,
                    thickness=thickness,
                    max_segment_length=max_segment_length,
                ),
                material=material if material is not None else MaterialDefinition(),
            ),
            loading,
            analysis if analysis is not None else SignatureCurveAnalysis(),
        )
    )


@server.tool(annotations=READ_ONLY_TOOL)
def analyze_section(
    section: SectionDefinition | None = None,
    analysis: SignatureCurveAnalysis | None = None,
    loading: LoadingDefinition | None = None,
) -> dict[str, Any]:
    """Analyze a webapp-style parametric section with the existing CUFSM solver.

    ``section.geometry`` is converted by the repository's public
    ``build_section_model`` template; callers do not provide node/element
    matrices. Loading and analysis map directly to the canonical JSON blocks.
    Omitted ``section``/``analysis`` fields (and their nested
    ``geometry``/``material``/``boundary_condition``/``lengths`` fields) fall
    back to MCP-convenience defaults (a typical mm/MPa cold-formed-steel
    lipped channel and an S-S signature-curve sweep); these are not canonical
    schema defaults, so any of them can still be overridden.
    """

    return _tool_call(
        lambda: _execute_section(
            section if section is not None else SectionDefinition(),
            loading,
            analysis if analysis is not None else SignatureCurveAnalysis(),
        )
    )


@server.tool(annotations=READ_ONLY_TOOL)
def signature_curve(
    section: SectionDefinition | None = None,
    analysis: SignatureCurveAnalysis | None = None,
    loading: LoadingDefinition | None = None,
) -> dict[str, Any]:
    """Calculate a signature curve from the repo/webapp section definition.

    This follows the checked-in workflow: parametric section template to JSON,
    ``octave-cli``/``cufsm_json.m``, then structured CUFSM results. It does not
    accept raw matrices, centerline arrays, or executable code. Omitted
    ``section``/``analysis`` fields (and their nested
    ``geometry``/``material``/``boundary_condition``/``lengths`` fields) fall
    back to MCP-convenience defaults (a typical mm/MPa cold-formed-steel
    lipped channel and an S-S signature-curve sweep); these are not canonical
    schema defaults, so any of them can still be overridden.
    """

    return _tool_call(
        lambda: _execute_section(
            section if section is not None else SectionDefinition(),
            loading,
            analysis if analysis is not None else SignatureCurveAnalysis(),
        )
    )


def _tool_call(operation: Any) -> dict[str, Any]:
    try:
        return operation()
    except ToolError:
        raise
    except (TypeError, ValueError) as exc:
        raise ToolError(str(exc)) from None
    except Exception:
        raise ToolError("CUFSM analysis failed unexpectedly; no result was produced.") from None


def _execute_section(
    section: SectionDefinition,
    loading: LoadingDefinition | None,
    analysis: SignatureCurveAnalysis,
) -> dict[str, Any]:
    geometry = section.geometry
    lip = geometry.lip if geometry.section_type in {"lipped-channel", "sigma-section"} else 0.0
    material_record = section.material.model_dump()
    loading_record = _loading_record(loading) if loading is not None else None
    analysis_record = _analysis_record(analysis)
    metadata = section.metadata.model_dump(exclude_none=True) if section.metadata else None

    model = build_section_model(
        geometry.section_type,
        depth=geometry.depth,
        flange=geometry.flange,
        lip=lip,
        thickness=geometry.thickness,
        max_segment_length=geometry.max_segment_length,
        material=material_record,
    )
    model["springs"] = deepcopy(_DEFAULT_SPRINGS)
    model["constraints"] = deepcopy(_DEFAULT_CONSTRAINTS)
    data: dict[str, Any] = {
        "version": section.version,
        "model": model,
        "analysis": analysis_record,
    }
    if metadata is not None:
        data["metadata"] = metadata
    if section.units is not None:
        units_record = section.units.model_dump(exclude_none=True)
        if units_record:
            data["units"] = units_record
    if loading_record is not None:
        data["loading"] = loading_record

    summary = {
        "version": section.version,
        "metadata": metadata,
        "units": data.get("units"),
        "geometry": {
            "section_type": geometry.section_type,
            "depth": geometry.depth,
            "flange": geometry.flange,
            "lip": lip,
            "thickness": geometry.thickness,
            "max_segment_length": geometry.max_segment_length,
        },
        "material": material_record,
        "loading": loading_record,
        "analysis": analysis_record,
        "generated_model": {
            "material_count": len(model.get("materials", [])),
            "node_count": len(model.get("nodes", [])),
            "element_count": len(model.get("elements", [])),
            "spring_count": len(model.get("springs", [])),
            "constraint_count": len(model.get("constraints", [])),
        },
    }
    return _run_isolated(data, summary)


def _loading_record(loading: LoadingDefinition) -> dict[str, Any]:
    return {
        "type": loading.type,
        "fy": loading.fy,
        "unsymmetric": loading.unsymmetric,
        "actions": loading.actions.model_dump(exclude_none=True),
    }


def _analysis_record(analysis: SignatureCurveAnalysis) -> dict[str, Any]:
    length_options = analysis.lengths
    if isinstance(length_options, ExplicitLengths):
        lengths = explicit_lengths(
            length_options.values,
            member_lengths=length_options.member_lengths,
        )
    else:
        length_builder = logspace_lengths if length_options.type == "logspace" else linspace_lengths
        lengths = length_builder(
            length_options.min,
            length_options.max,
            length_options.count,
            member_lengths=length_options.member_lengths,
        )

    record: dict[str, Any] = {
        "type": analysis.type,
        "boundary_condition": analysis.boundary_condition,
        "lengths": lengths,
        "eigenmodes": analysis.eigenmodes,
        "vectorized": analysis.vectorized,
        "mesh_refinement": {
            "doubler": (
                analysis.mesh_refinement.doubler
                if analysis.mesh_refinement is not None
                else bool(_DEFAULT_DOUBLER)
            )
        },
    }
    if analysis.longitudinal_terms is not None:
        terms = analysis.longitudinal_terms.model_dump(exclude_none=True)
        if terms:
            record["longitudinal_terms"] = terms
    else:
        record["longitudinal_terms"] = {"default": [1]}

    if analysis.cfsm is not None:
        cfsm_record = analysis.cfsm.model_dump(by_alias=True, exclude_none=True)
        if cfsm_record:
            record["cfsm"] = cfsm_record
    else:
        record["cfsm"] = cfsm_defaults()

    return record


def _run_isolated(data: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    timeout_seconds = _calculation_timeout()
    with tempfile.TemporaryDirectory(prefix="cufsm-") as temporary_directory:
        job_directory = Path(temporary_directory)
        _create_read_only_code_view(job_directory)
        input_path = job_directory / "input.json"
        result_path = job_directory / "result.json"
        data["output"] = {"path": str(result_path)}
        write_input(data, input_path)

        context = multiprocessing.get_context("spawn")
        messages = context.Queue()
        process = context.Process(
            target=_run_cufsm_worker,
            args=(str(input_path), str(job_directory), messages),
            daemon=False,
        )
        process.start()
        group_isolated = False
        try:
            ready = messages.get(timeout=10)
            if ready.get("kind") != "ready":
                _stop_worker(process, group_isolated=False)
                messages.close()
                raise ToolError("The isolated CUFSM worker could not start.")
            group_isolated = bool(ready.get("group_isolated"))
        except queue.Empty:
            _stop_worker(process, group_isolated=False)
            messages.close()
            raise ToolError("The isolated CUFSM worker could not start.") from None

        process.join(timeout_seconds)
        if process.is_alive():
            _stop_worker(process, group_isolated=group_isolated)
            messages.close()
            raise ToolError(f"CUFSM calculation exceeded the {timeout_seconds:g} second timeout.")

        try:
            outcome = messages.get(timeout=2)
        except queue.Empty:
            raise ToolError("CUFSM ended without reporting a result.") from None
        finally:
            messages.close()

        if outcome.get("kind") != "ok":
            raise ToolError(outcome.get("message", "CUFSM calculation failed."))
        if not result_path.is_file():
            raise ToolError("CUFSM completed without creating its JSON result.")

        result = CufsmResult.from_file(result_path)
        return _format_result(result, summary)


def _create_read_only_code_view(job_directory: Path) -> None:
    for name in ("cufsm_json.m", "analysis", "cutwp", "helpers"):
        source = REPO_ROOT / name
        if not source.exists():
            raise ToolError(f"Required cufsm-octave component is missing: {name}.")
        (job_directory / name).symlink_to(source, target_is_directory=source.is_dir())


def _run_cufsm_worker(input_path: str, job_directory: str, messages: Any) -> None:
    group_isolated = False
    if hasattr(os, "setsid"):
        try:
            os.setsid()
            group_isolated = True
        except OSError:
            pass
    messages.put({"kind": "ready", "group_isolated": group_isolated})
    try:
        run_cufsm(input_path, repo_root=job_directory)
    except FileNotFoundError:
        messages.put(
            {
                "kind": "error",
                "message": "octave-cli is unavailable or CUFSM did not create its expected output.",
            }
        )
    except Exception as exc:
        messages.put({"kind": "error", "message": _safe_worker_error(exc)})
    else:
        messages.put({"kind": "ok"})


def _stop_worker(process: multiprocessing.Process, *, group_isolated: bool) -> None:
    if not process.is_alive():
        return
    if group_isolated and process.pid is not None and hasattr(os, "killpg"):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    else:
        process.terminate()
    process.join(3)
    if process.is_alive():
        if group_isolated and process.pid is not None and hasattr(os, "killpg"):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.join(2)


def _safe_worker_error(exc: Exception) -> str:
    message = str(exc)
    error_lines = [line.strip() for line in message.splitlines() if line.strip().lower().startswith("error:")]
    if error_lines:
        detail = error_lines[-1].removeprefix("error:").strip()
        return f"GNU Octave/CUFSM rejected the analysis: {detail[:600]}"
    if isinstance(exc, ValueError):
        return message[:600]
    return "GNU Octave/CUFSM calculation failed; check the section, material, loading, and analysis inputs."


def _format_result(result: CufsmResult, summary: dict[str, Any]) -> dict[str, Any]:
    data = result.data
    critical_points = data.get("critical_points", {})
    overall = _classified_point(critical_points.get("overall_minimum_classified", []))
    curve_rows = _table(data.get("mode_participation", {}).get("lowest_modes", []), 7)
    if not curve_rows:
        curve_rows = _table(data.get("signature_curve", []), 2)
    curve = [_curve_point(row) for row in curve_rows]

    family_minima: dict[str, dict[str, Any] | None] = {
        "local": None,
        "distortional": None,
        "global": None,
        "other": None,
    }
    for row in _table(critical_points.get("family_minima", []), 8):
        if len(row) >= 8:
            family_name = FAMILY_NAMES.get(int(row[0]), "unknown")
            family_minima[family_name] = _classified_point(
                [row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[0]]
            )

    warnings: list[str] = []
    for family in ("local", "distortional", "global"):
        if family_minima[family] is None:
            warnings.append(f"No interior {family} minimum was detected in the analyzed length range.")
    if overall and curve and overall["length_index"] in (1, len(curve)):
        warnings.append("The overall minimum lies at an analyzed length-range endpoint.")

    participation = data.get("mode_participation", {})
    return {
        "status": "ok",
        "solver": "cufsm-octave via GNU Octave",
        "model_summary": summary,
        "analysis_settings": data.get("analysis_settings", {}),
        "section_properties": data.get("section_properties", {}),
        "critical": {
            "overall_minimum": overall,
            "critical_mode": overall["dominant_family"] if overall else "unknown",
            "family_minima": family_minima,
            "detected_local_minima": [
                _classified_point(row)
                for row in _table(critical_points.get("local_minima_classified", []), 8)
            ],
        },
        "signature_curve": {
            "columns": [
                "length",
                "load_factor",
                "global_percent",
                "distortional_percent",
                "local_percent",
                "other_percent",
                "dominant_family",
            ],
            "point_count": len(curve),
            "lengths": [point["length"] for point in curve],
            "load_factors": [point["load_factor"] for point in curve],
            "points": curve,
        },
        "member_length_modes": [
            _participation_point(row)
            for row in _table(participation.get("member_lengths", []), 10)
        ],
        "signature_minimum_modes": [
            _participation_point(row)
            for row in _table(participation.get("signature_minima", []), 10)
        ],
        "warnings": warnings,
        "errors": [],
    }


def _table(value: Any, width: int) -> list[list[Any]]:
    """Normalize Octave JSON tables, including its flattened one-row form."""
    if not isinstance(value, list) or not value:
        return []
    if all(isinstance(row, list) for row in value):
        return [row for row in value if len(row) >= width]
    if len(value) >= width:
        return [value]
    return []


def _classified_point(row: list[Any]) -> dict[str, Any] | None:
    if len(row) < 8:
        return None
    family_id = int(row[7])
    return {
        "length": row[0],
        "load_factor": row[1],
        "length_index": int(row[2]),
        "participation_percent": {
            "global": row[3],
            "distortional": row[4],
            "local": row[5],
            "other": row[6],
        },
        "dominant_family": FAMILY_NAMES.get(family_id, "unknown"),
    }


def _curve_point(row: list[Any]) -> dict[str, Any]:
    family_id = int(row[6]) if len(row) >= 7 else 0
    return {
        "length": row[0],
        "load_factor": row[1],
        "global_percent": row[2] if len(row) >= 7 else None,
        "distortional_percent": row[3] if len(row) >= 7 else None,
        "local_percent": row[4] if len(row) >= 7 else None,
        "other_percent": row[5] if len(row) >= 7 else None,
        "dominant_family": FAMILY_NAMES.get(family_id, "unknown"),
    }


def _participation_point(row: list[Any]) -> dict[str, Any]:
    family_id = int(row[9]) if len(row) >= 10 else 0
    return {
        "requested_length": row[0],
        "matched_length": row[1],
        "length_index": int(row[2]),
        "mode_number": int(row[3]),
        "load_factor": row[4],
        "participation_percent": {
            "global": row[5],
            "distortional": row[6],
            "local": row[7],
            "other": row[8],
        },
        "dominant_family": FAMILY_NAMES.get(family_id, "unknown"),
    }


def _calculation_timeout() -> float:
    raw_value = os.environ.get("CUFSM_TIMEOUT_SECONDS", "120")
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ToolError("CUFSM_TIMEOUT_SECONDS must be a number.") from exc
    if not 5 <= value <= 900:
        raise ToolError("CUFSM_TIMEOUT_SECONDS must be between 5 and 900.")
    return value


def _inline_local_schema_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline Pydantic ``$defs`` so MCP Inspector renders nested controls.

    Pydantic models remain the runtime validator. This only changes the
    equivalent JSON Schema representation advertised by ``tools/list``.
    """

    definitions = schema.get("$defs", {})

    def flatten_object_union(value: dict[str, Any]) -> dict[str, Any]:
        """Expose a discriminated object union as normal Inspector fields.

        Inspector renders a bare object ``oneOf`` as one JSON textarea, which
        hides defaults on leaf properties such as ``member_lengths``.  Hoist
        the branch properties and express the same branch requirements with
        conditional schemas.  Runtime validation remains the Pydantic union.
        """

        branches = value.get("oneOf")
        if not isinstance(branches, list) or len(branches) < 2:
            return value
        if not all(
            isinstance(branch, dict)
            and branch.get("type") == "object"
            and isinstance(branch.get("properties"), dict)
            and isinstance(branch["properties"].get("type"), dict)
            for branch in branches
        ):
            return value

        def discriminator_values(property_schema: dict[str, Any]) -> list[Any]:
            if "const" in property_schema:
                return [property_schema["const"]]
            enum = property_schema.get("enum")
            return list(enum) if isinstance(enum, list) else []

        branch_values = [
            discriminator_values(branch["properties"]["type"])
            for branch in branches
        ]
        if any(not choices for choices in branch_values):
            return value

        property_names = {
            name
            for branch in branches
            for name in branch["properties"]
        }
        properties: dict[str, Any] = {}
        for name in property_names:
            variants = [
                branch["properties"][name]
                for branch in branches
                if name in branch["properties"]
            ]
            if all(variant == variants[0] for variant in variants[1:]):
                properties[name] = deepcopy(variants[0])
            elif name == "type":
                choices = [choice for group in branch_values for choice in group]
                properties[name] = {
                    "title": variants[0].get("title", "Type"),
                    "type": variants[0].get("type", "string"),
                    "enum": list(dict.fromkeys(choices)),
                }
            else:
                properties[name] = {"anyOf": deepcopy(variants)}

        common_required = set(branches[0].get("required", []))
        for branch in branches[1:]:
            common_required.intersection_update(branch.get("required", []))

        conditions: list[dict[str, Any]] = []
        for branch, choices in zip(branches, branch_values, strict=True):
            selector: dict[str, Any]
            if len(choices) == 1:
                selector = {"const": choices[0]}
            else:
                selector = {"enum": choices}
            disallowed = property_names.difference(branch["properties"])
            then_schema: dict[str, Any] = {
                "required": deepcopy(branch.get("required", [])),
            }
            if disallowed:
                then_schema["properties"] = {
                    name: {"not": {}} for name in sorted(disallowed)
                }
            conditions.append(
                {
                    "if": {
                        "properties": {"type": selector},
                        "required": ["type"],
                    },
                    "then": then_schema,
                }
            )

        flattened = {
            key: item
            for key, item in value.items()
            if key != "oneOf"
        }
        flattened.update(
            {
                "type": "object",
                "properties": properties,
                "allOf": conditions,
            }
        )
        if common_required:
            flattened["required"] = sorted(common_required)
        if all(branch.get("additionalProperties") is False for branch in branches):
            flattened["additionalProperties"] = False
        return flattened

    def expand(value: Any, stack: tuple[str, ...] = ()) -> Any:
        if isinstance(value, list):
            return [expand(item, stack) for item in value]
        if not isinstance(value, dict):
            return value
        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            name = reference.removeprefix("#/$defs/")
            if name not in definitions:
                raise RuntimeError(f"Unknown local schema reference: {reference}")
            if name in stack:
                raise RuntimeError(f"Recursive MCP input schema reference: {name}")
            merged = deepcopy(definitions[name])
            merged.update({key: item for key, item in value.items() if key != "$ref"})
            return expand(merged, (*stack, name))
        expanded = {
            key: expand(item, stack)
            for key, item in value.items()
            if key not in {"$defs", "discriminator"}
        }
        expanded = flatten_object_union(expanded)
        # Pydantic uses `default: null` to make optional Python fields
        # omittable. The canonical schema defines no null defaults, so do not
        # advertise those implementation details as MCP defaults.
        if expanded.get("default", object()) is None:
            expanded.pop("default")
        # A JSON Schema `const` is a declared fixed initial value, but MCP
        # Inspector does not prefill it consistently. Mirror canonical consts
        # into the presentation-only `default` annotation while leaving the
        # property's required status and const constraint unchanged.
        if (
            "const" in expanded
            and expanded["const"] in _CANONICAL_CONST_VALUES
            and "default" not in expanded
        ):
            expanded["default"] = deepcopy(expanded["const"])
        return expanded

    return expand(schema)


def _publish_inspector_friendly_schemas() -> None:
    for tool_name in ("analyze_lipped_channel", "analyze_section", "signature_curve"):
        tool = server._tool_manager.get_tool(tool_name)
        if tool is None:
            raise RuntimeError(f"MCP tool registration missing: {tool_name}")
        expanded = _inline_local_schema_refs(tool.parameters)
        tool.parameters.clear()
        tool.parameters.update(expanded)


def _port() -> int:
    raw_value = os.environ.get("PORT", "8080")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise SystemExit("PORT must be an integer.") from exc
    if not 1 <= value <= 65535:
        raise SystemExit("PORT must be between 1 and 65535.")
    return value


def _host() -> str:
    value = os.environ.get("MCP_HOST", "0.0.0.0").strip()
    if value not in {"0.0.0.0", "127.0.0.1", "::1"}:
        raise SystemExit("MCP_HOST must be 0.0.0.0, 127.0.0.1, or ::1.")
    return value


def _transport_security() -> TransportSecuritySettings:
    default_hosts = "127.0.0.1:*,localhost:*,[::1]:*,0.0.0.0:*"
    hosts = [item.strip() for item in os.environ.get("MCP_ALLOWED_HOSTS", default_hosts).split(",") if item.strip()]
    origins = [item.strip() for item in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if item.strip()]
    return TransportSecuritySettings(allowed_hosts=hosts, allowed_origins=origins)


_publish_inspector_friendly_schemas()


if __name__ == "__main__":
    try:
        server.run(
            transport="streamable-http",
            host=_host(),
            port=_port(),
            stateless_http=True,
            json_response=True,
            transport_security=_transport_security(),
        )
    except KeyboardInterrupt:
        pass
