# Handoff offline source candidate — delivery 2

Status: **SOURCE CANDIDATE / STANDALONE OFFLINE ONLY**. Design #113 merged at
`53c37737f242e87d55cea1cf525977d0202a2b01` after operator approval. This candidate
implements the reviewed [design/schema](../../docs/HANDOFF-CHECKPOINT-DESIGN-TH.md)
in a separate PR, not a bridge tool/CLI/config/backend adapter or release artifact.
J0 is parked; no inventory/model/Dev/production/guest call, fifth attempt or merge.

## Source bytes for independent review

| File | SHA256 |
| --- | --- |
| `checkpoint.py` | `114bc057cb6ffbdc9d0c09f37250e52e9aed0673220b9d444e3508cfa44f854e` |
| `store.py` | `d5106483892ea9ae4832204bdfd9c446013b44e1894e21d5f8614fe245806c97` |
| `fixtures.py` | `953c8f833d803fe363fb281807cca12d995562875bcd2345c55f0aa0029b50c9` |
| `test_offline.py` | `569d6e09aa99149b62c6452014f0a5d7a575edb776444045de4edf72869c35f3` |

Approved schema remains byte-identical at SHA256
`3dc3f73a5d67f859c2f779e1f8bc9c49831420a4044f71de5f09aa71c241fadf`;
example remains `77166b839c51cc77f54d24c11532932ddac7ecac671580b25557f1c7e00fbb95`.
No original runtime module, SPEC, permission policy, contexts/jobs database,
requirement/dependency or S24 source/workflow changed. This directory is separate
acceptance code, not automatically loaded by the bridge.

## Interfaces and containment

`checkpoint.validate(raw: bytes)` reads no checkpoint path and dereferences no
payload refs. It validates <=64 KiB UTF-8, depth <=16, duplicate/nonfinite/float
rejection, pinned closed schema, canonical payload checksum, parent/generation
shape and evidence foreign keys. It reads only its fixed hash-bound schema file.
The stdlib checker supports exactly the approved schema keywords, not arbitrary
JSON Schema. Integers are strict non-boolean ints; even mathematically integral
floats reject. Explicit timestamp profile is uppercase RFC3339 T/Z or offset,
<=6 fraction digits, valid calendar/time/offset; leap seconds and other variants
HOLD. It never relies on an optional format checker. Errors contain fixed enums.

`Store(root, max_rows=256)` is Linux/POSIX-only, with an explicitly supplied
existing owner-only 0700 root. Every path component is opened no-follow; the final
directory descriptor is retained. SQLite goes through /proc/self/fd, with owner /
0600 / single-link / regular-file admission for DB and rollback journal, rejecting
WAL/SHM and symlink substitution. Existing modes are never repaired. 320 MiB file
cap, 1..4096 configurable immutable-row cap (default 256), 2 s SQLite lock wait.
Unknown schema/application ID/user version rejects. Directory creation is not an
API. Initialization is an explicit store write, distinct from pure validation.

`append(raw, expected_generation, expected_digest)` validates before transaction,
then BEGIN IMMEDIATE + immutable insert + head CAS in one FULL-synchronous DELETE-
journal transaction. IDs and (chain,generation) are unique. No overwrite/prune or
original backend-state mutation. `head(chain)` validates its committed snapshot
and predecessor chain. Store reads may perform SQLite recovery of a hot journal;
they are not advertised as side-effect-free loading of arbitrary untrusted DBs.

Filesystem policy assumes a trusted private root/current uid. It does not defend
against a malicious same-uid writer or full-store rollback. Stored row immutability
is an API property, not cryptographic authentication or SQL write protection.
Process-crash controls prove before/after-commit behavior in these fixtures, not
hardware power-loss durability. Windows/DrvFS ACL admission is NOT IMPLEMENTED.

`plan(raw, Facts(...))` returns a `Decision` with authorizes_actions=false, never
dispatches or invokes a callback. Facts are separately supplied trusted caller /
fixture snapshots, not constructed from checkpoint claims: head, repo/workspace,
dossier/profile, current authority/expiry, job identity, independent artifact /
verifier observations. There is no production Facts collector, approval reader,
backend capability probe, ownership authenticator or goal verifier in this PR.
Passing forged Facts is outside that boundary; a Decision is not authority.

The planner binds goal/criteria/profile to independent facts; preserves native
unknown_exit and waiting states; refuses Codex missing-job-ID replay; proposes
original-job observation/reconciliation only. No guarded replay/submit/cancel /
resume operation exists. A completed decision requires completed native evidence,
fixture exit=0, matching required artifact records and an independently supplied
verifier pass. Actual Hermes metadata is not assumed to contain an exit code;
a future backend-specific adapter/profile must bind the correct terminal proof.
No production goal-verification compatibility is claimed.

## Meaningful controls and disclosed substitutions

26 source-control tests: strict parsing/checksum/date/authority/foreign-key gates;
actual private SQLite permissions/schema drift/cap/replay/corruption; retained-root
rename; invalid-input DB unchanged; two actual writer processes with one CAS winner;
crash via os._exit before/after the real append commit (test-only commit-boundary
fault injection, no source fault switches). Closed journals/DBs and child cleanup
are checked under ResourceWarning-as-error.

H01/H02 use a separate durable fixture ledger and actual owned child with one
synthetic effect. ACK is discarded; reconstruction/idempotent fixture admission
finds original IDs and effect remains one; fingerprint conflict rejects. This is
not proof of actual Hermes/OpenCode replay or the native 23-hour contract.
Codex unknown ID always HOLDs. H03/H06/H09 check missing dossier/profile, changed
binding, closed context and current expired/missing scope before dependent plans.
H04 exercises both scheduled cancel-before-terminal and completion-before-cancel
orders with a real worker/transaction. H05 kills its own fixture worker before
terminal: the fixture collector supplies unknown_exit; actual backend restart
recovery is NOT IMPLEMENTED/TESTED here. H08 hashes actual synthetic artifact bytes,
then removes/drifts them or rejects verifier evidence; native completion alone
never closes goal. H07/H10 are real SQLite crash/CAS controls described above.

The fixture ledger models selected contract predicates; it is not an adapter to
core.py/codex_core.py/opencode_tasks.py. No model/API/SSH/CIM/guest/network is used.
Fault schedules/barriers act only on fixture children. This suite is **not** the
[paired preregistered evaluation](../../docs/HANDOFF-RECOVERY-EXPERIMENT-PLAN-TH.md):
no baseline-vs-candidate arm run, no held-out trial, no measured gain or transfer
claim. Source controls and future recovery trials have separate denominators.

Run only the offline controls:

```bash
python -W error::ResourceWarning -I -S -B -m unittest discover -s acceptance/handoff -p 'test_*.py' -v
```

Local Python 3.12.14: 26/26 OK, no skips/warning markers. New Linux
3.12/3.14 workflow enforces exact head/count/no-skips/post-exit warning gates;
exact-head CI must be inspected separately. Original baseline tests stay intact.
No source acceptance/merge/release claim follows automatically from green CI.
Next: independent exact-source review, then freeze a separate harness/schedules /
protocol for paired evaluation before any scoped adapter or runtime pilot.
R1 NOT AUTHORIZED / R2 HOLD; #80/#96/#112 and private bindings unchanged.
