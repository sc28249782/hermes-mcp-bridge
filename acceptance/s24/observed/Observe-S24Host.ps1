#requires -Version 7.0
param([Parameter(Mandatory)][string] $ConfigPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Bootstrap compiles exactly checked bytes; no dot-source reopening after hashing.
function Import-CheckedSupport([string] $Path, [string] $Digest='5b894a5563dd1ed1f9cbc0bf99e924065f90a53f5cf88b22d5711e93e4a52f7e') {
    $item=Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'HOLD: support path' }
        if ($item -is [IO.FileInfo]) { $item=$item.Directory } else { $item=$item.Parent }
    }
    $s=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        if ($s.Length -gt 131072) { throw 'HOLD: support size' }
        $b=[byte[]]::new([int]$s.Length); $i=0
        while ($i -lt $b.Length) { $n=$s.Read($b,$i,$b.Length-$i); if ($n -le 0) { throw 'HOLD: support read' }; $i+=$n }
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b)).ToLowerInvariant() -cne $Digest) { throw 'HOLD: support hash' }
        return [scriptblock]::Create([Text.UTF8Encoding]::new($false,$true).GetString($b))
    } finally { $s.Dispose() }
}
$sshChild=$sampleChild=$samplePin=$emptyConfig=$null
$log=$null
$coordinatorState=$null
$clock=[Diagnostics.Stopwatch]::StartNew()
$used=0
try {
    if (-not $IsWindows) { throw 'HOLD: Windows required' }
    . (Import-CheckedSupport (Join-Path $PSScriptRoot 'HostSupport.ps1'))
    Assert-S24PrivateAcl (Join-Path $PSScriptRoot 'HostSupport.ps1')
    Assert-S24PrivateAcl (Join-Path $PSScriptRoot 'HostCoordinator.ps1')
    . (Import-CheckedSupport (Join-Path $PSScriptRoot 'HostCoordinator.ps1') 'f093a18b78693e98e1c5d3ce1f32fc62c41b184092d22b3f9a9ec810d651b2df')
    Assert-S24PrivateAcl $ConfigPath
    $cfg=Read-S24Config $ConfigPath
    $wanted='binding,challenge,destination,guestConfig,guestPython,guestScript,identityFile,knownHosts,modulePath,outputDirectory,permitOwnedSampleTermination,permitOwnedSshTermination,port,pwsh,sampleScript,ssh,sshConfigFile'
    Assert-S24 ((($cfg.Keys | Sort-Object) -join ',') -ceq $wanted)
    Assert-S24 ($cfg.binding -is [string] -and $cfg.binding -cmatch '\A[a-f0-9]{64}\z' -and $cfg.challenge -is [string] -and $cfg.challenge -cmatch '\A[a-f0-9]{64}\z')
    Assert-S24 ($cfg.port -is [long] -and $cfg.port -ge 1 -and $cfg.port -le 65535)
    Assert-S24 ($cfg.destination -is [string] -and $cfg.destination -cmatch '\A[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+\z')
    Assert-S24 ($cfg.permitOwnedSampleTermination -is [bool] -and $cfg.permitOwnedSshTermination -is [bool])
    foreach ($name in @('pwsh','ssh','identityFile','knownHosts','modulePath','outputDirectory','sampleScript','sshConfigFile')) { Assert-S24NoReparse $cfg[$name] }
    foreach ($name in @('modulePath','outputDirectory','sampleScript','sshConfigFile')) { Assert-S24PrivateAcl $cfg[$name] }
    foreach ($name in @('guestPython','guestScript','guestConfig')) {
        Assert-S24 ($cfg[$name] -is [string] -and $cfg[$name] -cmatch '\A/[A-Za-z0-9_./-]+\z' -and $cfg[$name] -notmatch '(^|/)\.\.?(?:/|$)|//')
    }
    # Empty, separately staged SSH config prevents Match/exec or implicit configuration hooks.
    $emptyConfig=Open-S24Pinned $cfg.sshConfigFile 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    $samplePin=Open-S24Pinned $cfg.sampleScript 'b1c8387dca6c864066b0e58e345a9ba5f8cb1844e06c5211fd227b919745e321'
    $logPath=Join-Path $cfg.outputDirectory 'host-observer.jsonl'
    $log=[IO.FileStream]::new($logPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough)
    Assert-S24PrivateAcl $logPath

    $coordinatorState=@{Config=$cfg;Clock=$clock;Log=$log;Used=0;SampleChild=$null;SshChild=$null}
    Invoke-S24HostCoordinator $coordinatorState
    [Console]::Out.WriteLine('{"status":"HOST_OBSERVATION_PENDING_REVIEW","r1_complete":false,"r2_authorized":false,"authenticated":false,"scope_granted":false,"complete_writer_coverage":false,"host_identity_proved":false}')
} catch {
    [Console]::Error.WriteLine('HOLD: host observer incomplete; preserve files; no retry.')
    exit 2
} finally {
    if ($null -ne $coordinatorState) {
        $sshChild=$coordinatorState.SshChild
        $sampleChild=$coordinatorState.SampleChild
    }
    # Termination flags are caller data, not authorization. Both must be bound to
    # a future finite scope; no child-tree, existing service or provider termination.
    foreach ($pair in @(@($sampleChild,'permitOwnedSampleTermination'),@($sshChild,'permitOwnedSshTermination'))) {
        if ($null -ne $pair[0]) {
            try { Close-S24Child $pair[0] ($cfg[$pair[1]] -is [bool] -and $cfg[$pair[1]]) }
            catch { [Console]::Error.WriteLine('HOLD: owned child stop unconfirmed.') }
        }
    }
    if ($null -ne $samplePin) { $samplePin.Stream.Dispose() }
    if ($null -ne $emptyConfig) { $emptyConfig.Stream.Dispose() }
    if ($null -ne $log) { $log.Dispose() }
}
