#requires -Version 7.0
param([Parameter(Mandatory)][string] $ConfigPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Bootstrap compiles exactly checked bytes; no dot-source reopening after hashing.
function Import-CheckedSupport([string] $Path) {
    $item=Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'HOLD: support path' }
        if ($item -is [IO.FileInfo]) { $item=$item.Directory } else { $item=$item.Parent }
    }
    $s=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        if ($s.Length -gt 131072) { throw 'HOLD: support size' }
        $b=[byte[]]::new([int]$s.Length); $i=0
        while ($i -lt $b.Length) { $n=$s.Read($b,$i,$b.Length-$i); if ($n -le 0) { throw 'HOLD: support read' }; $i+=$n }
        if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b)).ToLowerInvariant() -cne '5b894a5563dd1ed1f9cbc0bf99e924065f90a53f5cf88b22d5711e93e4a52f7e') { throw 'HOLD: support hash' }
        return [scriptblock]::Create([Text.UTF8Encoding]::new($false,$true).GetString($b))
    } finally { $s.Dispose() }
}
$module=$null
try {
    if (-not $IsWindows) { throw 'HOLD: Windows required' }
    . (Import-CheckedSupport (Join-Path $PSScriptRoot 'HostSupport.ps1'))
    Assert-S24PrivateAcl (Join-Path $PSScriptRoot 'HostSupport.ps1')
    Assert-S24PrivateAcl $ConfigPath
    $cfg=Read-S24Config $ConfigPath
    Assert-S24 (($cfg.Keys | Sort-Object) -join ',' -ceq 'binding,challenge,modulePath,phase')
    Assert-S24 ($cfg.binding -is [string] -and $cfg.binding -cmatch '\A[a-f0-9]{64}\z' -and $cfg.challenge -is [string] -and $cfg.challenge -cmatch '\A[a-f0-9]{64}\z')
    Assert-S24 ($cfg.phase -cin @('before','during','after'))
    Assert-S24PrivateAcl $cfg.modulePath
    $module=Open-S24Pinned $cfg.modulePath '4509e645295f6b5748d9dbdbe2ab10221386ec4504c788a3bd121f574a5f09f8'
    Import-Module -Name $cfg.modulePath -Force -ErrorAction Stop
    $value=Get-S24HostMemorySample -BindingSha256 $cfg.binding -Challenge $cfg.challenge
    $value['phase']=$cfg.phase
    $raw=ConvertTo-Json -InputObject $value -Compress -Depth 10
    Assert-S24 ([Text.Encoding]::UTF8.GetByteCount($raw) -lt 2048)
    [Console]::Out.WriteLine($raw)
} catch {
    [Console]::Error.WriteLine('HOLD: host sample incomplete; no retry.')
    exit 2
} finally { if ($null -ne $module) { $module.Stream.Dispose() } }
