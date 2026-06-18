# Python Tooling

The Python layer is a thin interface around the JSON workflow. It does not
reimplement CUFSM theory or duplicate the Octave solver. Its job is to make the
existing runner easier to call from scripts, notebooks, future apps, and data
pipelines.

## Scope

The Python helpers support six practical tasks:

| Task | Helper |
| --- | --- |
| Load and write CUFSM JSON input files | `cufsm_octave.load_input`, `cufsm_octave.write_input` |
| Generate JSON input files from common section templates | `cufsm_octave.build_section_input`, `cufsm_octave.write_section_input` |
| Validate common input mistakes before running Octave | `cufsm_octave.validate_input` |
| Run the Octave JSON runner | `cufsm_octave.run_cufsm` |
| Read common result tables | `cufsm_octave.CufsmResult` |
| Post-process and plot result JSON files | `cufsm_octave.plotting` |

Optional plotting and DataFrame helpers are available when `matplotlib` or
`pandas` are installed.

## Basic Use

From the repository root:

```bash
python -m pip install -e .
```

Install optional extras as needed:

```bash
python -m pip install -e ".[validation]"
python -m pip install -e ".[plotting]"
python -m pip install -e ".[dataframe]"
```

Run the included example:

```python
from cufsm_octave import run_cufsm

result = run_cufsm("examples/lipped-channel.json")
print(result.overall_minimum)
print(result.family_minima)
```

Load an existing result without rerunning Octave:

```python
from cufsm_octave import CufsmResult

result = CufsmResult.from_file("examples/lipped-channel-results.json")
curve = result.signature_curve
```

## Generating JSON Inputs

The template layer can generate CUFSM JSON input dictionaries from labeled
thin-walled section families. The generated model is an open-section centerline
with strip elements between consecutive points.

Supported `section_type` labels:

| Label | Meaning |
| --- | --- |
| `unlipped-channel` | Channel with web and two plain flanges |
| `lipped-channel` | Channel with lips at both flange tips |
| `z-section` | Z section with top and bottom flanges on opposite sides |
| `sigma-section` | Lipped channel with a defined web-stiffener path |
| `stiffened-web-channel` | Channel with a defined central web-stiffener path |

Build a lipped-channel input object:

```python
from cufsm_octave import build_section_input, logspace_lengths, signature_analysis

analysis = signature_analysis(
    boundary_condition="S-S",
    lengths=logspace_lengths(1.0, 1000.0, 100, member_lengths=[120.0]),
    eigenmodes=10,
    doubler=False,
)

data = build_section_input(
    "lipped-channel",
    depth=9.0,
    flange=5.0,
    lip=1.0,
    thickness=0.1,
    max_segment_length=2.5,
    fy=50.0,
    analysis=analysis,
    output_path="examples/generated-lipped-channel-results.json",
    text_output_path="examples/generated-lipped-channel-results.txt",
)
```

Write the generated input:

```python
from cufsm_octave import write_input

write_input(data, "examples/generated-lipped-channel.json")
```

Or build and write in one call:

```python
from cufsm_octave import write_section_input

write_section_input(
    "examples/generated-z-section.json",
    "z-section",
    depth=8.0,
    top_flange=3.0,
    bottom_flange=3.0,
    thickness=0.075,
    fy=50.0,
    output_path="examples/generated-z-section-results.json",
)
```

To generate, run Octave, and read the result in one step:

```python
from cufsm_octave import run_section_input

result = run_section_input(
    "examples/generated-unlipped-channel.json",
    "unlipped-channel",
    depth=8.0,
    flange=3.0,
    thickness=0.075,
    fy=50.0,
    output_path="examples/generated-unlipped-channel-results.json",
)

print(result.overall_minimum)
```

### Template Geometry Notes

The template functions are intended to reduce repetitive JSON setup. They
generate centerline geometry from a small number of dimensions:

- `depth`: web depth;
- `flange`: shared top and bottom flange length;
- `top_flange` and `bottom_flange`: asymmetric flange lengths;
- `lip`: lip length for lipped and sigma sections;
- `web_stiffener_depth`: offset used by sigma and stiffened-web templates;
- `thickness`: strip thickness;
- `max_segment_length`: optional subdivision length for cleaner strip meshes.

For custom sections, use `model_from_centerline(points, thickness=...)` with an
ordered list of `(x, z)` centerline points.

The named templates currently generate these ordered centerline points before
optional subdivision by `max_segment_length`. `top` means `top_flange` when
provided, otherwise `flange`; `bottom` means `bottom_flange` when provided,
otherwise `flange`. If a web stiffener offset is not provided,
`web_stiffener_depth = 0.25 * min(top, bottom)`.

| Section label | Generated centerline points |
| --- | --- |
| `unlipped-channel` | `(bottom, 0) -> (0, 0) -> (0, depth) -> (top, depth)` |
| `lipped-channel` | `(bottom, lip) -> (bottom, 0) -> (0, 0) -> (0, depth) -> (top, depth) -> (top, depth - lip)` |
| `z-section` | `(-bottom, 0) -> (0, 0) -> (0, depth) -> (top, depth)` |
| `sigma-section` | `(bottom, lip) -> (bottom, 0) -> (0, 0) -> (0, 0.35 * depth) -> (web_stiffener_depth, 0.45 * depth) -> (web_stiffener_depth, 0.55 * depth) -> (0, 0.65 * depth) -> (0, depth) -> (top, depth) -> (top, depth - lip)` |
| `stiffened-web-channel` | `(bottom, 0) -> (0, 0) -> (0, 0.35 * depth) -> (web_stiffener_depth, 0.5 * depth) -> (0, 0.65 * depth) -> (0, depth) -> (top, depth)` |

The full set of public template helpers is:

| Helper | Purpose |
| --- | --- |
| `steel_material` | Build a material record. |
| `generated_action_loading` | Build a `generated_from_actions` loading block. |
| `stress_table_loading` | Build a `stress_table` loading block. |
| `logspace_lengths` | Build logarithmically spaced analysis lengths. |
| `linspace_lengths` | Build linearly spaced analysis lengths. |
| `explicit_lengths` | Build explicit analysis lengths. |
| `cfsm_defaults` | Build the default cFSM settings block. |
| `signature_analysis` | Build an `analysis.type = signature_curve` block. |
| `section_centerline` | Return centerline points for a supported section label. |
| `model_from_centerline` | Build model tables from custom centerline points. |
| `build_section_model` | Build only the `model` section for a supported section label. |
| `build_section_input` | Build a complete CUFSM JSON input object. |
| `write_section_input` | Build and write a complete CUFSM JSON input file. |
| `run_section_input` | Build, write, run Octave, and return `CufsmResult`. |

## Input Validation

`validate_input` uses the repository JSON schema when the optional `jsonschema`
package is installed:

```bash
python -m pip install -e ".[validation]"
```

Without `jsonschema`, it still performs lightweight checks for common interface
mistakes:

- duplicate material, node, or element IDs;
- elements referencing missing nodes;
- elements referencing missing materials;
- non-positive element thickness;
- unsupported boundary conditions;
- invalid length definitions;
- unsupported loading types.

These checks are intended to catch JSON contract errors before Octave reaches
the numerical routines. They are not a replacement for engineering review of a
model.

## Post-Processing And Plotting

Install plotting support:

```bash
python -m pip install -e ".[plotting]"
```

Then:

```python
from cufsm_octave import CufsmResult
from cufsm_octave.plotting import plot_signature_curve

result = CufsmResult.from_file("examples/lipped-channel-results.json")
ax = plot_signature_curve(result)
ax.figure.savefig("signature-curve.png", dpi=200)
```

The plotting helper can mark the overall minimum, detected local minima, and
family minima:

```python
from cufsm_octave.plotting import save_signature_curve_plot

save_signature_curve_plot(
    "examples/lipped-channel-results.json",
    "examples/lipped-channel-signature-curve.png",
    title="Lipped channel signature curve",
)
```

A runnable post-processing example is included:

```bash
python examples/postprocess_signature_curve.py \
  examples/lipped-channel-results.json \
  examples/lipped-channel-signature-curve.png
```

The example reads only the result JSON. It does not rerun Octave.

## Batch And Optimization Workflows

Batch and optimization are handled in Python as orchestration around the JSON
runner. The Octave solver still receives one JSON input at a time.

Two runnable examples are included:

| Example | Purpose |
| --- | --- |
| `examples/python_batch_lipped_channel.py` | Sweep lipped-channel lip length and thickness, run every case, write a CSV summary, and optionally plot all signature curves. |
| `examples/python_optimize_lipped_channel.py` | Grid-search flange width and lip length, choose the best member-length eigenvalue, and preserve the best input/result pair. |

Run the batch example:

```bash
python examples/python_batch_lipped_channel.py
```

It writes generated files under:

```text
examples/batch-results/
```

Run the optimization example:

```bash
python examples/python_optimize_lipped_channel.py
```

It writes generated files under:

```text
examples/optimization-results/
```

Both examples use only the Python standard library plus `cufsm_octave`.
Comparison plots are skipped automatically when `matplotlib` is not installed.
Install plotting support with:

```bash
python -m pip install -e ".[plotting]"
```

## DataFrame Helpers

Install DataFrame support:

```bash
python -m pip install -e ".[dataframe]"
```

Then:

```python
from cufsm_octave import CufsmResult

result = CufsmResult.from_file("examples/lipped-channel-results.json")

signature_curve = result.signature_curve_dataframe()
lowest_modes = result.lowest_modes_dataframe()
member_length_modes = result.participation_points_dataframe("member_lengths")
signature_minima_modes = result.participation_points_dataframe("signature_minima")
```

These helpers use the column names stored in the result JSON where available.

## Design Notes

The Python package treats JSON as the boundary between Python and Octave. This
keeps the solver implementation in Octave and keeps Python focused on:

- preparing valid inputs;
- launching reproducible runs;
- reading structured outputs;
- plotting or converting results for downstream tools.
