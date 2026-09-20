"""Redacted, rotating audit records for local bridge operations."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


class AuditError(ValueError):
    pass


class AuditLog:
    """Single-user JSONL audit log. Callers must never pass prompts or output."""

    def __init__(self, state: Path, config: dict | None = None):
        config = config or {}
        if not isinstance(config, dict):
            raise AuditError("audit configuration must be an object")
        self.enabled = config.get("enabled", True)
        self.max_bytes = config.get("max_bytes", 1_000_000)
        self.retention_files = config.get("retention_files", 7)
        if not isinstance(self.enabled, bool):
            raise AuditError("audit.enabled must be true or false")
        if not isinstance(self.max_bytes, int) or not 32_768 <= self.max_bytes <= 10_000_000:
            raise AuditError("audit.max_bytes must be 32768-10000000")
        if not isinstance(self.retention_files, int) or not 1 <= self.retention_files <= 30:
            raise AuditError("audit.retention_files must be 1-30")
        self.path = Path(state) / "audit.jsonl"

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "path": str(self.path),
            "max_bytes": self.max_bytes,
            "retention_files": self.retention_files,
            "exists": self.path.is_file(),
        }

    def _rotate(self) -> None:
        if not self.path.exists() or self.path.stat().st_size < self.max_bytes:
            return
        for number in range(self.retention_files, 0, -1):
            old = self.path.with_name(f"{self.path.name}.{number}")
            if number == self.retention_files:
                old.unlink(missing_ok=True)
            else:
                newer = self.path.with_name(f"{self.path.name}.{number + 1}")
                if old.exists():
                    os.replace(old, newer)
        os.replace(self.path, self.path.with_name(f"{self.path.name}.1"))

    def record(self, component: str, action: str, subject: str, outcome: str,
               details: dict[str, Any] | None = None) -> None:
        """Append an event. Deliberately accepts only caller-selected metadata."""
        if not self.enabled:
            return
        if not all(isinstance(value, str) and value for value in (component, action, subject, outcome)):
            raise AuditError("audit event labels must be non-empty strings")
        if details is not None and not isinstance(details, dict):
            raise AuditError("audit details must be an object")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._rotate()
        event = {
            "schema": 1,
            "time": datetime.now(timezone.utc).isoformat(),
            "component": component,
            "action": action,
            "subject": subject,
            "outcome": outcome,
            "details": details or {},
        }
        encoded = (json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.fchmod(fd, 0o600)
            os.write(fd, encoded)
        finally:
            os.close(fd)
