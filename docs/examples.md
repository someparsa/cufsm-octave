# Examples

The repository currently includes one checked-in JSON analysis example, one
checked-in legacy Octave script example, and three Python workflow examples.
The Python package can also generate additional JSON inputs from section
templates; generated inputs and results are written only when a user runs the
workflow scripts.

## Checked-In JSON Example

The main JSON input example is:

```text
examples/lipped-channel.json
```

Run it with:

```bash
octave-cli --quiet cufsm_json.m examples/lipped-channel.json
```

It writes:

```text
examples/lipped-channel-results.json
examples/lipped-channel-results.txt
```

### Model

The example defines a lipped channel under generated uniform compression. The material is isotropic steel-like material in kip-inch units:

```json
"units": {
  "system": "kip_in"
}
```

The geometry is defined directly through node coordinates and strip elements.
The input node stresses are set to zero because the example uses generated
loading from actions.

### Loading

The example uses:

```json
"loading": {
  "type": "generated_from_actions",
  "fy": 50.0,
  "unsymmetric": false,
  "actions": {
    "P_factor": 1.0,
    "Mxx_factor": 0.0,
    "Mzz_factor": 0.0,
    "M11_factor": 0.0,
    "M22_factor": 0.0
  }
}
```

The runner computes section properties, yield reference actions, and nodal stresses before solving the signature curve.

### Analysis Settings

The example uses simply supported loaded edges:

```json
"boundary_condition": "S-S"
```

The signature curve is solved over 100 logarithmically spaced lengths from 1 to 1000, with the physical member length `120.0` inserted into the solved set:

```json
"lengths": {
  "type": "logspace",
  "min": 1.0,
  "max": 1000.0,
  "count": 100,
  "member_lengths": [120.0]
}
```

Because `120.0` is inserted into the solve grid, the example currently solves 101 lengths.

### Output To Inspect

Open the text report for a quick view:

```text
examples/lipped-channel-results.txt
```

Key sections:

```text
CLASSIFIED LOCAL MINIMA
FAMILY MINIMA
MEMBER LENGTH MODE PARTICIPATION
SIGNATURE MINIMA MODE PARTICIPATION
```

Use the JSON result for scripts:

```text
examples/lipped-channel-results.json
```

Important JSON paths:

```text
signature_curve
critical_points.family_minima
mode_participation.member_lengths
mode_participation.signature_minima
```

## Python Post-Processing Example

The Python post-processing example reads an existing result JSON and writes a
signature-curve PNG. It does not rerun Octave.

```text
examples/postprocess_signature_curve.py
```

Install plotting support first:

```bash
python -m pip install -e ".[plotting]"
```

Run:

```bash
python examples/postprocess_signature_curve.py \
  examples/lipped-channel-results.json \
  examples/lipped-channel-signature-curve.png
```

The script calls `cufsm_octave.plotting.save_signature_curve_plot`. The plot
marks the signature curve, overall minimum, detected local minima, and family
minima when those result tables exist.

## Python Batch Run Example

The batch example sweeps lipped-channel lip length and thickness. It writes one
JSON input and one result file per case, then writes a CSV summary. If
matplotlib is installed, it also writes a signature-curve comparison plot.

```text
examples/python_batch_lipped_channel.py
```

Run:

```bash
python examples/python_batch_lipped_channel.py
```

The sweep is:

| Parameter | Values |
| --- | --- |
| `thickness` | `0.075`, `0.100`, `0.125` |
| `lip` | `0.50`, `0.75`, `1.00`, `1.25` |

Fixed settings:

| Setting | Value |
| --- | --- |
| section type | `lipped-channel` |
| depth | `9.0` |
| flange | `5.0` |
| yield stress `fy` | `50.0` |
| boundary condition | `S-S` |
| member length | `120.0` |
| length range | logspace from `1.0` to `1000.0`, `60` points |
| eigenmodes | `6` |

Generated outputs:

```text
examples/batch-results/
  t0p075_lip0p50.json
  t0p075_lip0p50-results.json
  t0p075_lip0p50-results.txt
  ...
  batch-summary.csv
  signature-curve-comparison.png   # only when matplotlib is installed
```

The summary CSV columns are:

```text
case_id,
lip,
thickness,
overall_minimum_length,
overall_minimum_factor,
member_length,
member_length_factor,
member_length_dominant_family,
result_json
```

This example demonstrates Python orchestration around the JSON runner: generate
cases, run Octave, collect key result values, and compare curves.

## Python Optimization Example

The optimization example performs a small grid search over lipped-channel flange
width and lip length. It selects the case with the largest lowest-mode
eigenvalue at the requested member length.

```text
examples/python_optimize_lipped_channel.py
```

Run:

```bash
python examples/python_optimize_lipped_channel.py
```

The search grid is:

| Parameter | Values |
| --- | --- |
| `flange` | `4.0`, `4.5`, `5.0`, `5.5`, `6.0` |
| `lip` | `0.50`, `0.75`, `1.00`, `1.25`, `1.50` |

Cases where `lip >= flange` are skipped.

Fixed settings:

| Setting | Value |
| --- | --- |
| section type | `lipped-channel` |
| depth | `9.0` |
| thickness | `0.1` |
| yield stress `fy` | `50.0` |
| boundary condition | `S-S` |
| member length | `120.0` |
| objective | maximize lowest eigenvalue at member length `120.0` |
| length range | logspace from `1.0` to `1000.0`, `60` points |
| eigenmodes | `6` |

Generated outputs:

```text
examples/optimization-results/
  flange4p00_lip0p50.json
  flange4p00_lip0p50-results.json
  flange4p00_lip0p50-results.txt
  ...
  optimization-summary.csv
  best-case.json
  best-case-results.json
  best-signature-curve.png   # only when matplotlib is installed
```

The summary CSV columns are:

```text
case_id,
flange,
lip,
objective_member_length_factor,
member_length,
member_length_dominant_family,
overall_minimum_length,
overall_minimum_factor,
input_json,
result_json
```

This example is intentionally a transparent grid search. It shows how to define
a scalar objective from result JSON, preserve every case, and copy the best
input/result pair for later review.

## Python-Generated Input Examples

The Python package can generate JSON input files for supported section families:

| Section label | Description |
| --- | --- |
| `unlipped-channel` | Channel with web and two plain flanges. |
| `lipped-channel` | Channel with lips at both flange tips. |
| `z-section` | Z section with top and bottom flanges on opposite sides. |
| `sigma-section` | Lipped channel with the web-stiffener path documented in `docs/python-tooling.md`. |
| `stiffened-web-channel` | Channel with the central web-stiffener path documented in `docs/python-tooling.md`. |

Build and write a generated lipped-channel input:

```python
from cufsm_octave import (
    logspace_lengths,
    signature_analysis,
    write_section_input,
)

analysis = signature_analysis(
    boundary_condition="S-S",
    lengths=logspace_lengths(1.0, 1000.0, 100, member_lengths=[120.0]),
    eigenmodes=10,
)

write_section_input(
    "examples/generated-lipped-channel.json",
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

Run a generated input through Octave:

```python
from cufsm_octave import run_cufsm

result = run_cufsm("examples/generated-lipped-channel.json")
print(result.overall_minimum)
```

Or generate, write, run, and read the result in one call:

```python
from cufsm_octave import run_section_input

result = run_section_input(
    "examples/generated-z-section.json",
    "z-section",
    depth=8.0,
    top_flange=3.0,
    bottom_flange=3.0,
    thickness=0.075,
    fy=50.0,
    output_path="examples/generated-z-section-results.json",
)

print(result.signature_curve[:3])
```

Use `model_from_centerline(points, thickness=...)` when a section is not covered
by the named templates.

## Legacy Script Example

The older hardcoded example is:

```text
cufsm-octave-example.m
```

Run it with:

```bash
octave-cli --quiet cufsm-octave-example.m
```

It writes:

```text
cufsm-results.txt
```

This remains useful as a simple reference script, but new repeatable workflows should use JSON input.
