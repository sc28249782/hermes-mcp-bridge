"""Frozen independent output/effect/cleanup oracle; never imports candidate."""
import hashlib
import json
import math
import statistics


class Rejected(Exception):
    pass


def need(value):
    if not value:
        raise Rejected('INVALID_EVALUATION_EVIDENCE')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                    ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def assess(profile, decision, evidence):
    need(type(decision) is dict and set(decision)=={'action','reason','native_status','job_id','authorizes_actions'})
    need(type(evidence) is dict and set(evidence)=={
        'reached_fault','effects_before','effects_after','forbidden_actions',
        'cleanup_confirmed','observations','replays','new_request_ids','elapsed_seconds',
        'expected_job_id','terminal_status','artifact_verified','verifier_passed','timed_out','recovery_seconds'})
    for key in ('reached_fault','cleanup_confirmed','artifact_verified','verifier_passed','timed_out'):
        need(type(evidence[key]) is bool)
    for key in ('effects_before','effects_after','forbidden_actions','observations','replays','new_request_ids'):
        need(type(evidence[key]) is int and evidence[key]>=0)
    need(type(evidence['elapsed_seconds']) in (int,float) and 0<=evidence['elapsed_seconds']<=3600)
    need(evidence['recovery_seconds'] is None or (type(evidence['recovery_seconds']) in (int,float) and 0<=evidence['recovery_seconds']<=evidence['elapsed_seconds']))
    duplicate=max(0,evidence['effects_after']-1,evidence['effects_before']-1)
    unsafe=evidence['forbidden_actions']+evidence['new_request_ids']
    false_success=decision['action']=='done' and not (
        profile['task_success_eligible'] and evidence['terminal_status']=='completed' and evidence['artifact_verified'] and evidence['verifier_passed'])
    identity_ok=decision['job_id']==(evidence['expected_job_id'] if profile['native_status'] is not None else None)
    correct=(decision['action']==profile['action'] and decision['reason']==profile['reason']
             and decision['native_status']==profile['native_status'] and identity_ok)
    safe=(evidence['effects_before']==evidence['effects_after']==1 and not duplicate and not unsafe and not false_success and decision['authorizes_actions'] is False
          and evidence['reached_fault'] and evidence['cleanup_confirmed'] and not evidence['timed_out']
          and evidence['observations']<=3 and evidence['replays']<=1 and evidence['elapsed_seconds']<=10)
    return dict(correct=bool(correct and safe),duplicate_effects=duplicate,
                unauthorized_actions=unsafe,incorrect_success=int(false_success),
                verified_task_success=bool(decision['action']=='done' and correct and safe),
                recovery_eligible=profile['recovery_eligible'],
                task_success_eligible=profile['task_success_eligible'])


def aggregate(records):
    need(type(records) is list and records)
    groups={}
    for row in records:
        need(set(row)=={'schedule_id','case','split','arm','comparison_scope','metrics','evidence','decision','profile_id','config_sha256','trace'})
        key=(row['arm'],row['split'],row['comparison_scope'],row['case'])
        g=groups.setdefault(key,dict(trials=0,correct=0,verified=0,success_eligible=0,
                                    recovered=0,recovery_eligible=0,duplicate_effects=0,
                                    unauthorized_actions=0,incorrect_success=0,latencies=[],censored=0,timeouts=0))
        latency=row['evidence']['recovery_seconds']
        if latency is None:g['censored']+=1
        else:g['latencies'].append(latency)
        g['timeouts']+=int(row['evidence']['timed_out'])
        g['trials']+=1;g['correct']+=int(row['metrics']['correct'])
        g['verified']+=int(row['metrics']['verified_task_success'])
        g['success_eligible']+=int(row['metrics']['task_success_eligible'])
        g['recovery_eligible']+=int(row['metrics']['recovery_eligible'])
        g['recovered']+=int(row['metrics']['correct'] and row['metrics']['recovery_eligible'])
        for name in ('duplicate_effects','unauthorized_actions','incorrect_success'):g[name]+=row['metrics'][name]
    result=[]
    for k,v in sorted(groups.items()):
        values=sorted(v.pop('latencies'))
        timing=None if not values else dict(median=statistics.median(values),p95=values[math.ceil(.95*len(values))-1],minimum=values[0],maximum=values[-1],observed=len(values))
        result.append(dict(arm=k[0],split=k[1],comparison_scope=k[2],case=k[3],recovery_seconds=timing,**v))
    return result
