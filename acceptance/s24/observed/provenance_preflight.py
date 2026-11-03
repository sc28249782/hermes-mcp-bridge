"""Unsigned policy preflight. Never a signed verifier or execution capability.

The closed projection models certificate fields from pinned sigstore-go source.
It deliberately does not accept raw gh output, bundles, caller auth booleans or
production classes. An authenticated adapter and tools are still UNBOUND.
"""

import hashlib
import json
import re


MAX_RECORD = 65536
MAX_OBJECT = 8 * 1024 * 1024  # Synthetic object comparison, not production limit.
ISSUER = "https://token.actions.githubusercontent.com"
PREDICATE = "https://slsa.dev/provenance/v1"
FIELDS = (
    "issuer", "subjectAlternativeName", "buildSignerURI", "buildSignerDigest",
    "runnerEnvironment", "sourceRepositoryURI", "sourceRepositoryDigest",
    "sourceRepositoryRef", "sourceRepositoryIdentifier", "sourceRepositoryOwnerURI",
    "sourceRepositoryOwnerIdentifier", "buildConfigURI", "buildConfigDigest",
    "buildTrigger", "runInvocationURI",
)
REASONS = frozenset({"INPUT", "SCHEMA", "CONTEXT", "CLAIM", "SUBJECT", "TOOL"})


class Hold(Exception):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else "INPUT"
        super().__init__()  # Never expose input, field value, path or exception text.


def require(condition, reason):
    if not condition:
        raise Hold(reason)


def _pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "INPUT")
        out[key] = value
    return out


def _reject(_):
    raise Hold("INPUT")


def _integer(value):
    require(len(value) <= 20, "INPUT")
    return int(value)


def record(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_RECORD, "INPUT")
    # Bound nesting before the JSON parser, without interpreting string braces.
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            require(depth <= 12, "INPUT")
        elif byte in (93, 125):
            depth -= 1
            require(depth >= 0, "INPUT")
    try:
        obj = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs,
                         parse_constant=_reject, parse_float=_reject,
                         parse_int=_integer)
    except Hold:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise Hold("INPUT") from None
    require(type(obj) is dict, "SCHEMA")
    return obj


def keys(obj, names):
    require(type(obj) is dict and set(obj) == set(names), "SCHEMA")


def digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            "SCHEMA")


def _text(value, pattern):
    require(type(value) is str and len(value) <= 512 and
            re.fullmatch(pattern, value) is not None, "SCHEMA")


def policy(raw):
    obj = record(raw)
    keys(obj, ("kind", "schema", "repository", "repository_id", "owner_id",
               "source_sha", "signer_sha", "workflow_sha", "ref", "workflow", "signer_workflow",
               "run_id", "attempt", "generation", "lock_sha256"))
    require(obj["kind"] == "j0-unsigned-preflight-policy" and
            type(obj["schema"]) is int and obj["schema"] == 1, "SCHEMA")
    _text(obj["repository"], r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
    for field in ("repository_id", "owner_id", "run_id", "attempt"):
        require(type(obj[field]) is int and 1 <= obj[field] <= 2**63-1, "SCHEMA")
    for field in ("source_sha", "signer_sha", "workflow_sha"):
        _text(obj[field], r"[0-9a-f]{40}")
    # This narrow preregistered profile only considers a dispatch from main.
    require(obj["ref"] == "refs/heads/main", "CONTEXT")
    for field in ("workflow", "signer_workflow"):
        _text(obj[field], r"\.github/workflows/[A-Za-z0-9_-]+\.ya?ml")
    _text(obj["generation"], r"[0-9a-f]{32}")
    digest(obj["lock_sha256"])
    return obj


def expected_certificate(p):
    repo = "https://github.com/" + p["repository"]
    signer = repo + "/" + p["signer_workflow"] + "@" + p["ref"]
    return dict(zip(FIELDS, (
        ISSUER, signer, signer, p["signer_sha"], "github-hosted", repo,
        p["source_sha"], p["ref"], str(p["repository_id"]),
        "https://github.com/" + p["repository"].split("/")[0], str(p["owner_id"]),
        repo + "/" + p["workflow"] + "@" + p["ref"], p["workflow_sha"],
        "workflow_dispatch", repo + "/actions/runs/" + str(p["run_id"]) +
        "/attempts/" + str(p["attempt"]),
    )))


def _object(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_OBJECT, "INPUT")
    return hashlib.sha256(raw).hexdigest()


def inspect_projection(projection, policy_raw, descriptor, ciphertext):
    """Compare UNSIGNED data only. Even a perfect match never authenticates it."""
    p = policy(policy_raw)
    d = record(descriptor)
    keys(d, ("kind", "schema", "generation", "lock_sha256", "run_id", "attempt",
             "ciphertext_sha256", "scope_granted"))
    require(d["kind"] == "j0-unsigned-preflight-descriptor" and
            type(d["schema"]) is int and d["schema"] == 1 and
            d["scope_granted"] is False, "SCHEMA")
    for field in ("run_id", "attempt"):
        require(type(d[field]) is int, "SCHEMA")
    for field in ("generation", "lock_sha256", "run_id", "attempt"):
        require(d[field] == p[field], "CONTEXT")
    digest(d["ciphertext_sha256"])
    cipher_digest = _object(ciphertext)
    require(d["ciphertext_sha256"] == cipher_digest, "SUBJECT")
    x = record(projection)
    keys(x, ("kind", "schema", "certificate", "predicate_type", "subjects"))
    require(x["kind"] == "j0-unsigned-certificate-projection" and
            type(x["schema"]) is int and x["schema"] == 1, "SCHEMA")
    keys(x["certificate"], FIELDS)
    expected = expected_certificate(p)
    require(all(type(x["certificate"][f]) is str and
                x["certificate"][f] == expected[f] for f in FIELDS), "CLAIM")
    require(x["predicate_type"] == PREDICATE, "CLAIM")
    keys(x["subjects"], ("descriptor", "ciphertext"))
    for value in x["subjects"].values():
        digest(value)
    require(x["subjects"] == {"descriptor": _object(descriptor),
                               "ciphertext": cipher_digest}, "SUBJECT")
    return {"state": "MATCHED_UNAUTHENTICATED", "projection_sha256": _object(projection),
            "descriptor_sha256": _object(descriptor), "ciphertext_sha256": cipher_digest,
            "provenance_authenticated": False, "tool_authenticated": False,
            "scope_granted": False, "secret_release_authorized": False,
            "j0_ready": False, "r1_complete": False, "r2_authorized": False}


def compare_tool_object(raw, expected_sha256, expected_size):
    """Fixture-size object equality only; provider metadata is not provenance."""
    digest(expected_sha256)
    require(type(expected_size) is int and 1 <= expected_size <= MAX_OBJECT, "TOOL")
    actual = _object(raw)
    require(len(raw) == expected_size and actual == expected_sha256, "TOOL")
    return {"state": "DIGEST_EQUAL_UNAUTHENTICATED", "sha256": actual,
            "tool_authenticated": False, "execution_authorized": False}
