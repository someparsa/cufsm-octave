#!/usr/bin/env bash

set -Eeuo pipefail

readonly SSH_TARGET="contabo"
readonly REMOTE_DIRECTORY="/home/parsa/cufsm-mcp-test"
readonly REMOTE_PORT="8080"
readonly LOCAL_PORT="8081"
readonly MCP_ENDPOINT="http://127.0.0.1:${LOCAL_PORT}/mcp"

ssh_pid=""
job_token="cufsm-mcp-dev-${$}-$(date +%s)"
remote_pid_file="/tmp/${job_token}.pid"

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Required command is unavailable: $1" >&2
        exit 1
    fi
}

cleanup_remote_job() {
    # The allocated remote PTY normally delivers HUP and runs the remote trap.
    # This exact-PID fallback covers servers (such as uvicorn) that outlive it.
    ssh -T -o ConnectTimeout=5 "$SSH_TARGET" "
set -eu
pid_file='${remote_pid_file}'
test -f \"\$pid_file\" || exit 0
pid=\$(sed -n '1p' \"\$pid_file\")
case \"\$pid\" in (*[!0-9]*|'') exit 1;; esac
if test -d \"/proc/\$pid\"; then
    cwd=\$(readlink \"/proc/\$pid/cwd\")
    command=\$(tr '\\0' ' ' < \"/proc/\$pid/cmdline\")
    test \"\$cwd\" = '${REMOTE_DIRECTORY}'
    test \"\$command\" = '.venv/bin/python mcp/server.py '
    kill -TERM \"\$pid\" 2>/dev/null || true
    for delay in 1 2 3 4 5; do
        kill -0 \"\$pid\" 2>/dev/null || break
        sleep 1
    done
    if kill -0 \"\$pid\" 2>/dev/null; then
        kill -KILL \"\$pid\"
    fi
fi
rm -f -- \"\$pid_file\"
" </dev/null || echo "Warning: could not verify remote MCP cleanup." >&2
}

cleanup() {
    status=$?
    trap - EXIT HUP INT TERM
    if [[ -n "$ssh_pid" ]] && kill -0 "$ssh_pid" 2>/dev/null; then
        echo "Stopping the SSH tunnel and remote MCP development process..."
        kill -TERM "$ssh_pid" 2>/dev/null || true
        wait "$ssh_pid" 2>/dev/null || true
    fi
    cleanup_remote_job
    exit "$status"
}

trap cleanup EXIT HUP INT TERM

require_command python3
require_command ssh
require_command curl
if [[ "${CUFSM_MCP_DEV_NO_INSPECTOR:-0}" != "1" ]]; then
    require_command npx
fi

if python3 - "$LOCAL_PORT" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
    try:
        connection.bind(("127.0.0.1", port))
    except OSError:
        occupied = True
    else:
        occupied = False
raise SystemExit(0 if occupied else 1)
PY
then
    echo "Local port ${LOCAL_PORT} is already occupied; no process was stopped." >&2
    exit 1
fi

echo "Starting CUFSM MCP on ${SSH_TARGET} and forwarding local port ${LOCAL_PORT}..."
ssh -tt \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -L "127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" \
    "$SSH_TARGET" \
    "set -eu
cd '${REMOTE_DIRECTORY}'
env MCP_HOST=127.0.0.1 PORT='${REMOTE_PORT}' .venv/bin/python mcp/server.py &
remote_server_pid=\$!
printf '%s\\n' \"\$remote_server_pid\" > '${remote_pid_file}'
cleanup_remote() {
    kill -TERM \"\$remote_server_pid\" 2>/dev/null || true
    wait \"\$remote_server_pid\" 2>/dev/null || true
    rm -f -- '${remote_pid_file}'
}
trap cleanup_remote EXIT HUP INT TERM
wait \"\$remote_server_pid\"" </dev/null &
ssh_pid=$!

ready=0
for _attempt in {1..60}; do
    if ! kill -0 "$ssh_pid" 2>/dev/null; then
        wait "$ssh_pid" || true
        echo "SSH or the remote MCP server exited before becoming ready." >&2
        exit 1
    fi
    if curl --silent --fail --output /dev/null \
        --connect-timeout 1 \
        --max-time 2 \
        --header 'Content-Type: application/json' \
        --header 'Accept: application/json, text/event-stream' \
        --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"cufsm-dev-remote","version":"1"}}}' \
        "$MCP_ENDPOINT"; then
        ready=1
        break
    fi
    sleep 0.5
done

if [[ "$ready" != "1" ]]; then
    echo "Timed out waiting for ${MCP_ENDPOINT}." >&2
    exit 1
fi

echo "MCP endpoint: ${MCP_ENDPOINT}"

# Used only by automated verification to exercise startup and cleanup without
# opening the interactive Inspector. Normal development runs do not set it.
if [[ "${CUFSM_MCP_DEV_NO_INSPECTOR:-0}" == "1" ]]; then
    echo "Remote development tunnel verified; Inspector launch skipped by environment."
    exit 0
fi

echo "Launching MCP Inspector. Use the endpoint printed above."
npx @modelcontextprotocol/inspector
