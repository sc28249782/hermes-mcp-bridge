#requires -Version 7.0
param([Parameter(Mandatory)][string] $ConfigPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Bootstrap compiles exactly checked bytes; no dot-source reopening after hashing.
function Import-CheckedSupport([string] $Path) {
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
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b)).ToLowerInvariant() -cne '5b894a5563dd1ed1f9cbc0bf99e924065f90a53f5cf88b22d5711e93e4a52f7e') { throw 'HOLD: support hash' }
        return [scriptblock]::Create([Text.UTF8Encoding]::new($false,$true).GetString($b))
    } finally { $s.Dispose() }
}
$sshChild=$sampleChild=$samplePin=$emptyConfig=$null
$log=$null
$clock=[Diagnostics.Stopwatch]::StartNew()
$used=0
try {
    if (-not $IsWindows) { throw 'HOLD: Windows required' }
    . (Import-CheckedSupport (Join-Path $PSScriptRoot 'HostSupport.ps1'))
    Assert-S24PrivateAcl (Join-Path $PSScriptRoot 'HostSupport.ps1')
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

    function Write-Observation($Value) {
        $bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $Value -Compress -Depth 20)+"`n")
        $script:used+=$bytes.Length
        Assert-S24 ($script:used -le 65536)
        $script:log.Write($bytes,0,$bytes.Length)
        $script:log.Flush($true)
    }

    function Get-OneSample([string] $Phase) {
        Assert-S24 ($clock.Elapsed.TotalSeconds -lt 92)
        $sampleCfg=Join-Path $cfg.outputDirectory ("sample-"+$Phase+".json")
        $spec=@{binding=$cfg.binding;challenge=$cfg.challenge;modulePath=$cfg.modulePath;phase=$Phase}
        Write-S24New $sampleCfg (ConvertTo-Json -InputObject $spec -Compress)
        $deadline=[Math]::Min(95,$clock.Elapsed.TotalSeconds+3)
        $script:sampleChild=Start-S24Child $cfg.pwsh @('-NoLogo','-NoProfile','-NonInteractive','-File',$cfg.sampleScript,'-ConfigPath',$sampleCfg)
        $script:sampleChild.Process.StandardInput.Close()
        Assert-S24 ($clock.Elapsed.TotalSeconds -lt $deadline)
        $sample=Receive-S24Line $script:sampleChild $clock $deadline
        Wait-S24Exit $script:sampleChild $clock $deadline
        Assert-S24 ($script:sampleChild.Queue.Count -eq 0)
        foreach ($name in @('evidence_class','binding_sha256','challenge','phase')) { Assert-S24 ($sample[$name] -is [string]) }
        Assert-S24 ($sample.evidence_class -ceq 'local-read-only-windows-host-memory' -and $sample.binding_sha256 -ceq $cfg.binding -and $sample.challenge -ceq $cfg.challenge -and $sample.phase -ceq $Phase)
        foreach ($name in @('full_checkpoint_pass','host_identity_proved','authenticated','guest_observed','original_runtime_continuity_observed','complete_writer_coverage')) {
            Assert-S24 ($sample[$name] -is [bool] -and -not $sample[$name])
        }
        Assert-S24 ($sample.host_available_bytes -is [long] -and $sample.host_available_bytes -ge 1610612736 -and $sample.host_total_visible_bytes -is [long] -and $sample.host_total_visible_bytes -ge $sample.host_available_bytes)
        Assert-S24 (($sample.elapsed_seconds -is [double] -or $sample.elapsed_seconds -is [long]) -and [double]::IsFinite([double]$sample.elapsed_seconds))
        Assert-S24 ($sample.host_limit_failures -is [array] -and $sample.host_limit_failures.Count -eq 0 -and $sample.elapsed_seconds -ge 0 -and $sample.elapsed_seconds -le 1)
        Write-Observation $sample
        Close-S24Child $script:sampleChild $false
        $script:sampleChild=$null
    }

    function Receive-Transport([string] $Kind) {
        $frame=Receive-S24Line $sshChild $clock 95
        foreach ($name in @('kind','binding','challenge')) { Assert-S24 ($frame[$name] -is [string]) }
        Assert-S24 ($frame.binding -ceq $cfg.binding -and $frame.challenge -ceq $cfg.challenge -and $frame.kind -ceq $Kind)
        Assert-S24FalseFlags $frame
        $expected=@('kind','binding','challenge','r1_complete','r2_authorized','authenticated','complete_writer_coverage','host_identity_proved','scope_granted')
        if ($Kind -ceq 'observation_complete_pending_review') { $expected+= 'receipt_sha256'; Assert-S24 ($frame.receipt_sha256 -is [string] -and $frame.receipt_sha256 -cmatch '\A[a-f0-9]{64}\z') }
        Assert-S24 ((($frame.Keys|Sort-Object)-join ',') -ceq (($expected|Sort-Object)-join ','))
        Write-Observation $frame
    }

    Get-OneSample 'before'
    $remote="'"+$cfg.guestPython+"' -I -S -B '"+$cfg.guestScript+"' --config '"+$cfg.guestConfig+"'"
    $arguments=@('-T','-F',$cfg.sshConfigFile,'-p',[string]$cfg.port,'-i',$cfg.identityFile,
        '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o',('UserKnownHostsFile='+$cfg.knownHosts),
        '-o','UpdateHostKeys=no','-o','CheckHostIP=no',
        '-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
        '-o','ControlMaster=no','-o','ControlPath=none','-o','PermitLocalCommand=no','-o','ConnectTimeout=5',
        $cfg.destination,$remote)
    $sshChild=Start-S24Child $cfg.ssh $arguments
    Receive-Transport 'sample_window_open'
    Get-OneSample 'during'
    $message=@{kind='check_window_after';binding=$cfg.binding;challenge=$cfg.challenge}
    $sshChild.Process.StandardInput.WriteLine((ConvertTo-Json -InputObject $message -Compress))
    $sshChild.Process.StandardInput.Flush()
    Receive-Transport 'window_confirmed'
    Receive-Transport 'observation_complete_pending_review'
    $sshChild.Process.StandardInput.Close()
    Wait-S24Exit $sshChild $clock 95
    Assert-S24 ($sshChild.Queue.Count -eq 0)
    Close-S24Child $sshChild $false
    $sshChild=$null
    Get-OneSample 'after'
    [Console]::Out.WriteLine('{"status":"HOST_OBSERVATION_PENDING_REVIEW","r1_complete":false,"r2_authorized":false,"authenticated":false,"scope_granted":false,"complete_writer_coverage":false,"host_identity_proved":false}')
} catch {
    [Console]::Error.WriteLine('HOLD: host observer incomplete; preserve files; no retry.')
    exit 2
} finally {
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
