"""Independent scripted client-reference policy; NOT the main bridge runtime.

No candidate import, checkpoint checksum/store access or implicit dispatch.
Same complete human dossier/current observations as candidate, except checkpoint
integrity fields have no meaning in this reference client.
"""
from datetime import datetime


def decide(dossier, f):
    def result(action, reason=None, native=None, job=None):
        return dict(action=action, reason=reason, native_status=native,
                    job_id=job, authorizes_actions=False)
    task, backend = dossier['task'], dossier['backend']
    needed = {task['goal_ref'], *task['criteria_refs'], *task['pending_step_refs'],
              dossier['verification']['acceptance_profile_ref']}
    if not task['criteria_refs'] or not needed.issubset(f.resolved_refs) or (
            f.goal_ref != task['goal_ref'] or f.criteria_refs != frozenset(task['criteria_refs'])
            or f.acceptance_profile_ref != dossier['verification']['acceptance_profile_ref']):
        return result('hold', 'MISSING_DOSSIER')
    if f.authority_ref is None or f.authority_ref != dossier['authorization']['authority_ref'] or f.expires_at is None:
        return result('hold', 'AUTHORITY_UNAVAILABLE')
    if datetime.fromisoformat(f.now.replace('Z','+00:00')) >= datetime.fromisoformat(f.expires_at.replace('Z','+00:00')):
        return result('hold', 'AUTHORITY_EXPIRED')
    if 'scope_handoff_observe' not in f.scope_refs or not set(dossier['authorization']['scope_refs']).issubset(f.scope_refs):
        return result('hold', 'AUTHORITY_OUT_OF_SCOPE')
    if f.repository != dossier['repository'] or f.workspace_ref != backend['workspace_ref'] or not f.context_open:
        return result('hold', 'BINDING_MISMATCH')
    if backend['name'] == 'codex' and backend['job_id'] is None:
        return result('hold', 'JOB_ID_UNKNOWN')
    if backend['job_id'] is None and (backend['request_id'] is None or
            backend['input_ref'] not in f.resolved_refs or backend['input_fingerprint_ref'] not in f.resolved_refs):
        return result('hold', 'JOB_ID_UNKNOWN')
    job = f.job
    if job is None:
        return result('reconcile_original', 'RECONCILIATION_REQUIRED')
    if job['workspace_ref'] != backend['workspace_ref'] or any(
            job.get(k) != backend[k] for k in ('request_id','session_id','input_fingerprint_ref')) or (
            backend['job_id'] is not None and backend['job_id'] != job['job_id']):
        return result('hold', 'BINDING_MISMATCH')
    status, jid = job['status'], job['job_id']
    if status in ('unknown','unknown_exit','new_fixture_status'):
        native = 'unknown' if status == 'new_fixture_status' else status
        return result('reconcile_original','RECONCILIATION_REQUIRED',native,jid)
    if status in ('running','pending','queued','started','pending_local_approval','waiting_for_approval'):
        return result('observe_original',native=status,job=jid)
    if status != 'completed' or type(job['exit_code']) is not int or job['exit_code'] != 0 or not f.verifier_passed:
        return result('hold','VERIFIER_REJECTED',status,jid)
    if not f.required_evidence or not f.required_evidence.issubset(dossier['verification']['evidence_ids']):
        return result('hold','EVIDENCE_MISSING',status,jid)
    entries = {e['evidence_id']:e for e in dossier['evidence']}
    for eid in f.required_evidence:
        e = entries.get(eid)
        if e is None or e['verdict'] != 'verified' or f.evidence.get(eid) != (
                e['kind'],e['sha256'],e['size_bytes'],e['verifier_ref']):
            return result('hold','EVIDENCE_MISMATCH',status,jid)
    return result('done',native=status,job=jid)
