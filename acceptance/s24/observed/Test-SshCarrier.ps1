#requires -Version 7.0
# Linux CI only: actual production coordinator/support + real OpenSSH client.
# Windows bootstrap/ACL and actual CIM/collect are deliberately outside this test.
param([Parameter(Mandatory)][string] $FixtureConfig)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsLinux -or $env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') {
    throw 'carrier fixture requires GitHub-hosted Linux CI'
}
. (Join-Path $PSScriptRoot 'HostSupport.ps1')
$digest=(Get-FileHash (Join-Path $PSScriptRoot 'HostCoordinator.ps1') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($digest -cne '38d8c10208b8816c95f46c21c7448db4f905d8967e2bc29bc4f8ec5392dc6151') { throw 'coordinator pin drift' }
. (Join-Path $PSScriptRoot 'HostCoordinator.ps1')
$fixture=ConvertFrom-Json ([IO.File]::ReadAllText($FixtureConfig)) -AsHashtable
$cfg=$fixture.config
$script:phases=[Collections.Generic.List[string]]::new()
# The new-config writer is the only overridden operation. Get-Acl is Windows-
# specific; fixture preparation on Linux never stands in for bootstrap ACL proof.
function Write-S24New([string] $Path,[string] $Text) {
    $script:phases.Add((ConvertFrom-Json $Text -AsHashtable).phase)
    $s=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try {
        $bytes=[Text.Encoding]::UTF8.GetBytes($Text)
        $s.Write($bytes,0,$bytes.Length); $s.Flush($true)
    } finally { $s.Dispose() }
    [IO.File]::SetUnixFileMode($Path,[IO.UnixFileMode]::UserRead -bor [IO.UnixFileMode]::UserWrite)
}
$log=[IO.FileStream]::new((Join-Path $cfg.outputDirectory 'carrier-log.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
$state=@{Config=$cfg;Clock=[Diagnostics.Stopwatch]::StartNew();Log=$log;Used=0;SampleChild=$null;SshChild=$null}
try {
    $failed=$false
    try { Invoke-S24HostCoordinator $state } catch { $failed=$true }
    Assert-S24 ($failed -eq ($fixture.case -ne 'success'))
    Assert-S24 ($state.Held -eq $failed)
    if (-not $failed) {
        Assert-S24 (($phases -join ',') -ceq 'before,during,after')
        Assert-S24 ($null -eq $state.SampleChild -and $null -eq $state.SshChild)
        $log.Flush($true)
        $records=@(Get-Content -LiteralPath (Join-Path $cfg.outputDirectory 'carrier-log.jsonl') | ForEach-Object { ConvertFrom-S24Json $_ })
        Assert-S24 ($records.Count -eq 6)
    } else { Assert-S24 (-not $phases.Contains('after')) }
    $again=$false
    try { Invoke-S24HostCoordinator $state } catch { $again=$true }
    Assert-S24 ($again -and $state.Held)
    [Console]::Out.WriteLine((ConvertTo-Json -Compress @{evidence_class='host-coordinator-openssh-loopback-fixture';
        case=$fixture.case;held=$failed;phases=@($phases);r1_complete=$false;r2_authorized=$false;
        authenticated=$false;host_identity_proved=$false;scope_granted=$false;complete_writer_coverage=$false}))
} finally {
    foreach ($name in @('SampleChild','SshChild')) {
        if ($null -ne $state[$name]) { Close-S24Child $state[$name] $true } # Test-owned direct children only.
    }
    $log.Dispose()
}
