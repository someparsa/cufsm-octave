# Development Roadmap

This roadmap describes the practical direction for the repository. It complements `TODO.md` and `IMPROVEMENTS.md`.

## Stable Direction

The JSON runner should become the primary workflow:

```bash
octave-cli --quiet cufsm_json.m path/to/input.json
```

The JSON file should remain the source of truth for engineering, model, loading, and analysis settings.

## CLI Scope

The CLI should stay thin. It should handle execution concerns, not duplicate the JSON configuration.

Reasonable future CLI options:

```text
input JSON path
--output
--text-output
--validate-only
--quiet
--pretty
```

Avoid adding engineering flags such as boundary condition, member length, yield stress, material properties, or node definitions to the CLI. Those belong in JSON.

## Near-Term Priorities

- Keep improving the JSON input and output contracts.
- Add lightweight compatibility checks around the JSON runner.
- Add clearer error messages and exit codes.
- Keep example results in `examples/` for easy inspection.
- Document stable and experimental fields clearly.

## Medium-Term Priorities

- Add JSON schema validation in the workflow.
- Expand Python section templates and input builders as new section families are needed.
- Add optional cross-section and mode-shape plotting outside the Octave numerical backend.
- Add more examples covering local, distortional, global, and mixed cases.

## Long-Term Options

- Package a command wrapper around `cufsm_json.m`.
- Generate static documentation from `docs/`.
- Publish reference examples where trusted CUFSM comparison data is available.
- Add CI for Octave execution across platforms.

## Current Development State

The project has a functioning headless JSON workflow, but it is not yet a fully packaged CLI application. The code should be treated as active development until the JSON/Python contracts, examples, compatibility checks, and release expectations are stronger.
