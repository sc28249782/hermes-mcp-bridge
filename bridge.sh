#!/usr/bin/env bash
set -euo pipefail
bridge_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
umask 077
exec "$bridge_dir/.venv/bin/python" "$bridge_dir/bridge.py" "$@"
