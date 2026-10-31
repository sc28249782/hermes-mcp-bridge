"""Validate E13 two-line output without printing raw stderr or unknown JSON fields."""
import json
from pathlib import Path
import re
import sys

SHA = 'bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e'
MAX_ARCHIVE = 1024**3
STAGES = frozenset(('START','GUARD','RESOURCE_LIMITS','RECEIPT_BINDING','TEMPFILE',
    'HTTP_OPEN','HTTP_HEADERS','HTTP_BODY','ARCHIVE_HASH','ARCHIVE_PARSE','CLEANUP','RECEIPT_ENCODE','COMPLETE'))
ERRORS = frozenset(('NONE','PREDICATE_REJECTED','REDIRECT_REJECTED','HTTP_403','HTTP_404',
    'HTTP_429','HTTP_5XX','HTTP_OTHER','TLS_ERROR','TIMEOUT','TRANSPORT_ERROR','IO_ERROR',
    'MEMORY_LIMIT','ARCHIVE_ERROR','JSON_ERROR','UNEXPECTED_ERROR'))
FLAGS = frozenset(('archive_verified_receipt','j0_ready','setup_ready','guest_imported',
                  'guest_started','r1_complete','r2_authorized','scope_granted'))
DIAG_KEYS = FLAGS | {'evidence_class','schema','stage','error','received_bytes','hashed_bytes',
                    'download_complete','hash_complete','archive_sha256','digest_matches','parsed_members'}
RESULT_FLAGS = (FLAGS - {'archive_verified_receipt'}) | {'provider_signature_verified',
    'links_resolved','import_compatibility_tested','prepared_guest_artifact'}
RESULT_KEYS = RESULT_FLAGS | {'evidence_class','archive_bytes','author_computed_archive_sha256',
    'archive_matches_provider_digest','tar_header_count','declared_logical_bytes',
    'ordered_header_catalog_sha256','selected_entries','catalog_scope'}


class Rejected(Exception):
    pass


def need(value):
    if not value:
        raise Rejected()


def integer(value, low, high):
    need(type(value) is int and low <= value <= high)


def sha(value):
    need(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}', value) is not None)


def pairs(values):
    result = {}
    for key, value in values:
        need(key not in result)
        result[key] = value
    return result


def parse(raw):
    try:
        return json.loads(raw.decode('ascii'), object_pairs_hook=pairs,
                          parse_constant=lambda _value: (_ for _ in ()).throw(Rejected()))
    except (UnicodeError,ValueError,TypeError,RecursionError):
        raise Rejected() from None


def diagnostic(d):
    need(type(d) is dict and set(d) == DIAG_KEYS)
    need(d['evidence_class']=='j0-artifact-diagnostic-only' and type(d['schema']) is int and d['schema']==1)
    need(d['stage'] in STAGES and d['error'] in ERRORS)
    for key in FLAGS:
        need(d[key] is False)
    for key in ('download_complete','hash_complete'):
        need(type(d[key]) is bool)
    for key in ('received_bytes','hashed_bytes'):
        integer(d[key],0,MAX_ARCHIVE+1)
    integer(d['parsed_members'],0,200000)
    if d['hash_complete']:
        sha(d['archive_sha256'])
        need(type(d['digest_matches']) is bool)
    else:
        need(d['archive_sha256'] is None and d['digest_matches'] is None)
    return d


def result(r):
    need(type(r) is dict and set(r)==RESULT_KEYS)
    need(r['evidence_class']=='j0-archive-inspection-only')
    for key in RESULT_FLAGS:
        need(r[key] is False)
    need(r['author_computed_archive_sha256']==SHA and r['archive_matches_provider_digest'] is True)
    integer(r['archive_bytes'],1,MAX_ARCHIVE)
    integer(r['tar_header_count'],1,200000)
    integer(r['declared_logical_bytes'],0,4*1024**3)
    sha(r['ordered_header_catalog_sha256'])
    need(r['catalog_scope']=='headers plus selected regular-file content hashes; no full content tree')
    need(type(r['selected_entries']) is list and len(r['selected_entries'])<=32)
    seen=set()
    for entry in r['selected_entries']:
        need(type(entry) is dict)
        base={'name','type_hex','size','mode','uid','gid','link'}
        regular=entry.get('type_hex') in ('30','00')
        need(set(entry)==base|({'content_sha256'} if regular else set()))
        name=entry['name']
        need(isinstance(name,str) and name not in seen)
        need(name in {'etc/os-release','usr/lib/os-release','usr/bin/python3','usr/sbin/sshd',
             'var/lib/dpkg/status','etc/wsl.conf','etc/wsl-distribution.conf'}
             or re.fullmatch(r'usr/bin/python3\.[0-9]+',name) is not None)
        seen.add(name)
        need(entry['type_hex'] in ('30','00','31','32','35'))
        integer(entry['size'],0,32*1024**2 if regular else 4*1024**3)
        for key in ('mode','uid','gid'):
            integer(entry[key],0,2**63-1)
        need(isinstance(entry['link'],str) and len(entry['link'])<=4096)
        if regular:
            sha(entry['content_sha256'])
    return r


def validate(raw, exit_code):
    need(type(exit_code) is int and exit_code in (0,2))
    need(len(raw)<=67586 and raw.endswith(b'\n') and b'\r' not in raw)
    need(not any(word in raw for word in (b'ResourceWarning',b'Exception ignored',b'Traceback')))
    lines=raw[:-1].split(b'\n')
    need(len(lines)==2 and len(lines[0])<=65536 and len(lines[1])<=2048)
    d=diagnostic(parse(lines[1]))
    if exit_code==2:
        need(lines[0]==b'HOLD: artifact preparation incomplete')
        need(d['error']!='NONE')
        return {'evidence_class':'j0-artifact-gate-hold','diagnostic':d,'archive_inspection_verified':False}, 2
    r=result(parse(lines[0]))
    need(d['stage']=='COMPLETE' and d['error']=='NONE')
    need(d['download_complete'] is True and d['hash_complete'] is True and d['digest_matches'] is True)
    need(d['archive_sha256']==SHA and d['received_bytes']==r['archive_bytes']==d['hashed_bytes'])
    need(d['parsed_members']==r['tar_header_count'])
    return {'evidence_class':'j0-artifact-gate-inspection-only','inspection':r,'diagnostic':d,'archive_inspection_verified':True}, 0


def main():
    try:
        need(len(sys.argv)==3)
        # Read a bounded prefix only; excess bytes cannot be accepted or printed.
        with Path(sys.argv[1]).open('rb') as handle:
            raw=handle.read(67587)
        accepted, code=validate(raw,int(sys.argv[2]))
        print(json.dumps(accepted,ensure_ascii=True,sort_keys=True,separators=(',',':')))
        return code
    except Exception:
        # Unknown/malformed/stderr/unavailable frames stay HOLD; never echo raw.
        try:
            print('HOLD: diagnostic gate rejected output')
        except Exception:
            pass
        return 2


if __name__=='__main__':
    sys.exit(main())
