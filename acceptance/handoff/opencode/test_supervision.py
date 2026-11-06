"""B4 controls use only new disposable processes/files, not a Dev owner."""
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import contextlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from acceptance.handoff.opencode import supervision as S
from acceptance.handoff.opencode.fixtures import native

SOURCE = Path(__file__).resolve().parent
LIB = Path('/lib/x86_64-linux-gnu/libsqlite3.so.0')

FIXTURE_C = r'''
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
int main(int argc,char **argv) {
 if(argc!=5 || strcmp(argv[1],"--batch"))return 90;
 signal(SIGTERM,SIG_IGN);
 if(MODE!=6) {char b[512];while(read(0,b,sizeof(b))>0){} }
 int witness=openat(atoi(argv[4]),"witness",O_WRONLY|O_NONBLOCK|O_NOFOLLOW);
 if(witness<0 || write(witness,"W",1)!=1)return 91;
 close(witness);
 if(MODE==1) {const unsigned char prefix[]={0,0,0,10,'O','C','S','N','A','P','1',0,2,2};
  if(write(1,prefix,sizeof(prefix))!=(ssize_t)sizeof(prefix))return 92;}
 if(MODE==2) {char b[4096];memset(b,'P',sizeof(b));for(int i=0;i<18;i++)if(write(1,b,sizeof(b))<0)return 93;return 0;}
 if(MODE==3) {if(write(2,"PRIVATE_SENTINEL",16)<0)return 94;return 0;}
 if(MODE==4)return 9;
 if(MODE==5) {if(write(1,"BAD",3)<0)return 95;return 0;}
 for(;;)pause();
}
'''


def close_other_fds(keep):
    # Test launcher only. Never an inventory of another process or Dev files.
    for name in os.listdir('/proc/self/fd'):
        fd = int(name)
        if fd > 2 and fd not in keep:
            try:
                os.close(fd)
            except OSError:
                pass


class Attempt:
    def __init__(self, directory, binary, *, lifetime=2, bad_hash=False, no_pidfd=False,
                 hold_eof=False, postfork_failure=False, uncertain_fork=False):
        self.state = native(Path(directory)/'state')
        os.mkfifo(self.state/'witness', 0o600)
        self.witness = os.open(self.state/'witness', os.O_RDWR|os.O_NONBLOCK)
        ctrl_r, self.ctrl = os.pipe2(os.O_CLOEXEC)
        command_r, command_w = os.pipe2(os.O_CLOEXEC)
        self.report, report_w = os.pipe2(os.O_CLOEXEC)
        self.started = time.monotonic()
        self.owner = os.fork()
        if self.owner == 0:
            close_other_fds({ctrl_r, command_w})
            try:
                while True:
                    c = os.read(ctrl_r, 1)
                    if not c:
                        os._exit(0)
                    if c == b'X':
                        os._exit(91)
                    if c == b'C':
                        os.close(command_w)
                        command_w = -1
                    elif command_w >= 0:
                        os.write(command_w, c)
            except BaseException:
                os._exit(92)
        self.ownerfd = os.pidfd_open(self.owner)
        rootfd = os.open(self.state, os.O_RDONLY|os.O_DIRECTORY)
        binaryfd = os.open(binary, os.O_RDONLY|os.O_NOFOLLOW)
        expected = '0'*64 if bad_hash else hashlib.sha256(Path(binary).read_bytes()).hexdigest()
        self.supervisor = os.fork()
        if self.supervisor == 0:
            close_other_fds({self.ownerfd, command_r, report_w, rootfd, binaryfd})
            try:
                held = []
                native_spawn = S._spawn
                def retained_spawn(*args):
                    pairs = []
                    pipe2, close = S.os.pipe2, S.os.close
                    def pipe(flags):
                        pair = pipe2(flags); pairs.append(pair); return pair
                    def closing(fd):
                        if len(pairs) == 3 and fd == pairs[1][1]:
                            held.append(os.dup(fd))
                        close(fd)
                    with mock.patch.object(S.os, 'pipe2', side_effect=pipe), mock.patch.object(S.os, 'close', side_effect=closing):
                        return native_spawn(*args)
                def failed_setup(*args):
                    with mock.patch.object(S.os, 'set_blocking', side_effect=OSError()):
                        return native_spawn(*args)
                def uncertain_setup(*args):
                    args[-1]['fork_attempted'] = True
                    raise S.Hold('BUDGET_EXHAUSTED')
                with contextlib.ExitStack() as stack:
                    if no_pidfd:
                        stack.enter_context(mock.patch.object(S.os, 'pidfd_open', side_effect=OSError()))
                        stack.enter_context(mock.patch.object(S.os, 'kill', side_effect=AssertionError('numeric signal forbidden')))
                    if hold_eof:
                        stack.enter_context(mock.patch.object(S, '_spawn', side_effect=retained_spawn))
                    if postfork_failure:
                        stack.enter_context(mock.patch.object(S, '_spawn', side_effect=failed_setup))
                    if uncertain_fork:
                        stack.enter_context(mock.patch.object(S, '_spawn', side_effect=uncertain_setup))
                    ok = S.supervise(self.ownerfd, command_r, report_w, rootfd, binaryfd,
                                     expected, 'ctx_fixture', 'oct_fixture', self.started, lifetime=lifetime)
                for fd in held:
                    os.close(fd)
                os._exit(0 if ok else 2)
            except BaseException:
                os._exit(3)
        self.supervisorfd = os.pidfd_open(self.supervisor)
        for fd in (ctrl_r, command_r, command_w, report_w, rootfd, binaryfd):
            os.close(fd)
        self.pending = bytearray()
        self.messages = []
        self.reaped = set()

    def send(self, value):
        os.write(self.ctrl, value)

    def event(self, expected, timeout=3):
        end = time.monotonic()+timeout
        while True:
            if b'\n' in self.pending:
                raw, _, rest = self.pending.partition(b'\n')
                self.pending = bytearray(rest)
                item = json.loads(raw)
                self.messages.append(item)
                if item['event'] != expected:
                    raise AssertionError((expected, item))
                return item
            ready = select.select([self.report], [], [], max(0, end-time.monotonic()))[0]
            if not ready:
                raise AssertionError('fixture report timeout')
            raw = os.read(self.report, 4096)
            if not raw:
                raise AssertionError('missing final report; UNKNOWN')
            self.pending.extend(raw)

    def arm(self):
        self.send(b'A')
        self.event('READY')

    def capture(self):
        self.send(b'G')
        self.event('CAPTURE')

    def active(self):
        if not select.select([self.witness], [], [], 2)[0]:
            raise AssertionError('helper did not reach real fixture body')
        if os.read(self.witness, 1) != b'W':
            raise AssertionError('bad witness')

    def reap(self, pid, pidfd, timeout=3):
        if pid in self.reaped:
            return None
        if not select.select([pidfd], [], [], timeout)[0]:
            raise AssertionError('owned process did not exit')
        actual, status = os.waitpid(pid, 0)
        if actual != pid:
            raise AssertionError('wrong child reaped')
        self.reaped.add(pid)
        return os.waitstatus_to_exitcode(status)

    def finish(self):
        result = self.event('FINAL')
        if self.reap(self.supervisor, self.supervisorfd) != 0:
            raise AssertionError('supervisor failed')
        # Test harness owns these direct actors and confirms supervisor exit.
        return result

    def close(self):
        if self.owner not in self.reaped:
            try:
                signal.pidfd_send_signal(self.ownerfd, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.reap(self.owner, self.ownerfd)
        # Owner loss lets the still-live supervisor clean its own helper first.
        if self.supervisor not in self.reaped:
            self.reap(self.supervisor, self.supervisorfd)
        os.close(self.witness)
        for fd in (self.ctrl, self.report, self.ownerfd, self.supervisorfd):
            os.close(fd)


class SupervisionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='oc-b4-build-')
        cls.build = Path(cls.temp.name)
        cls.helpers = {}
        native_path = cls.build/'native'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                        str(SOURCE/'oc_snapshot_vfs.c'), str(LIB), '-o', str(native_path)],
                       check=True, capture_output=True)
        native_path.chmod(0o700)
        cls.helpers['native'] = native_path
        fixture = cls.build/'owned.c'
        fixture.write_text(FIXTURE_C)
        for mode in range(7):
            binary = cls.build/('fixture'+str(mode))
            subprocess.run(['cc', '-D_GNU_SOURCE', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-O2', '-DMODE='+str(mode), str(fixture), '-o', str(binary)],
                           check=True, capture_output=True)
            binary.chmod(0o700)
            cls.helpers[mode] = binary
        print(json.dumps({'kind': 'b4-owned-build-facts', 'dev_observed': False,
                          'library_sha256': hashlib.sha256(LIB.read_bytes()).hexdigest(),
                          'helpers': {str(k): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for k,p in cls.helpers.items()}}), flush=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='oc-b4-case-')
        self.attempts = []

    def tearDown(self):
        for attempt in reversed(self.attempts):
            attempt.close()
        self.temp.cleanup()

    def attempt(self, helper='native', **kwargs):
        directory = Path(self.temp.name)/str(len(self.attempts))
        directory.mkdir(mode=0o700)
        a = Attempt(directory, self.helpers[helper], **kwargs)
        self.attempts.append(a)
        return a

    def killed(self, a):
        signal.pidfd_send_signal(a.ownerfd, signal.SIGKILL)
        self.assertEqual(a.reap(a.owner, a.ownerfd), -signal.SIGKILL)
        r = a.finish()
        self.assertEqual(r['reason'], 'OWNER_LOST')
        self.assertTrue(r['owner_lost'])
        self.assertFalse(r['authorizes_actions'])
        self.assertEqual(r['frames'], 0)
        return r

    def test_real_native_three_frames_and_stop_are_not_goal_done(self):
        a = self.attempt()
        before = {p.name: p.read_bytes() for p in a.state.iterdir() if p.is_file()}
        a.arm(); a.capture()
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_COMPLETE')
        self.assertEqual(r['frames'], 3)
        self.assertIs(r['helper_stopped'], True)
        self.assertFalse(r['goal_verified'])
        self.assertFalse(r['authorizes_actions'])
        for name, raw in before.items():
            self.assertEqual((a.state/name).read_bytes(), raw)

    def test_owner_sigkill_before_arm_spawns_no_helper(self):
        r = self.killed(self.attempt())
        self.assertFalse(r['helper_started'])
        self.assertIsNone(r['helper_stopped'])

    def test_owner_sigkill_after_ready_before_capture_reaps_idle_native(self):
        a = self.attempt(); a.arm()
        self.assertIs(self.killed(a)['helper_stopped'], True)

    def test_owner_sigkill_during_real_hung_fixture_reaps_term_ignorer(self):
        a = self.attempt(0); a.arm(); a.capture(); a.active()
        self.assertIs(self.killed(a)['helper_stopped'], True)

    def test_owner_sigkill_after_actual_success_prefix_never_completes(self):
        a = self.attempt(1); a.arm(); a.capture(); a.active()
        self.assertIs(self.killed(a)['helper_stopped'], True)

    def test_blocked_helper_input_still_stops_after_owner_death(self):
        a = self.attempt(6); a.arm(); a.capture(); a.active()
        self.assertIs(self.killed(a)['helper_stopped'], True)

    def test_owner_lease_eof_while_owner_alive_is_loss(self):
        a = self.attempt(); a.arm(); a.send(b'C')
        r = a.finish()
        self.assertEqual(r['reason'], 'OWNER_LOST')
        self.assertIs(r['helper_stopped'], True)
        self.assertFalse(select.select([a.ownerfd], [], [], 0)[0])

    def test_shortened_deadline_kills_only_owned_helper(self):
        a = self.attempt(0, lifetime=0.35); a.arm(); a.capture(); a.active()
        r = a.finish()
        self.assertEqual(r['reason'], 'BUDGET_EXHAUSTED')
        self.assertIs(r['helper_stopped'], True)
        self.assertLess(time.monotonic()-a.started, 2)
        self.assertFalse(select.select([a.ownerfd], [], [], 0)[0])

    def test_idle_no_arm_deadline_has_no_helper(self):
        a = self.attempt(lifetime=0.1)
        r = a.finish()
        self.assertEqual(r['reason'], 'BUDGET_EXHAUSTED')
        self.assertFalse(r['helper_started'])

    def test_go_before_arm_is_rejected_without_spawn(self):
        a = self.attempt(); a.send(b'G')
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')
        self.assertFalse(r['helper_started'])

    def test_duplicate_arm_stops_existing_helper_without_second_spawn(self):
        a = self.attempt(); a.arm(); a.send(b'A')
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')
        self.assertIs(r['helper_stopped'], True)

    def test_helper_hash_failure_prevents_arm(self):
        a = self.attempt(bad_hash=True)
        r = a.finish()
        self.assertFalse(r['helper_started'])
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')

    def test_pidfd_acquisition_failure_has_no_numeric_signal_fallback(self):
        a = self.attempt(no_pidfd=True); a.send(b'A')
        r = a.finish()
        self.assertTrue(r['helper_started'])
        self.assertIn(r['reason'], ('CAPTURE_REJECTED', 'STOP_UNCONFIRMED'))
        self.assertEqual(r['reason'] == 'STOP_UNCONFIRMED', r['helper_stopped'] is False)
        self.assertEqual(r['frames'], 0)

    def test_stdout_over_cap_is_bounded_and_not_returned(self):
        a = self.attempt(2); a.arm(); a.capture()
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')
        self.assertIs(r['helper_stopped'], True)
        self.assertLess(len(json.dumps(r)), 512)

    def test_stderr_sentinel_never_appears_in_report(self):
        a = self.attempt(3); a.arm(); a.capture()
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(a.messages))
        self.assertIs(r['helper_stopped'], True)

    def test_nonzero_exit_never_capture_complete(self):
        a = self.attempt(4); a.arm(); a.capture()
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')
        self.assertIs(r['helper_stopped'], True)

    def test_malformed_complete_output_is_rejected_after_reap(self):
        a = self.attempt(5); a.arm(); a.capture()
        r = a.finish()
        self.assertEqual(r['reason'], 'CAPTURE_REJECTED')
        self.assertIs(r['helper_stopped'], True)

    def test_targets_cannot_be_arbitrary_payload(self):
        for target in ('', '../x', 'job\nG', 'é', 'x'*129, True):
            with self.subTest(target=repr(target)), self.assertRaises(S.Hold):
                S._target(target)

    def test_full_report_pipe_is_nonblocking_failure(self):
        read, write = os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC)
        try:
            while True:
                try:
                    os.write(write, b'X'*4096)
                except BlockingIOError:
                    break
            self.assertFalse(S._report(write, {'event': 'FINAL'}))
        finally:
            os.close(read); os.close(write)

    def test_closed_report_reader_is_failure_not_public_exception(self):
        read, write = os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC)
        os.close(read)
        try:
            self.assertFalse(S._report(write, {'event': 'FINAL'}))
        finally:
            os.close(write)

    def test_observer_report_loss_stops_helper_without_a_final_claim(self):
        a = self.attempt(0); a.arm()
        os.close(a.report)
        # Keep teardown's fd set valid without retaining a pipe write end.
        a.report = os.open('/dev/null', os.O_RDONLY)
        a.send(b'G')
        self.assertEqual(a.reap(a.supervisor, a.supervisorfd), 2)
        self.assertFalse(select.select([a.ownerfd], [], [], 0)[0])
        # No final report exists. The observer must retain UNKNOWN.

    def test_supervisor_death_before_arm_has_no_final_report(self):
        a = self.attempt()
        signal.pidfd_send_signal(a.supervisorfd, signal.SIGKILL)
        self.assertEqual(a.reap(a.supervisor, a.supervisorfd), -signal.SIGKILL)
        with self.assertRaisesRegex(AssertionError, 'UNKNOWN'):
            a.event('FINAL')
        self.assertFalse(select.select([a.ownerfd], [], [], 0)[0])

    def test_death_at_startup_handoff_never_yields_capture_complete(self):
        a = self.attempt()
        a.send(b'A')
        signal.pidfd_send_signal(a.ownerfd, signal.SIGKILL)
        self.assertEqual(a.reap(a.owner, a.ownerfd), -signal.SIGKILL)
        # READY may race with death; consume at most one such event.
        try:
            r = a.event('FINAL')
        except AssertionError as error:
            self.assertEqual(error.args[0][1], {'event': 'READY'})
            r = a.event('FINAL')
        self.assertEqual(a.reap(a.supervisor, a.supervisorfd), 0)
        self.assertEqual(r['reason'], 'OWNER_LOST')
        self.assertIsNot(r['helper_stopped'], False)
        self.assertEqual(r['frames'], 0)

    def test_deadline_cannot_be_widened_or_restarted(self):
        for start, lifetime in ((time.monotonic(), 20.1), (time.monotonic(), True),
                                (time.monotonic()-44.9, 20), (float('nan'), 1)):
            with self.subTest(lifetime=lifetime), self.assertRaises(S.Hold):
                S.supervise(-1, -1, -1, -1, -1, 'x', 'ctx', 'job', start, lifetime=lifetime)

    def test_stopping_one_attempt_does_not_signal_another_owner(self):
        other = self.attempt(lifetime=2)
        a = self.attempt(0); a.arm(); a.capture(); a.active()
        self.killed(a)
        self.assertFalse(select.select([other.ownerfd, other.supervisorfd], [], [], 0)[0])
        self.killed(other)

    def test_reaped_helper_without_pipe_eof_is_stop_unconfirmed(self):
        # Test-only spawn instrumentation retains a real stdout write end.
        # Direct native helper exits, but EOF is absent; no orphan or socket.
        a = self.attempt(lifetime=0.75, hold_eof=True)
        a.arm(); a.capture()
        r = a.finish()
        self.assertEqual(r['reason'], 'STOP_UNCONFIRMED')
        self.assertIs(r['helper_stopped'], False)
        self.assertIs(r['helper_reaped'], True)
        self.assertIs(r['pipes_eof'], False)
        self.assertEqual(r['frames'], 0)
        self.assertFalse(r['goal_verified'])

    def test_source_and_unchanged_dependency_manifest(self):
        manifest = json.loads((SOURCE/'supervision-hashes.json').read_bytes())
        for entry in manifest['source'] + manifest['unchanged_dependencies']:
            raw = (ROOT/entry['path']).read_bytes()
            self.assertEqual(len(raw), entry['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
        self.assertFalse(manifest['dev_observed'])
        self.assertFalse(manifest['authorizes_actions'])

    def test_postfork_setup_failure_does_not_lose_actual_child_identity(self):
        a = self.attempt(postfork_failure=True); a.send(b'A')
        r = a.finish()
        self.assertIs(r['helper_started'], True)
        self.assertEqual(r['reason'] == 'STOP_UNCONFIRMED', r['helper_stopped'] is False)
        self.assertEqual(r['frames'], 0)

    def test_uncertain_fork_is_not_reported_as_no_helper(self):
        # Inject the otherwise unschedulable interrupted-return boundary without
        # creating an unowned process that the test could not safely reap.
        a = self.attempt(uncertain_fork=True); a.send(b'A')
        r = a.finish()
        self.assertEqual(r['reason'], 'STOP_UNCONFIRMED')
        self.assertIsNone(r['helper_started'])
        self.assertIs(r['helper_stopped'], False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
