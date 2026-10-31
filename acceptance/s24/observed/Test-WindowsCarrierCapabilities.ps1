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
# Explicit known locations only. No executable is invoked, registry/distro/profile
# enumeration performed, or Store/WSL engine activation requested. A candidate
# file is not proof that this is the configured or bootable kernel/client.
function File-Fact([string] $Role, [string] $Path) {
    $fact=[ordered]@{role=$Role;state='ABSENT_OR_UNREADABLE';bytes=$null;sha256=$null;file_version=$null}
    try {
        $item=Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            $fact.state='REJECTED_TYPE'; return $fact
        }
        # Fixed file-read ceiling; no recursion or arbitrary file selection.
        if ($item.Length -le 0 -or $item.Length -gt 268435456) {
            $fact.state='REJECTED_SIZE'; return $fact
        }
        $fact.bytes=[long]$item.Length
        $fact.sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
        $fact.file_version=[string]$item.VersionInfo.FileVersion
        $fact.state='READ_ONLY_SNAPSHOT'
    } catch {
        $fact.state='ABSENT_OR_UNREADABLE'; $fact.sha256=$null
    }
    return $fact
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
    image_os=[string]$env:ImageOS;image_version=[string]$env:ImageVersion;
    windows_version=[Environment]::OSVersion.Version.ToString();
    file_facts=@(
        (File-Fact 'native_ssh_client_candidate' $ssh),
        (File-Fact 'inbox_wsl_client_candidate' (Join-Path $env:WINDIR 'System32/wsl.exe')),
        (File-Fact 'inbox_kernel_candidate' (Join-Path $env:WINDIR 'System32/lxss/tools/kernel')),
        (File-Fact 'msi_kernel_candidate' (Join-Path $env:ProgramFiles 'WSL/tools/kernel'))
    );
    existing_distro_activity='UNKNOWN_NOT_QUERIED';configured_kernel_identity='UNBOUND';
    boot_virtualization_support='NOT_TESTED';kernel_pidfd_procfs_support='NOT_TESTED';
    wsl_invoked=$false;archive_downloaded=$false;j0_ready=$false;
    guest_availability='NOT_TESTED';ssh_started=$false;guest_started=$false;configuration_changed=$false;
    r1_complete=$false;r2_authorized=$false;scope_granted=$false
}))
