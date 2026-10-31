"""Disposable GitHub-hosted Linux CI only. Never run against an operator host.

Creates a NEW fixture account/private keys and foreground loopback sshd; changes
no existing account, SSH config, service, credential or authorized_keys. No key
bytes/server logs are printed or uploaded. No SSH attempt is retried. This tests
the production host coordinator/client argv, not Windows/CIM/collect integration.
"""
import json
import os
from pathlib import Path
import pwd
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
ACCOUNT='s24carrier'
PORT=22229


def require(value):
    if not value: raise RuntimeError('CI carrier fixture incomplete; preserve evidence')


def command(argv,**kwargs):
    value=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=False,**kwargs)
    require(value.returncode==0)
    return value


def uid_processes(uid):
    found=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit(): continue
        try:
            if path.stat().st_uid==uid: found.append(path.name)
        except FileNotFoundError:
            pass  # Concurrent exit during test-only cleanup inventory.
    return found


def main():
    require(os.geteuid()==0 and os.environ.get('GITHUB_ACTIONS')=='true'
            and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted'
            and os.environ.get('RUNNER_OS')=='Linux')
    tools={name:shutil.which(name) for name in ('ssh','sshd','ssh-keygen','pwsh','useradd','userdel')}
    require(all(tools.values()))
    tools={name:str(Path(path).resolve(strict=True)) for name,path in tools.items()}
    try: pwd.getpwnam(ACCOUNT)
    except KeyError: pass
    else: raise RuntimeError('fixture account already exists; no reuse')
    root=Path(tempfile.mkdtemp(prefix='s24-ssh-carrier-'))
    server=server_pidfd=server_log=None
    created_account=False
    created_runtime=False
    account=None
    try:
        home=root/'home'; home.mkdir(mode=0o700)
        # 'x' is an invalid password hash, not a usable password. SSH password,
        # PAM and keyboard-interactive authentication are independently disabled.
        command([tools['useradd'],'--no-create-home','--home-dir',str(home),
                 '--shell','/bin/sh','--password','x','--user-group',ACCOUNT])
        created_account=True; account=pwd.getpwnam(ACCOUNT)
        os.chown(root,account.pw_uid,account.pw_gid)
        os.chown(home,account.pw_uid,account.pw_gid)
        for name in ('host','client','wrong-host'):
            command([tools['ssh-keygen'],'-q','-t','ed25519','-N','','-f',str(root/name)])
        public=(root/'client.pub').read_text().split()
        (home/'authorized_keys').write_text(' '.join(public[:2])+'\n')
        for name,key in (('known_hosts','host.pub'),('wrong_known_hosts','wrong-host.pub')):
            fields=(root/key).read_text().split()
            (root/name).write_text(f'[127.0.0.1]:{PORT} '+' '.join(fields[:2])+'\n')
        (root/'empty.conf').write_bytes(b'')
        shutil.copyfile(HERE/'ssh_contract_peer.py',root/'peer.py')
        peer_config=root/'peer.json'
        peer_config.write_text('{}\n')
        force=shlex.join([str(Path(sys.executable).resolve()),'-I','-S','-B',str(root/'peer.py'),str(peer_config)])
        server_config=root/'sshd.conf'
        server_config.write_text('\n'.join([
            f'Port {PORT}','ListenAddress 127.0.0.1',f'HostKey {root}/host',f'PidFile {root}/sshd.pid',
            f'AuthorizedKeysFile {home}/authorized_keys','StrictModes yes','UsePAM no',
            'PasswordAuthentication no','KbdInteractiveAuthentication no','PubkeyAuthentication yes',
            'PermitRootLogin no',f'AllowUsers {ACCOUNT}','DisableForwarding yes','PermitTTY no',
            'PermitUserRC no','PermitUserEnvironment no','MaxSessions 1','MaxAuthTries 1',
            'LoginGraceTime 5','LogLevel INFO',f'ForceCommand {force}','']))
        for path in root.rglob('*'):
            if path.is_file(): path.chmod(0o600); os.chown(path,account.pw_uid,account.pw_gid)
        # Stock sshd requires this privilege-separation runtime directory. Create
        # only if absent, never chmod/replace an existing system directory.
        runtime=Path('/run/sshd')
        if not runtime.exists(): runtime.mkdir(mode=0o755); created_runtime=True
        require(runtime.is_dir() and not runtime.is_symlink())
        command([tools['sshd'],'-t','-f',str(server_config)])
        server_log=(root/'server.log').open('wb')
        server=subprocess.Popen([tools['sshd'],'-D','-e','-f',str(server_config)],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=server_log,start_new_session=True,
            env={'PATH':'/usr/bin:/bin','LANG':'C'})
        server_pidfd=os.pidfd_open(server.pid)
        deadline=time.monotonic()+5
        while b'Server listening on 127.0.0.1' not in (root/'server.log').read_bytes():
            require(server.poll() is None and time.monotonic()<deadline)
            time.sleep(0.01) # Bounded server-start observation only; not an inventory delay.
        receipts=[]
        for case in ('success','wrong_challenge','unknown_host'):
            output=root/case; output.mkdir(mode=0o700)
            trace=root/(case+'.peer-trace')
            cfg={'binding':'a'*64,'challenge':'b'*64,'modulePath':'fixture-only',
                'outputDirectory':str(output),'pwsh':tools['pwsh'],
                'sampleScript':str(HERE/'host_flow_fixture.ps1'),'ssh':tools['ssh'],
                'sshConfigFile':str(root/'empty.conf'),'port':PORT,'identityFile':str(root/'client'),
                'knownHosts':str(root/('wrong_known_hosts' if case=='unknown_host' else 'known_hosts')),
                'destination':ACCOUNT+'@127.0.0.1','guestPython':'/fixture/python',
                'guestScript':'/fixture/observer.py','guestConfig':'/fixture/config.json'}
            remote="'/fixture/python' -I -S -B '/fixture/observer.py' --config '/fixture/config.json'"
            peer_config.write_text(json.dumps({'case':case,'trace':str(trace),'expected_command':remote}))
            spec=output/'fixture.json'; spec.write_text(json.dumps({'case':case,'config':cfg}))
            # This small sample script is a fixture producer, never real CIM.
            # Its role/case parameters must be explicit; use a new per-case wrapper.
            sample=output/'sample.ps1'
            sample.write_text("param([string] $ConfigPath)\n& "+"'"+str(HERE/'host_flow_fixture.ps1')+
                "' -Role sample -ConfigPath $ConfigPath -Case success -TracePath 'fixture-unused'\n")
            cfg['sampleScript']=str(sample); spec.write_text(json.dumps({'case':case,'config':cfg}))
            child=subprocess.Popen([tools['pwsh'],'-NoLogo','-NoProfile','-NonInteractive','-File',
                str(HERE/'Test-SshCarrier.ps1'),'-FixtureConfig',str(spec)],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:
                out,err=child.communicate(timeout=105)
            except subprocess.TimeoutExpired:
                require(os.getpgid(child.pid)==child.pid)
                os.killpg(child.pid,signal.SIGTERM) # Only the newly owned CI driver session.
                child.communicate(timeout=5)
                raise RuntimeError('carrier fixture deadline; no retry')
            require(child.returncode==0 and err==b'')
            receipt=json.loads(out)
            require(receipt['case']==case and receipt['held']==(case!='success'))
            require(all(receipt[k] is False for k in ('r1_complete','r2_authorized','authenticated',
                'host_identity_proved','scope_granted','complete_writer_coverage')))
            if case=='success': require(trace.read_text()=='started\npost-received\n')
            elif case=='wrong_challenge': require(trace.read_text()=='started\n')
            else: require(not trace.exists()) # Unknown host key never starts the forced peer.
            receipts.append(receipt)
            print(json.dumps(receipt),flush=True)
        require(len(receipts)==3)
        print('SSH carrier controls: 3 cases passed; disposable CI loopback; fixture peer/sample only',flush=True)
        return 0
    finally:
        if server is not None:
            if server.poll() is None: signal.pidfd_send_signal(server_pidfd,signal.SIGTERM)
            server.wait(timeout=5)
        if server_pidfd is not None: os.close(server_pidfd)
        if server_log is not None: server_log.close()
        if created_account:
            # Never delete/reuse an account with remaining fixture-UID processes.
            deadline=time.monotonic()+5
            while uid_processes(account.pw_uid):
                require(time.monotonic()<deadline)
                time.sleep(0.01)
            require(pwd.getpwnam(ACCOUNT).pw_uid==account.pw_uid)
            command([tools['userdel'],ACCOUNT])
        if created_runtime: Path('/run/sshd').rmdir()
        # Preserve private fixture files for runner teardown, never upload keys/logs.


if __name__=='__main__': raise SystemExit(main())
