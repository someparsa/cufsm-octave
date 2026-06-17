# Validation

This project is under active development. The JSON runner currently executes the included lipped-channel example and produces JSON and text reports, but a formal regression test suite is still a development priority.

## Current Status

The current example has been run successfully with GNU Octave using:

```bash
octave-cli --quiet cufsm_json.m examples/lipped-channel.json
```

The generated outputs are:

```text
examples/lipped-channel-results.json
examples/lipped-channel-results.txt
```

The JSON output includes:

- signature curve values;
- overall minimum;
- detected local minima;
- classified minima;
- family minima where detected;
- member-length mode participation;
- signature-minima mode participation.

## Needed Validation Work

Planned validation work should include:

- compare signature curves against trusted CUFSM/MATLAB results;
- compare critical half-wavelengths and load factors;
- compare cFSM participation percentages at selected lengths;
- add repeatable Octave regression tests;
- add schema validation tests for representative JSON inputs;
- test Linux, Windows, WSL, and macOS execution paths.

## Recommended Regression Data

A useful validation dataset should include:

- simple stiffened and unstiffened sections;
- cases with clear local, distortional, and global minima;
- cases with fewer than three identifiable minima;
- stress-table loading cases;
- generated-action loading cases;
- member-length participation checks.

## Residual Risk

Until regression tests are added, users should treat the JSON workflow as a development interface and compare important numerical results against trusted CUFSM runs.
