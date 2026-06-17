# Compatibility And Regression

This project adapts CUFSM routines for headless GNU Octave execution with a
JSON input/output boundary. The purpose of compatibility work is to keep that
runner boundary reliable, not to independently rederive or revalidate the
finite strip method.

## Scope

The numerical formulation and core routines originate from CUFSM. Development
in this repository focuses on:

- Octave-compatible execution;
- stable JSON input and output contracts;
- clear input errors for common modeling mistakes;
- reproducible examples;
- Python tooling around the JSON workflow;
- checks that runner changes do not unexpectedly alter known outputs.

## Useful Checks

Lightweight regression checks should emphasize the interface layer:

- the included example runs without graphics;
- JSON output is written to the requested path;
- text output is written when `output.text_path` is provided;
- required result sections are present;
- declared member lengths are inserted into the solved length set;
- common malformed inputs fail with clear messages;
- Python helpers can load inputs, run Octave, and read outputs.

For important engineering use, comparing a representative case against a trusted
CUFSM run remains good practice. That comparison is a compatibility check for
the Octave runner, not a statement that the underlying theory is being
revalidated here.

## Documentation Tone

Examples should demonstrate how to use the JSON and Python interfaces. They do
not need to serve as theoretical benchmarks unless explicitly labeled as
reference cases.
