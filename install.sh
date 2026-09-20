#!/usr/bin/env bash
set -euo pipefail
bridge_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
umask 077
cd "$bridge_dir"
if [[ "$(id -u)" == 0 ]]; then
  echo 'Run as your normal Hermes user (somchaip), without sudo.' >&2
  exit 1
fi
if command -v uv >/dev/null 2>&1; then
  if [[ ! -x .venv/bin/python ]]; then uv venv .venv; fi
  uv pip install --python .venv/bin/python -r requirements.txt
else
  if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
  # A pre-existing venv (including one created by uv) may have Python but no pip.
  if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    echo 'Installing pip into the bridge virtual environment...'
    if ! .venv/bin/python -m ensurepip --upgrade; then
      echo 'Could not bootstrap pip. On Ubuntu with Python 3.12, install python3.12-venv, then run:' >&2
      echo '  python3 -m venv --upgrade .venv' >&2
      echo '  bash install.sh' >&2
      exit 1
    fi
  fi
  .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path('bridge-config.json')
if not p.exists():
    hermes_root = Path.home()/'.hermes'
    p.write_text(json.dumps({'api_url':'http://127.0.0.1:8642',
                            'hermes_env':str(hermes_root/'.env'),
                            'hermes_config':str(hermes_root/'config.yaml'),
                            'audit': {'enabled':True, 'max_bytes':1000000, 'retention_files':7},
                            'codex': {'binary':'codex', 'allowed_workspaces':[],
                                      'max_prompt_chars':32000,
                                      'max_runtime_seconds':1800,
                                      'approval_ttl_seconds':3600}}, indent=2)+'\n')
    p.chmod(0o600)
else:
    data = json.loads(p.read_text())
    if 'codex' not in data:
        data['codex'] = {'binary':'codex', 'allowed_workspaces':[],
                         'max_prompt_chars':32000, 'max_runtime_seconds':1800,
                         'approval_ttl_seconds':3600}
        p.write_text(json.dumps(data, indent=2)+'\n')
        p.chmod(0o600)
    elif 'approval_ttl_seconds' not in data['codex']:
        data['codex']['approval_ttl_seconds'] = 3600
        p.write_text(json.dumps(data, indent=2)+'\n')
        p.chmod(0o600)
    if 'audit' not in data:
        data['audit'] = {'enabled':True, 'max_bytes':1000000, 'retention_files':7}
        p.write_text(json.dumps(data, indent=2)+'\n')
        p.chmod(0o600)
PY
chmod 700 bridge.sh
./bridge.sh doctor
echo 'Local bridge check passed. Next: configure Secure MCP Tunnel (docs/README-TH.md).'
echo 'For Codex/WSL2, edit codex.allowed_workspaces then run: ./bridge.sh codex-doctor'
