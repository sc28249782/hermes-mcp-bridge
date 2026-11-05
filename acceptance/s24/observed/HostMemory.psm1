#requires -Version 7.0
# Read-only local Windows memory sample. No transport, persistence or approval.
Set-StrictMode -Version Latest

function ConvertTo-S24MemoryBytes {
    param([object] $Value)
    if ($null -eq $Value -or $Value.GetType() -notin @([uint64], [uint32], [int64], [int32]) -or
        [decimal]$Value -lt 0 -or [decimal]$Value * 1024 -gt [long]::MaxValue) {
        throw 'HOLD: invalid CIM memory counter'
    }
    return [long]([decimal]$Value * 1024)
}

function ConvertTo-S24HostMemory {
    [CmdletBinding()]
    param([AllowNull()][object] $AvailableKiB, [AllowNull()][object] $TotalKiB)
    $available = ConvertTo-S24MemoryBytes $AvailableKiB
    $total = ConvertTo-S24MemoryBytes $TotalKiB
    if ($total -le 0 -or $available -gt $total) { throw 'HOLD: inconsistent CIM memory counters' }
    $failures = @()
    if ($available -lt 1536L * 1024 * 1024) { $failures += 'host_available_below_1536_mib' }
    return [ordered]@{
        evidence_class = 'offline-host-memory-conversion'
        host_available_bytes = $available
        host_total_visible_bytes = $total
        host_limit_failures = @($failures)
        full_checkpoint_pass = $false
    }
}

function Read-S24LocalMemory {
    # No ComputerName, CimSession, InputObject, credentials or method invocation.
    # Module qualification avoids an accidental same-name function substitution.
    CimCmdlets\Get-CimInstance -Namespace root/cimv2 -ClassName Win32_OperatingSystem `
        -Property FreePhysicalMemory, TotalVisibleMemorySize -OperationTimeoutSec 1 -ErrorAction Stop
}

function Get-S24HostMemorySample {
    [CmdletBinding()]
    param([object] $BindingSha256, [object] $Challenge)
    # Echoed correlation data never authenticates a source or an approval.
    if ($BindingSha256 -isnot [string] -or $BindingSha256 -cnotmatch '\A[0-9a-f]{64}\z' -or
        $Challenge -isnot [string] -or $Challenge -cnotmatch '\A[0-9a-f]{64}\z') {
        throw 'HOLD: exact binding digest and challenge required'
    }
    if (-not $IsWindows) { throw 'HOLD: local Windows CIM required' }
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $started = [DateTimeOffset]::UtcNow.ToString('o')
    try {
        $rows = @(Read-S24LocalMemory)
        if ($rows.Count -ne 1) { throw 'HOLD: one local OS instance required' }
        $sample = ConvertTo-S24HostMemory -AvailableKiB $rows[0].FreePhysicalMemory `
            -TotalKiB $rows[0].TotalVisibleMemorySize
        $elapsed = $watch.Elapsed.TotalSeconds
        if ($elapsed -gt 1.0) { throw 'HOLD: host sample exceeded one second' }
        $sample.evidence_class = 'local-read-only-windows-host-memory'
        $sample['binding_sha256'] = $BindingSha256
        $sample['challenge'] = $Challenge
        $sample['started_utc'] = $started
        $sample['finished_utc'] = [DateTimeOffset]::UtcNow.ToString('o')
        $sample['elapsed_seconds'] = $elapsed
        $sample['host_identity_proved'] = $false
        $sample['authenticated'] = $false
        $sample['guest_observed'] = $false
        $sample['original_runtime_continuity_observed'] = $false
        $sample['complete_writer_coverage'] = $false
        return $sample
    }
    catch {
        # No raw provider errors, machine/account/path identifiers or partial sample.
        throw 'HOLD: local host memory observation unavailable'
    }
    finally { $watch.Stop() }
}

Export-ModuleMember -Function ConvertTo-S24HostMemory, Get-S24HostMemorySample
