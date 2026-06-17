# JSON Input Format

The JSON runner reads one input file:

```bash
octave-cli --quiet cufsm_json.m examples/lipped-channel.json
```

The schema is tracked in:

```text
schema/input-v1.schema.json
```

The current input version is:

```json
"version": "1.0"
```

## Top-Level Structure

```json
{
  "version": "1.0",
  "metadata": {},
  "units": {},
  "model": {},
  "loading": {},
  "analysis": {},
  "output": {}
}
```

`version`, `model`, and `analysis` are required. `metadata`, `units`, `loading`, and `output` are optional, although most useful analyses should define `loading` and `output` explicitly.

## Model

`model` maps to the CUFSM matrices used internally.

| JSON field | CUFSM variable | Meaning |
| --- | --- | --- |
| `model.materials` | `prop` | Material rows: `material_id`, `Ex`, `Ey`, `nu_x`, `nu_y`, `G`. |
| `model.nodes` | `node` | Node rows: `node_id`, `x`, `z`, restraints, stress. |
| `model.elements` | `elem` | Element rows: `element_id`, end nodes, thickness, material. |
| `model.springs` | `springs` | Optional spring definitions. |
| `model.constraints` | `constraints` | Optional multipoint constraints. |

Material example:

```json
"materials": [
  {
    "id": 100,
    "Ex": 29500.0,
    "Ey": 29500.0,
    "nu_x": 0.3,
    "nu_y": 0.3,
    "G": 11346.15
  }
]
```

Node restraints use CUFSM's numeric restraint columns:

```json
{
  "id": 1,
  "x": 5.0,
  "z": 1.0,
  "dof_x": 1,
  "dof_z": 1,
  "dof_y": 1,
  "dof_rotation": 1,
  "stress": 0.0
}
```

## Loading

Two loading modes are supported.

### Stress Table

Use stresses already provided in `model.nodes[].stress`:

```json
"loading": {
  "type": "stress_table"
}
```

### Generated From Actions

Generate nodal stresses from section properties, reference yield actions, and action factors:

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

Absolute actions can also be supplied with `P`, `Mxx`, `Mzz`, `M11`, and `M22`.

## Analysis

The current supported analysis type is:

```json
"analysis": {
  "type": "signature_curve"
}
```

Supported boundary conditions are:

```text
S-S, C-C, S-C, C-F, C-G
```

### Lengths

`analysis.lengths` defines the signature-curve length set. Three forms are supported.

Logarithmic spacing:

```json
"lengths": {
  "type": "logspace",
  "min": 1.0,
  "max": 1000.0,
  "count": 100
}
```

Linear spacing:

```json
"lengths": {
  "type": "linspace",
  "min": 1.0,
  "max": 1000.0,
  "count": 100
}
```

Explicit values:

```json
"lengths": {
  "type": "explicit",
  "values": [1.0, 2.0, 5.0, 10.0]
}
```

### Member Lengths

Use `member_lengths` to request mode participation at actual member lengths. These values are inserted into the solved length set, so they are solved directly rather than matched approximately.

```json
"lengths": {
  "type": "logspace",
  "min": 1.0,
  "max": 1000.0,
  "count": 100,
  "member_lengths": [120.0]
}
```

The output appears under:

```text
mode_participation.member_lengths
```

### Longitudinal Terms

Use one default set for all lengths:

```json
"longitudinal_terms": {
  "default": [1]
}
```

Or define terms per analyzed length with `per_length`.

### Eigenmodes And Vectorization

```json
"eigenmodes": 10,
"vectorized": false
```

`eigenmodes` controls how many eigenvalues and modes are requested at each length.

### Mesh Refinement

```json
"mesh_refinement": {
  "doubler": true
}
```

When `doubler` is true, the input mesh is refined before section properties, loading, and buckling analysis are computed.

### cFSM Settings

```json
"cfsm": {
  "ospace": 1,
  "couple": 1,
  "orth": 2,
  "norm": 1,
  "local": [],
  "distortional": [],
  "global": [],
  "other": []
}
```

Empty mode-family arrays leave modal constraints disabled. The basis settings are still used for mode participation classification in the JSON output.

## Output Paths

```json
"output": {
  "path": "examples/lipped-channel-results.json",
  "text_path": "examples/lipped-channel-results.txt"
}
```

Relative paths are resolved relative to the repository directory.
