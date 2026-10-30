"""Real collect/marker/pidfd + local framed Linux sample; fixture coordinator.

No Windows/SSH or production host-coordinator coverage is claimed. Fast collect
is an explicit HOLD with no retry, not a skipped test or an enlarged window.
"""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import types
import unittest

import observer_guest as guest
import observation_protocol as p
from test_r1_integration import HERE,B,C


class JoinedCollectControls(unittest.TestCase):
    def run_joined(self,mode):
        p.identity(os.getpid())  # Mandatory: incoherent procfs is an error, not skip.
        read_fd,write_fd=os.pipe2(os.O_CLOEXEC|os.O_NONBLOCK)
        child=worker=None
        log=[]
        lines=p.Lines(p.FRAME_LIMIT,p.FRAME_LIMIT*3)
        window=p.Window(B,C)
        def drain():
            while not lines.eof:
                try: data=os.read(read_fd,4096)
                except BlockingIOError: break
                for frame in lines.feed(data):
                    log.append(frame['kind']); window.event(frame)
        def sample():
            # Real local Linux reading, transported as one bounded frame through
            # a real pipe. The producer/coordinator are test code, not Windows.
            log.append('sample_started')
            if mode=='exit_during_sample' and child.poll() is None:
                child.terminate()  # Only this test's own Popen child.
                child.wait(timeout=3)
            started=time.monotonic()
            memory=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
            available=int(memory['MemAvailable'].split()[0])*1024
            value={'kind':'host_sample','binding':B,'challenge':C,
                   'evidence_class':'joined-fixture-local-linux-memory',
                   'host_available_bytes':available,'elapsed_seconds':time.monotonic()-started,
                   **p.FALSE_FLAGS}
            carrier_read,carrier_write=os.pipe2(os.O_CLOEXEC|os.O_NONBLOCK)
            try:
                raw=p.encode(value,p.HOST_LIMIT)
                self.assertEqual(os.write(carrier_write,raw),len(raw))
                os.close(carrier_write); carrier_write=None
                frames=p.Lines(p.HOST_LIMIT,p.HOST_LIMIT)
                received=frames.feed(os.read(carrier_read,p.HOST_LIMIT))
                frames.feed(os.read(carrier_read,p.HOST_LIMIT))
                self.assertTrue(frames.eof)
                self.assertEqual(len(received),1)
                sample_value=received[0]
                self.assertEqual(sample_value,value)
                self.assertTrue(all(sample_value[k] is False for k in p.FALSE_FLAGS))
                p.require(available>=1536*1024**2 and 0<=value['elapsed_seconds']<=1)
                log.append('sample_finished')
            finally:
                os.close(carrier_read)
                if carrier_write is not None: os.close(carrier_write)
        try:
            child=subprocess.Popen([sys.executable,'-W','error::ResourceWarning','-I','-S','-B',
                str(HERE/'joined_collect_fixture.py'),str(write_fd)],stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(write_fd,),bufsize=0)
            os.close(write_fd); write_fd=None
            self.assertTrue(select.select([child.stdout],[],[],5)[0],'worker startup deadline')
            ready=p.loads(child.stdout.readline())
            self.assertEqual(ready,{'ready':True,'pid':child.pid})
            guest.P=guest._load_observation_protocol()
            identity=guest.P.identity(child.pid)
            worker=guest.ReadOnlyWorker(child.pid,guest.P.fingerprint(identity),
                types.SimpleNamespace(pid=os.getpid()),sys.executable)
            bound={'kind':'worker_bound','binding':B,'challenge':C,'pid':child.pid,
                   'identity':p.fingerprint(identity),'ok':True}
            window.event(bound); log.append('worker_bound')
            child.stdin.write(b'G'); child.stdin.close()
            outcome='HOLD'
            reason='fast_collect'
            deadline=time.monotonic()+3
            while window.phase=='bound' and not lines.eof:
                self.assertGreater(deadline-time.monotonic(),0)
                self.assertTrue(select.select([read_fd],[],[],max(0,deadline-time.monotonic()))[0])
                drain()
            try:
                drain()
                window.pre(worker.live(),partial=bool(lines.pending),eof=lines.eof)
                log.append('sample_window_open')
                sample()
                if mode=='leaving_before_post':
                    child.wait(timeout=3)
                log.append('post_request')
                drain()
                window.post({'kind':'check_window_after','binding':B,'challenge':C},worker.live(),
                            partial=bool(lines.pending),eof=lines.eof)
                log.append('window_confirmed')
                child.wait(timeout=3)
                drain(); window.finish()
                outcome='CONFIRMED_FIXTURE_ONLY'
                self.assertEqual(mode,'natural')
                self.assertLess(log.index('collect_entered'),log.index('sample_started'))
                self.assertLess(log.index('sample_finished'),log.index('post_request'))
                self.assertLess(log.index('window_confirmed'),log.index('collect_leaving'))
            except (p.Hold,guest.P.Hold):
                reason='post_rejected' if window.opened else 'fast_collect'
                if not window.held:
                    # finish() does not latch; the fixture coordinator does.
                    try: window.hold()
                    except p.Hold: pass
                self.assertTrue(window.held)
                with self.assertRaises(p.Hold): window.pre(True)
                with self.assertRaises(p.Hold): window.finish()
                log.append('hold')
            if mode!='natural':
                self.assertEqual(outcome,'HOLD')
                self.assertTrue(window.opened,'negative case must reach an actual sample window')
                self.assertIn('sample_finished',log)
                self.assertIn('post_request',log)
                self.assertEqual(reason,'post_rejected')
            child.wait(timeout=3)
            drain()
            self.assertTrue(lines.eof)
            self.assertFalse(worker.live())
            out=child.stdout.read(); err=child.stderr.read()
            self.assertEqual(err,b'')
            if child.returncode==0:
                self.assertEqual(p.loads(out),{'collected':True,'r1_complete':False,'r2_authorized':False})
            else:
                self.assertEqual(mode,'exit_during_sample')
                self.assertEqual(child.returncode,-15)
                self.assertEqual(out,b'')
            print(json.dumps({'evidence_class':'joined-fixture-result','case':mode,'outcome':outcome,
                'hold_reason':reason if outcome=='HOLD' else None,'sequence':log,
                'worker_exit':child.returncode,'r1_complete':False,'r2_authorized':False}))
        finally:
            if write_fd is not None: os.close(write_fd)
            os.close(read_fd)
            if child is not None:
                if child.poll() is None: child.terminate()
                child.wait(timeout=3)
                for stream in (child.stdin,child.stdout,child.stderr): stream.close()
            if worker is not None: os.close(worker.fd)

    def test_natural_collect_local_sample_and_post_or_fast_hold(self):
        self.run_joined('natural')

    def test_real_worker_exit_during_sample_holds(self):
        self.run_joined('exit_during_sample')

    def test_real_leaving_before_post_holds(self):
        self.run_joined('leaving_before_post')


if __name__=='__main__': unittest.main()
