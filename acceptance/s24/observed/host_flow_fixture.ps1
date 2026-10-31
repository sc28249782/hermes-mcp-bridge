#requires -Version 7.0
# Disposable protocol producer. No CIM, SSH, guest or credential access.
param([string] $Role,[string] $ConfigPath,[string] $Case,[string] $TracePath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$cfg=ConvertFrom-Json ([IO.File]::ReadAllText($ConfigPath)) -AsHashtable
function Emit($Value) { [Console]::Out.WriteLine((ConvertTo-Json -InputObject $Value -Compress -Depth 10)) }
if ($Role -eq 'sample') {
    $value=@{evidence_class='local-read-only-windows-host-memory';binding_sha256=$cfg.binding;
        challenge=$cfg.challenge;phase=$cfg.phase;host_available_bytes=[long]2147483648;
        host_total_visible_bytes=[long]8589934592;elapsed_seconds=0.01;host_limit_failures=@();
        full_checkpoint_pass=$false;host_identity_proved=$false;authenticated=$false;
        guest_observed=$false;original_runtime_continuity_observed=$false;complete_writer_coverage=$false}
    if ($cfg.phase -eq 'during') {
        switch ($Case) {
            'provider_low' { $value.host_available_bytes=[long]1 }
            'provider_elapsed' { $value.elapsed_seconds=2.0 }
            'provider_missing' { exit 0 }
            'provider_corrupt' { [Console]::Out.WriteLine('{broken'); exit 0 }
            'provider_stderr' { [Console]::Error.WriteLine('SYNTHETIC_PROVIDER_ERROR'); exit 2 }
            'provider_blocked' { Start-Sleep -Seconds 10; exit 2 } # Fixture only; no inventory worker.
            'provider_wrong_binding' { $value.binding_sha256='d'*64 }
        }
    }
    Emit $value
    exit 0
}
if ($Role -ne 'transport') { throw 'fixture role' }
function Frame([string] $Kind) {
    return @{kind=$Kind;binding=$cfg.binding;challenge=$cfg.challenge;r1_complete=$false;
        r2_authorized=$false;authenticated=$false;complete_writer_coverage=$false;
        host_identity_proved=$false;scope_granted=$false}
}
$open=Frame 'sample_window_open'
switch ($Case) {
    'transport_wrong_challenge' { $open.challenge='d'*64; Emit $open; exit 0 }
    'transport_corrupt' { [Console]::Out.WriteLine('{broken'); exit 0 }
    'transport_partial' { [Console]::Out.Write('{"partial":'); exit 0 }
    'transport_flood' { [Console]::Out.WriteLine(('x'*17000)); exit 0 }
}
Emit $open
if ($Case -eq 'transport_eof') { exit 0 }
$line=[Console]::In.ReadLine()
if ($null -eq $line) { exit 2 }
$post=ConvertFrom-Json $line -AsHashtable
if ($post.Count -ne 3 -or $post.kind -cne 'check_window_after' -or
    $post.binding -cne $cfg.binding -or $post.challenge -cne $cfg.challenge) { exit 2 }
[IO.File]::AppendAllText($TracePath,"post-received`n")
Emit (Frame 'window_confirmed')
$done=Frame 'observation_complete_pending_review'; $done.receipt_sha256='c'*64
Emit $done
