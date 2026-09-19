#!/usr/bin/env bash
set -euo pipefail
umask 077

bridge_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_root="${XDG_CONFIG_HOME:-$HOME/.config}/hermes-mcp-bridge"
key_file="$config_root/openai-runtime-api-key"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
unit_file="$unit_dir/hermes-mcp-tunnel.service"
unit_name="hermes-mcp-tunnel.service"

export PATH="$HOME/.local/bin:$PATH"

usage() {
  cat <<'EOF'
Usage:
  bash tunnel.sh init tunnel_YOUR_ID [--force]
  bash tunnel.sh run
  bash tunnel.sh status
  bash tunnel.sh key-set
  bash tunnel.sh key-status
  bash tunnel.sh key-clear
  bash tunnel.sh service-install
  bash tunnel.sh service-start|service-stop|service-restart|service-status
  bash tunnel.sh service-logs
  bash tunnel.sh service-uninstall

The OpenAI Platform runtime key is read from CONTROL_PLANE_API_KEY when set,
otherwise from ~/.config/hermes-mcp-bridge/openai-runtime-api-key (mode 600).
EOF
}

require_tunnel_client() {
  if ! command -v tunnel-client >/dev/null 2>&1; then
    echo 'Install the official OpenAI tunnel-client first; see README-TH.md.' >&2
    exit 1
  fi
}

require_safe_bridge_path() {
  case "$bridge_dir" in
    *[[:space:]]*) echo 'Place the bridge in a path without spaces before configuring the tunnel.' >&2; exit 1 ;;
  esac
}

key_set() {
  install -d -m 700 "$config_root"
  local temporary key_value
  IFS= read -rsp 'OpenAI Platform runtime API key (not the Hermes key): ' key_value
  printf '\n'
  if [[ -z "$key_value" || "$key_value" == *$'\n'* || "$key_value" == *$'\r'* ]]; then
    unset key_value
    echo 'Key must be non-empty and contain no newlines.' >&2
    exit 1
  fi
  temporary="$(mktemp "$config_root/.runtime-key.XXXXXX")"
  printf '%s' "$key_value" > "$temporary"
  unset key_value
  chmod 600 "$temporary"
  mv -f "$temporary" "$key_file"
  echo "Saved runtime key at $key_file (mode 600)."
}

key_status() {
  if [[ ! -f "$key_file" ]]; then
    echo "Runtime key is not saved. Run: bash tunnel.sh key-set"
    return 0
  fi
  local mode
  mode="$(stat -c '%a' "$key_file")"
  if [[ "$mode" != "600" ]]; then
    echo "Runtime key exists at $key_file but has mode $mode; run: chmod 600 '$key_file'" >&2
    return 1
  fi
  echo "Runtime key exists at $key_file with mode 600."
}

key_clear() {
  if [[ ! -f "$key_file" ]]; then
    echo 'Runtime key is already absent.'
    return 0
  fi
  if [[ ! -t 0 ]]; then
    echo 'Refusing to remove the runtime key without an interactive terminal.' >&2
    exit 1
  fi
  local confirmation
  read -rp "Type REMOVE to delete $key_file: " confirmation
  if [[ "$confirmation" != "REMOVE" ]]; then
    echo 'Runtime key was not removed.'
    return 0
  fi
  rm -f -- "$key_file"
  echo 'Runtime key removed.'
}

load_runtime_key() {
  if [[ -z "${CONTROL_PLANE_API_KEY:-}" && -r "$key_file" ]]; then
    CONTROL_PLANE_API_KEY="$(<"$key_file")"
    export CONTROL_PLANE_API_KEY
  fi
  if [[ -z "${CONTROL_PLANE_API_KEY:-}" ]]; then
    if [[ ! -t 0 ]]; then
      echo 'OpenAI Platform runtime API key is unavailable. Run: bash tunnel.sh key-set' >&2
      exit 1
    fi
    IFS= read -rsp 'OpenAI Platform runtime API key (not the Hermes key): ' CONTROL_PLANE_API_KEY
    printf '\n'
    export CONTROL_PLANE_API_KEY
  fi
  if [[ -z "$CONTROL_PLANE_API_KEY" || "$CONTROL_PLANE_API_KEY" == *$'\n'* || "$CONTROL_PLANE_API_KEY" == *$'\r'* ]]; then
    echo 'An OpenAI Platform runtime API key is required.' >&2
    exit 1
  fi
}

require_systemd_user() {
  if ! command -v systemctl >/dev/null 2>&1; then
    echo 'systemctl is not available in this WSL distribution.' >&2
    exit 1
  fi
  if ! systemctl --user show-environment >/dev/null 2>&1; then
    echo 'systemd user manager is unavailable. Enable systemd in WSL before using service commands.' >&2
    exit 1
  fi
}

write_unit() {
  require_safe_bridge_path
  install -d -m 700 "$unit_dir"
  local temporary
  temporary="$(mktemp "$unit_dir/.hermes-mcp-tunnel.XXXXXX")"
  printf '%s\n' '[Unit]' \
    'Description=Hermes Local Bridge Secure MCP Tunnel' \
    'After=network-online.target' \
    'Wants=network-online.target' \
    '' \
    '[Service]' \
    'Type=simple' \
    "WorkingDirectory=$bridge_dir" \
    "ExecStart=/bin/bash $bridge_dir/tunnel.sh run" \
    'Restart=on-failure' \
    'RestartSec=5' \
    'NoNewPrivileges=true' \
    'PrivateTmp=true' \
    '' \
    '[Install]' \
    'WantedBy=default.target' > "$temporary"
  chmod 600 "$temporary"
  mv -f "$temporary" "$unit_file"
}

service_install() {
  require_systemd_user
  if [[ ! -r "$key_file" && -z "${CONTROL_PLANE_API_KEY:-}" ]]; then
    echo 'Save a runtime key first: bash tunnel.sh key-set' >&2
    exit 1
  fi
  write_unit
  systemctl --user daemon-reload
  systemctl --user enable "$unit_name"
  echo "Installed and enabled $unit_name. Start it with: bash tunnel.sh service-start"
}

service_uninstall() {
  require_systemd_user
  systemctl --user disable --now "$unit_name" >/dev/null 2>&1 || true
  rm -f -- "$unit_file"
  systemctl --user daemon-reload
  echo "Removed $unit_name. The runtime key was kept."
}

command_name="${1:-run}"
case "$command_name" in
  -h|--help|help)
    usage
    ;;
  key-set)
    key_set
    ;;
  key-status)
    key_status
    ;;
  key-clear)
    key_clear
    ;;
  service-install)
    service_install
    ;;
  service-uninstall)
    service_uninstall
    ;;
  service-start|service-stop|service-restart|service-status)
    require_systemd_user
    systemctl --user "${command_name#service-}" "$unit_name"
    ;;
  service-logs)
    require_systemd_user
    journalctl --user -u "$unit_name" -n 100 --no-pager
    ;;
  init)
    require_tunnel_client
    require_safe_bridge_path
    load_runtime_key
    bridge_tunnel_id="${2:-}"
    init_force="${3:-}"
    if [[ ! "$bridge_tunnel_id" =~ ^tunnel_[A-Za-z0-9_-]+$ ]]; then
      echo 'Usage: bash tunnel.sh init tunnel_YOUR_ID [--force]' >&2
      exit 1
    fi
    if [[ -n "$init_force" && "$init_force" != "--force" ]]; then
      echo 'Usage: bash tunnel.sh init tunnel_YOUR_ID [--force]' >&2
      exit 1
    fi
    tunnel-client init --sample sample_mcp_stdio_local --profile hermes-wsl \
      --tunnel-id "$bridge_tunnel_id" --mcp-command "$bridge_dir/bridge.sh" ${init_force:+--force}
    tunnel-client doctor --profile hermes-wsl --explain
    exec tunnel-client run --profile hermes-wsl
    ;;
  run|status)
    require_tunnel_client
    require_safe_bridge_path
    load_runtime_key
    tunnel-client doctor --profile hermes-wsl --explain
    if [[ "$command_name" == "run" ]]; then
      exec tunnel-client run --profile hermes-wsl
    fi
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
