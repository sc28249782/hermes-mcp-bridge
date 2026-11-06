"""One owned helper; context/job/context captures with no lock held for parent I/O."""
import os
import selectors
import subprocess
import time
import signal

from .owner import Hold, need, private_dir, open_file, unchanged, read_all, digest, _limits, _stop, _decode


class Batch:
    def __init__(self, rootfd, helperfd, helper_sha, deadline):
        self.rootfd,self.helperfd,self.helper_sha = rootfd,helperfd,helper_sha
        self.deadline=min(deadline,time.monotonic()+20)
        self.dbfd=self.ctxfd=self.pidfd=None
        self.proc=None
        self.selector=selectors.DefaultSelector()
        self.buffer=bytearray()
        self.stderr=bytearray()
        self.total=self.phase=0
        self.context=None
        self.finished=False

    def __enter__(self):
        try:
            private_dir(self.rootfd)
            need(digest(read_all(self.helperfd,4*1024*1024)) == self.helper_sha,'BINDING_MISMATCH')
            info=os.fstat(self.helperfd)
            need(info.st_uid == os.geteuid() and info.st_nlink == 1 and info.st_mode&0o7777 == 0o700)
            self.dbfd=open_file(self.rootfd,'opencode-tasks.sqlite3',64*1024*1024)
            self.ctxfd=open_file(self.rootfd,'contexts.sqlite3',64*1024*1024)
            self.proc=subprocess.Popen(['/proc/self/fd/'+str(self.helperfd),'--batch',str(self.dbfd),str(self.ctxfd),str(self.rootfd)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,
                pass_fds=(self.helperfd,self.dbfd,self.ctxfd,self.rootfd),shell=False,
                env={'LANG':'C','LC_ALL':'C','PATH':''},preexec_fn=_limits)
            self.pidfd=os.pidfd_open(self.proc.pid)
            for stream,name in ((self.proc.stdout,'stdout'),(self.proc.stderr,'stderr')):
                os.set_blocking(stream.fileno(),False)
                self.selector.register(stream,selectors.EVENT_READ,name)
            return self
        except BaseException:
            self.close()
            raise

    def _pump(self):
        need(time.monotonic() < self.deadline,'BUDGET_EXHAUSTED')
        events=self.selector.select(max(0,self.deadline-time.monotonic()))
        need(events,'BUDGET_EXHAUSTED')
        for event,_ in events:
            raw=os.read(event.fileobj.fileno(),4096)
            if not raw:
                self.selector.unregister(event.fileobj)
            elif event.data == 'stderr':
                need(len(self.stderr)+len(raw)<=4096)
                self.stderr.extend(raw)
            else:
                self.total+=len(raw)
                need(self.total<=65536)
                self.buffer.extend(raw)

    def request(self, role, target):
        need(not self.finished and self.phase<3 and role==('jobs' if self.phase==1 else 'context'))
        need(type(target) is str and 0<len(target)<=128 and all(c.isascii() and (c.isalnum() or c in '_.-') for c in target))
        if self.phase==0:self.context=target
        if self.phase==2:need(target==self.context)
        self.proc.stdin.write((role+'\n'+target+'\n').encode('ascii'))
        self.proc.stdin.flush()
        self.phase+=1
        if self.phase==3:self.proc.stdin.close()
        while len(self.buffer)<4:
            need(self.selector.get_map())
            self._pump()
        size=int.from_bytes(self.buffer[:4],'big')
        need(10<=size<=65536)
        while len(self.buffer)<size+4:
            need(self.selector.get_map())
            self._pump()
        raw=bytes(self.buffer[4:size+4]);del self.buffer[:size+4]
        need(not self.stderr)
        return _decode(raw,role)

    def finish(self):
        need(self.phase==3 and not self.finished)
        while self.selector.get_map():self._pump()
        self.proc.wait(timeout=max(0.001,self.deadline-time.monotonic()))
        need(self.proc.returncode==0 and not self.buffer and not self.stderr)
        unchanged(self.rootfd,'opencode-tasks.sqlite3',self.dbfd)
        unchanged(self.rootfd,'contexts.sqlite3',self.ctxfd)
        need(digest(read_all(self.helperfd,4*1024*1024))==self.helper_sha,'BINDING_MISMATCH')
        self.finished=True

    def close(self):
        self.selector.close()
        try:
            if self.proc is not None and self.proc.returncode is None:
                _stop(self.proc,self.pidfd,self.deadline+2)
        finally:
            if self.proc is not None:
                for stream in (self.proc.stdin,self.proc.stdout,self.proc.stderr):
                    if stream is not None:stream.close()
            for fd in (self.pidfd,self.dbfd,self.ctxfd):
                if fd is not None:os.close(fd)
            self.pidfd=self.dbfd=self.ctxfd=None

    def __exit__(self,*args):
        self.close()
