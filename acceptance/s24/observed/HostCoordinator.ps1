#requires -Version 7.0
# Checked host coordinator. Bootstrap/config/source/ACL admission stays in Observe-S24Host.
# State holds the same owned children for caller cleanup on success and failure.
function Invoke-S24HostCoordinator([hashtable] $State) {
    if ($State.ContainsKey('Claimed')) {
        $State.Held=$true
        throw 'HOLD: coordinator instance consumed'
    }
    $State.Claimed=$true
    $State.Held=$false
    $cfg=$State.Config
    $clock=$State.Clock
    try {
        function Write-Observation($Value) {
            $bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $Value -Compress -Depth 20)+"`n")
            $State.Used+=$bytes.Length
            Assert-S24 ($State.Used -le 65536)
            $State.Log.Write($bytes,0,$bytes.Length)
            $State.Log.Flush($true)
        }

        function Get-OneSample([string] $Phase) {
            Assert-S24 ($clock.Elapsed.TotalSeconds -lt 92)
            $sampleCfg=Join-Path $cfg.outputDirectory ("sample-"+$Phase+".json")
            $spec=@{binding=$cfg.binding;challenge=$cfg.challenge;modulePath=$cfg.modulePath;phase=$Phase}
            Write-S24New $sampleCfg (ConvertTo-Json -InputObject $spec -Compress)
            $deadline=[Math]::Min(95,$clock.Elapsed.TotalSeconds+3)
            $State.SampleChild=Start-S24Child $cfg.pwsh @('-NoLogo','-NoProfile','-NonInteractive','-File',$cfg.sampleScript,'-ConfigPath',$sampleCfg)
            $State.SampleChild.Process.StandardInput.Close()
            Assert-S24 ($clock.Elapsed.TotalSeconds -lt $deadline)
            $sample=Receive-S24Line $State.SampleChild $clock $deadline
            Wait-S24Exit $State.SampleChild $clock $deadline
            Assert-S24 ($State.SampleChild.Queue.Count -eq 0)
            foreach ($name in @('evidence_class','binding_sha256','challenge','phase')) { Assert-S24 ($sample[$name] -is [string]) }
            Assert-S24 ($sample.evidence_class -ceq 'local-read-only-windows-host-memory' -and $sample.binding_sha256 -ceq $cfg.binding -and $sample.challenge -ceq $cfg.challenge -and $sample.phase -ceq $Phase)
            foreach ($name in @('full_checkpoint_pass','host_identity_proved','authenticated','guest_observed','original_runtime_continuity_observed','complete_writer_coverage')) {
                Assert-S24 ($sample[$name] -is [bool] -and -not $sample[$name])
            }
            Assert-S24 ($sample.host_available_bytes -is [long] -and $sample.host_available_bytes -ge 1610612736 -and $sample.host_total_visible_bytes -is [long] -and $sample.host_total_visible_bytes -ge $sample.host_available_bytes)
            Assert-S24 (($sample.elapsed_seconds -is [double] -or $sample.elapsed_seconds -is [long]) -and [double]::IsFinite([double]$sample.elapsed_seconds))
            Assert-S24 ($sample.host_limit_failures -is [array] -and $sample.host_limit_failures.Count -eq 0 -and $sample.elapsed_seconds -ge 0 -and $sample.elapsed_seconds -le 1)
            Write-Observation $sample
            Close-S24Child $State.SampleChild $false
            $State.SampleChild=$null
        }

        function Receive-Transport([string] $Kind) {
            $frame=Receive-S24Line $State.SshChild $clock 95
            foreach ($name in @('kind','binding','challenge')) { Assert-S24 ($frame[$name] -is [string]) }
            Assert-S24 ($frame.binding -ceq $cfg.binding -and $frame.challenge -ceq $cfg.challenge -and $frame.kind -ceq $Kind)
            Assert-S24FalseFlags $frame
            $expected=@('kind','binding','challenge','r1_complete','r2_authorized','authenticated','complete_writer_coverage','host_identity_proved','scope_granted')
            if ($Kind -ceq 'observation_complete_pending_review') { $expected+= 'receipt_sha256'; Assert-S24 ($frame.receipt_sha256 -is [string] -and $frame.receipt_sha256 -cmatch '\A[a-f0-9]{64}\z') }
            Assert-S24 ((($frame.Keys|Sort-Object)-join ',') -ceq (($expected|Sort-Object)-join ','))
            Write-Observation $frame
        }

        Get-OneSample 'before'
        $remote="'"+$cfg.guestPython+"' -I -S -B '"+$cfg.guestScript+"' --config '"+$cfg.guestConfig+"'"
        $arguments=@('-T','-F',$cfg.sshConfigFile,'-p',[string]$cfg.port,'-i',$cfg.identityFile,
            '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o',('UserKnownHostsFile='+$cfg.knownHosts),
            '-o','UpdateHostKeys=no','-o','CheckHostIP=no',
            '-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
            '-o','ControlMaster=no','-o','ControlPath=none','-o','PermitLocalCommand=no','-o','ConnectTimeout=5',
            $cfg.destination,$remote)
        $State.SshChild=Start-S24Child $cfg.ssh $arguments
        Receive-Transport 'sample_window_open'
        Get-OneSample 'during'
        $message=@{kind='check_window_after';binding=$cfg.binding;challenge=$cfg.challenge}
        $State.SshChild.Process.StandardInput.WriteLine((ConvertTo-Json -InputObject $message -Compress))
        $State.SshChild.Process.StandardInput.Flush()
        Receive-Transport 'window_confirmed'
        Receive-Transport 'observation_complete_pending_review'
        $State.SshChild.Process.StandardInput.Close()
        Wait-S24Exit $State.SshChild $clock 95
        Assert-S24 ($State.SshChild.Queue.Count -eq 0)
        Close-S24Child $State.SshChild $false
        $State.SshChild=$null
        Get-OneSample 'after'
    } catch {
        $State.Held=$true
        throw
    }
}
