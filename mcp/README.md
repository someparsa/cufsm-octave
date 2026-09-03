# CUFSM Remote MCP Server

This directory contains a minimal, read-only calculation service around the
existing `cufsm-octave` interfaces. It exposes engineering inputs through MCP,
runs the repository's GNU Octave CUFSM solver, and returns compact structured
signature-curve results.

The MCP layer does not reimplement CUFSM and does not accept arbitrary shell,
Python, or Octave code.

## Architecture

```text
MCP client
  -> Streamable HTTP POST /mcp
  -> mcp/server.py
  -> cufsm_octave template/input helpers and run_cufsm
  -> octave-cli -> cufsm_json.m -> helpers/cufsm_json_run.m
  -> existing CUFSM routines
  -> CufsmResult
  -> structured MCP result
```

Each calculation creates a unique `cufsm-*` temporary directory. Its input and
result files, working directory, and read-only symlink view of the CUFSM code
are private to that request. A worker process enforces the calculation timeout;
the complete temporary directory is removed after success or failure.

## Tools

### `analyze_lipped_channel`

Convenience wrapper for the webapp's lipped-channel generator. It exposes
`depth` (web depth), `flange` (equal flange width), `lip`, `thickness`, and
`max_segment_length` directly. It uses the same `metadata`, `units`,
`material`, `loading`, and `analysis` definitions as the other tools.

### `analyze_section`

Analyzes a `section` definition using one existing Python template:

- `unlipped-channel`
- `lipped-channel`
- `z-section`
- `sigma-section`
- `stiffened-web-channel`

The public geometry fields are the ones exposed by the webapp parametric
generator: `section_type`, `depth`, `flange`, `lip`, `thickness`, and
`max_segment_length`. The lipped and sigma templates require a positive lip.
For families without lips, the webapp/template behavior sets `lip` to zero.

### `signature_curve`

Runs the repository's signature-curve workflow from exactly the same `section`,
`loading`, and `analysis` representation as `analyze_section`. It no longer
requires a custom centerline or low-level node/element arrays.

`analyze_section` and `signature_curve` intentionally run the same current
analysis type. The separate name makes an explicit signature-curve request
clear to an MCP client while retaining the general analysis entry point for
future repo-supported analysis types.

## Interface source of truth

The MCP fields are translations of existing repository interfaces, not a
separate numerical input model:

- `schema/input-v1.schema.json` defines the canonical JSON structure,
  required fields, enums, numeric constraints, and nested objects.
- `cufsm_octave/templates.py` supplies the public parametric
  `build_section_model` and length builders. It does not supply MCP defaults.
- `examples/lipped-channel.json` supplies the checked-in signature-curve
  workflow and imperial example values.
- The repository's `cufsm-web` branch contains the checked-in front end at
  `web/webapp.py` and its presets at `web/section_library.py`. Those sources
  define the user-facing labels, section-family choices, unit choices, and the
  metric quick-start values used for comparison and presentation. They are not
  present as source files in the current `main` worktree, so they were
  inspected directly from Git without checking out or restoring files.

### Field mapping

| MCP field | Existing JSON/webapp destination |
| --- | --- |
| `section.version` | `version`, fixed by the schema to `1.0` |
| `section.metadata.name`, `description` | `metadata.name`, `metadata.description` |
| `section.units.system` | `units.system`; web choices are `mm_MPa`, `in_ksi`, `mm_N`, `m_N`, `in_lb`, with custom values allowed |
| `section.geometry.section_type` | Webapp Section family; argument to `build_section_model` |
| `depth`, `flange`, `lip`, `thickness`, `max_segment_length` | Webapp Parametric Section Generator; corresponding template arguments |
| `section.material.id`, `Ex`, `Ey`, `nu_x`, `nu_y`, `G` | The generated `model.materials[0]` row and the webapp Material table |
| `loading.type`, `fy`, `unsymmetric`, `actions` | Canonical `loading` object; action names are `P`, `Mxx`, `Mzz`, `M11`, `M22` and their `_factor` forms |
| `analysis.type` | `analysis.type`, fixed to `signature_curve` |
| `analysis.boundary_condition` | `analysis.boundary_condition`: `S-S`, `C-C`, `S-C`, `C-F`, or `C-G` |
| `analysis.lengths` | The schema's `logspace`, `linspace`, or `explicit` object, including `member_lengths` |
| `analysis.longitudinal_terms` | `analysis.longitudinal_terms.default` or `per_length` |
| `eigenmodes`, `vectorized` | Same-named `analysis` fields |
| `analysis.mesh_refinement.doubler` | Same nested JSON/webapp field |
| `analysis.cfsm` | `ospace`, `couple`, `orth`, `norm`, and local/distortional/global/other mode selections shown by the cFSM tab |

The MCP layer generates `model.nodes` and `model.elements` with
`build_section_model`; these solver tables are deliberately not MCP inputs.
The output path is also deliberately not exposed because every request gets
server-controlled, isolated temporary paths.

The raw JSON/webapp editor also supports `stress_table` loading and editable
spring/constraint/node tables. Those options require the low-level node model
(including per-node stress), so they are not exposed by these parametric MCP
tools. The MCP uses the repo template and checked example's
`generated_from_actions` workflow instead of presenting a non-functional
stress-table option without node stresses.

### Inspector schema representation

The server uses strongly typed Pydantic models mirroring the supported part of
the canonical JSON schema. Pydantic performs runtime validation. Before the
tools are published, the server expands Pydantic's local `$ref` entries into
equivalent nested JSON Schema. This presentation step is needed because MCP
Inspector otherwise renders the referenced `section`, `loading`, and
`analysis` models as generic object controls.

Accordingly, `tools/list` exposes direct nested `properties` for all three
objects. It also preserves their types, defaults, descriptions, enums, array
item types, and applicable numeric constraints. Unknown fields are rejected.

### Defaults

`schema/input-v1.schema.json` is the only source of MCP initial values. The
server reads both `default` and fixed `const` annotations at startup and does
not copy example, test, README, webapp, or Python template starter values into
the tool schemas. Canonical `const` values are mirrored to the presentation-only
MCP `default` annotation so Inspector prefills them, while their required status
and `const` constraint remain unchanged.

| Effective/MCP path | Exact schema `const`/`default` path | Value |
| --- | --- | --- |
| `section.version` | `properties.version.const` | `"1.0"` |
| `loading.type` | `$defs.generatedActionLoading.properties.type.const` | `"generated_from_actions"` |
| `analysis.type` | `properties.analysis.properties.type.const` | `"signature_curve"` |
| explicit `analysis.lengths.type` | `$defs.explicitLengths.properties.type.const` | `"explicit"` |
| `loading.unsymmetric` | `$defs.generatedActionLoading.properties.unsymmetric.default` | `false` |
| generated `analysis.lengths.member_lengths` | `$defs.memberLengths.default` | `[]` |
| explicit `analysis.lengths.member_lengths` | `$defs.memberLengths.default` | `[]` |
| `analysis.eigenmodes` | `properties.analysis.properties.eigenmodes.default` | `20` |
| `analysis.vectorized` | `properties.analysis.properties.vectorized.default` | `false` |
| `analysis.mesh_refinement.doubler` | `properties.analysis.properties.mesh_refinement.properties.doubler.default` | `false` |
| generated `model.springs` | `properties.model.properties.springs.default` | `[]` |
| generated `model.constraints` | `properties.model.properties.constraints.default` | `[]` |

The canonical schema defines no initial values for geometry, material, unit system,
yield stress, loading actions, boundary condition, length type/range/count,
longitudinal terms, or cFSM options. Those fields are therefore not populated
from an example. Geometry and material are required MCP inputs, while optional
canonical objects remain optional. The schema's required `analysis.type`,
`analysis.boundary_condition`, and `analysis.lengths` fields must be supplied.

Consequently, `{}` is intentionally not a valid analysis call. A minimum
successful call supplies the non-default geometry, material, loading, and
required analysis definition, while omitting only fields with the schema
defaults listed above.

## Results

All three tools return a structured object containing:

- `model_summary`, including study, units, geometry, material, loading,
  analysis, and generated table counts;
- solver `analysis_settings` and `section_properties`;
- the overall minimum and its dominant mode family;
- detected local, distortional, global, and other family minima;
- `signature_curve.points`, with length, load factor, participation percentages,
  and dominant family;
- requested member-length modes;
- all modes at detected signature minima;
- `warnings` and an empty `errors` list on success.

Load factors are dimensionless multipliers on the supplied reference loading.
An absent family minimum is reported as `null`; the server does not invent a
minimum when CUFSM did not detect one in the analyzed range.

## Local installation and startup

From the repository root:

```bash
python3 -m venv /tmp/cufsm-mcp-venv
/tmp/cufsm-mcp-venv/bin/python -m pip install -r mcp/requirements.txt
PORT=8080 /tmp/cufsm-mcp-venv/bin/python mcp/server.py
```

The server binds to `0.0.0.0`; connect locally at:

```text
http://127.0.0.1:8080/mcp
```

No separate web framework is used. The official Python MCP SDK serves
stateless Streamable HTTP with JSON responses.

## Local MCP testing

With the server running, the SDK client can initialize, discover tools, and
call a real analysis:

```python
import asyncio
from mcp import Client

async def main():
    async with Client("http://127.0.0.1:8080/mcp") as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools.tools])
        result = await client.call_tool(
            "analyze_lipped_channel",
            {
                "depth": 150.0,
                "flange": 50.0,
                "lip": 15.0,
                "thickness": 1.5,
                "max_segment_length": 50.0,
                "units": {"system": "mm_MPa"},
                "material": {
                    "id": 100,
                    "Ex": 200000.0,
                    "Ey": 200000.0,
                    "nu_x": 0.3,
                    "nu_y": 0.3,
                    "G": 76923.07692307692,
                },
                "loading": {
                    "type": "generated_from_actions",
                    "fy": 350.0,
                    "actions": {"P_factor": 1.0},
                },
                "analysis": {
                    "type": "signature_curve",
                    "boundary_condition": "S-S",
                    "lengths": {
                        "type": "logspace",
                        "min": 10.0,
                        "max": 10000.0,
                        "count": 60,
                        "member_lengths": [3000.0],
                    },
                }
            },
        )
        print(result.structured_content)

asyncio.run(main())
```

## MCP Inspector inputs

Connect Inspector to `http://127.0.0.1:8080/mcp`, select a tool, and paste one
of the following objects into its arguments JSON editor.

### Minimum call using canonical defaults

The following is valid for either `analyze_section` or `signature_curve`. Its
geometry and engineering values are explicit call inputs, not defaults. It
omits `unsymmetric`, `member_lengths`, `eigenmodes`, `vectorized`, and
`mesh_refinement.doubler`, which resolve to the canonical defaults above.

```json
{
  "section": {
    "version": "1.0",
    "geometry": {
      "section_type": "lipped-channel",
      "depth": 9.0,
      "flange": 5.0,
      "lip": 1.0,
      "thickness": 0.1,
      "max_segment_length": 3.0
    },
    "material": {
      "id": 100,
      "Ex": 29500.0,
      "Ey": 29500.0,
      "nu_x": 0.3,
      "nu_y": 0.3,
      "G": 11346.15
    }
  },
  "loading": {
    "type": "generated_from_actions",
    "fy": 50.0,
    "actions": {"P_factor": 1.0}
  },
  "analysis": {
    "type": "signature_curve",
    "boundary_condition": "S-S",
    "lengths": {
      "type": "logspace",
      "min": 1.0,
      "max": 1000.0,
      "count": 30
    }
  }
}
```

For `analyze_lipped_channel`, move the five geometry values to top-level
arguments, omit `section` and `section_type`, and keep the same `material`,
`loading`, and `analysis` objects.

### Partial overrides

Only fields having canonical defaults may be omitted. MCP is stateless, so a
request must still contain every non-default required field. To test a partial
engineering change, reuse the minimum request above and change only one value,
for example `section.geometry.thickness` from `0.1` to `0.12`. The effective
input retains `unsymmetric = false`, `member_lengths = []`, `eigenmodes = 20`,
`vectorized = false`, and `doubler = false` from the schema. The complete
checked examples below are directly pasteable.

### Checked-in signature-curve example

This is the parametric equivalent of `examples/lipped-channel.json`. The 3.0
maximum segment length reproduces its 10-node/9-element pre-doubler mesh.

Tool: `signature_curve`

```json
{
  "section": {
    "version": "1.0",
    "metadata": {
      "name": "lipped-channel-compression-example",
      "description": "Checked-in signature-curve example through MCP."
    },
    "units": {"system": "kip_in"},
    "geometry": {
      "section_type": "lipped-channel",
      "depth": 9.0,
      "flange": 5.0,
      "lip": 1.0,
      "thickness": 0.1,
      "max_segment_length": 3.0
    },
    "material": {
      "id": 100,
      "Ex": 29500.0,
      "Ey": 29500.0,
      "nu_x": 0.3,
      "nu_y": 0.3,
      "G": 11346.15
    }
  },
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
  },
  "analysis": {
    "type": "signature_curve",
    "boundary_condition": "S-S",
    "lengths": {
      "type": "logspace",
      "min": 1.0,
      "max": 1000.0,
      "count": 100,
      "member_lengths": [120.0]
    },
    "longitudinal_terms": {"default": [1]},
    "eigenmodes": 10,
    "vectorized": false,
    "mesh_refinement": {"doubler": true},
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
  }
}
```

### Lipped-channel webapp example

Tool: `analyze_lipped_channel`

```json
{
  "depth": 150.0,
  "flange": 50.0,
  "lip": 15.0,
  "thickness": 1.5,
  "max_segment_length": 50.0,
  "units": {"system": "mm_MPa"},
  "material": {
    "id": 100,
    "Ex": 200000.0,
    "Ey": 200000.0,
    "nu_x": 0.3,
    "nu_y": 0.3,
    "G": 76923.07692307692
  },
  "loading": {
    "type": "generated_from_actions",
    "fy": 350.0,
    "unsymmetric": false,
    "actions": {
      "P_factor": 1.0,
      "Mxx_factor": 0.0,
      "Mzz_factor": 0.0,
      "M11_factor": 0.0,
      "M22_factor": 0.0
    }
  },
  "analysis": {
    "type": "signature_curve",
    "boundary_condition": "S-S",
    "lengths": {
      "type": "logspace",
      "min": 10.0,
      "max": 10000.0,
      "count": 60,
      "member_lengths": [3000.0]
    },
    "longitudinal_terms": {"default": [1]},
    "eigenmodes": 6,
    "vectorized": false,
    "mesh_refinement": {"doubler": false},
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
  }
}
```

## Environment variables

- `PORT`: HTTP port; default `8080`.
- `MCP_HOST`: bind address; default `0.0.0.0`. The development helper sets it
  to `127.0.0.1` on the VPS so the test process is reachable only through SSH.
- `CUFSM_TIMEOUT_SECONDS`: per-analysis timeout; default `120`, allowed range
  5-900 seconds.
- `MCP_ALLOWED_HOSTS`: comma-separated exact Host-header allowlist. The local
  default permits `127.0.0.1`, `localhost`, `[::1]`, and `0.0.0.0` with ports.
  Set the real public hostname before deployment, for example
  `mcp.example.com,mcp.example.com:*`.
- `MCP_ALLOWED_ORIGINS`: optional comma-separated browser Origin allowlist.

## One-command remote development

With the existing `ssh contabo` alias, isolated test copy at
`/home/parsa/cufsm-mcp-test`, and its `.venv` prepared, run from the local
repository root:

```bash
./mcp/dev_remote.sh
```

The helper starts the remote MCP process bound to remote localhost, forwards
local `127.0.0.1:8081` to remote `127.0.0.1:8080`, waits for a successful MCP
initialize response, prints:

```text
http://127.0.0.1:8081/mcp
```

and launches `npx @modelcontextprotocol/inspector`. Closing Inspector or
pressing Ctrl+C terminates the exact SSH session. A remote trap stops and waits
for its Python child; an exact-PID/cwd/command check provides a cleanup fallback
if the server outlives the SSH PTY. The script refuses to start if local port
8081 is already occupied and never kills the occupying process. It does not
install software or change server/network configuration.

## Contabo testing

Use an isolated user-owned copy and localhost only:

```bash
ssh contabo
cd ~/cufsm-mcp-test
python3 -m venv .venv
.venv/bin/python -m pip install -r mcp/requirements.txt
PORT=8080 .venv/bin/python mcp/server.py
```

The tested VPS had Python 3.12 but not Ubuntu's `python3.12-venv`/`ensurepip`.
To avoid a system package change, its existing user-space pip installed into
the otherwise usable isolated venv path:

```bash
python3 -m venv .venv  # creates the environment, then reports missing ensurepip
python3 -m pip install \
  --target "$HOME/cufsm-mcp-test/.venv/lib/python3.12/site-packages" \
  -r mcp/requirements.txt
```

From another SSH session, run the MCP client example against
`http://127.0.0.1:8080/mcp`. This requires no firewall, web-server, DNS, TLS,
SSH, or system-service change.

### Test record: 2026-09-03

The isolated copy at `/home/parsa/cufsm-mcp-test` was tested on Ubuntu 24.04.4
LTS with Python 3.12.3 and GNU Octave 8.4.0. The final
`./mcp/dev_remote.sh` started the server on VPS localhost, created only an SSH
tunnel, received a successful MCP initialize response, and launched the actual
MCP Inspector locally.

Through that live tunnel, the official MCP client discovered all three tools,
confirmed direct nested `section`, `loading`, and `analysis` properties, and
ran the checked 9 x 5 x 1 x 0.1 inch lipped-channel signature curve through
Python -> JSON -> Octave -> CUFSM. It returned 101 curve points, classified
local and distortional minima, 10 member-length modes, 20 signature-minimum
modes, and an overall factor of `0.020829253194500557`. The small difference
from the local/checked result is consistent with the Octave/platform versions.

Both normal exit and Ctrl+C cleanup were exercised. The occupied-local-port
failure path was also exercised without stopping the occupying process. After
the tests, no port-8080 listener, PID file, CUFSM job directory, MCP server, or
Octave process remained on the VPS. Docker was not tested because Docker was
not installed.

## Docker

Build from the repository root:

```bash
docker build -f Dockerfile.mcp -t cufsm-octave-mcp .
```

Run locally:

```bash
docker run --rm -p 127.0.0.1:8080:8080 -e PORT=8080 cufsm-octave-mcp
```

The image contains Python, GNU Octave, this repository, and the MCP dependency.

## Example LLM workflow

1. A user asks: "Analyse a 150 x 50 x 15 x 1.5 mm lipped channel."
2. The LLM calls `analyze_lipped_channel` with those dimensions.
3. The MCP server generates the standard CUFSM input, runs Octave, and returns
   the curve and classified critical points.
4. The LLM explains the critical mode and local/distortional/global behavior.

## Future deployment (not performed here)

### Public HTTPS on Contabo

Keep the Python process on localhost, place a maintained HTTPS reverse proxy in
front of `/mcp`, configure DNS and TLS, set `MCP_ALLOWED_HOSTS` to the public
hostname, add health/operational monitoring as appropriate, and review the risk
of operating a deliberately unauthenticated public compute service. These
steps require separate authorization and were not performed by this task.

### ChatGPT Developer Mode

After an HTTPS endpoint is reachable, enable Developer Mode for an eligible
ChatGPT workspace/account, create a custom MCP app, enter the full
`https://.../mcp` endpoint, choose no authentication for this public tool, scan
the tools, and test the draft app. ChatGPT cannot connect directly to this
localhost-only test instance.

### Google Cloud Run

Build and publish `Dockerfile.mcp`, deploy it as a Cloud Run service, leave
`PORT` under Cloud Run control, set `MCP_ALLOWED_HOSTS` to the service/custom
domain, and configure an appropriate request timeout and concurrency. No Cloud
Run resources are created by this repository.
