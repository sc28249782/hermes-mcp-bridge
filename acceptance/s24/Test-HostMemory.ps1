#requires -Version 7.0
# Dependency-free controls. Synthetic reader replacements are offline unit data.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$module = Import-Module (Join-Path $PSScriptRoot 'HostMemory.psm1') -Force -PassThru
$realReader = & $module { (Get-Item Function:Read-S24LocalMemory).ScriptBlock }
$script:count = 0
$binding = 'a' * 64
$challenge = 'b' * 64

function Assert-True([bool] $Condition, [string] $Message) {
    if (-not $Condition) { throw "assertion failed: $Message" }
}

function Assert-Hold([scriptblock] $Action, [string] $Message = '') {
    $caught = $false
    try { $null = & $Action }
    catch {
        $caught = $true
        Assert-True ($_.Exception.Message.StartsWith('HOLD:')) 'failure must be HOLD'
        if ($Message) { Assert-True ($_.Exception.Message -ceq $Message) 'constant error shape' }
    }
    Assert-True $caught 'operation must fail closed'
}

function Set-TestReader([scriptblock] $Reader) {
    & $module { param($Body) Set-Item Function:script:Read-S24LocalMemory -Value $Body } $Reader
}

function Test-Control([string] $Name, [scriptblock] $Action) {
    try {
        Set-TestReader $realReader
        & $Action
        $script:count += 1
        Write-Output "OK: $Name"
    }
    finally { Set-TestReader $realReader }
}

Test-Control 'actual local Windows CIM positive (CI host only)' {
    $sample = Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge
    Assert-True ($sample.host_total_visible_bytes -gt 0) 'positive total memory'
    Assert-True ($sample.host_available_bytes -ge 0) 'available memory'
    Assert-True ($sample.host_available_bytes -le $sample.host_total_visible_bytes) 'counter consistency'
    Assert-True ($sample.elapsed_seconds -le 1.0) 'completed sample bound'
    Assert-True (-not $sample.full_checkpoint_pass) 'never full checkpoint pass'
    Assert-True (-not $sample.host_identity_proved) 'CI host is not operator host proof'
    # Do not publish the runner resource values or turn a CI value into B evidence.
}

Test-Control 'strict integer counters and exact binary-unit conversion' {
    foreach ($value in @([uint64]2048, [uint32]2048, [int64]2048, [int32]2048)) {
        $sample = ConvertTo-S24HostMemory -AvailableKiB $value -TotalKiB ([uint64]4096)
        Assert-True ($sample.host_available_bytes -eq 2097152) 'KiB converted exactly to bytes'
        Assert-True ($sample.evidence_class -ceq 'offline-host-memory-conversion') 'unit evidence label'
    }
}

Test-Control '1536 MiB boundary and one KiB below' {
    $at = ConvertTo-S24HostMemory -AvailableKiB ([uint64](1536 * 1024)) -TotalKiB ([uint64](4096 * 1024))
    $below = ConvertTo-S24HostMemory -AvailableKiB ([uint64](1536 * 1024 - 1)) -TotalKiB ([uint64](4096 * 1024))
    Assert-True ($at.host_limit_failures.Count -eq 0) 'boundary allowed by guest-independent host limit'
    Assert-True ($below.host_limit_failures.Count -eq 1) 'below boundary reported'
    Assert-True (-not $at.full_checkpoint_pass -and -not $below.full_checkpoint_pass) 'neither is checkpoint PASS'
}

Test-Control 'reject null bool floating string and negative counters' {
    foreach ($bad in @($null, $true, 1.0, [double]::NaN, [double]::PositiveInfinity, '2048', -1, @{})) {
        Assert-Hold { ConvertTo-S24HostMemory -AvailableKiB $bad -TotalKiB ([uint64]4096) }
        Assert-Hold { ConvertTo-S24HostMemory -AvailableKiB ([uint64]1) -TotalKiB $bad }
    }
}

Test-Control 'overflow zero total and available-over-total' {
    Assert-Hold { ConvertTo-S24HostMemory -AvailableKiB ([uint64]::MaxValue) -TotalKiB ([uint64]::MaxValue) }
    Assert-Hold { ConvertTo-S24HostMemory -AvailableKiB ([uint64]0) -TotalKiB ([uint64]0) }
    Assert-Hold { ConvertTo-S24HostMemory -AvailableKiB ([uint64]2) -TotalKiB ([uint64]1) }
    $maxKiB = [uint64][decimal]::Floor([decimal][long]::MaxValue / 1024)
    $sample = ConvertTo-S24HostMemory -AvailableKiB $maxKiB -TotalKiB $maxKiB
    Assert-True ($sample.host_available_bytes -eq [long]([decimal]$maxKiB * 1024)) 'largest allowed integer exact'
    Assert-Hold { ConvertTo-S24HostMemory -AvailableKiB ($maxKiB + 1) -TotalKiB ($maxKiB + 1) }
}

Test-Control 'correlation rejected before provider query' {
    Set-TestReader { throw 'provider must not run' }
    foreach ($bad in @($null, '', ('x' * 64), ('A' * 64), "$('a' * 64)`n", 123, @(('a' * 64)))) {
        Assert-Hold { Get-S24HostMemorySample -BindingSha256 $bad -Challenge $challenge } 'HOLD: exact binding digest and challenge required'
        Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $bad } 'HOLD: exact binding digest and challenge required'
    }
}

Test-Control 'zero or duplicate provider rows rejected' {
    Set-TestReader { @() }
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge } 'HOLD: local host memory observation unavailable'
    Set-TestReader {
        [pscustomobject]@{ FreePhysicalMemory = [uint64]2048; TotalVisibleMemorySize = [uint64]4096 }
        [pscustomobject]@{ FreePhysicalMemory = [uint64]2048; TotalVisibleMemorySize = [uint64]4096 }
    }
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge }
}

Test-Control 'missing or invalid provider property rejected' {
    Set-TestReader { [pscustomobject]@{ FreePhysicalMemory = [uint64]2048 } }
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge }
    Set-TestReader { [pscustomobject]@{ FreePhysicalMemory = $null; TotalVisibleMemorySize = [uint64]4096 } }
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge }
    Set-TestReader { [pscustomobject]@{ FreePhysicalMemory = '2048'; TotalVisibleMemorySize = [uint64]4096 } }
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge }
}

Test-Control 'provider exception sanitized with one invocation and no retry' {
    $calls = [System.Collections.Generic.List[int]]::new()
    $reader = { $calls.Add(1); throw 'UNIT_PRIVATE_PROVIDER_DETAIL' }.GetNewClosure()
    Set-TestReader $reader
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge } 'HOLD: local host memory observation unavailable'
    Assert-True ($calls.Count -eq 1) 'provider called once only'
}

Test-Control 'synthetic reader result has exact limited scope and no raw provider object' {
    Set-TestReader { [pscustomobject]@{
        FreePhysicalMemory = [uint64](2048 * 1024); TotalVisibleMemorySize = [uint64](4096 * 1024)
        CSName = 'UNIT_PRIVATE_MACHINE'; SerialNumber = 'UNIT_PRIVATE_SERIAL'
    } }
    $sample = Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge
    Assert-True ($sample.binding_sha256 -ceq $binding -and $sample.challenge -ceq $challenge) 'echo correlation only'
    foreach ($key in @('host_identity_proved', 'authenticated', 'guest_observed',
                        'original_runtime_continuity_observed', 'complete_writer_coverage', 'full_checkpoint_pass')) {
        Assert-True ($sample[$key] -is [bool] -and -not $sample[$key]) "explicit incomplete field $key"
    }
    $raw = $sample | ConvertTo-Json -Compress
    Assert-True ($raw -notmatch 'UNIT_PRIVATE') 'no raw provider detail'
    Assert-True ($sample.host_limit_failures.Count -eq 0) 'memory-only check clear'
    Assert-True ([DateTimeOffset]::Parse($sample.finished_utc) -ge [DateTimeOffset]::Parse($sample.started_utc)) 'local timestamps parse'
    # Injected provider values remain unit evidence, irrespective of the output label.
}

Test-Control 'late query produces no successful sample' {
    Set-TestReader {
        Start-Sleep -Milliseconds 1050
        [pscustomobject]@{ FreePhysicalMemory = [uint64]2048; TotalVisibleMemorySize = [uint64]4096 }
    }
    Assert-Hold { Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge } 'HOLD: local host memory observation unavailable'
}

Test-Control 'low memory returned as a failure and never complete checkpoint pass' {
    Set-TestReader { [pscustomobject]@{ FreePhysicalMemory = [uint64]0; TotalVisibleMemorySize = [uint64]4096 } }
    $sample = Get-S24HostMemorySample -BindingSha256 $binding -Challenge $challenge
    Assert-True ($sample.host_limit_failures.Count -eq 1) 'host threshold failure retained'
    Assert-True (-not $sample.full_checkpoint_pass) 'no pass from measurement'
    $decoded = ($sample | ConvertTo-Json -Compress) | ConvertFrom-Json
    Assert-True ($decoded.host_limit_failures -is [array]) 'failure list remains an array'
}

if ($script:count -ne 12) { throw 'control inventory mismatch' }
Write-Output 'HOST_MEMORY_CONTROLS_OK 12/12 (Windows CI host + labeled unit injections; no operator-host measurement)'
