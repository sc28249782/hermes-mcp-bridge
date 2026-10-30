#requires -Version 7.0
# Actual coordinator and support I/O; fixture process factory/config writer only.
# No real SSH, CIM, operator path or authorization is involved in this runner.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsWindows) { throw 'Windows coordinator controls require Windows' }
foreach ($name in @('HostCoordinator.ps1','host_flow_fixture.ps1','Observe-S24Host.ps1')) {
    $tokens=$errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name),[ref]$tokens,[ref]$errors)
    if ($errors.Count -ne 0) { throw 'coordinator source parse failed' }
}
$digest=(Get-FileHash (Join-Path $PSScriptRoot 'HostCoordinator.ps1') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($digest -cne '38d8c10208b8816c95f46c21c7448db4f905d8967e2bc29bc4f8ec5392dc6151') { throw 'coordinator source hash failed' }
. (Join-Path $PSScriptRoot 'HostSupport.ps1')
. (Join-Path $PSScriptRoot 'HostCoordinator.ps1')
$script:originalStart=(Get-Command Start-S24Child).ScriptBlock
$script:pwsh=(Get-Process -Id $PID).Path
$script:producer=Join-Path $PSScriptRoot 'host_flow_fixture.ps1'

function Write-S24New([string] $Path,[string] $Text) {
    # Explicit preparation of NEW fixtures for elevated CI default-owner tokens.
    # Production Write-S24New is not modified or tested by this substitution.
    $bytes=[Text.Encoding]::UTF8.GetBytes($Text)
    $s=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try { $s.Write($bytes,0,$bytes.Length); $s.Flush($true) } finally { $s.Dispose() }
    $acl=Get-Acl -LiteralPath $Path
    $acl.SetOwner([Security.Principal.WindowsIdentity]::GetCurrent().User)
    Set-Acl -LiteralPath $Path -AclObject $acl
}
function Start-S24Child([string] $Executable,[string[]] $Arguments) {
    $script:starts++
    if ($Executable -ceq 'fixture:sample') {
        $path=$Arguments[-1]
        $sampleCfg=ConvertFrom-Json ([IO.File]::ReadAllText($path)) -AsHashtable
        $script:phases.Add($sampleCfg.phase)
        if ($script:case -eq 'log_closed_during' -and $sampleCfg.phase -eq 'during') { $script:state.Log.Dispose() }
        return & $script:originalStart $script:pwsh @('-NoLogo','-NoProfile','-NonInteractive',
            '-File',$script:producer,'-Role','sample','-ConfigPath',$path,'-Case',$script:case,'-TracePath',$script:trace)
    }
    Assert-S24 ($Executable -ceq 'fixture:transport' -and $Arguments[0] -ceq '-T')
    foreach ($flag in @('BatchMode=yes','StrictHostKeyChecking=yes','UpdateHostKeys=no',
        'IdentitiesOnly=yes','IdentityAgent=none','ForwardAgent=no','ClearAllForwardings=yes',
        'ControlMaster=no','ControlPath=none','PermitLocalCommand=no','ConnectTimeout=5')) {
        Assert-S24 ($Arguments -ccontains $flag)
    }
    return & $script:originalStart $script:pwsh @('-NoLogo','-NoProfile','-NonInteractive',
        '-File',$script:producer,'-Role','transport','-ConfigPath',$script:transportCfg,
        '-Case',$script:case,'-TracePath',$script:trace)
}
$cases=@('success','provider_low','provider_elapsed','provider_missing','provider_corrupt',
    'provider_stderr','provider_blocked','provider_wrong_binding','transport_wrong_challenge',
    'transport_eof','transport_corrupt','transport_partial','transport_flood',
    'log_closed_before','log_closed_during','log_budget')
$passed=0
foreach ($script:case in $cases) {
    $root=Join-Path ([IO.Path]::GetTempPath()) ('s24-coordinator-'+[Guid]::NewGuid().ToString('N'))
    $null=New-Item -ItemType Directory -Path $root
    $script:trace=Join-Path $root 'transport-fixture.trace'
    $script:transportCfg=Join-Path $root 'transport.json'
    Write-S24New $script:transportCfg '{"binding":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","challenge":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}'
    $cfg=@{binding='a'*64;challenge='b'*64;modulePath='fixture-module';outputDirectory=$root;
        pwsh='fixture:sample';sampleScript='fixture-sample';ssh='fixture:transport';
        sshConfigFile='fixture-empty-config';port=2222;identityFile='fixture-identity';
        knownHosts='fixture-known-hosts';destination='fixture@invalid';guestPython='/fixture/python';
        guestScript='/fixture/observer.py';guestConfig='/fixture/config.json'}
    $stream=[IO.FileStream]::new((Join-Path $root 'log.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    $script:state=@{Config=$cfg;Clock=[Diagnostics.Stopwatch]::StartNew();Log=$stream;
        Used=0;SampleChild=$null;SshChild=$null}
    $script:starts=0
    $script:phases=[Collections.Generic.List[string]]::new()
    if ($case -eq 'log_closed_before') { $stream.Dispose() }
    if ($case -eq 'log_budget') { $state.Used=65536 }
    try {
        $failed=$false
        try { Invoke-S24HostCoordinator $state } catch { $failed=$true }
        Assert-S24 ($failed -eq ($case -ne 'success'))
        Assert-S24 ($state.Held -eq $failed)
        if ($case -eq 'success') {
            Assert-S24 (($phases -join ',') -ceq 'before,during,after')
            Assert-S24 ($starts -eq 4 -and $null -eq $state.SampleChild -and $null -eq $state.SshChild)
            Assert-S24 ([IO.File]::ReadAllText($trace) -ceq "post-received`n")
            $stream.Flush($true)
            $records=@(Get-Content -LiteralPath (Join-Path $root 'log.jsonl') | ForEach-Object { ConvertFrom-S24Json $_ })
            Assert-S24 ($records.Count -eq 6)
        } else {
            Assert-S24 (-not $phases.Contains('after'))
            Assert-S24 (-not [IO.File]::Exists($trace))
            if ($case -in @('log_closed_before','log_budget')) { Assert-S24 ($starts -eq 1) }
        }
        $count=$starts
        $rejected=$false
        try { Invoke-S24HostCoordinator $state } catch { $rejected=$true }
        Assert-S24 ($rejected -and $state.Held -and $starts -eq $count)
        $passed++
        [Console]::Out.WriteLine((ConvertTo-Json -Compress @{evidence_class='host-coordinator-fixture-result';
            case=$case;held=$failed;starts=$starts;phases=@($phases);r1_complete=$false;r2_authorized=$false}))
    } catch {
        [Console]::Error.WriteLine('Coordinator fixture failed: '+$case)
        [Console]::Error.WriteLine($_.ScriptStackTrace)
        throw
    } finally {
        foreach ($name in @('SampleChild','SshChild')) {
            if ($null -ne $state[$name]) {
                if ($case -eq 'provider_blocked' -and $name -eq 'SampleChild') {
                    Assert-S24 (-not $state[$name].Process.HasExited)
                    $refused=$false
                    try { Close-S24Child $state[$name] $false } catch { $refused=$true }
                    Assert-S24 $refused
                }
                Close-S24Child $state[$name] $true # Test-owned children only; no runtime authority.
                $state[$name]=$null
            }
        }
        $stream.Dispose()
    }
}
Assert-S24 ($passed -eq 16)
[Console]::Out.WriteLine("Windows coordinator controls: $passed cases passed; process/config fixtures; no SSH/CIM/operator evidence")
