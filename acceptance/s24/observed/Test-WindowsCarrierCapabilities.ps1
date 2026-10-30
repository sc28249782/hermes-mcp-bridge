#requires -Version 7.0
# Read-only CI image facts, not an SSH/WSL/VM readiness or operational probe.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if (-not $IsWindows -or $env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') {
    throw 'capability inventory requires GitHub-hosted Windows CI'
}
function Feature-State([string] $Name) {
    try { return [string](Get-WindowsOptionalFeature -Online -FeatureName $Name -ErrorAction Stop).State }
    catch { return 'UNKNOWN' }
}
$ssh=Join-Path $env:WINDIR 'System32/OpenSSH/ssh.exe'
$sshd=Join-Path $env:WINDIR 'System32/OpenSSH/sshd.exe'
$service=Get-Service -Name sshd -ErrorAction SilentlyContinue
$serviceState=if ($null -eq $service) { 'ABSENT_OR_UNREADABLE' } else { [string]$service.Status }
[Console]::Out.WriteLine((ConvertTo-Json -Compress @{
    evidence_class='windows-ci-carrier-capability-inventory';
    ssh_client_present=(Test-Path -LiteralPath $ssh -PathType Leaf);
    ssh_server_present=(Test-Path -LiteralPath $sshd -PathType Leaf);ssh_service_state=$serviceState;
    wsl_feature_state=(Feature-State 'Microsoft-Windows-Subsystem-Linux');
    virtual_machine_platform_state=(Feature-State 'VirtualMachinePlatform');
    guest_availability='NOT_TESTED';ssh_started=$false;guest_started=$false;configuration_changed=$false;
    r1_complete=$false;r2_authorized=$false;scope_granted=$false
}))
