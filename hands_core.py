"""Fail-closed, read-only Local Hands runtime for WSL2/Linux."""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
import errno
import fnmatch
import os
from pathlib import Path
import re
import stat
from typing import Any

from audit import AuditLog
from config_schema import ConfigError, load_bridge_config


class HandsError(RuntimeError):
    """A normalized Local Hands policy or availability error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_MAX_PATH_BYTES = 1024
_BASELINE_PATTERNS = (
    ".env*", "*.pem", "*.key", "*.p12", "*.pfx", "*.crt", "*.cer",
    "id_rsa*", "id_ed25519*", "credentials*.json", "service-account*.json",
)
_HOME_PROTECTED = (".ssh", ".aws", ".azure", ".config/gcloud", ".gnupg", ".kube")

# linux/openat2.h.  The syscall number is deliberately explicit: the runtime
# refuses a workspace on an unsupported ABI instead of falling back to a
# check-then-open path resolver.
_RESOLVE_NO_MAGICLINKS = 0x02
_RESOLVE_NO_SYMLINKS = 0x04
_RESOLVE_BENEATH = 0x08
_RESOLVE_FLAGS = _RESOLVE_BENEATH | _RESOLVE_NO_SYMLINKS | _RESOLVE_NO_MAGICLINKS
_SYS_OPENAT2 = {"x86_64": 437, "amd64": 437, "aarch64": 437, "arm64": 437}


class _OpenHow(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_ulonglong), ("mode", ctypes.c_ulonglong),
                ("resolve", ctypes.c_ulonglong)]


@dataclass
class _Workspace:
    name: str
    root_fd: int | None
    protected_prefixes: tuple[tuple[str, ...], ...]
    filesystem: str | None
    unavailable_reason: str | None = None


def _mount_filesystem(path: Path) -> str | None:
    """Return a non-sensitive mount type for diagnostics only."""
    try:
        lines = Path("/proc/self/mountinfo").read_text(errors="replace").splitlines()
    except OSError:
        return None
    candidate: tuple[int, str] | None = None
    text_path = str(path)
    for line in lines:
        left, marker, right = line.partition(" - ")
        fields = left.split()
        right_fields = right.split()
        if not marker or len(fields) < 5 or not right_fields:
            continue
        mountpoint = fields[4].replace("\\040", " ").replace("\\011", "\t")
        if text_path == mountpoint or text_path.startswith(mountpoint.rstrip("/") + "/"):
            if candidate is None or len(mountpoint) > candidate[0]:
                candidate = (len(mountpoint), right_fields[0])
    if not candidate:
        return None
    # WSL reports Windows-mounted drives as drvfs on some distributions and 9p
    # on others. Keep the observable category stable without exposing a path.
    if candidate[1] == "9p" and re.match(r"^/mnt/[A-Za-z](?:/|$)", text_path):
        return "drvfs"
    return candidate[1]


class HandsRuntime:
    """Read-only workspace operations; never imports or invokes Hermes/Codex."""

    def __init__(self, config: dict[str, Any] | None, state: Path,
                 audit_config: dict[str, Any] | None = None, config_warnings: list[str] | None = None):
        config = config or {}
        self.enabled = config.get("enabled", False)
        self.max_read_bytes = config.get("max_read_bytes", 65_536)
        self.max_read_chars = config.get("max_read_chars", 65_536)
        self.max_list_entries = config.get("max_list_entries", 200)
        self.config_warnings = list(config_warnings or [])
        self.audit = AuditLog(Path(state), audit_config)
        self._workspaces: dict[str, _Workspace] = {}
        if not self.enabled:
            return
        patterns = tuple(x.casefold() for x in (*_BASELINE_PATTERNS, *config.get("protected_name_patterns", [])))
        configured_paths = [Path(x).expanduser() for x in config.get("protected_paths", [])]
        baseline_paths = [Path.home() / item for item in _HOME_PROTECTED]
        protected_paths = [p.resolve(strict=False) for p in (*baseline_paths, *configured_paths)]
        for entry in config.get("workspaces", []):
            name = entry["name"]
            root_fd: int | None = None
            try:
                root = Path(entry["path"]).expanduser().resolve(strict=True)
                root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
                root_stat = os.fstat(root_fd)
                if not stat.S_ISDIR(root_stat.st_mode):
                    raise OSError(errno.ENOTDIR, "workspace root is not a directory")
                prefixes: list[tuple[str, ...]] = []
                for protected in protected_paths:
                    try:
                        relative = protected.relative_to(root)
                    except ValueError:
                        try:
                            root.relative_to(protected)
                        except ValueError:
                            continue
                        raise HandsError("policy_denied", "workspace overlaps a protected credential location")
                    if relative.parts:
                        prefixes.append(tuple(part.casefold() for part in relative.parts))
                    else:
                        raise HandsError("policy_denied", "workspace is a protected credential location")
                workspace = _Workspace(name, root_fd, tuple(prefixes), _mount_filesystem(root))
                self._strict_probe(workspace)
                # Preserve the compiled patterns once per runtime, avoiding a
                # configuration-controlled behavior change per request.
                workspace.patterns = patterns  # type: ignore[attr-defined]
                self._workspaces[name] = workspace
            except (HandsError, OSError, ValueError) as exc:
                if isinstance(root_fd, int):
                    try:
                        os.close(root_fd)
                    except OSError:
                        pass
                self._workspaces[name] = _Workspace(name, None, (), None,
                                                    "strict_resolver_unavailable" if isinstance(exc, OSError) else "policy_denied")

    @classmethod
    def from_config(cls, root: Path) -> "HandsRuntime":
        try:
            config, warnings = load_bridge_config(root)
        except ConfigError as exc:
            raise HandsError("invalid_config", "Local Hands configuration is invalid") from exc
        return cls(config.get("hands"), Path(root) / "state", config.get("audit"), warnings)

    @staticmethod
    def _openat2(dirfd: int, relative: str, flags: int) -> int:
        syscall_number = _SYS_OPENAT2.get(os.uname().machine.lower())
        if syscall_number is None:
            raise OSError(errno.ENOSYS, "openat2 ABI unavailable")
        encoded = relative.encode("utf-8")
        how = _OpenHow(flags=flags, mode=0, resolve=_RESOLVE_FLAGS)
        libc = ctypes.CDLL(None, use_errno=True)
        result = libc.syscall(syscall_number, dirfd, ctypes.c_char_p(encoded),
                              ctypes.byref(how), ctypes.sizeof(how))
        if result == -1:
            raise OSError(ctypes.get_errno(), "openat2 failed")
        return result

    def _strict_probe(self, workspace: _Workspace) -> None:
        if workspace.root_fd is None:
            raise OSError(errno.EBADF, "workspace descriptor unavailable")
        fd = self._openat2(workspace.root_fd, ".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            if not stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError(errno.ENOTDIR, "strict resolver root mismatch")
        finally:
            os.close(fd)

    @staticmethod
    def _clean_relative(value: str, *, allow_root: bool) -> tuple[str, tuple[str, ...]]:
        if not isinstance(value, str) or "\x00" in value or "\\" in value:
            raise HandsError("invalid_path", "path must be a relative POSIX path")
        if len(value.encode("utf-8")) > _MAX_PATH_BYTES or value.startswith("/"):
            raise HandsError("invalid_path", "path is outside the allowed format")
        if value in ("", "."):
            if allow_root:
                return ".", ()
            raise HandsError("invalid_path", "a file path is required")
        parts = tuple(value.split("/"))
        if any(part in ("", ".", "..") for part in parts):
            raise HandsError("invalid_path", "path traversal is not allowed")
        return "/".join(parts), parts

    @staticmethod
    def _workspace_name(value: str) -> str:
        if not isinstance(value, str) or not _NAME.fullmatch(value):
            raise HandsError("invalid_workspace", "workspace is invalid")
        return value

    def _require_workspace(self, name: str) -> _Workspace:
        if not self.enabled:
            raise HandsError("disabled", "Local Hands is disabled")
        workspace = self._workspaces.get(self._workspace_name(name))
        if not workspace:
            raise HandsError("not_found", "workspace is not configured")
        if workspace.root_fd is None:
            raise HandsError("unavailable", "workspace strict resolver is unavailable")
        return workspace

    @staticmethod
    def _is_protected(workspace: _Workspace, parts: tuple[str, ...]) -> bool:
        folded = tuple(part.casefold() for part in parts)
        if any(folded[:len(prefix)] == prefix for prefix in workspace.protected_prefixes):
            return True
        patterns = getattr(workspace, "patterns", ())
        return any(any(fnmatch.fnmatchcase(part, pattern) for pattern in patterns) for part in folded)

    def _open_relative(self, workspace: _Workspace, relative: str, flags: int) -> int:
        if workspace.root_fd is None:
            raise HandsError("unavailable", "workspace strict resolver is unavailable")
        try:
            return self._openat2(workspace.root_fd, relative, flags | os.O_CLOEXEC)
        except OSError as exc:
            if exc.errno in (errno.ENOENT, errno.ENOTDIR):
                raise HandsError("not_found", "path was not found") from exc
            if exc.errno in (errno.ELOOP, errno.EXDEV):
                raise HandsError("policy_denied", "path is not safely contained") from exc
            if exc.errno in (errno.ENOSYS, errno.EINVAL, errno.EPERM, errno.EOPNOTSUPP):
                raise HandsError("unavailable", "strict resolver is unavailable") from exc
            raise HandsError("unavailable", "path could not be opened safely") from exc

    @staticmethod
    def _entry_kind(mode: int) -> str | None:
        if stat.S_ISREG(mode):
            return "file"
        if stat.S_ISDIR(mode):
            return "directory"
        return None

    def health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "status": "disabled", "enabled": False, "workspaces": []}
        rows = []
        for name in sorted(self._workspaces):
            workspace = self._workspaces[name]
            row: dict[str, Any] = {"name": name, "status": "available" if workspace.root_fd is not None else "unavailable"}
            if workspace.filesystem:
                row["filesystem"] = workspace.filesystem
            if workspace.root_fd is None:
                row["reason"] = workspace.unavailable_reason or "unavailable"
            rows.append(row)
        available = any(row["status"] == "available" for row in rows)
        return {"ok": available, "status": "available" if available else "unavailable", "enabled": True,
                "workspaces": rows, "limits": {"max_read_bytes": self.max_read_bytes,
                                                   "max_read_chars": self.max_read_chars,
                                                   "max_list_entries": self.max_list_entries}}

    def local_status(self) -> dict[str, Any]:
        return {**self.health(), "upstream_checked": False}

    def diagnostics(self) -> dict[str, Any]:
        return {"local_hands": self.health(), "audit": self.audit.status(),
                "config_warnings": self.config_warnings}

    @staticmethod
    def _disabled_result() -> dict[str, Any]:
        return {"ok": False, "status": "disabled", "error_code": "disabled"}

    def list(self, workspace_name: str, path: str = "", limit: int = 100) -> dict[str, Any]:
        if not self.enabled:
            return self._disabled_result()
        workspace = self._require_workspace(workspace_name)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= self.max_list_entries:
            raise HandsError("limit_exceeded", "list limit is outside policy")
        relative, parts = self._clean_relative(path, allow_root=True)
        if self._is_protected(workspace, parts):
            raise HandsError("policy_denied", "path is protected")
        fd = self._open_relative(workspace, relative, os.O_RDONLY | os.O_DIRECTORY)
        try:
            names = os.listdir(fd)
        except OSError as exc:
            os.close(fd)
            raise HandsError("unavailable", "directory could not be listed safely") from exc
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
        folded = [name.casefold() for name in names]
        if len(set(folded)) != len(folded):
            raise HandsError("policy_denied", "directory has ambiguous case-colliding entries")
        entries = []
        skipped = 0
        for name in sorted(names, key=lambda x: (x.casefold(), x)):
            child_parts = (*parts, name)
            if self._is_protected(workspace, child_parts):
                skipped += 1
                continue
            child = name if relative == "." else relative + "/" + name
            try:
                child_fd = self._open_relative(workspace, child, getattr(os, "O_PATH", os.O_RDONLY) | os.O_NOFOLLOW)
                try:
                    info = os.fstat(child_fd)
                finally:
                    os.close(child_fd)
            except HandsError:
                skipped += 1
                continue
            kind = self._entry_kind(info.st_mode)
            if kind is None or (kind == "file" and info.st_nlink != 1):
                skipped += 1
                continue
            entries.append({"name": name, "kind": kind})
            if len(entries) == limit:
                break
        result = {"ok": True, "workspace": workspace.name, "path": "" if relative == "." else relative,
                  "entries": entries, "truncated": len(entries) == limit}
        self.audit.record("hands", "list", workspace.name, "ok", {"returned": len(entries), "skipped": skipped})
        return result

    def read(self, workspace_name: str, path: str) -> dict[str, Any]:
        if not self.enabled:
            return self._disabled_result()
        workspace = self._require_workspace(workspace_name)
        relative, parts = self._clean_relative(path, allow_root=False)
        if self._is_protected(workspace, parts):
            raise HandsError("policy_denied", "path is protected")
        fd = self._open_relative(workspace, relative, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise HandsError("policy_denied", "only single-link regular files may be read")
            if info.st_size > self.max_read_bytes:
                raise HandsError("limit_exceeded", "file exceeds the read limit")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(fd, min(65_536, self.max_read_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > self.max_read_bytes:
                    raise HandsError("limit_exceeded", "file exceeds the read limit")
            raw = b"".join(chunks)
        finally:
            os.close(fd)
        if b"\x00" in raw:
            raise HandsError("policy_denied", "binary files cannot be read")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HandsError("policy_denied", "file must be valid UTF-8 text") from exc
        if len(content) > self.max_read_chars:
            raise HandsError("limit_exceeded", "file exceeds the character limit")
        self.audit.record("hands", "read", workspace.name, "ok", {"bytes": len(raw)})
        return {"ok": True, "workspace": workspace.name, "path": relative, "content": content,
                "bytes": len(raw), "encoding": "utf-8"}
