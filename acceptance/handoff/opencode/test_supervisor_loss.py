"""Post-spawn supervisor SIGKILL controls; isolated disposable subreaper only.

No production recovery/observer interface. The test-owned observer temporarily
adopts only its new fixture descendants; no host-wide process enumeration or kill.
"""
import contextlib
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from acceptance.handoff.opencode import supervision as S
from acceptance.handoff.opencode import test_supervision as previous

SOURCE = Path(__file__).resolve().parent
LIB = Path('/lib/x86_64-linux-gnu/libsqlite3.so.0')

LOSS_C = r'''
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv) {
 if(argc!=5 || strcmp(argv[1],"--batch"))return 90;
 if(MODE!=3)signal(SIGTERM,SIG_IGN);
 if(MODE!=2) {char b[512];while(read(0,b,sizeof(b))>0){} }
 if(MODE==1) {
  const unsigned char prefix[]={0,0,0,12,'O','C','S','N','A','P','1',0,2,2,5,5};
  if(write(1,prefix,sizeof(prefix))!=(ssize_t)sizeof(prefix))return 91;
 }
 int fd=openat(atoi(argv[4]),"witness",O_WRONLY|O_NONBLOCK|O_NOFOLLOW);
 if(fd<0 || write(fd,"W",1)!=1)return 92;
 close(fd);
 for(;;)pause();
}
'''


def subreaper(value=None):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int] + [ctypes.c_ulong]*4
    libc.prctl.restype = ctypes.c_int
    if value is not None and libc.prctl(36, int(value), 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'fixture subreaper unavailable')
    result = ctypes.c_int()
    if libc.prctl(37, ctypes.addressof(result), 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'fixture subreaper query failed')
    return result.value


def ready(fd, deadline):
    return bool(select.select([fd], [], [], max(0, deadline-time.monotonic()))[0])


def exact(fd, size, deadline):
    raw = bytearray()
    while len(raw) < size:
        if not ready(fd, deadline):
            raise AssertionError('private fixture handshake timeout')
        chunk = os.read(fd, size-len(raw))
        if not chunk:
            raise AssertionError('private fixture handshake EOF')
        raw.extend(chunk)
    return bytes(raw)


def direct_child(pid):
    # A successful WNOWAIT call, including None for a running child, proves
    # direct-child eligibility in this isolated observer. ECHILD denies cleanup.
    return os.waitid(os.P_PID, pid, os.WEXITED|os.WNOHANG|os.WNOWAIT)


def adopted_stop(pid, pidfd, deadline):
    direct_child(pid)
    used = []
    for sig, grace in ((signal.SIGTERM, 0.2), (signal.SIGKILL, 1.0)):
        if ready(pidfd, time.monotonic()):
            break
        direct_child(pid)
        signal.pidfd_send_signal(pidfd, sig)
        used.append(sig.name)
        if ready(pidfd, min(deadline, time.monotonic()+grace)):
            break
    if not ready(pidfd, time.monotonic()):
        raise AssertionError('fixture adopted stop UNCONFIRMED')
    actual, status = os.waitpid(pid, 0)
    if actual != pid:
        raise AssertionError('wrong fixture child reaped')
    return used, os.waitstatus_to_exitcode(status)


def case_body(directory, binary, phase):
    """Runs only after fork in a new test observer process; never in host owner."""
    if subreaper(True) != 1:
        raise AssertionError('isolated observer is not subreaper')
    started = time.monotonic()
    deadline = started+12
    identity_r, identity_w = os.pipe2(os.O_CLOEXEC)
    gate_r, gate_w = os.pipe2(os.O_CLOEXEC)
    final_r, final_w = os.pipe2(os.O_CLOEXEC)
    helper_pipes = [os.pipe2(os.O_CLOEXEC) for _ in range(3)]
    capture_readers = [helper_pipes[1][0], helper_pipes[2][0]]
    native_spawn, native_report = S._spawn, S._report
    native_close = previous.close_other_fds
    a = None
    helper_pid = helperfd = None
    helper_reaped = False
    extra = []
    result = None

    def close_with_test_channels(keep):
        # Owner gets no extra channel. Only the fresh supervisor keeps the
        # private launch witness/barrier; helper exec closes them via fd 0..6.
        channels = {identity_w, gate_r, final_w, *(fd for pair in helper_pipes for fd in pair)}
        native_close(keep | (channels if len(keep) > 2 else set()))

    def witnessed_spawn(*args):
        # Pre-created ordinary pipes allow the independent test observer to
        # retain read ends only. No SCM_RIGHTS/socket/pidfd_getfd is needed.
        with mock.patch.object(S.os, 'pipe2', side_effect=iter(helper_pipes)):
            child, streams = native_spawn(*args)
        if os.write(identity_w, struct.pack('!I', child)) != 4:
            raise AssertionError('private identity write failed')
        os.close(identity_w)
        if phase == 'post_spawn':
            # Actual fork/exec path completed, but no READY/pidfd acquisition.
            # Pause only this new fixture supervisor, never a backend worker.
            if exact(gate_r, 1, deadline) != b'G':
                raise AssertionError('bad fixture gate')
        return child, streams

    def report_at_boundary(fd, value):
        if phase == 'pre_final' and value['event'] == 'FINAL':
            if value['reason'] != 'CAPTURE_COMPLETE' or value['helper_reaped'] is not True or value['pipes_eof'] is not True:
                raise AssertionError('pre-final control did not reach actual capture completion')
            if os.write(final_w, b'F') != 1:
                raise AssertionError('private final boundary unavailable')
            # Source has reaped the native helper but no FINAL was emitted.
            exact(gate_r, 1, deadline)
        return native_report(fd, value)

    try:
        with mock.patch.object(previous, 'close_other_fds', side_effect=close_with_test_channels), \
             mock.patch.object(S, '_spawn', side_effect=witnessed_spawn), \
             mock.patch.object(S, '_report', side_effect=report_at_boundary):
            a = previous.Attempt(directory, binary, lifetime=8)
        for fd in (identity_w, gate_r, final_w):
            os.close(fd)
        for fd in (helper_pipes[0][0], helper_pipes[0][1], helper_pipes[1][1], helper_pipes[2][1]):
            os.close(fd)
        extra = [identity_r, gate_w, final_r, *capture_readers]
        a.send(b'A')
        helper_pid = struct.unpack('!I', exact(identity_r, 4, deadline))[0]
        # Trusted test witness only, while the original parent is live and has
        # not reaped this child. Raw PID never authorizes a signal or publication.
        helperfd = os.pidfd_open(helper_pid)
        with mock.patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('must not signal')) as send:
            try:
                adopted_stop(helper_pid, helperfd, deadline)
            except ChildProcessError:
                denied_before_adoption = True
            else:
                raise AssertionError('unexpected adoption before supervisor death')
            send.assert_not_called()
        if phase != 'post_spawn':
            a.event('READY')
        if phase in ('hung', 'prefix', 'blocked', 'term', 'both', 'pre_final'):
            a.capture()
            if phase == 'pre_final':
                if exact(final_r, 1, deadline) != b'F':
                    raise AssertionError('missing pre-final boundary')
            else:
                a.active()
        if phase == 'both':
            signal.pidfd_send_signal(a.ownerfd, signal.SIGKILL)
            if a.reap(a.owner, a.ownerfd) != -signal.SIGKILL:
                raise AssertionError('owner not killed')
        signal.pidfd_send_signal(a.supervisorfd, signal.SIGKILL)
        if a.reap(a.supervisor, a.supervisorfd) != -signal.SIGKILL:
            raise AssertionError('supervisor not killed')

        # The original report pipe must end without FINAL. Any partial frames,
        # READY/CAPTURE, or privately witnessed pre-FINAL do not become a receipt.
        report = bytearray(a.pending)
        while True:
            if not ready(a.report, deadline):
                raise AssertionError('report pipe EOF UNCONFIRMED')
            raw = os.read(a.report, 4096)
            if not raw:
                break
            report.extend(raw)
            if len(report) > 4096:
                raise AssertionError('fixture report over cap')
        reports = a.messages + [json.loads(line) for line in report.splitlines()]
        if any(item['event'] == 'FINAL' for item in reports):
            raise AssertionError('unexpected FINAL after killed supervisor')

        if phase == 'pre_final':
            # Already reaped by supervisor, so observer must not claim adoption
            # or use numeric-PID cleanup against a now-unowned identity.
            if not ready(helperfd, deadline):
                raise AssertionError('previously reaped helper not exited')
            try:
                direct_child(helper_pid)
            except ChildProcessError:
                pass
            else:
                raise AssertionError('already reaped helper unexpectedly adopted')
            used, code, adopted = [], None, False
            helper_reaped = True  # Test cleanup has no child to reap; not observer evidence.
        else:
            direct_child(helper_pid)
            adopted = True
            if phase in ('post_spawn', 'idle'):
                # Idle native helper should see pipe EOF and exit on its own.
                if not ready(helperfd, min(deadline, time.monotonic()+1)):
                    raise AssertionError('idle native helper failed to exit after EOF')
            elif ready(helperfd, time.monotonic()):
                raise AssertionError('hung fixture unexpectedly ceased with supervisor')
            used, code = adopted_stop(helper_pid, helperfd, min(deadline, time.monotonic()+1.5))
            helper_reaped = True

        # EOF on helper stdout/stderr is observed independently, separately from
        # the original report-pipe EOF and from child exit/reap.
        for reader, cap in zip(capture_readers, (65536, 4096)):
            total = 0
            while True:
                if not ready(reader, deadline):
                    raise AssertionError('helper pipe EOF UNCONFIRMED')
                raw = os.read(reader, 4096)
                if not raw:
                    break
                total += len(raw)
                if total > cap:
                    raise AssertionError('helper stream exceeded fixture cap')

        # With the one known helper gone, no fixture descendant may remain.
        # ECHILD is a cleanup oracle only within this fresh isolated test observer.
        if a.owner not in a.reaped:
            signal.pidfd_send_signal(a.ownerfd, signal.SIGKILL)
            a.reap(a.owner, a.ownerfd)
        try:
            os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            no_children = True
        else:
            raise AssertionError('unreaped or live fixture descendant remains')
        result = dict(disposition='UNKNOWN', final_received=False, report_eof=True,
                      helper_pipes_eof=True,
                      supervisor_reaped=True, adoption_guard_denied=denied_before_adoption,
                      helper_adopted=adopted, helper_reaped_by_observer=adopted and helper_reaped,
                      helper_exit_observed=True, cleanup_signals=used, helper_exit=code,
                      no_children=no_children, authorizes_actions=False, dev_observed=False,
                      goal_verified=False, elapsed_ms=int((time.monotonic()-started)*1000))
        return result
    finally:
        # Cleanup authority belongs only to this isolated test observer.
        if a is not None:
            if a.supervisor not in a.reaped:
                signal.pidfd_send_signal(a.supervisorfd, signal.SIGKILL)
                a.reap(a.supervisor, a.supervisorfd)
            if helperfd is not None and not helper_reaped:
                try:
                    adopted_stop(helper_pid, helperfd, min(deadline, time.monotonic()+1.5))
                except ChildProcessError:
                    pass
            a.close()
        if helperfd is not None:
            os.close(helperfd)
        for fd in extra:
            os.close(fd)


class SupervisorLossControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='oc-loss-build-')
        cls.build = Path(cls.temp.name)
        cls.helpers = {}
        for key, source, flags in [('native', SOURCE/'oc_snapshot_vfs.c', [str(LIB)])]:
            binary = cls.build/key
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                            str(source), *flags, '-o', str(binary)], check=True, capture_output=True)
            binary.chmod(0o700); cls.helpers[key] = binary
        fixture = cls.build/'loss.c'; fixture.write_text(LOSS_C)
        for mode in range(4):
            binary = cls.build/str(mode)
            subprocess.run(['cc', '-D_GNU_SOURCE', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-O2', '-DMODE='+str(mode), str(fixture), '-o', str(binary)],
                           check=True, capture_output=True)
            binary.chmod(0o700); cls.helpers[mode] = binary
        print(json.dumps({'kind': 'owned-supervisor-loss-build-facts', 'dev_observed': False,
                          'helper_hashes': {str(k): hashlib.sha256(p.read_bytes()).hexdigest()
                                            for k,p in cls.helpers.items()}}), flush=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_case(self, phase, helper='native'):
        parent_setting = subreaper()
        with tempfile.TemporaryDirectory(prefix='oc-loss-case-') as directory:
            read, write = os.pipe2(os.O_CLOEXEC)
            observer = os.fork()
            if observer == 0:
                previous.close_other_fds({write})
                try:
                    def expired(_sig, _frame):
                        raise TimeoutError('test observer deadline')
                    signal.signal(signal.SIGALRM, expired)
                    signal.setitimer(signal.ITIMER_REAL, 20)
                    result = case_body(directory, self.helpers[helper], phase)
                    raw = json.dumps(result, sort_keys=True).encode()+b'\n'
                    if len(raw) > 2048 or os.write(write, raw) != len(raw):
                        os._exit(4)
                    os._exit(0)
                except BaseException as error:
                    # Only exception class; no paths/native IDs/raw private data.
                    os.write(write, json.dumps({'test_error': type(error).__name__}).encode()+b'\n')
                    os._exit(3)
            os.close(write)
            observerfd = os.pidfd_open(observer)
            try:
                self.assertTrue(ready(observerfd, time.monotonic()+22), 'isolated observer exceeded budget')
                actual, status = os.waitpid(observer, 0)
                self.assertEqual(actual, observer)
                raw = os.read(read, 4096)
                self.assertEqual(os.waitstatus_to_exitcode(status), 0, raw)
                self.assertEqual(os.read(read, 1), b'')
                result = json.loads(raw)
                self.assertEqual(result['disposition'], 'UNKNOWN')
                self.assertFalse(result['final_received'])
                self.assertTrue(result['report_eof'])
                self.assertTrue(result['helper_pipes_eof'])
                self.assertTrue(result['supervisor_reaped'])
                self.assertTrue(result['adoption_guard_denied'])
                self.assertTrue(result['no_children'])
                self.assertLess(result['elapsed_ms'], 12000)
                for name in ('authorizes_actions', 'dev_observed', 'goal_verified'):
                    self.assertFalse(result[name])
                self.assertNotIn(str(directory), raw.decode())
                self.assertEqual(subreaper(), parent_setting)
                print(json.dumps({'kind': 'owned-supervisor-loss-receipt', 'case': phase,
                                  **result}, sort_keys=True), flush=True)
                return result
            finally:
                os.close(observerfd); os.close(read)

    def test_actual_supervisor_sigkill_immediately_after_spawn(self):
        r = self.run_case('post_spawn')
        self.assertTrue(r['helper_reaped_by_observer'])
        self.assertEqual(r['cleanup_signals'], [])

    def test_actual_supervisor_sigkill_after_ready_before_go(self):
        r = self.run_case('idle')
        self.assertTrue(r['helper_adopted'])
        self.assertEqual(r['cleanup_signals'], [])

    def test_hung_helper_survives_supervisor_until_adopted_cleanup(self):
        r = self.run_case('hung', 0)
        self.assertTrue(r['helper_reaped_by_observer'])
        self.assertEqual(r['cleanup_signals'], ['SIGTERM', 'SIGKILL'])
        self.assertEqual(r['helper_exit'], -signal.SIGKILL)

    def test_real_success_prefix_is_not_a_final_receipt(self):
        r = self.run_case('prefix', 1)
        self.assertEqual(r['cleanup_signals'], ['SIGTERM', 'SIGKILL'])

    def test_nonreading_helper_after_supervisor_death(self):
        r = self.run_case('blocked', 2)
        self.assertEqual(r['helper_exit'], -signal.SIGKILL)

    def test_adopted_cleanup_can_confirm_term_without_kill(self):
        r = self.run_case('term', 3)
        self.assertEqual(r['cleanup_signals'], ['SIGTERM'])
        self.assertEqual(r['helper_exit'], -signal.SIGTERM)

    def test_original_capture_complete_but_final_not_written_stays_unknown(self):
        r = self.run_case('pre_final')
        self.assertTrue(r['helper_exit_observed'])
        self.assertFalse(r['helper_adopted'])
        self.assertFalse(r['helper_reaped_by_observer'])
        self.assertEqual(r['cleanup_signals'], [])

    def test_both_owner_and_supervisor_dead_do_not_orphan_helper(self):
        r = self.run_case('both', 0)
        self.assertTrue(r['helper_reaped_by_observer'])
        self.assertEqual(r['cleanup_signals'], ['SIGTERM', 'SIGKILL'])

    def test_source_and_unchanged_dependency_manifest(self):
        m = json.loads((SOURCE/'supervisor-loss-hashes.json').read_bytes())
        for entry in m['source']+m['unchanged_dependencies']:
            raw = (ROOT/entry['path']).read_bytes()
            self.assertEqual(len(raw), entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
        self.assertFalse(m['dev_observed']); self.assertFalse(m['authorizes_actions'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
