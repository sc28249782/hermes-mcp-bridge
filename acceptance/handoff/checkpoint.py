"""Offline-only v1 checkpoint validation/planning; no backend or input-path dereference."""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 65536
MAX_DEPTH = 16
SCHEMA_SHA = '3dc3f73a5d67f859c2f779e1f8bc9c49831420a4044f71de5f09aa71c241fadf'
ERRORS = frozenset(('INVALID_CHECKPOINT', 'CHECKSUM_MISMATCH', 'UNSUPPORTED_SCHEMA',
    'STALE_GENERATION', 'BINDING_MISMATCH', 'MISSING_DOSSIER', 'AUTHORITY_UNAVAILABLE',
    'AUTHORITY_EXPIRED', 'AUTHORITY_OUT_OF_SCOPE', 'JOB_ID_UNKNOWN', 'BACKEND_UNAVAILABLE',
    'RECONCILIATION_REQUIRED', 'EVIDENCE_MISSING', 'EVIDENCE_MISMATCH', 'VERIFIER_REJECTED',
    'CONCURRENT_UPDATE', 'STORE_UNAVAILABLE', 'BUDGET_EXHAUSTED'))


class Hold(Exception):
    def __init__(self, code='INVALID_CHECKPOINT'):
        self.code = code if code in ERRORS else 'INVALID_CHECKPOINT'
        super().__init__(self.code)


def need(value, code='INVALID_CHECKPOINT'):
    if not value:
        raise Hold(code)


def timestamp(value):
    # Explicit fail-closed RFC3339 subset: uppercase T/Z, <=6 fractional digits,
    # no leap seconds. No optional format-checker dependency or local timezone.
    need(type(value) is str and re.fullmatch(
        r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
        r'(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})', value))
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        need(result.tzinfo is not None)
        return result
    except ValueError:
        raise Hold() from None


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError):
        raise Hold() from None


def _pairs(values):
    result = {}
    for key, value in values:
        need(key not in result)
        result[key] = value
    return result


def _shape(value, depth=0):
    need(depth <= MAX_DEPTH)
    if type(value) is dict:
        for key, item in value.items():
            need(type(key) is str)
            _shape(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _shape(item, depth + 1)
    else:
        need(type(value) in (str, int, bool, type(None)))


def _matches(value, rule, schema):
    try:
        _check(value, rule, schema)
        return True
    except Hold:
        return False


def _check(value, rule, schema):
    """Only keywords present in the pinned approved schema; not a general engine."""
    if '$ref' in rule:
        _check(value, schema['$defs'][rule['$ref'].split('/')[-1]], schema)
    if 'const' in rule:
        need(type(value) is type(rule['const']) and value == rule['const'])
    if 'enum' in rule:
        need(any(type(value) is type(v) and value == v for v in rule['enum']))
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'null': type(None)}
    if 'type' in rule:
        need(type(value) is types[rule['type']])
    if type(value) is dict:
        need(all(k in value for k in rule.get('required', [])))
        if rule.get('additionalProperties') is False:
            need(set(value) <= set(rule['properties']))
        for key, child in rule.get('properties', {}).items():
            if key in value:
                _check(value[key], child, schema)
    if type(value) is list:
        need(rule.get('minItems', 0) <= len(value) <= rule.get('maxItems', MAX_BYTES))
        if rule.get('uniqueItems'):
            need(len({canonical(item) for item in value}) == len(value))
        for child in value:
            if 'items' in rule:
                _check(child, rule['items'], schema)
    if type(value) is str:
        need(len(value) <= rule.get('maxLength', MAX_BYTES))
        if 'pattern' in rule:
            need(re.fullmatch(rule['pattern'], value, re.ASCII) is not None)
        if rule.get('format') == 'date-time':
            timestamp(value)
    if type(value) is int:
        need(rule.get('minimum', -9007199254740991) <= value <= rule.get('maximum', 9007199254740991))
    if 'anyOf' in rule:
        need(any(_matches(value, r, schema) for r in rule['anyOf']))
    for child in rule.get('allOf', []):
        if 'if' in child:
            branch = 'then' if _matches(value, child['if'], schema) else 'else'
            _check(value, child.get(branch, {}), schema)
        else:
            _check(value, child, schema)


def validate(raw):
    """Return a fresh parsed envelope; does not read a checkpoint path or runtime DB."""
    need(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES)
    try:
        envelope = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                              parse_constant=lambda _v: (_ for _ in ()).throw(Hold()))
        _shape(envelope)
        need(type(envelope) is dict)
        need(type(envelope.get('schema_version')) is int and envelope['schema_version'] == 1,
             'UNSUPPORTED_SCHEMA')
        schema_bytes = Path(__file__).resolve().parents[2].joinpath(
            'docs/schemas/handoff-checkpoint-v1.schema.json').read_bytes()
        need(hashlib.sha256(schema_bytes).hexdigest() == SCHEMA_SHA)
        schema = json.loads(schema_bytes)
        _check(envelope, schema, schema)
        need(hashlib.sha256(canonical(envelope['payload'])).hexdigest() == envelope['payload_sha256'],
             'CHECKSUM_MISMATCH')
        p = envelope['payload']
        ids = [e['evidence_id'] for e in p['evidence']]
        need(len(set(ids)) == len(ids))
        need(set(p['verification']['evidence_ids']) <= set(ids), 'EVIDENCE_MISSING')
        return envelope
    except Hold:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OSError):
        raise Hold() from None


@dataclass(frozen=True)
class Facts:
    """Trusted fixture/caller observations, never constructed from checkpoint claims.

    No resolver/callback/adapter is invoked. A production collector is NOT supplied.
    """
    head: tuple
    repository: dict
    resolved_refs: frozenset
    authority_ref: str | None
    scope_refs: frozenset
    expires_at: str | None
    now: str
    backend: str
    workspace_ref: str | None
    job: dict | None
    context_open: bool
    evidence: dict
    required_evidence: frozenset
    verifier_passed: bool
    goal_ref: str
    criteria_refs: frozenset
    acceptance_profile_ref: str


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str | None = None
    native_status: str | None = None
    job_id: str | None = None
    authorizes_actions: bool = False


def plan(raw, facts):
    """Pure advisory decision; no submit/replay/resume/cancel/status/result call."""
    envelope = validate(raw)
    p = envelope['payload']
    b = p['backend']
    status = None
    job_id = None
    try:
        need(type(facts) is Facts)
        need(type(facts.repository) is dict and type(facts.resolved_refs) is frozenset
             and type(facts.scope_refs) is frozenset and type(facts.required_evidence) is frozenset
             and type(facts.evidence) is dict and (facts.job is None or type(facts.job) is dict))
        need(facts.head == (p['chain_id'], p['generation'], envelope['payload_sha256']), 'STALE_GENERATION')
        dossier = {p['task']['goal_ref'], p['verification']['acceptance_profile_ref'],
                   *p['task']['criteria_refs'], *p['task']['pending_step_refs']}
        need(p['task']['criteria_refs'] and dossier <= facts.resolved_refs
             and p['task']['goal_ref'] == facts.goal_ref
             and frozenset(p['task']['criteria_refs']) == facts.criteria_refs
             and p['verification']['acceptance_profile_ref'] == facts.acceptance_profile_ref, 'MISSING_DOSSIER')
        need(facts.authority_ref is not None and facts.authority_ref == p['authorization']['authority_ref']
             and facts.expires_at is not None, 'AUTHORITY_UNAVAILABLE')
        need(timestamp(facts.now) < timestamp(facts.expires_at), 'AUTHORITY_EXPIRED')
        need('scope_handoff_observe' in facts.scope_refs and
             set(p['authorization']['scope_refs']) <= facts.scope_refs, 'AUTHORITY_OUT_OF_SCOPE')
        need(facts.repository == p['repository'] and facts.repository['worktree_state'] != 'unknown',
             'BINDING_MISMATCH')
        need(facts.repository['worktree_state'] != 'dirty' or facts.repository['dirty_manifest_ref'] is not None,
             'BINDING_MISMATCH')
        need(facts.backend == b['name'] and facts.workspace_ref == b['workspace_ref'] and facts.context_open is True,
             'BINDING_MISMATCH')
        if b['name'] in ('none', 'local_hands'):
            return Decision('hold', 'JOB_ID_UNKNOWN')
        if b['name'] == 'codex' and b['job_id'] is None:
            return Decision('hold', 'JOB_ID_UNKNOWN')
        if b['job_id'] is None:
            need(b['request_id'] is not None and b['input_ref'] in facts.resolved_refs
                 and b['input_fingerprint_ref'] in facts.resolved_refs, 'JOB_ID_UNKNOWN')
        if facts.job is None:
            return Decision('reconcile_original', 'RECONCILIATION_REQUIRED')
        job = facts.job
        need(job.get('workspace_ref') == b['workspace_ref'], 'BINDING_MISMATCH')
        for key in ('request_id', 'session_id', 'input_fingerprint_ref'):
            need(job.get(key) == b[key], 'BINDING_MISMATCH')
        need(b['job_id'] is None or b['job_id'] == job.get('job_id'), 'BINDING_MISMATCH')
        observed_id = job.get('job_id')
        need(type(observed_id) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', observed_id),
             'BINDING_MISMATCH')
        job_id = observed_id
        status = job.get('status')
        allowed = {
            'hermes': {'pending', 'queued', 'started', 'running', 'waiting_for_approval', 'completed', 'failed', 'cancelled', 'unknown'},
            'codex': {'pending_local_approval', 'queued', 'running', 'completed', 'failed', 'cancelled', 'denied', 'expired', 'timed_out', 'unknown_exit'},
            'opencode': {'pending', 'running', 'completed', 'failed', 'cancelled', 'permission_required', 'unknown_exit'}}
        if status not in allowed[b['name']]:
            return Decision('reconcile_original', 'RECONCILIATION_REQUIRED', 'unknown', job_id)
        if status in ('unknown', 'unknown_exit'):
            return Decision('reconcile_original', 'RECONCILIATION_REQUIRED', status, job_id)
        if status in ('running', 'queued', 'pending', 'started', 'pending_local_approval', 'waiting_for_approval'):
            return Decision('observe_original', None, status, job_id)
        need(status == 'completed' and job.get('exit_code') == 0
             and type(job.get('exit_code')) is int and facts.verifier_passed is True, 'VERIFIER_REJECTED')
        need(facts.required_evidence and facts.required_evidence <= set(p['verification']['evidence_ids']),
             'EVIDENCE_MISSING')
        indexed = {e['evidence_id']: e for e in p['evidence']}
        for eid in facts.required_evidence:
            e = indexed[eid]
            observed = facts.evidence.get(eid)
            need(type(observed) is tuple and e['verdict'] == 'verified' and
                 canonical(list(observed)) == canonical([e['kind'], e['sha256'], e['size_bytes'], e['verifier_ref']]),
                 'EVIDENCE_MISMATCH')
        return Decision('done', None, status, job_id)
    except Hold as error:
        return Decision('hold', error.code, status if isinstance(status, str) else None, job_id)
    except (KeyError, TypeError, ValueError):
        return Decision('hold', 'BINDING_MISMATCH')
