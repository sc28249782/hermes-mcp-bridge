"""Consolidated R1 integration controls; no operator configuration or VM access.

The unchanged 22 baseline helper controls are reused against the observed helper
with a recording boundary sink. Their synthetic file/hash/system-read injections
remain test fixtures. A separate mandatory control runs the actual controller,
worker and collect failure path with real markers and procfs/pidfd admission.
Neither path supplies Windows sampling, transport, authority or private bindings.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import observation_protocol as protocol

HERE=Path(__file__).resolve().parent
B='a'*64
C='b'*64
BASELINE_TEST_SHA='7d5f6624e484c52722e46ecc1ecabc16ca92aa0bb959c8835bbdcbe02ea72e42'
HELPER_SHA='515d9ed26dd5b189a10cf1562a37064ce3f21528c83dc6dd902bd3675c36ddce'


def baseline_variant_suite(loader):
    # Execute checked bytes. Import resolution is scoped to the unchanged public
    # baseline fixture module, then the test module's inventory reference is bound
    # to a distinct checked observed helper module. Original modules stay intact.
    baseline=protocol.load_source('prebind_inventory.py',
        'db0e56b5f91b3214b864d8fd5a7fd2743f52e3fc1e94e9573e516cc36d904847',
        HERE.parent/'anchor.py')
    previous=sys.modules.get('prebind_inventory')
    sys.modules['prebind_inventory']=baseline
    try:
        tests=protocol.load_source('test_prebind_inventory.py',BASELINE_TEST_SHA,HERE.parent/'anchor.py')
    finally:
        if previous is None: sys.modules.pop('prebind_inventory',None)
        else: sys.modules['prebind_inventory']=previous
    variant=protocol.load_source('prebind_inventory_observed.py',HELPER_SHA,__file__)
    original_collect=variant.collect

    def collect(*args,**kwargs):
        events=[]
        class Boundary:
            def boundary(self,kind,ok): events.append((kind,ok))
        ok=False
        try:
            result=original_collect(*args,observation=Boundary(),**kwargs)
            ok=True
            return result
        finally:
            if events != [('collect_entered',True),('collect_leaving',ok)]:
                raise AssertionError('observed regression boundary mismatch')
    variant.collect=collect  # Test-only adapter supplies the added required argument.
    tests.inventory=variant
    suite=loader.loadTestsFromTestCase(tests.InventoryControls)
    if suite.countTestCases()!=22:
        raise AssertionError('baseline control count drift')
    return suite


class RealControllerWorkerIntegration(unittest.TestCase):
    def test_missing_input_real_collect_failure_is_bounded_and_reaped(self):
        # Fail before launching anything when procfs is incoherent. This remains
        # mandatory on both CI interpreters; never skip or fabricate identity.
        protocol.identity(os.getpid())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            root.chmod(0o700)
            attempt=root/'r1-remaining-integration'
            attempt.mkdir(mode=0o700)
            python=root/'candidate/.venv/bin/python'
            python.parent.mkdir(parents=True)
            python.symlink_to(sys.executable)
            read_fd,write_fd=os.pipe2(os.O_CLOEXEC|os.O_NONBLOCK)
            try:
                argv=[sys.executable,'-I','-S','-B',str(HERE/'inventory_control_observed.py'),
                    '--root',str(root),'--attempt-name',attempt.name,
                    '--python-argv',str(python),'--health-port','18081',
                    '--scope-start-epoch',str(time.time()),'--observation-fd',str(write_fd),
                    '--binding-sha256',B,'--challenge',C]
                result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,pass_fds=(write_fd,),cwd='/',
                    env={'PATH':'/usr/bin:/bin','LANG':'C'},timeout=70,check=False)
                os.close(write_fd); write_fd=None
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertEqual(result.stderr,b'')
                summary=protocol.loads(result.stdout)
                self.assertEqual(summary['status'],'HOLD')
                receipt_path=attempt/'inventory-control-receipt.json'
                receipt_raw=receipt_path.read_bytes()
                self.assertEqual(hashlib.sha256(receipt_raw).hexdigest(),summary['receipt_sha256'])
                receipt=protocol.loads(receipt_raw)
                self.assertEqual(receipt['status'],'HOLD')
                self.assertIs(receipt['leader_reaped'],True)
                self.assertEqual(receipt['exit_code'],2)
                self.assertEqual(receipt['failure_stage'],'worker')
                self.assertIs(receipt['inventory_bytes_verified_after_stop'],False)
                self.assertIsNone(receipt['result'])
                self.assertEqual(receipt['signals'],[])
                self.assertFalse((attempt/'binding-inventory.json').exists())
                frames=protocol.Lines(protocol.FRAME_LIMIT,protocol.FRAME_LIMIT*3)
                values=[]
                while not frames.eof:
                    # After controller exit/reap and its worker cleanup, this
                    # nonblocking read must reach EOF, not leave a live writer.
                    values.extend(frames.feed(os.read(read_fd,4096)))
                self.assertEqual([v['kind'] for v in values],
                                 ['worker_bound','collect_entered','collect_leaving'])
                self.assertEqual([v['ok'] for v in values],[True,True,False])
                self.assertTrue(all(v['binding']==B and v['challenge']==C for v in values))
                self.assertEqual(len({(v['pid'],v['identity']) for v in values}),1)
                trace=[protocol.loads(line) for line in (attempt/'inventory-control-trace.jsonl').read_bytes().splitlines()]
                identity=json.loads(base64.b64decode(next(v['bytes_base64'] for v in trace
                                                          if v['direction']=='owned_identity')))
                self.assertEqual(values[0]['pid'],identity['pid'])
                self.assertEqual(values[0]['identity'],protocol.fingerprint(identity))
                self.assertIn('handoff_written_not_consumption',[v['direction'] for v in trace])
                for value in (summary,receipt):
                    self.assertTrue(all(value[k] is False for k in (
                        'scope_granted','r1_complete','r2_authorized','authenticated',
                        'complete_writer_coverage')))
                for path in attempt.iterdir():
                    self.assertEqual(path.stat().st_mode & 0o777,0o600)
            finally:
                os.close(read_fd)
                if write_fd is not None: os.close(write_fd)


def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite()
    suite.addTests(baseline_variant_suite(loader))
    suite.addTests(loader.loadTestsFromTestCase(RealControllerWorkerIntegration))
    return suite


if __name__=='__main__': unittest.main()
