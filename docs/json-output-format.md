# JSON Output Format

The JSON runner writes a machine-readable result file to `output.path`.

For the included example:

```text
examples/lipped-channel-results.json
```

The text report at `output.text_path` is a human-readable companion file.

Python helpers can read the result JSON and expose common tables through
`CufsmResult`. See [`docs/python-tooling.md`](python-tooling.md).

## Top-Level Result Structure

Important top-level fields include:

| Field | Meaning |
| --- | --- |
| `version` | Input format version copied from the input file. |
| `analysis_type` | Currently `signature_curve`. |
| `model` | Refined model matrices used by the solver. |
| `analysis_settings` | Boundary condition, length range, member lengths, eigenmodes, and flags. |
| `section_properties` | Area, centroid, inertias, torsion, shear center, warping, and related section properties. |
| `signature_curve` | Lowest eigenvalue at each analyzed length. |
| `critical_points` | Overall minimum, detected local minima, and classified minima. |
| `mode_participation` | cFSM participation tables. |

## Signature Curve

`signature_curve` is a numeric table:

```text
[length, lowest_eigenvalue]
```

Example row:

```json
[120.0, 0.6548950281107577]
```

## Critical Points

`critical_points.overall_minimum` reports:

```text
[length, lowest_eigenvalue]
```

`critical_points.local_minima` reports detected interior minima from the signature curve. If fewer than three local minima exist, only the identified minima are reported.

`critical_points.local_minima_classified` reports each detected local minimum with mode participation:

```text
[length, eigenvalue, length_index, global_percent, distortional_percent, local_percent, other_percent, dominant_family_id]
```

`critical_points.family_minima` reports the lowest detected minimum for each dominant buckling family that appears:

```text
[dominant_family_id, length, eigenvalue, length_index, global_percent, distortional_percent, local_percent, other_percent]
```

If a family has no identified minimum, it is not forced into the output.

## Buckling Family Codes

Mode-family percentages are reported as numeric columns, and the dominant family is encoded by `dominant_family_id`.

| Code | Buckling mode family |
| --- | --- |
| `1` | Global |
| `2` | Distortional |
| `3` | Local |
| `4` | Other |

## Mode Participation

`mode_participation.family_labels` gives the family order:

```json
["global", "distortional", "local", "other"]
```

`mode_participation.table_columns` describes `lowest_modes`:

```text
length, eigenvalue, global_percent, distortional_percent, local_percent, other_percent, dominant_family_id
```

`mode_participation.participation_point_columns` describes `member_lengths` and `signature_minima`:

```text
requested_length, matched_length, length_index, mode_number, eigenvalue, global_percent, distortional_percent, local_percent, other_percent, dominant_family_id
```

Because `analysis.lengths.member_lengths` are inserted into the solved length vector, member-length rows should normally have `requested_length == matched_length`.

### Lowest Modes

`mode_participation.lowest_modes` reports the lowest mode at every analyzed length.

### Member Lengths

`mode_participation.member_lengths` reports every solved eigenmode at each declared member length.

### Signature Minima

`mode_participation.signature_minima` reports every solved eigenmode at each detected signature-curve local minimum.

This is useful when the minimum itself is mixed and the second or third eigenmode helps interpret nearby local, distortional, or global behavior.

## Text Report Sections

The text report contains the same major result groups in a simpler CSV-like form. Important sections include:

```text
SIGNATURE CURVE
CRITICAL POINTS
CLASSIFIED LOCAL MINIMA
FAMILY MINIMA
LOWEST MODE PARTICIPATION
MEMBER LENGTH MODE PARTICIPATION
SIGNATURE MINIMA MODE PARTICIPATION
```

The text report is intended for quick inspection. Use the JSON result for programmatic workflows.
