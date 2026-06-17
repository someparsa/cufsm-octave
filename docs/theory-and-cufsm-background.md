# Theory And CUFSM Background

CUFSM Octave CLI is an Octave-oriented adaptation of CUFSM routines for finite strip elastic buckling analysis of thin-walled members.

The original CUFSM project is maintained at:

https://github.com/thinwalled/cufsm-git

This repository is not a replacement for the official CUFSM distribution. It focuses on headless command-line execution, JSON inputs, and automation-friendly outputs.

## Signature Curve

A signature curve reports elastic buckling load factor against half-wavelength. For each analyzed length, the finite strip eigenvalue problem is solved and the lowest positive eigenvalue is reported.

The JSON output stores this as:

```text
signature_curve
```

with rows:

```text
[length, lowest_eigenvalue]
```

Local minima in this curve are important because they often correspond to local, distortional, or global buckling behavior.

## Buckling Mode Families

The cFSM classification basis is used to estimate participation in four families:

| Code | Buckling mode family |
| --- | --- |
| `1` | Global |
| `2` | Distortional |
| `3` | Local |
| `4` | Other |

The JSON output reports percentages for all four families and gives the dominant family code for each classified row.

## Local Minima And Family Minima

The runner identifies interior local minima in the lowest-mode signature curve. It does not force the result to contain exactly one local, one distortional, and one global minimum. If only one or two minima are found, only those minima are reported.

`critical_points.local_minima_classified` reports each detected local minimum with mode participation.

`critical_points.family_minima` reports the lowest detected minimum for each dominant family that appears.

## Member-Length Mode Participation

For design or interpretation, it is often useful to know the modal participation at the actual physical member length. Define this with:

```json
"analysis": {
  "lengths": {
    "member_lengths": [120.0]
  }
}
```

The runner inserts member lengths into the solved length set and reports all solved eigenmodes at those lengths under:

```text
mode_participation.member_lengths
```

## Attribution

Core finite strip implementation and engineering methods originate from CUFSM by Benjamin W. Schafer and contributors. Users publishing research based on this software should cite the official CUFSM project and relevant finite strip method literature.
