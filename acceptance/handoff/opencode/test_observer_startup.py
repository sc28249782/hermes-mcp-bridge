"""Actual owned startup and arbitration controls; no native/Dev capture."""
from dataclasses import asdict, replace
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from acceptance.handoff.opencode import observer_preflight as P, observer_startup as S
SOURCE = Path(__file__).resolve().parent


def setting():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int]+[ctypes.c_ulong]*4
    value = ctypes.c_int()
    if libc.prctl(37, ctypes.addressof(value), 0, 0, 0) != 0:
        raise AssertionError('fixture setting unavailable')
    return value.value


def kill_child(child):
    signal.pidfd_send_signal(child.pidfd, signal.SIGKILL)
    if not select.select([child.pidfd], [], [], 1)[0]:
        raise AssertionError('fixture actor did not die')


class StartupControls(unittest.TestCase):
    def trial(self, case='normal'):
        original_setting = setting()
        with tempfile.TemporaryDirectory(prefix='oa-startup-owned-') as directory:
            read, write = os.pipe2(os.O_CLOEXEC)
            rpid = os.fork()
            if rpid == 0:
                S._close_except((write,))
                try:
                    def timeout(*_):
                        raise P.Hold('BUDGET_EXHAUSTED')
                    signal.signal(signal.SIGALRM, timeout)
                    rootfd = os.open(directory, os.O_RDONLY|os.O_DIRECTORY)
                    dummy_r, dummy_w = os.pipe2(os.O_CLOEXEC)
                    issuer = P.FixtureIssuer(rootfd, 1)
                    binding = P.Binding('attempt_fixture','nonce_fixture',1,
                        hashlib.sha256((SOURCE/'observer_startup.py').read_bytes()).hexdigest(),
                        'b'*64,P.SCOPES,'fixture-owned-cleanup',time.monotonic(),time.monotonic()+40)
                    if case == 'unbound': binding = replace(binding, containment='UNBOUND')
                    if case == 'dev': binding = replace(binding, environment='dev')
                    if case == 'source': binding = replace(binding, source_sha256='c'*64)
                    issuer.register(binding, dummy_r)
                    native_emit, native_ack, native_go = S._emit, S.Startup._ack, S.Startup._go
                    native_retain = S.Startup._retain

                    def emitting(fd, value):
                        if value['kind'] == 'witness' and case == 'bad_nonce':
                            value = dict(value, nonce='foreign_fixture')
                        if value['kind'] == 'witness' and case == 'duplicate':
                            raw = (json.dumps(value,separators=(',',':')).encode()+b'\n')*2
                            os.write(fd, raw); return
                        if value['kind'] == 'final' and case == 'missing_final':
                            os._exit(91)
                        if value['kind'] == 'final' and case == 'bad_final':
                            value = dict(value, helper_reaped='true')
                        return native_emit(fd, value)

                    def ack(self, fd):
                        if case == 'stall_ack': return
                        if case == 's_before_ack':
                            kill_child(self.s)
                        if case == 'revoke':
                            self.issuer.revoke(self.ref)
                        if case == 'adoption_guard':
                            with mock.patch.object(S.signal, 'pidfd_send_signal', side_effect=AssertionError('foreign reaper signal')) as send:
                                try: S._signal(self.h, signal.SIGTERM)
                                except ChildProcessError: pass
                                else: raise AssertionError('adoption guard accepted before S death')
                                send.assert_not_called()
                        return native_ack(self, fd)

                    def retain(self, value):
                        if case == 's_before_retain':kill_child(self.s)
                        if case == 'pidfd_failure':
                            with mock.patch.object(S.os, 'pidfd_open', side_effect=OSError()):
                                return native_retain(self, value)
                        return native_retain(self, value)

                    def go(self, fd):
                        if case == 'owner_loss': kill_child(self.o)
                        native_go(self, fd)
                        if case in ('s_after_g','both_after_g'):
                            if not select.select([self._error_r], [], [], 1)[0] or os.read(self._error_r,1)!=b'W':
                                raise AssertionError('hung helper did not reach fixture body')
                            kill_child(self.s)
                            if case=='both_after_g':kill_child(self.o)

                    def hung(gate, output, error):
                        if S._byte(gate, time.monotonic()+1) != b'G':
                            raise P.Hold('CHANNEL_LOST')
                        signal.signal(signal.SIGTERM, signal.SIG_IGN)
                        if os.write(error,b'W') != 1: raise AssertionError('fixture witness lost')
                        while True: signal.pause()

                    def bad_proof(gate, output, error):
                        if S._byte(gate,time.monotonic()+1)!=b'G':raise P.Hold('CHANNEL_LOST')
                        os.write(output,b'BAD\n')

                    with mock.patch.object(S,'_emit',side_effect=emitting), \
                         mock.patch.object(S.Startup,'_ack',ack), \
                         mock.patch.object(S.Startup,'_go',go), \
                         mock.patch.object(S.Startup,'_retain',retain):
                        if case == 'claim_failure':
                            with mock.patch.object(P.os,'fsync',side_effect=OSError()):
                                result=S.Startup(issuer,binding.attempt_ref).run()
                        elif case in ('s_after_g','both_after_g'):
                            with mock.patch.object(S,'_helper',side_effect=hung):
                                result = S.Startup(issuer,binding.attempt_ref).run()
                        elif case == 'bad_proof':
                            with mock.patch.object(S,'_helper',side_effect=bad_proof):
                                result=S.Startup(issuer,binding.attempt_ref).run()
                        else:
                            startup=S.Startup(issuer,binding.attempt_ref,3.5 if case=='stall_ack' else 8)
                            result=startup.run()
                            if case == 'reuse':
                                try: startup.run()
                                except P.Hold as error:
                                    if error.reason!='ATTEMPT_CONSUMED':raise
                                else:raise AssertionError('stale startup object reused')
                    # Test-only cleanup oracle in this fresh isolated R process.
                    try: os.waitpid(-1,os.WNOHANG)
                    except ChildProcessError: no_children=True
                    else: raise AssertionError('fixture child remains')
                    payload = {'outcome':asdict(result),'no_children':no_children,
                               'claims':len(list(Path(directory).iterdir()))}
                    issuer.close();os.close(rootfd);os.close(dummy_r);os.close(dummy_w)
                    raw=json.dumps(payload,sort_keys=True).encode()+b'\n'
                    if len(raw)>4096 or os.write(write,raw)!=len(raw):os._exit(4)
                    os._exit(0)
                except BaseException as error:
                    os.write(write,json.dumps({'test_error':type(error).__name__}).encode()+b'\n')
                    os._exit(3)
            os.close(write);rfd=os.pidfd_open(rpid)
            try:
                self.assertTrue(select.select([rfd],[],[],15)[0],'fresh fixture R timed out')
                pid,status=os.waitpid(rpid,0);self.assertEqual(pid,rpid)
                raw=os.read(read,4096)
                self.assertEqual(os.waitstatus_to_exitcode(status),0,raw)
                self.assertEqual(os.read(read,1),b'')
                value=json.loads(raw);self.assertTrue(value['no_children'])
                self.assertEqual(setting(),original_setting)
                outcome=value['outcome']
                for name in ('capture_allowed','authorizes_actions','dev_observed','goal_verified'):
                    self.assertFalse(outcome[name])
                for private in ('nonce_fixture','attempt_fixture',directory,'b'*64):
                    self.assertNotIn(private,raw.decode())
                print(json.dumps({'kind':'owned-startup-result','case':case,**value},sort_keys=True),flush=True)
                return outcome,value['claims']
            finally:
                os.close(rfd);os.close(read)

    def test_actual_startup_orders_pidfd_ack_before_inert_g(self):
        r,claims=self.trial()
        self.assertEqual(r['state'],'FIXTURE_STARTUP_CONFIRMED')
        self.assertEqual(r['trace'],['CLAIM','SUBREAPER','OWNER','SUPERVISOR','WITNESS','PIDFD','ACK','ACKED','FIXTURE_G','FINAL'])
        self.assertTrue(r['original_final']);self.assertTrue(r['fixture_g_sent'])
        self.assertEqual(r['helper_reaped_by'],'S')
        self.assertTrue(r['stdout_eof']);self.assertTrue(r['stderr_eof'])
        self.assertEqual(r['actors_reaped'],2);self.assertEqual(claims,1)

    def test_unbound_containment_rejects_before_any_actor_or_claim(self):
        r,claims=self.trial('unbound')
        self.assertEqual(r['state'],'HOLD');self.assertEqual(r['trace'],[])
        self.assertEqual(claims,0);self.assertEqual(r['actors_reaped'],0)

    def test_dev_binding_cannot_select_fixture_positive_path(self):
        r,claims=self.trial('dev')
        self.assertEqual(r['reason'],'PRODUCTION_BINDINGS_UNBOUND')
        self.assertEqual(claims,0);self.assertFalse(r['fixture_g_sent'])

    def test_source_drift_consumes_claim_but_creates_no_actors(self):
        r,claims=self.trial('source')
        self.assertEqual(r['reason'],'SOURCE_CHANGED');self.assertEqual(claims,1)
        self.assertEqual(r['trace'],['CLAIM']);self.assertEqual(r['actors_reaped'],0)

    def test_wrong_nonce_rejects_before_ack_or_g(self):
        r,_=self.trial('bad_nonce')
        self.assertNotIn('ACK',r['trace']);self.assertFalse(r['fixture_g_sent'])
        self.assertFalse(r['original_final'])

    def test_duplicate_witness_does_not_open_g(self):
        r,_=self.trial('duplicate')
        self.assertFalse(r['fixture_g_sent']);self.assertFalse(r['original_final'])

    def test_supervisor_death_before_ack_allows_only_adopted_cleanup(self):
        r,_=self.trial('s_before_ack')
        self.assertFalse(r['fixture_g_sent']);self.assertEqual(r['state'],'UNKNOWN')
        self.assertEqual(r['helper_reaped_by'],'R');self.assertTrue(r['helper_exit_observed'])

    def test_owner_death_prevents_inert_g(self):
        r,_=self.trial('owner_loss')
        self.assertFalse(r['fixture_g_sent']);self.assertEqual(r['state'],'UNKNOWN')

    def test_revoke_after_witness_prevents_ack_and_g(self):
        r,_=self.trial('revoke')
        self.assertIn('PIDFD',r['trace']);self.assertNotIn('ACK',r['trace'])
        self.assertFalse(r['fixture_g_sent']);self.assertEqual(r['state'],'UNKNOWN')

    def test_pidfd_failure_has_no_retry_or_numeric_signal_fallback(self):
        r,_=self.trial('pidfd_failure')
        self.assertFalse(r['fixture_g_sent']);self.assertNotIn('ACK',r['trace'])
        self.assertEqual(r['reason'],'STOP_UNCONFIRMED')

    def test_helper_cleanup_guard_denies_while_s_is_alive(self):
        r,_=self.trial('adoption_guard')
        self.assertEqual(r['state'],'FIXTURE_STARTUP_CONFIRMED')
        self.assertEqual(r['helper_reaped_by'],'S')

    def test_real_s_death_after_inert_g_reaps_adopted_term_ignorer(self):
        r,_=self.trial('s_after_g')
        self.assertTrue(r['fixture_g_sent']);self.assertFalse(r['original_final'])
        self.assertEqual(r['state'],'UNKNOWN');self.assertEqual(r['helper_reaped_by'],'R')
        self.assertTrue(r['stdout_eof']);self.assertTrue(r['stderr_eof'])

    def test_s_reaped_h_but_missing_final_does_not_claim_observer_reap(self):
        r,_=self.trial('missing_final')
        self.assertTrue(r['helper_exit_observed']);self.assertFalse(r['original_final'])
        self.assertIsNone(r['helper_reaped_by']);self.assertEqual(r['state'],'UNKNOWN')

    def test_string_true_in_final_is_rejected(self):
        r,_=self.trial('bad_final')
        self.assertFalse(r['original_final']);self.assertEqual(r['state'],'UNKNOWN')

    def test_partial_claim_failure_is_reported_consumed_without_actors(self):
        r,claims=self.trial('claim_failure')
        self.assertEqual(r['reason'],'CLAIM_UNCONFIRMED')
        self.assertTrue(r['reservation_consumed']);self.assertEqual(claims,1)
        self.assertEqual(r['actors_reaped'],0);self.assertFalse(r['fixture_g_sent'])

    def test_reusing_startup_object_cannot_reuse_prior_final_or_go(self):
        r,claims=self.trial('reuse')
        self.assertEqual(r['state'],'FIXTURE_STARTUP_CONFIRMED')
        self.assertEqual(claims,1)

    def test_stalled_ack_hits_shared_capture_cutoff_without_go(self):
        r,_=self.trial('stall_ack')
        self.assertIn(r['reason'],('BUDGET_EXHAUSTED','ACTOR_LOST'))
        self.assertEqual(r['state'],'UNKNOWN');self.assertFalse(r['fixture_g_sent'])
        self.assertNotIn('ACKED',r['trace'])

    def test_wrong_actual_helper_proof_cannot_produce_final(self):
        r,_=self.trial('bad_proof')
        self.assertEqual(r['state'],'UNKNOWN');self.assertTrue(r['fixture_g_sent'])
        self.assertFalse(r['original_final'])

    def test_s_dead_before_capture_pidfd_can_bind_only_adopted_cleanup(self):
        r,_=self.trial('s_before_retain')
        self.assertFalse(r['fixture_g_sent']);self.assertNotIn('PIDFD',r['trace'])
        self.assertEqual(r['state'],'UNKNOWN');self.assertEqual(r['helper_reaped_by'],'R')

    def test_simultaneous_o_s_loss_after_inert_go_keeps_original_unknown(self):
        r,_=self.trial('both_after_g')
        self.assertTrue(r['fixture_g_sent']);self.assertFalse(r['original_final'])
        self.assertEqual(r['state'],'UNKNOWN');self.assertEqual(r['helper_reaped_by'],'R')

    def test_source_and_unchanged_dependency_manifest(self):
        m=json.loads((SOURCE/'observer-startup-hashes.json').read_bytes())
        for entry in m['source']+m['pinned_dependencies']:
            raw=(ROOT/entry['path']).read_bytes()
            self.assertEqual(len(raw),entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
        self.assertFalse(m['dev_observed']);self.assertFalse(m['authorizes_actions'])


if __name__=='__main__':unittest.main(verbosity=2)
