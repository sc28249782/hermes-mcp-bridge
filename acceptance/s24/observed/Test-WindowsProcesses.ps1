#requires -Version 7.0
# Disposable process controls only. No SSH, CIM, guest or existing-process target.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsWindows) { throw 'HOLD: Windows process controls require Windows' }
. (Join-Path $PSScriptRoot 'HostSupport.ps1')
$pwsh=(Get-Process -Id $PID -ErrorAction Stop).Path
$passed=0

function Check([bool] $Condition) {
    if (-not $Condition) { throw 'Windows process control failed' }
    $script:passed++
}

function New-Fixture([string] $Code) {
    $state=Start-S24Child $pwsh @('-NoLogo','-NoProfile','-NonInteractive','-Command',$Code)
    $state.Process.StandardInput.Close()
    return $state
}

$state=$null
try {
    $state=New-Fixture '[Console]::Out.WriteLine(''{"offline_fixture":true}'')'
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $frame=Receive-S24Line $state $clock 20
    Wait-S24Exit $state $clock 20
    Check ($frame.offline_fixture -is [bool] -and $frame.offline_fixture -and $state.Queue.Count -eq 0)
    Close-S24Child $state $false; $state=$null

    foreach ($code in @('[Console]::Out.WriteLine(''{"x":1,"x":2}'')',
                        '[Console]::Out.WriteLine((''x''*3000))',
                        '[Console]::Error.WriteLine(''SYNTHETIC_PRIVATE'')',
                        '[Console]::Out.Write(''{"partial":'')')) {
        $state=New-Fixture $code
        $clock=[Diagnostics.Stopwatch]::StartNew()
        $rejected=$false
        try { $null=Receive-S24Line $state $clock 20 } catch { $rejected=$true }
        Check $rejected
        Close-S24Child $state $true; $state=$null
    }

    # Sleep is confined to this disposable process fixture. No inventory worker
    # is launched, delayed or given a larger observation window.
    $state=New-Fixture 'Start-Sleep -Seconds 10'
    $clock=[Diagnostics.Stopwatch]::StartNew()
    $rejected=$false
    try { $null=Receive-S24Line $state $clock 0.05 } catch { $rejected=$true }
    Check $rejected
    $rejected=$false
    try { Close-S24Child $state $false } catch { $rejected=$true }
    Check $rejected
    $saved=$state.Started
    $state.Started=$saved.AddSeconds(-1)
    $rejected=$false
    try { Close-S24Child $state $true } catch { $rejected=$true }
    Check $rejected
    $state.Started=$saved
    Close-S24Child $state $true; $state=$null
    Check $true
    [Console]::Out.WriteLine("Windows process controls: $passed checks passed; disposable fixtures only")
} finally {
    if ($null -ne $state) { Close-S24Child $state $true }
}
