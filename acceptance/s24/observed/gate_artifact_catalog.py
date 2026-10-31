"""Validate CATALOG ONLY output; no strict-inspection/import authority."""
import json
from pathlib import Path
import re
import sys
import tarfile

SHA = 'bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e'
MAX_ARCHIVE = 1024**3
POLICY_ID = 'ROOTFS_METADATA_CATALOG_V1'
TYPE_CLASSES = frozenset(('REGULAR','DIRECTORY','SYMLINK','HARDLINK','CHAR_DEVICE','BLOCK_DEVICE'))
REGULAR_HEX = frozenset(t.hex() for t in tarfile.REGULAR_TYPES if t != tarfile.GNUTYPE_SPARSE)
STAGES = frozenset(('START','GUARD','RESOURCE_LIMITS','RECEIPT_BINDING','TEMPFILE',
    'HTTP_OPEN','HTTP_HEADERS','HTTP_BODY','ARCHIVE_HASH','ARCHIVE_PARSE','CLEANUP','RECEIPT_ENCODE','COMPLETE'))
ERRORS = frozenset(('NONE','PREDICATE_REJECTED','REDIRECT_REJECTED','HTTP_403','HTTP_404',
    'HTTP_429','HTTP_5XX','HTTP_OTHER','TLS_ERROR','TIMEOUT','TRANSPORT_ERROR','IO_ERROR',
    'MEMORY_LIMIT','ARCHIVE_ERROR','JSON_ERROR','UNEXPECTED_ERROR'))
PREDICATE_REASONS = frozenset(('NAME_LENGTH_OR_TYPE', 'ABSOLUTE_PATH', 'BACKSLASH', 'PATH_COMPONENT', 'NAME_CONTROL', 'NAME_DUPLICATE', 'COUNT_MEMBERS', 'HEADER_SIZE_RANGE', 'SIZE_LOGICAL', 'LINK_LENGTH', 'SPARSE', 'TYPE_REJECTED', 'ROOT_NOT_DIRECTORY', 'COUNT_SELECTED', 'SIZE_SELECTED', 'SELECTED_STREAM_MISSING', 'SIZE_SELECTED_READ', 'SELECTED_READ_SIZE', 'EMPTY_ARCHIVE', 'DEVICE_METADATA_REJECTED', 'SELECTED_DEVICE_COLLISION'))
FLAGS = frozenset(('archive_verified_receipt','j0_ready','setup_ready','guest_imported',
                  'guest_started','r1_complete','r2_authorized','scope_granted','archive_inspection_verified','extraction_authorized',
                  'prepared_guest_artifact','import_compatibility_tested'))
DIAG_KEYS = FLAGS | {'evidence_class','schema','stage','error','received_bytes','hashed_bytes',
                    'download_complete','hash_complete','archive_sha256','digest_matches','parsed_members','predicate_reason','policy_id','type_counts',
                    'type_counts_complete','metadata_catalog_complete'}
RESULT_FLAGS = (FLAGS - {'archive_verified_receipt'}) | {'provider_signature_verified',
    'links_resolved','import_compatibility_tested','prepared_guest_artifact'}
RESULT_KEYS = RESULT_FLAGS | {'evidence_class','archive_bytes','author_computed_archive_sha256',
    'archive_matches_provider_digest','tar_header_count','declared_logical_bytes',
    'ordered_header_catalog_sha256','selected_entries','catalog_scope','schema','policy_id',
    'metadata_catalog_complete','type_counts'}


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


def counts(value, members, complete):
    need(type(value) is dict and set(value)==TYPE_CLASSES)
    for number in value.values():
        integer(number,0,200000)
    need(sum(value.values())==members if complete else sum(value.values())<=members)


def diagnostic(d):
    need(type(d) is dict and set(d) == DIAG_KEYS)
    need(d['evidence_class']=='j0-metadata-catalog-diagnostic-only' and type(d['schema']) is int and d['schema']==1)
    need(d['policy_id']==POLICY_ID and d['metadata_catalog_complete'] is False)
    need(d['stage'] in STAGES and d['error'] in ERRORS)
    reason=d['predicate_reason']
    need(reason is None or (type(reason) is str and reason in PREDICATE_REASONS
         and d['stage']=='ARCHIVE_PARSE' and d['error']=='PREDICATE_REJECTED'))
    for key in FLAGS:
        need(d[key] is False)
    for key in ('download_complete','hash_complete'):
        need(type(d[key]) is bool)
    for key in ('received_bytes','hashed_bytes'):
        integer(d[key],0,MAX_ARCHIVE+1)
    integer(d['parsed_members'],0,200000)
    need(type(d['type_counts_complete']) is bool)
    need(not d['type_counts_complete'] or (d['stage']=='COMPLETE' and d['error']=='NONE'))
    counts(d['type_counts'], d['parsed_members'], d['type_counts_complete'])
    if d['hash_complete']:
        sha(d['archive_sha256'])
        need(type(d['digest_matches']) is bool)
    else:
        need(d['archive_sha256'] is None and d['digest_matches'] is None)
    return d


def result(r):
    need(type(r) is dict and set(r)==RESULT_KEYS)
    need(r['evidence_class']=='j0-rootfs-metadata-catalog-only')
    need(type(r['schema']) is int and r['schema']==1 and r['policy_id']==POLICY_ID)
    need(r['metadata_catalog_complete'] is True)
    for key in RESULT_FLAGS:
        need(r[key] is False)
    need(r['author_computed_archive_sha256']==SHA and r['archive_matches_provider_digest'] is True)
    integer(r['archive_bytes'],1,MAX_ARCHIVE)
    integer(r['tar_header_count'],1,200000)
    counts(r['type_counts'],r['tar_header_count'],True)
    integer(r['declared_logical_bytes'],0,4*1024**3)
    sha(r['ordered_header_catalog_sha256'])
    need(r['catalog_scope']=='policy-prefixed headers including device metadata; selected regular hashes; no full content tree')
    need(type(r['selected_entries']) is list and len(r['selected_entries'])<=32)
    seen=set()
    for entry in r['selected_entries']:
        need(type(entry) is dict)
        base={'name','type_hex','size','mode','uid','gid','link'}
        regular=entry.get('type_hex') in REGULAR_HEX
        need(set(entry)==base|({'content_sha256'} if regular else set()))
        name=entry['name']
        need(isinstance(name,str) and name not in seen)
        need(name in {'etc/os-release','usr/lib/os-release','usr/bin/python3','usr/sbin/sshd',
             'var/lib/dpkg/status','etc/wsl.conf','etc/wsl-distribution.conf'}
             or re.fullmatch(r'usr/bin/python3\.[0-9]+',name) is not None)
        seen.add(name)
        need(entry['type_hex'] in REGULAR_HEX | {'31','32','35'})
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
        need(d['error']!='NONE' and d['type_counts_complete'] is False)
        return {'evidence_class':'j0-metadata-catalog-gate-hold','diagnostic':d,'archive_inspection_verified':False,'metadata_catalog_complete':False}, 2
    r=result(parse(lines[0]))
    need(d['stage']=='COMPLETE' and d['error']=='NONE')
    need(d['download_complete'] is True and d['hash_complete'] is True and d['digest_matches'] is True)
    need(d['archive_sha256']==SHA and d['received_bytes']==r['archive_bytes']==d['hashed_bytes'])
    need(d['parsed_members']==r['tar_header_count'])
    need(d['type_counts_complete'] is True and d['type_counts']==r['type_counts'])
    return {'evidence_class':'j0-metadata-catalog-gate-only','inspection':r,'diagnostic':d,'archive_inspection_verified':False,'metadata_catalog_complete':True}, 0


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
            print('HOLD: metadata catalog gate rejected output')
        except Exception:
            pass
        return 2


if __name__=='__main__':
    sys.exit(main())
