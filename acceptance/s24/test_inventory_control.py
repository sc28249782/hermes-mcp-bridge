"""Offline synthetic evidence and fresh disposable Linux child controls only.

Synthetic completion does not establish real inventory/guest readiness. The real
pidfd controls are mandatory: incoherent procfs must fail, never skip or relax.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import Mock, patch

import inventory_control as control

HERE = Path(__file__).resolve().parent


class PrivateCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.attempt = self.root / 'r1-remaining-synthetic'
        self.attempt.mkdir(mode=0o700)
        self.helper = control.load_inventory()
        self.args = argparse.Namespace(root=str(self.root), attempt_name=self.attempt.name,
            python_argv=str(self.root / 'candidate/.venv/bin/python'), health_port=18081,
            scope_start_epoch=time.time(), allow_kill=False)

    def report(self):
        return {'evidence_class': 'private-prebind-inventory', 'root': str(self.root),
                'attempt_name': self.attempt.name, 'python_argv': self.args.python_argv,
                'health_port_nomination': self.args.health_port,
                'directory_identities': {'root': self.dir_id(self.root),
                                         'attempt': self.dir_id(self.attempt)},
                **{k: False for k in self.helper.FALSE_FLAGS}}

    def dir_id(self, path):
        fd = self.helper._open_dir(str(path))
        try:
            return list(self.helper._private_dir(fd))
        finally:
            os.close(fd)

    def no_receipt(self):
        self.assertFalse((self.attempt / control.RECEIPT).exists())


class ProtocolControls(PrivateCase):
    def test_startup_deadline_without_data(self):
        reader, writer = os.pipe()
        self.addCleanup(os.close, writer)
        with os.fdopen(reader, 'rb', buffering=0) as stream:
            with self.assertRaisesRegex(control.Hold, 'startup deadline'):
                control.ready_frame(types.SimpleNamespace(pid=1, stdout=stream), time.monotonic() + 0.03)

    def test_ready_strict_types_duplicates_size_and_eof(self):
        good = {'event': 'inventory_ready', 'pid': 1, 'parent': os.getpid()}
        samples = [(json.dumps(good).encode() + b'\n', True),
                   (json.dumps({**good, 'pid': True}).encode() + b'\n', False),
                   (json.dumps({**good, 'pid': 1.0}).encode() + b'\n', False),
                   (b'{"event":"wrong","event":"inventory_ready","pid":1,"parent":'
                    + str(os.getpid()).encode() + b'}\n', False),
                   (b'{}\n{}\n', False), (b'x' * 513, False), (b'', False)]
        for raw, valid in samples:
            with self.subTest(raw=raw):
                reader, writer = os.pipe()
                os.write(writer, raw)
                os.close(writer)
                with os.fdopen(reader, 'rb', buffering=0) as stream:
                    proc = types.SimpleNamespace(pid=1, stdout=stream)
                    if valid:
                        self.assertEqual(control.ready_frame(proc, time.monotonic() + 1), raw)
                    else:
                        with self.assertRaises((control.Hold, ValueError)):
                            control.ready_frame(proc, time.monotonic() + 1)

    def test_worker_tuple_binding_and_no_g_barrier_synthetic(self):
        helper = Mock()
        report = self.report()
        report['directory_identities'] = {k: tuple(v) for k, v in report['directory_identities'].items()}
        helper.collect.return_value = report
        helper.record.return_value = 'a' * 64
        self.args.parent = os.getpid()
        self.args.directory_identities = json.dumps(self.report()['directory_identities'])
        for gate in (b'', b'NO', b'G'):
            with self.subTest(gate=gate), patch.object(control, 'arm_worker'), \
                    patch.object(control, 'load_inventory', return_value=helper), \
                    patch.object(control.select, 'select', return_value=([0], [], [])), \
                    patch.object(control.os, 'read', return_value=gate), \
                    patch.object(control.os, 'write', side_effect=lambda fd, raw: len(raw)):
                helper.reset_mock()
                if gate == b'G':
                    self.assertEqual(control.worker(self.args), 0)
                    helper.record.assert_called_once_with(report)
                else:
                    with self.assertRaises(control.Hold):
                        control.worker(self.args)
                    helper.collect.assert_not_called()
                    helper.record.assert_not_called()

    def test_exact_source_and_no_candidate_or_fixture_imports(self):
        self.assertEqual(hashlib.sha256((HERE / 'prebind_inventory.py').read_bytes()).hexdigest(),
                         control.INVENTORY_SHA256)
        self.assertFalse(any(n in sys.modules for n in ('parent_contract', 's24_fixture', 'bridge')))
        self.assertEqual(self.helper.OUTPUT_NAME, 'binding-inventory.json')

    def test_source_drift_and_symlink_rejected_before_compile(self):
        fake = self.root / 'inventory_control.py'
        source = fake.with_name('prebind_inventory.py')
        source.write_text('raise AssertionError("must not compile")\n')
        with patch.object(control, '__file__', str(fake)):
            with self.assertRaises(control.Hold):
                control.load_inventory()
            source.unlink()
            source.symlink_to(HERE / 'prebind_inventory.py')
            with self.assertRaises(OSError):
                control.load_inventory()

    def test_existing_evidence_rejected_before_claim_or_spawn(self):
        for name in (self.helper.OUTPUT_NAME, control.CLAIM, control.TRACE, control.RECEIPT):
            with self.subTest(name=name):
                path = self.attempt / name
                path.write_bytes(b'preserve')
                with patch.object(control.subprocess, 'Popen', side_effect=AssertionError('spawn')):
                    with self.assertRaises(control.Hold):
                        control.run_once(self.args)
                self.assertEqual(path.read_bytes(), b'preserve')
                path.unlink()  # Disposable test fixture only; never production cleanup.

    def test_existing_dangling_symlink_is_evidence(self):
        (self.attempt / self.helper.OUTPUT_NAME).symlink_to(self.root / 'missing')
        with self.assertRaises(control.Hold):
            control.run_once(self.args)
        self.no_receipt()
        self.assertFalse((self.attempt / control.CLAIM).exists())

    def test_scope_and_types_fail_before_spawn(self):
        for age in (-1, 841, float('nan'), float('inf')):
            with self.subTest(age=age), patch.object(control.subprocess, 'Popen', side_effect=AssertionError):
                self.args.scope_start_epoch = time.time() - age
                with self.assertRaises(control.Hold):
                    control.run_once(self.args)
        self.no_receipt()

    def test_bool_arguments_rejected(self):
        self.args.health_port = True
        with self.assertRaises(control.Hold):
            control.run_once(self.args)
        self.args.health_port = 18081
        self.args.allow_kill = 1
        with self.assertRaises(control.Hold):
            control.run_once(self.args)

    def test_spawn_failure_keeps_single_use_claim_and_trace(self):
        with patch.object(control.subprocess, 'Popen', side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):
                control.run_once(self.args)
        claim = (self.attempt / control.CLAIM).read_bytes()
        self.assertTrue((self.attempt / control.TRACE).exists())
        self.no_receipt()
        with patch.object(control.subprocess, 'Popen', side_effect=AssertionError('retry forbidden')):
            with self.assertRaises(control.Hold):
                control.run_once(self.args)
        self.assertEqual((self.attempt / control.CLAIM).read_bytes(), claim)

    def test_controller_absolute_timer_interrupts_blocked_python_work(self):
        # Test-only short constant in a disposable controller; real CLI is 60s.
        script = (f"import sys,signal; sys.path.insert(0,{str(HERE)!r}); "
                  "import inventory_control as c; c.CONTROL_SECONDS=0.15; "
                  "c.run_once=lambda args: signal.pause(); "
                  f"sys.argv=['controller','--root',{str(self.root)!r},'--attempt-name',{self.attempt.name!r},"
                  f"'--python-argv',{self.args.python_argv!r},'--health-port','18081','--scope-start-epoch','1']; "
                  "c.main()")
        p = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', script],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3, check=False)
        self.assertEqual(p.returncode, -signal.SIGALRM)
        self.assertEqual(p.stdout, b'')
        self.assertEqual(p.stderr, b'')
        self.no_receipt()

    def test_claim_fsync_failure_preserves_partial_and_never_spawns(self):
        with patch.object(control.os, 'fsync', side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):
                control.run_once(self.args)
        self.assertTrue((self.attempt / control.CLAIM).exists())
        self.no_receipt()
        with self.assertRaises(control.Hold):
            control.run_once(self.args)

    def test_trace_private_exclusive_budget_and_partial_fsync(self):
        fd = self.helper._open_dir(str(self.attempt))
        self.addCleanup(os.close, fd)
        trace = control.Trace(fd)
        self.addCleanup(trace.close)
        trace.append('stdout', b'synthetic\x00\xff')
        path = self.attempt / control.TRACE
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(base64.b64decode(json.loads(path.read_bytes())['bytes_base64']), b'synthetic\x00\xff')
        with self.assertRaises(FileExistsError):
            control.Trace(fd)
        with patch.object(control, 'TRACE_LIMIT', path.stat().st_size):
            with self.assertRaises(control.Hold):
                trace.append('stdout', b'overflow')
        before = path.read_bytes()
        with patch.object(control.os, 'fsync', side_effect=OSError):
            with self.assertRaises(OSError):
                trace.append('stderr', b'partial')
        self.assertTrue(path.read_bytes().startswith(before))
        self.no_receipt()

    def test_result_rejects_duplicates_nonfinite_bool_and_upgrades(self):
        good = {'event': 'inventory_result', 'status': 'INVENTORY_RECORDED_PENDING_REVIEW',
                'sha256': 'a' * 64, 'key_contents_read': False, 'r1_complete': False, 'r2_authorized': False}
        self.assertEqual(control.result_frame(json.dumps(good).encode() + b'\n'), good)
        malformed = [json.dumps({**good, 'r2_authorized': True}).encode() + b'\n',
                     json.dumps({**good, 'r1_complete': 0}).encode() + b'\n',
                     json.dumps({**good, 'extra': 1}).encode() + b'\n',
                     json.dumps(good).encode() + b'\n{}\n', b'{}',
                     b'{"x":NaN}\n', b'{"event":"x","event":"y"}\n']
        for raw in malformed:
            with self.subTest(raw=raw), self.assertRaises((control.Hold, ValueError)):
                control.result_frame(raw)

    def test_named_directory_replacement_rejected(self):
        ids = self.report()['directory_identities']
        self.attempt.rename(self.root / 'displaced')
        self.attempt.mkdir(mode=0o700)
        with self.assertRaises(control.Hold):
            control.verify_directories(self.helper, str(self.root), self.attempt.name, ids)

    def test_private_cli_errors_and_kill_default_off(self):
        with patch.object(sys, 'argv', ['inventory_control', '--root', 'SYNTHETIC_PRIVATE']), \
                patch.object(sys, 'stderr', io.StringIO()) as stderr:
            self.assertEqual(control.main(), 2)
        self.assertNotIn('SYNTHETIC_PRIVATE', stderr.getvalue())
        self.assertFalse(self.args.allow_kill)


class SyntheticCompletion(PrivateCase):
    """Real pipes/reap, fabricated report/worker and fake adoption; no identity proof."""
    def simulate(self, *, change=None, bad_result=False, stderr=False, partial=False, trace_fail=False):
        report = self.report()
        if change:
            change(report)
        raw = (json.dumps(report) + '\n').encode()
        result = {'event': 'inventory_result', 'status': 'INVENTORY_RECORDED_PENDING_REVIEW',
                  'sha256': ('0' * 64 if bad_result else hashlib.sha256(raw).hexdigest()),
                  'key_contents_read': False, 'r1_complete': False, 'r2_authorized': False}
        # This test-only child deliberately bypasses real collection. Production
        # has no configurable executable or injectable worker CLI.
        script = f'''import json,os,sys
print(json.dumps({{'event':'inventory_ready','pid':os.getpid(),'parent':os.getppid()}}),flush=True)
assert os.read(0,2)==b'G'
fd=os.open({str(self.attempt / self.helper.OUTPUT_NAME)!r},os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
os.write(fd,{raw[:5] if partial else raw!r}); os.fsync(fd); os.close(fd)
{'print("synthetic failure",file=sys.stderr)' if stderr else ''}
print({json.dumps(result)!r},flush=True)
'''
        popen = subprocess.Popen
        children = []

        def spawn(argv, **kwargs):
            p = popen([sys.executable, '-I', '-S', '-B', '-c', script], **kwargs)
            children.append(p)
            return p

        class SyntheticTarget:
            def __init__(self, process, argv):
                self.process, self.signals, self.identity = process, [], {'synthetic': True}
            def close(self):
                pass
            def send_signal(self, number):
                raise control.Hold('synthetic target cannot signal')

        try:
            with patch.object(control.subprocess, 'Popen', side_effect=spawn), \
                    patch.object(control, 'Target', SyntheticTarget):
                if trace_fail:
                    with patch.object(control.Trace, 'append', side_effect=OSError('trace')):
                        summary, code = control.run_once(self.args)
                else:
                    summary, code = control.run_once(self.args)
        finally:
            for p in children:
                # Test-only fixture has bounded code, no ignored TERM or retry.
                p.wait(timeout=3)
                for stream in (p.stdin, p.stdout, p.stderr):
                    if not stream.closed:
                        stream.close()
        receipt = json.loads((self.attempt / control.RECEIPT).read_bytes())
        self.assertTrue(receipt['leader_reaped'])
        for name in control.SCOPE_FLAGS:
            self.assertIs(receipt[name], False)
            self.assertIs(summary[name], False)
        return receipt, summary, code

    def test_synthetic_completion_only_after_reap_and_verified_bytes(self):
        receipt, summary, code = self.simulate()
        self.assertEqual(code, 0)
        self.assertEqual(summary['status'], 'CONTROL_COMPLETE_PENDING_REVIEW')
        self.assertTrue(receipt['inventory_bytes_verified_after_stop'])
        self.assertEqual((self.attempt / control.RECEIPT).stat().st_mode & 0o777, 0o600)
        before = (self.attempt / control.RECEIPT).read_bytes()
        with self.assertRaises(control.Hold):
            control.run_once(self.args)
        self.assertEqual(before, (self.attempt / control.RECEIPT).read_bytes())

    def test_wrong_hash_is_hold(self):
        receipt, _, code = self.simulate(bad_result=True)
        self.assertEqual(code, 2)
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])

    def test_partial_inventory_is_hold_and_preserved(self):
        receipt, _, code = self.simulate(partial=True)
        self.assertEqual(code, 2)
        self.assertEqual((self.attempt / self.helper.OUTPUT_NAME).stat().st_size, 5)
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])

    def test_scope_upgrade_is_hold(self):
        receipt, _, code = self.simulate(change=lambda r: r.update(authenticated=True))
        self.assertEqual(code, 2)
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])

    def test_nomination_drift_is_hold(self):
        receipt, _, code = self.simulate(change=lambda r: r.update(health_port_nomination=True))
        self.assertEqual(code, 2)
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])

    def test_stderr_is_hold(self):
        receipt, _, code = self.simulate(stderr=True)
        self.assertEqual(code, 2)
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])

    def test_trace_failure_closes_no_g_and_reaps_without_completion(self):
        receipt, _, code = self.simulate(trace_fail=True)
        self.assertEqual(code, 2)
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])
        self.assertFalse((self.attempt / self.helper.OUTPUT_NAME).exists())


class FreshChildControls(PrivateCase):
    def setUp(self):
        super().setUp()
        self.children, self.targets, self.fds = [], [], []
        self.addCleanup(self.cleanup_children)

    def cleanup_children(self):
        for p in self.children:
            if p.poll() is None:
                fd = os.pidfd_open(p.pid)
                try:
                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                finally:
                    os.close(fd)
            p.wait(timeout=3)
            for stream in (p.stdin, p.stdout, p.stderr):
                if stream and not stream.closed:
                    stream.close()
        for target in self.targets:
            target.close()
        for fd in self.fds:
            os.close(fd)

    def spawn(self, tail='signal.pause()', pre=''):
        script = ("import os,sys,json,signal,time; " + pre +
                  "print(json.dumps({'event':'inventory_ready','pid':os.getpid(),'parent':os.getppid()}),flush=True); " + tail)
        argv = [sys.executable, '-I', '-S', '-B', '-c', script]
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.children.append(p)
        control.ready_frame(p, time.monotonic() + 3)
        return p, argv

    def adopt(self, p, argv):
        target = control.Target(p, argv)
        self.targets.append(target)
        return target

    def test_real_identity_pidfd_term_and_other_child_untouched(self):
        p, argv = self.spawn()
        other, _ = self.spawn()
        target = self.adopt(p, argv)
        self.assertEqual(target.identity['ppid'], os.getpid())
        with patch.object(os, 'kill', side_effect=AssertionError('numeric PID forbidden')), \
                patch.object(os, 'killpg', side_effect=AssertionError('group forbidden')):
            target.send_signal(signal.SIGTERM)
        p.wait(timeout=3)
        self.assertEqual(p.returncode, -signal.SIGTERM)
        self.assertIsNone(other.poll())
        self.assertEqual(target.signals, [signal.SIGTERM])
        self.no_receipt()

    def test_real_mismatched_argv_and_changed_identity_reject_signaling(self):
        p, argv = self.spawn()
        with self.assertRaises(control.Hold):
            control.Target(p, argv + ['wrong'])
        target = self.adopt(p, argv)
        with patch.object(control, 'identity', return_value={**target.identity, 'start_ticks': -1}), \
                patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('must not signal')):
            with self.assertRaises(control.Hold):
                target.send_signal(signal.SIGTERM)
        self.assertIsNone(p.poll())

    def test_stale_identity_cleanup_retains_target_without_signal_or_receipt(self):
        p, argv = self.spawn()
        target = self.adopt(p, argv)
        with patch.object(control, 'identity', return_value={**target.identity, 'uid': -1}), \
                patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('stale target')):
            with self.assertRaises(control.StopUnconfirmed) as caught:
                control.settle(p, target, allow_kill=True, grace=0.03)
        self.assertIs(caught.exception.process, p)
        self.assertIs(caught.exception.target, target)
        self.assertEqual(target.signals, [])
        self.assertIsNone(p.poll())
        os.fstat(target.fd)
        self.no_receipt()

    def test_expiry_term_drains_to_eof(self):
        p, argv = self.spawn()
        target = self.adopt(p, argv)
        class Trace:
            def append(self, *args):
                pass
        _, _, held = control.monitor(target, Trace(), time.monotonic(), stop_after=0.05, grace=0.1)
        self.assertTrue(held)
        self.assertEqual(p.returncode, -signal.SIGTERM)
        self.assertEqual(target.signals, [signal.SIGTERM])

    def test_kill_default_off_retains_unconfirmed_handles(self):
        p, argv = self.spawn(pre='signal.signal(signal.SIGTERM,signal.SIG_IGN); ')
        target = self.adopt(p, argv)
        class Trace:
            def append(self, *args):
                pass
        with self.assertRaises(control.StopUnconfirmed) as caught:
            control.monitor(target, Trace(), time.monotonic(), stop_after=0.05, grace=0.05)
        self.assertIs(caught.exception.target, target)
        self.assertIsNone(p.poll())
        self.assertEqual(target.signals, [signal.SIGTERM])
        os.fstat(target.fd)
        with self.assertRaises(control.Hold):
            target.close()
        self.no_receipt()

    def test_opted_in_kill_drains_pipes_after_reap(self):
        p, argv = self.spawn(pre='signal.signal(signal.SIGTERM,signal.SIG_IGN); ',
                            tail="os.read(0,1); os.write(1,b'x'*12000); signal.pause()")
        target = self.adopt(p, argv)
        class Trace:
            def append(self, *args):
                pass
        os.write(p.stdin.fileno(), b'G')
        stdout, stderr, held = control.monitor(target, Trace(), time.monotonic(),
            stop_after=0.05, grace=0.05, allow_kill=True)
        self.assertEqual(stdout, b'x' * 12000)
        self.assertEqual(stderr, b'')
        self.assertTrue(held)
        self.assertEqual(p.returncode, -signal.SIGKILL)
        self.assertEqual(target.signals, [signal.SIGTERM, signal.SIGKILL])
        self.no_receipt()

    def test_real_worker_startup_eof_without_g_never_collects(self):
        argv = [sys.executable, '-I', '-S', '-B', str(HERE / 'inventory_control.py'),
                '--worker', '--parent', str(os.getpid()), '--root', str(self.root),
                '--attempt-name', self.attempt.name, '--python-argv', self.args.python_argv,
                '--health-port', '18081', '--scope-start-epoch', str(time.time()),
                '--directory-identities', json.dumps(self.report()['directory_identities'])]
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.children.append(p)
        control.ready_frame(p, time.monotonic() + 3)
        p.stdin.close()
        p.wait(timeout=3)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout.read(), b'')
        self.assertFalse((self.attempt / self.helper.OUTPUT_NAME).exists())
        self.no_receipt()

    def test_real_worker_safe_inventory_failure(self):
        # No guest files or credential created. Real worker is allowed G only
        # after the exact adoption predicates, and must fail inventory safely.
        summary, code = control.run_once(self.args)
        self.assertEqual(code, 2)
        self.assertEqual(summary['status'], 'HOLD')
        receipt = json.loads((self.attempt / control.RECEIPT).read_bytes())
        self.assertTrue(receipt['leader_reaped'])
        self.assertEqual(receipt['failure_stage'], 'worker')
        self.assertFalse(receipt['inventory_bytes_verified_after_stop'])
        self.assertFalse((self.attempt / self.helper.OUTPUT_NAME).exists())
        for k in control.SCOPE_FLAGS:
            self.assertIs(receipt[k], False)

    def test_independent_worker_timer_without_parent_poll(self):
        pre = f"sys.path.insert(0,{str(HERE)!r}); import inventory_control as c; c.WORKER_SECONDS=0.15; c.arm_worker(os.getppid()); "
        p, _ = self.spawn(pre=pre)
        p.wait(timeout=3)
        self.assertEqual(p.returncode, -signal.SIGALRM)
        self.no_receipt()

    def test_worker_parent_death_signal(self):
        inner = (f"import sys,os,signal; sys.path.insert(0,{str(HERE)!r}); "
                 "import inventory_control as c; c.WORKER_SECONDS=3; c.arm_worker(os.getppid()); "
                 "print(os.getpid(),flush=True); signal.pause()")
        owner_script = ("import subprocess,sys,os,signal,json; "
                        f"p=subprocess.Popen([sys.executable,'-I','-S','-B','-c',{inner!r}],stdout=subprocess.PIPE); "
                        "pid=int(p.stdout.readline()); "
                        "print(json.dumps({'event':'inventory_ready','pid':os.getpid(),'parent':os.getppid()}),flush=True); "
                        "print(pid,flush=True); signal.pause()")
        argv = [sys.executable, '-I', '-S', '-B', '-c', owner_script]
        owner = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.children.append(owner)
        # Read exactly the first frame, leaving the grandchild PID for this test.
        line = owner.stdout.readline()
        self.assertEqual(json.loads(line)['pid'], owner.pid)
        target = self.adopt(owner, argv)
        child_pid = int(owner.stdout.readline())
        fd = os.pidfd_open(child_pid)
        self.fds.append(fd)
        self.assertFalse(select.select([fd], [], [], 0)[0])
        target.send_signal(signal.SIGTERM)
        owner.wait(timeout=3)
        self.assertTrue(select.select([fd], [], [], 1)[0])
        self.no_receipt()


if __name__ == '__main__':
    unittest.main()
