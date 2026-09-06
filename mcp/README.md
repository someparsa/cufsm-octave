# CUFSM MCP server

This directory provides the public MCP interface for the CUFSM Octave solver.
The production endpoint is:

```text
<public-mcp-url>
```

The server accepts section-analysis requests, runs the existing repository code
with GNU Octave, and returns calculation results or plots. Tool names,
parameters, defaults, and validation rules belong in `mcp/server.py` and
`schema/input-v1.schema.json`; they are not duplicated here.

## Production setup

The production service is hosted on `<server-host>`:

```text
MCP client
  -> Caddy (HTTPS)
  -> 127.0.0.1:8080
  -> cufsm-mcp.service
  -> mcp/server.py
  -> GNU Octave and the CUFSM files in this repository
```

The relevant host settings are:

| Item | Value to configure |
| --- | --- |
| SSH host or alias | `<server-host>` |
| Repository | `<repository-path>` |
| Branch | `main` |
| Service | `cufsm-mcp.service` |
| Service user | `<service-user>` |
| Python | `<repository-path>/.venv/bin/python` |
| MCP listener | `127.0.0.1:8080` |
| Public route | `<public-mcp-url>` |
| systemd unit | `/etc/systemd/system/cufsm-mcp.service` |
| Caddy configuration | `/etc/caddy/Caddyfile` |

Replace every angle-bracket placeholder with the value for your deployment.

The service runs directly from the Git checkout and virtual environment. The
production service does not use `Dockerfile.mcp`.

The systemd unit and Caddy configuration are stored only on the host. A Git
update does not change or restore them.

## Deploy an update from GitHub

Pushing to GitHub does not update the production host. Deploy runtime changes
with the following procedure.

### 1. Inspect the checkout

```bash
ssh <server-host>
repo="<repository-path>"

sudo -u <service-user> -H git -C "$repo" status --short --untracked-files=no
```

The command must print nothing. If it reports tracked changes, stop and review
them before pulling. Do not discard production changes automatically.

The SSH account may differ from the checkout owner. Run Git and Python package
commands as `<service-user>`, as shown here. Running them as another account
can trigger Git's dubious-ownership protection and create files with the wrong
owner.

The virtual environment currently appears as untracked `.venv/`. Do not run
`git clean` in this checkout because it can remove the environment used by
the service.

### 2. Review the incoming commits

```bash
sudo -u <service-user> -H git -C "$repo" fetch origin main
sudo -u <service-user> -H git -C "$repo" log --oneline HEAD..origin/main
sudo -u <service-user> -H git -C "$repo" diff --name-only HEAD..origin/main
```

Confirm that the listed commits and files are the intended release. Save the
current commit hash if a rollback may be needed:

```bash
sudo -u <service-user> -H git -C "$repo" rev-parse HEAD
```

### 3. Fast-forward `main`

```bash
sudo -u <service-user> -H git -C "$repo" switch main
sudo -u <service-user> -H git -C "$repo" pull --ff-only origin main
```

`--ff-only` prevents a production-only merge commit. If the pull cannot
fast-forward, stop and resolve the branch history outside production.

### 4. Install changed Python dependencies

Run this when `mcp/requirements.txt` changed:

```bash
sudo -u <service-user> -H "$repo/.venv/bin/python" -m pip install \
  -r "$repo/mcp/requirements.txt"
```

A Git pull does not install Python packages or operating-system packages. GNU
Octave, Python, Caddy, and systemd are managed separately on the host.

### 5. Restart the MCP service

Restart after changes to the MCP server, schema, Python helpers, or Octave
solver:

```bash
sudo systemctl restart cufsm-mcp
sudo systemctl status cufsm-mcp --no-pager
```

The status must be `active (running)`. If startup fails, inspect recent logs:

```bash
sudo journalctl -u cufsm-mcp -n 100 --no-pager
```

Caddy does not need to be restarted for a repository code change.

### 6. Confirm the deployed revision

```bash
sudo -u <service-user> -H git -C "$repo" rev-parse HEAD
sudo -u <service-user> -H git -C "$repo" rev-parse origin/main
```

The two hashes should match after a deployment from `main`.

### 7. Verify the public service

First check that Caddy and the MCP process can complete an MCP initialization:

```bash
curl --fail-with-body --silent --show-error --output /dev/null \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"health-check","version":"1"}}}' \
  <public-mcp-url>
```

No output and exit status zero means initialization succeeded. This does not
test GNU Octave.

After a runtime or solver change, run one small calculation as an end-to-end
smoke test:

```bash
curl --fail-with-body --silent --show-error \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_lipped_channel","arguments":{"analysis":{"lengths":{"type":"logspace","min":10.0,"max":100.0,"count":3},"eigenmodes":2}}}}' \
  <public-mcp-url> \
  | python3 -c 'import json, sys; result = json.load(sys.stdin)["result"]; assert result["isError"] is False; assert result["structuredContent"]["status"] == "ok"; print("MCP and CUFSM calculation: OK")'
```

This verifies the public route, MCP server, Python wrapper, temporary-job
handling, GNU Octave, and result parsing. It is only an operational smoke test,
not a numerical benchmark.

If tool names, inputs, or defaults changed, rescan the tools in each connected
MCP client after deployment.

## Which changes require a restart?

| Changed files | Production action |
| --- | --- |
| `mcp/server.py` | Pull, restart, and run the end-to-end smoke test |
| `mcp/requirements.txt` | Pull, install requirements, restart, and smoke-test |
| `cufsm_octave/`, `schema/`, `cufsm_json.m`, `analysis/`, `helpers/`, or `cutwp/` | Pull, restart, and smoke-test |
| Documentation or examples only | Pull to keep the checkout current; no restart is required |
| `Dockerfile.mcp` only | No effect on the current systemd deployment |
| systemd unit | Run `systemctl daemon-reload`, then restart and verify the service |
| Caddy configuration | Validate the Caddy file, reload Caddy, and verify the public endpoint |

When several categories change, perform all applicable actions.

## Roll back a failed deployment

Use the known-good commit recorded before deployment:

```bash
repo="<repository-path>"

sudo -u <service-user> -H git -C "$repo" switch --detach <known-good-commit>
sudo -u <service-user> -H "$repo/.venv/bin/python" -m pip install \
  -r "$repo/mcp/requirements.txt"
sudo systemctl restart cufsm-mcp
sudo systemctl status cufsm-mcp --no-pager
```

Repeat both public checks after rollback. The detached checkout is intentional
for the rollback. Before the next normal deployment, return to `main` and use
the fast-forward procedure above.

Do not use `git reset --hard` or `git clean` as a deployment shortcut.

## Server configuration changes

Repository updates and host configuration changes are separate operations.

For a systemd unit change:

```bash
sudo systemctl cat cufsm-mcp
sudo systemctl daemon-reload
sudo systemctl restart cufsm-mcp
sudo systemctl status cufsm-mcp --no-pager
```

Keep the MCP process bound to `127.0.0.1:8080`. Port 8080 should not be
opened publicly; Caddy is the public HTTPS entry point.

For a Caddy change:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy --no-pager
```

Back up the systemd unit and Caddy configuration before editing them. They are
not part of Git and cannot be recovered by checking out this repository.

The server also supports these runtime settings:

| Variable | Meaning |
| --- | --- |
| `MCP_HOST` | Bind address; production uses `127.0.0.1` |
| `PORT` | Listener port; production uses `8080` |
| `CUFSM_TIMEOUT_SECONDS` | Per-calculation limit; default `120`, allowed range `5` to `900` |
| `MCP_ALLOWED_HOSTS` | Optional comma-separated Host-header allowlist |
| `MCP_ALLOWED_ORIGINS` | Optional comma-separated browser Origin allowlist |

Changing a systemd environment value requires a daemon reload and service
restart.

## Long-term maintenance

- Keep `mcp==2.1.1` or any replacement version deliberate and tested. An MCP
  SDK upgrade can affect server startup, transport security, and published tool
  schemas.
- Test at least one real analysis whenever the MCP layer, JSON schema, Python
  wrapper, or Octave routines change. An initialization-only check cannot find
  solver failures.
- Compare representative results with a trusted CUFSM result before releasing
  numerical changes. This repository currently has no automated test suite.
- Recreate `.venv` and reinstall `mcp/requirements.txt` after a Python
  major-version change. Confirm `octave-cli` remains available after operating
  system upgrades.
- Monitor `cufsm-mcp.service`, the public endpoint, disk space, and journal
  growth. Each calculation uses a temporary `cufsm-*` directory that should be
  removed when the request finishes.
- Treat the public endpoint as an unauthenticated compute service. Review
  traffic and resource use, and add access controls or rate limits if exposure
  changes or abuse appears.
- Record the deployed commit and host-configuration changes for each release.
  Git records application code, but not the live systemd and Caddy files.

## Development helper and Docker image

`Dockerfile.mcp` packages the MCP server, Python dependencies, GNU Octave, and
the required repository files. It is useful for container deployments, but
changes to it do not affect the current systemd service.
