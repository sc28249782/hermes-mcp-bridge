"""Small, dependency-free validator for the private bridge configuration."""
from __future__ import annotations

import json
from pathlib import Path
import re


class ConfigError(ValueError):
    pass


def _object(value, label):
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be an object")
    return value


def _integer(value, label, low, high):
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise ConfigError(f"{label} must be an integer in {low}-{high}")


def _unknown(data, allowed, label, warnings):
    for key in sorted(set(data) - allowed):
        warnings.append(f"unknown configuration key ignored: {label}.{key}")


def load_bridge_config(root: Path) -> tuple[dict, list[str]]:
    path = Path(root) / "bridge-config.json"
    try:
        config = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError("bridge-config.json is missing or invalid JSON") from exc
    _object(config, "bridge-config")
    warnings = []
    version = config.get("schema_version")
    if version is None:
        warnings.append("legacy configuration without schema_version; treated as schema version 1")
    elif version != 1:
        raise ConfigError("unsupported schema_version; expected 1")
    _unknown(config, {"schema_version", "api_url", "hermes_env", "hermes_config", "hermes", "audit", "codex", "hands"},
             "bridge-config", warnings)
    for key in ("api_url", "hermes_env"):
        if not isinstance(config.get(key), str) or not config[key]:
            raise ConfigError(f"{key} must be a non-empty string")
    if "hermes_config" in config and not isinstance(config["hermes_config"], str):
        raise ConfigError("hermes_config must be a string")
    hermes = _object(config.get("hermes", {}), "hermes")
    _unknown(hermes, {"stale_run_seconds", "approval_stale_seconds"}, "hermes", warnings)
    for key in ("stale_run_seconds", "approval_stale_seconds"):
        if key in hermes:
            _integer(hermes[key], f"hermes.{key}", 1, 86400)
    audit = _object(config.get("audit", {}), "audit")
    _unknown(audit, {"enabled", "max_bytes", "retention_files"}, "audit", warnings)
    if "enabled" in audit and not isinstance(audit["enabled"], bool):
        raise ConfigError("audit.enabled must be boolean")
    for key, low, high in (("max_bytes", 32_768, 10_000_000), ("retention_files", 1, 30)):
        if key in audit:
            _integer(audit[key], f"audit.{key}", low, high)
    codex = _object(config.get("codex", {}), "codex")
    _unknown(codex, {"binary", "allowed_workspaces", "workspaces", "max_prompt_chars", "max_runtime_seconds",
                     "watchdog_interval_seconds", "approval_ttl_seconds", "allowed_models",
                     "allowed_reasoning_efforts"}, "codex", warnings)
    if "binary" in codex and (not isinstance(codex["binary"], str) or not codex["binary"]):
        raise ConfigError("codex.binary must be a non-empty string")
    for key, low, high in (("max_prompt_chars", 1, 32000), ("max_runtime_seconds", 1, 86400),
                           ("watchdog_interval_seconds", 5, 300), ("approval_ttl_seconds", 60, 86400)):
        if key in codex:
            _integer(codex[key], f"codex.{key}", low, high)
    for key in ("allowed_workspaces", "workspaces", "allowed_models", "allowed_reasoning_efforts"):
        if key in codex and not isinstance(codex[key], list):
            raise ConfigError(f"codex.{key} must be a list")
    for index, workspace in enumerate(codex.get("workspaces", [])):
        workspace = _object(workspace, f"codex.workspaces[{index}]")
        _unknown(workspace, {"path", "modes", "max_prompt_chars", "max_runtime_seconds", "max_concurrency",
                             "deny_prompt_patterns", "allowed_models", "allowed_reasoning_efforts"},
                 f"codex.workspaces[{index}]", warnings)
        if not isinstance(workspace.get("path"), str) or not workspace["path"]:
            raise ConfigError(f"codex.workspaces[{index}].path must be a non-empty string")
    hands = _object(config.get("hands", {}), "hands")
    _unknown(hands, {"enabled", "workspaces", "max_read_bytes", "max_read_chars",
                     "max_list_entries", "protected_name_patterns", "protected_paths"},
             "hands", warnings)
    if "enabled" in hands and not isinstance(hands["enabled"], bool):
        raise ConfigError("hands.enabled must be boolean")
    for key, low, high in (("max_read_bytes", 1024, 1_048_576),
                           ("max_read_chars", 1024, 1_048_576),
                           ("max_list_entries", 1, 1000)):
        if key in hands:
            _integer(hands[key], f"hands.{key}", low, high)
    for key in ("workspaces", "protected_name_patterns", "protected_paths"):
        if key in hands and not isinstance(hands[key], list):
            raise ConfigError(f"hands.{key} must be a list")
    for key in ("protected_name_patterns", "protected_paths"):
        for index, value in enumerate(hands.get(key, [])):
            if not isinstance(value, str) or not value or len(value) > 1024:
                raise ConfigError(f"hands.{key}[{index}] must be a non-empty string up to 1024 characters")
            if key == "protected_name_patterns" and ("/" in value or "\\\\" in value or "\\x00" in value):
                raise ConfigError(f"hands.{key}[{index}] must be a filename pattern")
    names, paths = set(), set()
    for index, workspace in enumerate(hands.get("workspaces", [])):
        workspace = _object(workspace, f"hands.workspaces[{index}]")
        _unknown(workspace, {"name", "path"}, f"hands.workspaces[{index}]", warnings)
        name, path_value = workspace.get("name"), workspace.get("path")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
            raise ConfigError(f"hands.workspaces[{index}].name is invalid")
        if not isinstance(path_value, str) or not path_value or len(path_value) > 4096:
            raise ConfigError(f"hands.workspaces[{index}].path must be a non-empty string up to 4096 characters")
        if name.casefold() in names:
            raise ConfigError("hands workspace names must be unique")
        names.add(name.casefold())
        canonical = str(Path(path_value).expanduser().resolve(strict=False))
        if canonical in paths:
            raise ConfigError("hands workspace paths must be unique")
        paths.add(canonical)
    if hands.get("enabled", False) and not hands.get("workspaces", []):
        raise ConfigError("hands.enabled requires at least one workspace")
    return config, warnings
