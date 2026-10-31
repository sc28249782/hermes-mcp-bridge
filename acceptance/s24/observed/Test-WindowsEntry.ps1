#requires -Version 7.0
# Exact host ENTRY/bootstrap/ACL/config writer/CIM; only transport executable is a fixture.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsWindows -or $env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') {
    throw 'entry fixture requires a new GitHub-hosted Windows CI driver'
}
. (Join-Path $PSScriptRoot 'HostSupport.ps1')
# Fixture precondition only. Default owner on elevated CI tokens can be Admins.
# Change only this newly launched driver's default owner, to its existing user
# SID; privileges/groups/user identity stay unchanged. Children inherit it.
Add-Type -Path (Join-Path $PSScriptRoot 'EntryFixtureOwner.cs')
[EntryFixtureOwner]::SetSelfDefaultOwner()
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
$pwsh=(Get-Process -Id $PID).Path
$root=Join-Path ([IO.Path]::GetTempPath()) ('s24-entry-'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $root
$acl=[Security.AccessControl.DirectorySecurity]::new()
$acl.SetOwner($sid); $acl.SetAccessRuleProtection($true,$false)
$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
Set-Acl -LiteralPath $root -AclObject $acl
$probe=Join-Path $root 'owner-probe'
[IO.File]::WriteAllText($probe,'fixture')
Assert-S24 ((Get-Acl -LiteralPath $probe).GetOwner([Security.Principal.SecurityIdentifier]).Value -ceq $sid.Value)
Assert-S24PrivateAcl $probe
$csc=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
Assert-S24 (Test-Path -LiteralPath $csc -PathType Leaf)
$exe=Join-Path $root 'transport.exe'
$compilerOutput=& $csc /nologo /warnaserror+ /target:exe ('/out:'+$exe) /reference:System.Web.Extensions.dll (Join-Path $PSScriptRoot 'EntryTransportFixture.cs') 2>&1
if ($LASTEXITCODE -ne 0) { $compilerOutput | Write-Output; throw 'entry fixture compiler failed' }
Assert-S24 ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $exe))
$pins=@{
    'Observe-S24Host.ps1'='8ea28ed095904039b778bdd0c9b97b65a369b7cd1148447a1657674a22eaca8c';
    'HostCoordinator.ps1'='38d8c10208b8816c95f46c21c7448db4f905d8967e2bc29bc4f8ec5392dc6151';
    'HostSupport.ps1'='9724d3ce4fb68f2172ce18ae9ed6006443077de94358aa46d1a23846f95f8180';
    'Read-S24HostSample.ps1'='79ed818637b4a26a07f36fca4c8645446a2a5eab7a6882f37cab610f130cc3b3';
    'HostMemory.psm1'='4509e645295f6b5748d9dbdbe2ab10221386ec4504c788a3bd121f574a5f09f8'}
$passed=0
$child=$null
foreach ($case in @('success','wrong_challenge','config_acl','coordinator_drift','sample_drift','existing_log')) {
    $dir=Join-Path $root $case
    $null=New-Item -ItemType Directory -Path $dir
    foreach ($name in $pins.Keys) {
        $source=Join-Path $PSScriptRoot $name
        Assert-S24 ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $pins[$name])
        Copy-Item -LiteralPath $source -Destination (Join-Path $dir $name)
        Assert-S24PrivateAcl (Join-Path $dir $name)
    }
    $transport=Join-Path $dir 'transport.exe'; Copy-Item -LiteralPath $exe -Destination $transport
    [IO.File]::WriteAllText((Join-Path $dir 'case.txt'),$case)
    $empty=Join-Path $dir 'empty.conf'; [IO.File]::WriteAllBytes($empty,[byte[]]::new(0))
    $identity=Join-Path $dir 'fixture-identity'; [IO.File]::WriteAllText($identity,'not a key')
    $known=Join-Path $dir 'fixture-known-hosts'; [IO.File]::WriteAllText($known,'fixture only')
    $cfg=@{binding='a'*64;challenge='b'*64;destination='fixture@invalid';port=2222;
        pwsh=$pwsh;ssh=$transport;identityFile=$identity;knownHosts=$known;sshConfigFile=$empty;
        modulePath=(Join-Path $dir 'HostMemory.psm1');outputDirectory=$dir;
        sampleScript=(Join-Path $dir 'Read-S24HostSample.ps1');guestPython='/fixture/python';
        guestScript='/fixture/observer.py';guestConfig='/fixture/config.json';
        permitOwnedSampleTermination=$false;permitOwnedSshTermination=$false}
    $config=Join-Path $dir 'config.json'
    [IO.File]::WriteAllText($config,(ConvertTo-Json -InputObject $cfg -Compress))
    Assert-S24PrivateAcl $config
    $hostLog=Join-Path $dir 'host-observer.jsonl'
    switch ($case) {
        'config_acl' {
            $bad=Get-Acl -LiteralPath $config
            $bad.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
                [Security.Principal.SecurityIdentifier]::new('S-1-1-0'),'Read','Allow'))
            Set-Acl -LiteralPath $config -AclObject $bad
        }
        'coordinator_drift' { [IO.File]::AppendAllText((Join-Path $dir 'HostCoordinator.ps1'),"`n# fixture drift`n") }
        'sample_drift' { [IO.File]::AppendAllText($cfg.sampleScript,"`n# fixture drift`n") }
        'existing_log' { [IO.File]::WriteAllText($hostLog,'preserve-fixture-log') }
    }
    try {
        $child=Start-S24Child $pwsh @('-NoLogo','-NoProfile','-NonInteractive','-File',
            (Join-Path $dir 'Observe-S24Host.ps1'),'-ConfigPath',$config)
        $child.Process.StandardInput.Close()
        if ($case -eq 'success') {
            $clock=[Diagnostics.Stopwatch]::StartNew()
            $result=Receive-S24Line $child $clock 100
            Wait-S24Exit $child $clock 100
            Assert-S24 ($result.status -ceq 'HOST_OBSERVATION_PENDING_REVIEW' -and $child.Queue.Count -eq 0)
            Assert-S24FalseFlags $result
            $records=@(Get-Content -LiteralPath $hostLog | ForEach-Object { ConvertFrom-S24Json $_ })
            Assert-S24 ($records.Count -eq 6)
            $samples=@($records | Where-Object { $_.ContainsKey('phase') })
            Assert-S24 (($samples.phase -join ',') -ceq 'before,during,after')
            foreach ($sample in $samples) {
                Assert-S24 ($sample.evidence_class -ceq 'local-read-only-windows-host-memory' -and $sample.elapsed_seconds -le 1)
                Assert-S24 ($sample.host_available_bytes -ge 1610612736 -and $sample.host_limit_failures.Count -eq 0)
            }
            Assert-S24 ([IO.File]::ReadAllText((Join-Path $dir 'peer.trace')) -ceq "started`npost-received`n")
        } else {
            $rejected=$false
            try { $null=Receive-S24Line $child ([Diagnostics.Stopwatch]::StartNew()) 100 } catch { $rejected=$true }
            Assert-S24 ($child.Process.WaitForExit(10000) -and $child.Process.ExitCode -eq 2 -and $rejected)
            Assert-S24 (-not (Test-Path -LiteralPath (Join-Path $dir 'sample-after.json')))
            if ($case -eq 'wrong_challenge') {
                Assert-S24 ([IO.File]::ReadAllText((Join-Path $dir 'peer.trace')) -ceq "started`n")
                Assert-S24 (Test-Path -LiteralPath (Join-Path $dir 'sample-before.json'))
                Assert-S24 (-not (Test-Path -LiteralPath (Join-Path $dir 'sample-during.json')))
            } else {
                Assert-S24 (-not (Test-Path -LiteralPath (Join-Path $dir 'peer.trace')))
                Assert-S24 (-not (Test-Path -LiteralPath (Join-Path $dir 'sample-before.json')))
            }
            if ($case -eq 'existing_log') { Assert-S24 ([IO.File]::ReadAllText($hostLog) -ceq 'preserve-fixture-log') }
        }
        Close-S24Child $child $false; $child=$null
        $passed++
        [Console]::Out.WriteLine((ConvertTo-Json -Compress @{evidence_class='windows-entry-cim-fixture-transport';
            case=$case;held=($case -ne 'success');default_owner_fixture=$true;
            r1_complete=$false;r2_authorized=$false;authenticated=$false;scope_granted=$false}))
    } catch {
        [Console]::Error.WriteLine('Entry fixture failed: '+$case)
        [Console]::Error.WriteLine($_.ScriptStackTrace)
        throw
    } finally {
        if ($null -ne $child) { Close-S24Child $child $true } # New test-owned entry child only.
    }
}
Assert-S24 ($passed -eq 6)
[Console]::Out.WriteLine("Windows entry controls: $passed cases passed; exact bootstrap and real CIM; fixture transport only")
