# Examples

The main JSON example is:

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

## Example Model

The example defines a lipped channel under generated uniform compression. The material is isotropic steel-like material in kip-inch units:

```json
"units": {
  "system": "kip_in"
}
```

The geometry is defined through node coordinates and strip elements. The input node stresses are set to zero because the example uses generated loading from actions.

## Loading

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

## Analysis Settings

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

## Output To Inspect

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
