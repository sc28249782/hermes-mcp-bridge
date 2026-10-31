"""Disposable joined-test worker, never a production launcher or scope tool.

Reuse the pinned synthetic baseline input builder, then call the unchanged
observed collect and real Marker. No sleep, ACK wait inside collect or timer
extension. The synthetic ELF file exercises a bounded 16 MiB hash read; it is
never executed. Production inputs, guest observations and credentials are absent.
"""
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))  # Explicit checked test-source directory under -I.
import observation_protocol as p
from test_r1_integration import HERE,BASELINE_TEST_SHA,HELPER_SHA,B,C


def main():
    p.identity(os.getpid())  # Real coherent procfs required, before fixture setup.
    signal.signal(signal.SIGALRM,signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL,10)
    helper=p.load_source('prebind_inventory_observed.py',HELPER_SHA,__file__)
    baseline=p.load_source('prebind_inventory.py',
        'db0e56b5f91b3214b864d8fd5a7fd2743f52e3fc1e94e9573e516cc36d904847',HERE.parent/'anchor.py')
    sys.modules['prebind_inventory']=baseline
    tests=p.load_source('test_prebind_inventory.py',BASELINE_TEST_SHA,HERE.parent/'anchor.py')
    tests.inventory=helper
    fixture=tests.InventoryControls('test_success_never_opens_key_or_spawns_or_connects')
    try:
        fixture.setUp()
        raw=b'\x7fELF'+b'\0'*(16*1024*1024-4)
        fixture.executable.write_bytes(raw)
        saved=fixture.root/'inspection-continuation/python.stdout'
        value=json.loads(saved.read_bytes())
        value['executable_sha256']=hashlib.sha256(raw).hexdigest()
        saved.write_text(json.dumps(value))
        del raw
        marker=p.Marker(int(sys.argv[1]),B,C)
        os.write(sys.stdout.fileno(),p.encode({'ready':True,'pid':os.getpid()}))
        p.require(select.select([sys.stdin],[],[],3)[0])
        p.require(os.read(sys.stdin.fileno(),2)==b'G')  # Admission before collect only.
        report=helper.collect(str(fixture.root),fixture.attempt.name,fixture.python,
            health_port=18081,system_read=fixture.system.__getitem__,observation=marker)
        p.require(all(report[key] is False for key in helper.FALSE_FLAGS))
        os.write(sys.stdout.fileno(),p.encode({'collected':True,'r1_complete':False,'r2_authorized':False}))
        return 0
    finally:
        fixture.doCleanups()


if __name__=='__main__': raise SystemExit(main())
