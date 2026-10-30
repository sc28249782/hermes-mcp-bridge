#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-S24([bool] $Condition) {
    if (-not $Condition) { throw 'HOLD: observer condition failed' }
}

function Assert-S24NoReparse([string] $Path) {
    Assert-S24 ([IO.Path]::IsPathFullyQualified($Path))
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    while ($null -ne $item) {
        Assert-S24 (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0)
        if ($item -is [IO.FileInfo]) { $item = $item.Directory } else { $item = $item.Parent }
    }
}

function Assert-S24PrivateAcl([string] $Path) {
    Assert-S24NoReparse $Path
    $sidType=[Security.Principal.SecurityIdentifier]
    $current=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $acl=Microsoft.PowerShell.Security\Get-Acl -LiteralPath $Path -ErrorAction Stop
    Assert-S24 ($acl.GetOwner($sidType).Value -ceq $current)
    $allowed=@($current,'S-1-5-18','S-1-5-32-544') # Proposed SPEC24 policy: current owner, SYSTEM, local administrators.
    foreach ($rule in $acl.GetAccessRules($true,$true,$sidType)) {
        if ($rule.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow) {
            Assert-S24 ($rule.IdentityReference.Value -cin $allowed)
        }
    }
    # Validation only: no Set-Acl/permission repair or account/host identity claim.
}

function Open-S24Pinned([string] $Path, [string] $Digest) {
    Assert-S24NoReparse $Path
    Assert-S24 ($Digest -cmatch '\A[a-f0-9]{64}\z')
    $stream = [IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        Assert-S24 ($stream.Length -le 131072)
        $bytes = [byte[]]::new([int]$stream.Length)
        $offset = 0
        while ($offset -lt $bytes.Length) {
            $n = $stream.Read($bytes,$offset,$bytes.Length-$offset)
            Assert-S24 ($n -gt 0)
            $offset += $n
        }
        Assert-S24 ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant() -ceq $Digest)
        return @{ Stream=$stream; Bytes=$bytes }
    } catch { $stream.Dispose(); throw }
}

function Test-S24JsonNode($Node) {
    if ($Node.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $Node.EnumerateObject()) {
            Assert-S24 ($names.Add($property.Name))
            Test-S24JsonNode $property.Value
        }
    } elseif ($Node.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        foreach ($value in $Node.EnumerateArray()) { Test-S24JsonNode $value }
    }
}

function ConvertFrom-S24Json([string] $Text) {
    Assert-S24 ([Text.Encoding]::UTF8.GetByteCount($Text) -le 16384)
    $document = [Text.Json.JsonDocument]::Parse($Text)
    try { Test-S24JsonNode $document.RootElement } finally { $document.Dispose() }
    return ConvertFrom-Json -InputObject $Text -AsHashtable -Depth 30
}

function Read-S24Config([string] $Path) {
    Assert-S24NoReparse $Path
    $stream=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        $bytes=[byte[]]::new(16385)
        $used=0
        while ($used -lt $bytes.Length) {
            $n=$stream.Read($bytes,$used,$bytes.Length-$used)
            if ($n -eq 0) { break }
            $used+=$n
        }
        Assert-S24 ($used -le 16384)
        return ConvertFrom-S24Json ([Text.UTF8Encoding]::new($false,$true).GetString($bytes,0,$used))
    } finally { $stream.Dispose() }
}

function Write-S24New([string] $Path, [string] $Text) {
    Assert-S24NoReparse ([IO.Path]::GetDirectoryName($Path))
    Assert-S24PrivateAcl ([IO.Path]::GetDirectoryName($Path))
    $bytes=[Text.Encoding]::UTF8.GetBytes($Text)
    Assert-S24 ($bytes.Length -le 16384)
    $s=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough)
    try { Assert-S24PrivateAcl $Path; $s.Write($bytes,0,$bytes.Length); $s.Flush($true) } finally { $s.Dispose() }
}

function Start-S24Child([string] $Executable, [string[]] $Arguments) {
    Assert-S24NoReparse $Executable
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName=$Executable
    $start.UseShellExecute=$false
    $start.RedirectStandardInput=$true
    $start.RedirectStandardOutput=$true
    $start.RedirectStandardError=$true
    $start.CreateNoWindow=$true
    foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo=$start
    Assert-S24 ($process.Start())
    $safe = $process.SafeHandle # Retain a handle to this newly started child.
    $state = @{ Process=$process; Handle=$safe; Started=$process.StartTime.ToUniversalTime();
                Queue=[Collections.Generic.Queue[object]]::new(); Pending=[Collections.Generic.List[byte]]::new();
                Used=0; OutEOF=$false; ErrEOF=$false; OutBuffer=[byte[]]::new(4096); ErrBuffer=[byte[]]::new(4096) }
    $state.OutTask=$process.StandardOutput.BaseStream.ReadAsync($state.OutBuffer,0,4096)
    $state.ErrTask=$process.StandardError.BaseStream.ReadAsync($state.ErrBuffer,0,4096)
    return $state
}

function Update-S24Child($State) {
    if (-not $State.ErrEOF -and $State.ErrTask.IsCompleted) {
        $count = $State.ErrTask.GetAwaiter().GetResult()
        Assert-S24 ($count -eq 0) # No raw SSH/provider error is copied to evidence.
        $State.ErrEOF=$true
    }
    if (-not $State.OutEOF -and $State.OutTask.IsCompleted) {
        $count = $State.OutTask.GetAwaiter().GetResult()
        if ($count -eq 0) {
            $State.OutEOF=$true
            Assert-S24 ($State.Pending.Count -eq 0)
        } else {
            $State.Used += $count
            Assert-S24 ($State.Used -le 16384)
            for ($i=0; $i -lt $count; $i++) {
                $State.Pending.Add($State.OutBuffer[$i])
                Assert-S24 ($State.Pending.Count -le 2048)
                if ($State.OutBuffer[$i] -eq 10) {
                    $utf8 = [Text.UTF8Encoding]::new($false,$true)
                    $line=$utf8.GetString($State.Pending.ToArray())
                    $State.Pending.Clear()
                    Assert-S24 ($State.Queue.Count -lt 4)
                    $State.Queue.Enqueue((ConvertFrom-S24Json $line))
                }
            }
            $State.OutTask=$State.Process.StandardOutput.BaseStream.ReadAsync($State.OutBuffer,0,4096)
        }
    }
}

function Receive-S24Line($State, [Diagnostics.Stopwatch] $Clock, [double] $Deadline) {
    while ($Clock.Elapsed.TotalSeconds -lt $Deadline) {
        Update-S24Child $State
        if ($State.Queue.Count -gt 0) { return $State.Queue.Dequeue() }
        Assert-S24 (-not $State.OutEOF)
        # Wait only on already outstanding I/O; no protocol retry or collection delay.
        [void][Threading.Tasks.Task]::WaitAny([Threading.Tasks.Task[]]@($State.OutTask,$State.ErrTask),10)
    }
    throw 'HOLD: observer deadline'
}

function Wait-S24Exit($State, [Diagnostics.Stopwatch] $Clock, [double] $Deadline) {
    while ($Clock.Elapsed.TotalSeconds -lt $Deadline) {
        Update-S24Child $State
        if ($State.Process.HasExited -and $State.OutEOF -and $State.ErrEOF) {
            $State.Process.WaitForExit()
            Assert-S24 ($State.Process.ExitCode -eq 0)
            return
        }
        [void][Threading.Tasks.Task]::WaitAny([Threading.Tasks.Task[]]@($State.OutTask,$State.ErrTask),10)
    }
    throw 'HOLD: child stop unconfirmed'
}

function Close-S24Child($State, [bool] $PermitTermination) {
    if ($null -eq $State) { return }
    if (-not $State.Process.HasExited) {
        if (-not $PermitTermination) { throw 'HOLD: owned child stop unconfirmed' }
        Assert-S24 ($State.Process.StartTime.ToUniversalTime() -eq $State.Started -and -not $State.Handle.IsInvalid)
        $State.Process.Kill($false) # Proposed owned-child-only stop; never Kill(entireProcessTree).
        Assert-S24 ($State.Process.WaitForExit(1000))
    }
    # The retained child is now known exited. A failed/EOF transport can leave
    # buffered stdin whose disposal flush raises IOException. Discarding that
    # input is cleanup only, never proof of delivery or a successful exchange.
    try {
        try { $State.Process.StandardInput.Dispose() }
        catch [IO.IOException] { } # Exited child only; coordinator HOLD is retained.
    } finally {
        try { $State.Process.StandardOutput.Dispose() }
        finally {
            try { $State.Process.StandardError.Dispose() }
            finally { $State.Process.Dispose() }
        }
    }
}

function Assert-S24FalseFlags($Frame) {
    foreach ($name in @('r1_complete','r2_authorized','authenticated','complete_writer_coverage','host_identity_proved','scope_granted')) {
        Assert-S24 ($Frame.ContainsKey($name) -and $Frame[$name] -is [bool] -and -not $Frame[$name])
    }
}
