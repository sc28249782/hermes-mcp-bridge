# E13 — finite artifact diagnostics source for review only

Date: 31 October 2026. Input: approved E12 failure record at `d1a50a64`.
Status: **SOURCE CANDIDATE; NO SECOND LIVE ATTEMPT / SETUP / PROVISIONING**.
The [E12 attempt](ARTIFACT-ATTEMPT-RECORD.md) remains failed, stage UNKNOWN.
This variant cannot retroactively diagnose E12. Keep this work on draft #112.

## 1. Source identity and preserved mechanics

| New source | Author-computed SHA256 |
| --- | --- |
| prepare_join_artifact_diagnostic.py | `ed1f9b689b6fb38593ffd101a437f1d8985260de993fb45c6b6213fee8d4482d` |
| test_artifact_diagnostic.py | `0379589c28062d1c0c73100a8eaf776ebfc3745459f42bf89684fe9b6c271f46` |

The diagnostic variant is a separately named copy with optional progress hooks,
fixed error classification and bounded output. E11 source (`293f0f61…`), original
13 controls, E10 receipt/pin and E12 record/selector/source pins are unchanged.
It preserves URL/provider digest, no proxy/redirect/retry/fallback, hash before
parser, same-stream reading, 1 GiB/200,000/4 GiB/32 MiB limits, selected hashes,
no link resolution/extraction, private temporary-file cleanup, 120 s alarm and
512 MiB address-space limit. No subprocess/SSH/WSL/package/guest execution added.
All operational runtime sources/pins/timers and sampler actors remain unchanged.

The variant accepts ONLY `--download-and-inspect-diagnostic`, with the same
GitHub-hosted Linux guard. This proposed argv has NOT been run live or added to a
workflow execution step. CI imports/tests the source using synthetic inputs only.
Acceptance of this source would not itself authorize a second attempt. A future
finite action needs its own approval, exact source hashes, one-attempt selector
and a wrapper reviewed for this TWO-line protocol. The consumed E12 job still
pins the old one-line driver and skips this head; do not repurpose it silently.

## 2. Fixed diagnostic contract

Failure keeps the first line exactly `HOLD: artifact preparation incomplete`,
exit 2, followed by one ASCII diagnostic JSON line <=2,048 bytes. Success keeps
the original bounded E11 inspection JSON first, exit 0, followed by the diagnostic
line. The existing inspection JSON may contain public archive entry names as
already reviewed; the NEW diagnostic line contains no names or paths. A complete
process receipt and strict future wrapper gate are still necessary for evidence.
A diagnostic frame alone is never an archive verification/approval token.

| Field | Allowed value/meaning |
| --- | --- |
| stage | START, GUARD, RESOURCE_LIMITS, RECEIPT_BINDING, TEMPFILE, HTTP_OPEN, HTTP_HEADERS, HTTP_BODY, ARCHIVE_HASH, ARCHIVE_PARSE, CLEANUP, RECEIPT_ENCODE, COMPLETE |
| error | NONE, PREDICATE_REJECTED, REDIRECT_REJECTED, HTTP_403, HTTP_404, HTTP_429, HTTP_5XX, HTTP_OTHER, TLS_ERROR, TIMEOUT, TRANSPORT_ERROR, IO_ERROR, MEMORY_LIMIT, ARCHIVE_ERROR, JSON_ERROR, UNEXPECTED_ERROR |
| received_bytes | Bytes returned by body reads, including at most the single byte detecting an exceeded cap; not guaranteed written/flushed/complete |
| download_complete | True only after headers/length/body predicates and output flush complete |
| hashed_bytes | Bytes returned by the full-archive hash reads, with the same one-byte oversize ceiling; excludes selected-file hashes |
| hash_complete / archive_sha256 | Digest exists only after full-archive hash EOF; partial hash remains null; size/digest admission may still fail |
| digest_matches | Null until hash EOF, then equality with expected digest; never implies parser/import/setup success |
| parsed_members | Count of unique, normalized members admitted into the header set so far, before the remaining size/type/content checks; not a completed validated inventory |
| readiness/guest/scope | archive_verified_receipt, j0_ready, setup_ready, guest_imported/started, r1_complete, r2_authorized, scope_granted always false in diagnostic frames |

Error classification uses fixed exception types and whitelisted HTTP code
categories only. Wrapped SSL/timeouts inspect reason TYPE only; no exception
string/args, response reason/header/body, redirect URL, filename, errno, credential
or archive content is serialized. Unknown errors collapse to UNEXPECTED_ERROR.
No debug logging, traceback, resolver probe or alternate request is added.

Stage is the last entered instrumented operation, NOT proof of root cause.
Context-manager enter/exit/unwind errors can occur while that last stage remains
set. An HTTP error category is not a diagnosis of provider policy or intent.
Received/hashed byte counts are separate milestones. Failed validation cannot
become a successful receipt, and digest equality does not close any J0 binding.
No inferred download/hash/parser progress is appended to the old E12 record.

The alarm is disarmed after resource unwinding on failure before reporting;
success disarms after cleanup/inspection encoding as before. Diagnostic output
is best effort under memory pressure or broken stdout. Serialization failure
uses only fixed JSON class `j0-artifact-diagnostic-unavailable`, schema 1, error
DIAGNOSTIC_UNAVAILABLE, with NO stage/counters fabricated. It is not a normal
frame and cannot satisfy any successful future gate. Broken-output exceptions
inside failure reporting are suppressed to avoid a chained traceback formatting
the original private exception; exit remains 2 and missing output stays HOLD. A hard process death may
produce no diagnostic at all; EOF/missing/invalid/extra output must remain HOLD.
No claim that stdout reporting is independently supervised or operationally
bounded is added; outer ownership/cessation remains open.

## 3. Offline evidence and review exit

25 offline controls consist of twelve unchanged E11 mechanic tests rebound to
this variant, plus thirteen diagnostic tests. The original thirteen E11 controls
still run separately unchanged. Its old one-line guard test is not rebound;
the new constant-plus-JSON guard is tested explicitly, without skip/relaxation.
Tests include HTTP/header/partial-body and hash/parser milestones, whitelist and
private-sentinel suppression across exception classes, hash-before-parser, no
partial digest, full main HTTP failure and two-frame synthetic success, alarm
setup/disarm calls, fixed diagnostic-failure/broken-output handling and differential success
receipt/limit equality with E11. Main tests replace network responses, resource
limits/alarms and (only for success) synthetic input receipt/digest bindings;
actual parsing/hashing/tempfile/control flow executes. No real network, alarm,
address-space change, provider archive, guest or credential is used.

CI adds this suite on Python 3.12/3.14 with ResourceWarning-as-error, full post-exit
warning scan, exact count/OK/no-skips gate. Existing 69 + original 13 and Windows/
identity/carrier suites remain mandatory. Source compilation, links and whitespace
are checked separately; CI results belong to their exact head.

Review the enum/milestone/privacy/failure/output-contract delta before any second
attempt. No live download, retry, alternative image, setup source completion,
prepared image, import or provisioning is claimed here. J0 NOT READY; R1 NOT
AUTHORIZED; R2 HOLD; all outstanding ledger/private bindings and #80/#96 remain.

## Initial CI finding and response cleanup correction

Initial source head `d33060ad`, run 41171286462: 25 tests reported OK on 3.14,
but the mandatory post-exit gate rejected ResourceWarning from unclosed synthetic
HTTPError response wrappers. This failed result is retained; no warning filter,
assertion relaxation or scan removal. Python 3.12 passed at that historical head.
The variant now closes HTTPError before rethrow and closes rejected redirect
responses before raising its fixed enum; tests explicitly assert both closures.
Classification-only fixture exceptions also register close cleanup. This avoids
finalizer warnings that can format an exception's private text, not just a test
cosmetic issue. Failure still exits HOLD with bounded diagnostics and no retry;
E11 bytes and the failed E12 record stay unchanged. No live download occurred.
