"""Permanently fixture-only SSH contract peer; no inventory/backend capability."""
import json
import os
from pathlib import Path
import sys


def main():
    cfg=json.loads(Path(sys.argv[1]).read_bytes())
    if os.environ.get('SSH_ORIGINAL_COMMAND')!=cfg['expected_command']:
        return 2
    trace=Path(cfg['trace'])
    trace.write_text('started\n')
    def emit(kind,**extra):
        value={'kind':kind,'binding':'a'*64,'challenge':'b'*64,
               'r1_complete':False,'r2_authorized':False,'authenticated':False,
               'complete_writer_coverage':False,'host_identity_proved':False,
               'scope_granted':False,**extra}
        raw=(json.dumps(value,separators=(',',':'))+'\n').encode()
        if len(raw)>2048: raise RuntimeError('fixture frame budget')
        sys.stdout.buffer.write(raw); sys.stdout.buffer.flush()
    if cfg['case']=='wrong_challenge':
        emit('sample_window_open',challenge='d'*64)
        return 0
    emit('sample_window_open')
    # Contract-peer wait only. No collect/worker is run or delayed here.
    raw=sys.stdin.buffer.readline(2049)
    if len(raw)>2048 or not raw.endswith(b'\n'): return 2
    post=json.loads(raw)
    if post!={'kind':'check_window_after','binding':'a'*64,'challenge':'b'*64}: return 2
    with trace.open('a') as out: out.write('post-received\n')
    emit('window_confirmed')
    emit('observation_complete_pending_review',receipt_sha256='c'*64)
    return 0


if __name__=='__main__': raise SystemExit(main())
