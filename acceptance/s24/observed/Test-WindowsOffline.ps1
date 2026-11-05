#requires -Version 7.0
# No SSH, process launch, provider query or operator preparation files.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsWindows) { throw 'HOLD: Windows offline controls require Windows' }
$count=0
function Check([bool] $Condition) {
    if (-not $Condition) { throw 'offline control failed' }
    $script:count++
}
foreach ($name in @('HostSupport.ps1','Read-S24HostSample.ps1','Observe-S24Host.ps1','HostMemory.psm1','Test-WindowsOffline.ps1','Test-WindowsProcesses.ps1')) {
    $tokens=$null; $errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name),[ref]$tokens,[ref]$errors)
    Check ($errors.Count -eq 0)
}
# Loading the support function definitions does not launch a process or read CIM.
. (Join-Path $PSScriptRoot 'HostSupport.ps1')
$obj=ConvertFrom-S24Json '{"a":1,"b":[true]}'
Check ($obj.a -eq 1)
foreach ($bad in @('{"a":1,"a":2}','{"nested":{"x":0,"x":1}}','{"x":NaN}','{"x":Infinity}')) {
    $rejected=$false
    try { $null=ConvertFrom-S24Json $bad } catch { $rejected=$true }
    Check $rejected
}
Import-Module (Join-Path $PSScriptRoot 'HostMemory.psm1') -Force
$memory=ConvertTo-S24HostMemory -AvailableKiB ([long]1572864) -TotalKiB ([long]8388608)
Check ($memory.evidence_class -ceq 'offline-host-memory-conversion' -and -not $memory.full_checkpoint_pass)
Check ($memory.host_available_bytes -eq 1610612736)
$rejected=$false
try { $null=ConvertTo-S24HostMemory -AvailableKiB '1572864' -TotalKiB ([long]8388608) } catch { $rejected=$true }
Check $rejected
[Console]::Out.WriteLine("Windows offline controls: $count checks passed; no CIM/SSH/process launch")
