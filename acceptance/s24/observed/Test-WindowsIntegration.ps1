#requires -Version 7.0
# Real ACL/pinned sampler/CIM on the CI machine; never SSH or operator evidence.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsWindows) { throw 'HOLD: Windows integration requires Windows' }
. (Join-Path $PSScriptRoot 'HostSupport.ps1')
$pwsh=(Get-Process -Id $PID).Path
$root=Join-Path ([IO.Path]::GetTempPath()) ('s24-integration-'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $root
$passed=0
$child=$null
function Check([bool] $Condition) {
    if (-not $Condition) { throw 'Windows integration control failed' }
    $script:passed++
}
function Config([string] $Name, [hashtable] $Value) {
    $path=Join-Path $root ($Name+'.json')
    Write-S24New $path (ConvertTo-Json -InputObject $Value -Compress)
    return $path
}
function Launch([string] $Path) {
    $state=Start-S24Child $pwsh @('-NoLogo','-NoProfile','-NonInteractive','-File',
        (Join-Path $root 'Read-S24HostSample.ps1'),'-ConfigPath',$Path)
    $state.Process.StandardInput.Close()
    return $state
}
function Reject-Sampler([string] $Path) {
    $script:child=Launch $Path
    $rejected=$false
    try { $null=Receive-S24Line $script:child ([Diagnostics.Stopwatch]::StartNew()) 20 }
    catch { $rejected=$true }
    $exited=$script:child.Process.WaitForExit(10000)
    Check ($rejected -and $exited -and $script:child.Process.ExitCode -eq 2)
    Close-S24Child $script:child $true
    $script:child=$null
}
try {
    # Fixture creation only. Production Assert-S24PrivateAcl never repairs ACLs.
    $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl=[Security.AccessControl.DirectorySecurity]::new()
    $acl.SetOwner($sid)
    $acl.SetAccessRuleProtection($true,$false)
    $rule=[Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl',
        'ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
    Set-Acl -LiteralPath $root -AclObject $acl
    foreach ($name in @('HostSupport.ps1','HostMemory.psm1','Read-S24HostSample.ps1')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $root $name)
    }
    Assert-S24PrivateAcl $root
    Assert-S24PrivateAcl (Join-Path $root 'HostSupport.ps1')
    Check $true
    $binding='a'*64; $challenge='b'*64
    $module=Join-Path $root 'HostMemory.psm1'
    foreach ($phase in @('before','during','after')) {
        $path=Config $phase @{binding=$binding;challenge=$challenge;modulePath=$module;phase=$phase}
        $child=Launch $path
        $clock=[Diagnostics.Stopwatch]::StartNew()
        $sample=Receive-S24Line $child $clock 20
        Wait-S24Exit $child $clock 20
        Assert-S24 ($sample.evidence_class -ceq 'local-read-only-windows-host-memory')
        Assert-S24 ($sample.binding_sha256 -ceq $binding -and $sample.challenge -ceq $challenge -and $sample.phase -ceq $phase)
        Assert-S24 ($sample.elapsed_seconds -ge 0 -and $sample.elapsed_seconds -le 1)
        Assert-S24 ($sample.host_available_bytes -ge 1610612736 -and $sample.host_limit_failures.Count -eq 0)
        foreach ($flag in @('full_checkpoint_pass','host_identity_proved','authenticated','guest_observed',
                           'original_runtime_continuity_observed','complete_writer_coverage')) {
            Assert-S24 ($sample[$flag] -is [bool] -and -not $sample[$flag])
        }
        Check ($child.Queue.Count -eq 0)
        Close-S24Child $child $false; $child=$null
    }
    $world=[Security.Principal.SecurityIdentifier]::new('S-1-1-0')
    $badAcl=Get-Acl -LiteralPath $root
    $badAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($world,'Read','Allow'))
    Set-Acl -LiteralPath $root -AclObject $badAcl
    $rejected=$false
    try { Assert-S24PrivateAcl $root } catch { $rejected=$true }
    Check $rejected
    Set-Acl -LiteralPath $root -AclObject $acl  # Restore only the disposable fixture.
    $alias=Join-Path $root 'junction'
    $target=Join-Path $root 'target'
    $null=New-Item -ItemType Directory -Path $target
    $null=New-Item -ItemType Junction -Path $alias -Target $target
    $rejected=$false
    try { Assert-S24NoReparse $alias } catch { $rejected=$true }
    Check $rejected
    Reject-Sampler (Config 'bad-phase' @{binding=$binding;challenge=$challenge;modulePath=$module;phase='unknown'})
    Reject-Sampler (Config 'bad-schema' @{binding=$binding;challenge=$challenge;modulePath=$module;phase='before';extra=1})
    $badConfig=Config 'bad-acl' @{binding=$binding;challenge=$challenge;modulePath=$module;phase='before'}
    $fileAcl=Get-Acl -LiteralPath $badConfig
    $fileAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($world,'Read','Allow'))
    Set-Acl -LiteralPath $badConfig -AclObject $fileAcl
    Reject-Sampler $badConfig
    [IO.File]::AppendAllText($module,"`n# disposable source drift`n")
    Reject-Sampler (Config 'bad-module' @{binding=$binding;challenge=$challenge;modulePath=$module;phase='before'})
    Assert-S24 ($passed -eq 10)
    [Console]::Out.WriteLine("Windows integration controls: $passed checks passed; CI ACL and CIM only; no SSH/operator evidence")
} finally {
    if ($null -ne $child) { Close-S24Child $child $true }
    # Preserve fixtures for failed CI diagnosis; runner teardown owns their lifetime.
}
