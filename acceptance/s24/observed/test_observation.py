"""Offline protocol/source/marker controls. No operator files, SSH or CIM."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import observation_protocol as p

HERE=Path(__file__).resolve().parent
B='a'*64
C='b'*64
ID={'pid':999,'start_ticks':7,'ppid':998,'uid':1,'exe':'/test/python','argv':['/test/python']}


def event(kind,ok=True):
    return {'kind':kind,'binding':B,'challenge':C,'pid':999,'identity':p.fingerprint(ID),'ok':ok}


def window():
    w=p.Window(B,C)
    w.event(event('worker_bound'))
    w.event(event('collect_entered'))
    return w


def post():
    return {'kind':'check_window_after','binding':B,'challenge':C}


class ProtocolControls(unittest.TestCase):
    def test_honest_completed_causal_sequence(self):
        w=window(); w.pre(True); w.post(post(),True)
        w.event(event('collect_leaving')); w.finish()
        self.assertTrue(w.confirmed)

    def test_live_before_entry_rejected(self):
        w=p.Window(B,C)
        w.event(event('worker_bound'))
        with self.assertRaises(p.Hold): w.pre(True)

    def test_g_write_without_entry_not_sufficient(self):
        w=p.Window(B,C)
        with self.assertRaises(p.Hold): w.pre(True)

    def test_leaving_before_post_rejected(self):
        w=window(); w.pre(True); w.event(event('collect_leaving'))
        with self.assertRaises(p.Hold): w.post(post(),True)

    def test_liveness_is_exact_bool_and_false_rejects(self):
        for value in (False,1,None,'true'):
            with self.subTest(value=value),self.assertRaises(p.Hold): window().pre(value)

    def test_death_during_sample_rejected(self):
        w=window(); w.pre(True)
        with self.assertRaises(p.Hold): w.post(post(),False)

    def test_partial_frame_or_eof_cannot_authorize(self):
        for opts in ({'partial':True},{'eof':True}):
            with self.assertRaises(p.Hold): window().pre(True,**opts)
            w=window(); w.pre(True)
            with self.assertRaises(p.Hold): w.post(post(),True,**opts)

    def test_failure_latch_never_recovers(self):
        w=window()
        with self.assertRaises(p.Hold): w.pre(False)
        with self.assertRaises(p.Hold): w.pre(True)
        with self.assertRaises(p.Hold): w.finish()

    def test_no_repeated_open_or_sample_check(self):
        w=window(); w.pre(True)
        with self.assertRaises(p.Hold): w.pre(True)
        w=window(); w.pre(True); w.post(post(),True)
        with self.assertRaises(p.Hold): w.post(post(),True)

    def test_changed_pid_digest_or_correlation_rejected(self):
        for key,value in [('pid',998),('pid',True),('identity','c'*64),('binding','d'*64),('challenge','c'*64)]:
            w=p.Window(B,C); w.event(event('worker_bound'))
            bad=event('collect_entered'); bad[key]=value
            with self.subTest(key=key),self.assertRaises(p.Hold): w.event(bad)

    def test_duplicate_and_out_of_order_event_rejected(self):
        for kind in ('worker_bound','collect_entered'):
            w=window()
            with self.assertRaises(p.Hold): w.event(event(kind))
        w=p.Window(B,C)
        with self.assertRaises(p.Hold): w.event(event('collect_leaving'))

    def test_failed_collect_does_not_complete(self):
        w=window(); w.pre(True); w.post(post(),True)
        with self.assertRaises(p.Hold): w.event(event('collect_leaving',False))
        with self.assertRaises(p.Hold): w.finish()

    def test_missing_leaving_rejected_at_finalization(self):
        w=window(); w.pre(True); w.post(post(),True)
        with self.assertRaises(p.Hold): w.finish()

    def test_post_message_strict_schema(self):
        for value in ({**post(),'extra':0},{**post(),'challenge':'c'*64},{'kind':'check_window_after'}):
            w=window(); w.pre(True)
            with self.assertRaises(p.Hold): w.post(value,True)

    def test_strict_json_duplicates_nonfinite(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}'):
            with self.assertRaises(p.Hold): p.loads(raw)

    def test_fragmentation_and_eof(self):
        lines=p.Lines(1024,3072)
        raw=p.encode(event('worker_bound'))
        self.assertEqual(lines.feed(raw[:20]),[])
        self.assertEqual(lines.feed(raw[20:]),[event('worker_bound')])
        self.assertEqual(lines.feed(b''),[])
        with self.assertRaises(p.Hold): lines.feed(raw)

    def test_partial_eof_oversize_and_flood(self):
        lines=p.Lines(5,10)
        lines.feed(b'{')
        with self.assertRaises(p.Hold): lines.feed(b'')
        with self.assertRaises(p.Hold): p.Lines(5,10).feed(b'x'*5)
        with self.assertRaises(p.Hold): p.Lines(10,5).feed(b'x'*6)

    def test_correlation_format(self):
        for value in ('A'*64,'a'*63,False,None):
            with self.assertRaises(p.Hold): p.correlation(value,C)


class StorageAndMarkerControls(unittest.TestCase):
    def child(self,script):
        return subprocess.run([sys.executable,'-I','-S','-B','-c',
            f'import sys; sys.path.insert(0,{str(HERE)!r}); '+script],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,check=False)

    def test_real_pipe_atomic_marker_and_no_ack_wait(self):
        r,w=os.pipe2(os.O_NONBLOCK)
        try:
            marker=p.Marker(w,B,C)
            with patch.object(p,'identity',return_value=ID):
                marker.boundary('collect_entered',True)
                marker.boundary('collect_leaving',True)
            lines=p.Lines(1024,3072)
            frames=lines.feed(os.read(r,4096))
            self.assertEqual([f['kind'] for f in frames],['collect_entered','collect_leaving'])
        finally: os.close(r); os.close(w)

    def test_closed_pipe_actual_fatal_exit(self):
        result=self.child("import os, observation_protocol as p; r,w=os.pipe2(os.O_NONBLOCK); m=p.Marker(w,'a'*64,'b'*64); os.close(r); p.identity=lambda _: "+repr(ID)+"; m.boundary('collect_entered',True); print('BAD')")
        self.assertEqual(result.returncode,72)
        self.assertEqual(result.stdout,b'')

    def test_full_pipe_actual_fatal_exit_no_retry(self):
        result=self.child("exec("+repr("import os\nimport observation_protocol as p\nr,w=os.pipe2(os.O_NONBLOCK)\nm=p.Marker(w,'a'*64,'b'*64)\nwhile True:\n try: os.write(w,b'x'*4096)\n except BlockingIOError: break\np.identity=lambda _: "+repr(ID)+"\nm.boundary('collect_entered',True)\nprint('BAD')\n")+")")
        self.assertEqual(result.returncode,72)
        self.assertEqual(result.stdout,b'')

    def test_short_write_actual_fatal_exit(self):
        result=self.child("import os, observation_protocol as p; r,w=os.pipe2(os.O_NONBLOCK); m=p.Marker(w,'a'*64,'b'*64); p.identity=lambda _: "+repr(ID)+"; p.os.write=lambda *args: 1; m.boundary('collect_entered',True); print('BAD')")
        self.assertEqual(result.returncode,72)
        self.assertEqual(result.stdout,b'')

    def test_private_log_exclusive_and_fsync_failure(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'observer.jsonl'
            log=p.PrivateLog(path)
            try:
                log.append({'event':'offline'})
                with self.assertRaises(FileExistsError): p.PrivateLog(path)
                with patch.object(p.os,'fsync',side_effect=OSError('synthetic')):
                    with self.assertRaises(OSError): log.append({'event':'partial'})
            finally: log.close()
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            self.assertIn(b'partial',path.read_bytes())

    def test_private_log_budget_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            log=p.PrivateLog(Path(root)/'log')
            try:
                log.used=p.LOG_LIMIT
                with self.assertRaises(p.Hold): log.append({'x':0})
            finally: log.close()
            alias=Path(root)/'alias'; alias.symlink_to(Path(root)/'log')
            with self.assertRaises(FileExistsError): p.PrivateLog(alias)

    def test_checked_source_drift_and_writable_mode(self):
        with tempfile.TemporaryDirectory() as root:
            anchor=Path(root)/'anchor.py'; source=Path(root)/'m.py'
            source.write_bytes(b'value=42\n')
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(p.load_source('m.py',digest,anchor).value,42)
            source.chmod(0o664)
            with self.assertRaises(p.Hold): p.load_source('m.py',digest,anchor)
            source.chmod(0o600); source.write_bytes(b'value=43\n')
            with self.assertRaises(p.Hold): p.load_source('m.py',digest,anchor)


class VariantControls(unittest.TestCase):
    def helper(self):
        spec=importlib.util.spec_from_file_location('observed_helper',HERE/'prebind_inventory_observed.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_collect_body_ast_preserved(self):
        original=ast.parse((HERE/'baseline'/'prebind_inventory.py').read_text())
        variant=ast.parse((HERE/'prebind_inventory_observed.py').read_text())
        before=next(x for x in original.body if isinstance(x,ast.FunctionDef) and x.name=='collect')
        after=next(x for x in variant.body if isinstance(x,ast.FunctionDef) and x.name=='_collect_body')
        after.name='collect'
        self.assertEqual(ast.dump(before),ast.dump(after))

    def test_marker_inside_collect_success_and_exception_finally(self):
        h=self.helper()
        class Observer:
            def __init__(self): self.events=[]
            def boundary(self,kind,ok): self.events.append((kind,ok))
        o=Observer()
        with patch.object(h,'_collect_body',return_value={'offline':True}):
            self.assertEqual(h.collect('x','x','x',health_port=18081,observation=o),{'offline':True})
        self.assertEqual(o.events,[('collect_entered',True),('collect_leaving',True)])
        o=Observer()
        with patch.object(h,'_collect_body',side_effect=ValueError('synthetic')):
            with self.assertRaises(ValueError): h.collect('x','x','x',health_port=18081,observation=o)
        self.assertEqual(o.events,[('collect_entered',True),('collect_leaving',False)])

    def test_helper_boundary_fault_actual_fatal_before_and_after_body(self):
        for fail in ('collect_entered','collect_leaving'):
            script="""import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('h',Path(%r)/'prebind_inventory_observed.py')
h=importlib.util.module_from_spec(s); s.loader.exec_module(h)
class Observer:
 def boundary(self,kind,ok):
  if kind==%r: raise OSError('SYNTHETIC_PRIVATE')
h._collect_body=lambda *a,**k: {}
h.collect('x','x','x',health_port=18081,observation=Observer())
print('BAD')
""" % (str(HERE),fail)
            result=subprocess.run([sys.executable,'-I','-S','-B','-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
            self.assertEqual(result.returncode,72)
            self.assertEqual(result.stdout,b'')
            self.assertEqual(result.stderr,b'')

    def test_all_python_candidates_compile(self):
        for path in HERE.glob('*.py'):
            compile(path.read_bytes(),str(path),'exec')

    def test_guest_wrapper_alarm_precedes_source_config_read(self):
        script=(f'import sys,signal; sys.path.insert(0,{str(HERE)!r}); '
                'import observer_guest as g; '
                'sys.argv=["test","--config","/synthetic"]; '
                'real=signal.setitimer; '
                'signal.setitimer=lambda kind,seconds: real(kind,0.03 if seconds==75 else seconds); '
                'g.read_config=lambda *_: signal.pause(); '
                'sys.exit(g.main())')
        result=subprocess.run([sys.executable,'-I','-S','-B','-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)
        self.assertEqual(result.returncode,73)
        self.assertEqual(result.stdout,b'')

    def controller_child(self,mode):
        script=(f'import sys,os,signal; sys.path.insert(0,{str(HERE)!r}); '
                'import inventory_control_observed as c; '
                'r,w=os.pipe2(os.O_NONBLOCK); '
                'sys.argv=["test","--root","/synthetic","--attempt-name","r1-remaining-offline",'
                '"--python-argv","/synthetic/.venv/bin/python","--health-port","18081",'
                '"--scope-start-epoch","0","--observation-fd",str(w),'
                '"--binding-sha256","a"*64,"--challenge","b"*64]; ')
        if mode=='worker_alarm':
            script+='sys.argv += ["--worker","--parent",str(os.getppid()),"--directory-identities","{}"]; '
        if mode in ('controller_alarm','worker_alarm'):
            seconds=60 if mode=='controller_alarm' else 40
            script+=f'real=signal.setitimer; signal.setitimer=lambda kind,seconds: real(kind,0.03 if seconds=={seconds} else seconds); c._load_observation_protocol=lambda: signal.pause(); '
        else:
            script+='sys.argv += ["--worker","--parent",str(os.getppid()),"--directory-identities","{}"]; '
        script+='sys.exit(c.main())'
        return subprocess.run([sys.executable,'-I','-S','-B','-c',script],input=b'',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3)

    def test_controller_alarm_covers_protocol_source_load(self):
        result=self.controller_child('controller_alarm')
        self.assertEqual(result.returncode,-__import__('signal').SIGALRM)
        self.assertEqual(result.stdout,b'')

    def test_worker_alarm_covers_protocol_source_load(self):
        result=self.controller_child('worker_alarm')
        self.assertEqual(result.returncode,-__import__('signal').SIGALRM)
        self.assertEqual(result.stdout,b'')

    def test_real_worker_no_g_never_collects(self):
        result=self.controller_child('no_g')
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout)['event'],'inventory_ready')
        self.assertNotIn(b'inventory_result',result.stdout)


class WrapperPipeControls(unittest.TestCase):
    """Real wrapper loop/pipes; controller and identity admission are fixtures.

    No inventory body, operator configuration, SSH or host sampling is invoked.
    These negative controls do not establish real worker adoption or transport.
    """
    def fixture(self, mode):
        frames = p.encode(event('worker_bound'))
        if mode == 'fast_leave':
            frames += p.encode(event('collect_entered')) + p.encode(event('collect_leaving'))
        elif mode == 'malformed':
            frames += b'{"kind":}\n'
        elif mode == 'partial_eof':
            frames += b'{"kind":'
        else:
            self.fail('unknown fixture')
        # A single atomic write queues the complete fixture before any drain.
        self.assertLessEqual(len(frames), p.FRAME_LIMIT)
        controller_script = (
            'import os,sys; fd=int(sys.argv[1]); '
            f'raw={frames!r}; assert os.write(fd,raw)==len(raw); os.close(fd)')
        with tempfile.TemporaryDirectory() as root:
            log_path = str(Path(root) / 'wrapper.jsonl')
            script = f'''
import os,sys,types
sys.path.insert(0,{str(HERE)!r})
import observer_guest as g
g.P=g._load_observation_protocol()
real_popen=g.subprocess.Popen
children=[]
def launch(argv,**kwargs):
    fd=kwargs['pass_fds'][0]
    child=real_popen([sys.executable,'-I','-S','-B','-c',{controller_script!r},str(fd)],**kwargs)
    children.append(child)
    return child
class FixtureTarget:
    def __init__(self,child,argv): self.child=child
    def send_signal(self,sig): self.child.send_signal(sig)
    def close(self): pass
class FixtureWorker:
    def __init__(self,*args): self.fd=os.open('/dev/null',os.O_RDONLY)
    def live(self): return True
g.subprocess.Popen=launch
g.P.load_source=lambda *args: types.SimpleNamespace(Target=FixtureTarget,SCOPE_FLAGS=tuple(g.P.FALSE_FLAGS))
g.ReadOnlyWorker=FixtureWorker
# Keep the host pipe open and empty: EOF must not mask the marker failure.
host_read,host_write=os.pipe()
sys.stdin=os.fdopen(host_read,'r')
try:
    code=g.run({{'log_path':{log_path!r},'binding_sha256':{'a'*64!r},'challenge':{'b'*64!r},
        'controller_python':sys.executable,'root':'/synthetic','attempt_name':'r1-remaining-fixture',
        'python_argv':sys.executable,'health_port':18081,'scope_start_epoch':0}})
    assert len(children)==1 and children[0].poll() is not None
finally:
    os.close(host_write)
    sys.stdin.close()
raise SystemExit(code)
'''
            result = subprocess.run([sys.executable,'-W','error::ResourceWarning','-I','-S','-B','-c',script],
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertEqual(result.stderr,b'')
            output = [p.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual([frame['kind'] for frame in output],['hold'])
            self.assertTrue(all(frame[key] is False for frame in output for key in p.FALSE_FLAGS))
            logged = [p.loads(line) for line in Path(log_path).read_bytes().splitlines()]
            self.assertEqual([frame['kind'] for frame in logged],
                             (['worker_bound','collect_entered','collect_leaving','hold']
                              if mode == 'fast_leave' else
                              ['hold'] if mode == 'malformed' else ['worker_bound','hold']))

    def test_wrapper_buffered_leaving_never_opens_or_resamples(self):
        self.fixture('fast_leave')

    def test_wrapper_malformed_real_pipe_holds(self):
        self.fixture('malformed')

    def test_wrapper_partial_marker_eof_holds(self):
        self.fixture('partial_eof')


class RequiredRealAdoptionControls(unittest.TestCase):
    def test_real_owned_child_pidfd_adoption(self):
        # This deliberately fails on incoherent procfs. No skip or predicate relaxation.
        import observer_guest as guest
        guest.P=guest._load_observation_protocol()
        controller=guest.P.load_source('inventory_control_observed.py',guest.CONTROLLER_SHA,guest.__file__)
        argv=[sys.executable,'-I','-S','-B','-c','import signal; signal.pause()']
        child=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        target=None
        try:
            target=controller.Target(child,argv)
            target.send_signal(__import__('signal').SIGTERM)
            child.communicate(timeout=2)
        finally:
            if child.poll() is None:
                child.terminate() # Test-only cleanup of the Popen child, not operational fallback.
                child.communicate(timeout=2)
            if target is not None: target.close()
            for stream in (child.stdin,child.stdout,child.stderr): stream.close()


if __name__=='__main__': unittest.main()
