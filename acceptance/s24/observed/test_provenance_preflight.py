"""Synthetic policy tests only. No certificates/signatures/tools are executed."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('preflight', ROOT / 'provenance_preflight.py')
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class PreflightControls(unittest.TestCase):
    def setUp(self):
        self.policy = dict(kind='j0-unsigned-preflight-policy', schema=1,
                           repository='fixture/project', repository_id=123,
                           owner_id=456, source_sha='a'*40, signer_sha='b'*40, workflow_sha='e'*40,
                           ref='refs/heads/main', workflow='.github/workflows/build.yml',
                           signer_workflow='.github/workflows/trusted.yml', run_id=789,
                           attempt=1, generation='c'*32, lock_sha256='d'*64)
        self.cipher = b'OPAQUE SYNTHETIC BYTES; NOT ENCRYPTED'
        self.descriptor = dict(kind='j0-unsigned-preflight-descriptor', schema=1,
                               generation='c'*32, lock_sha256='d'*64, run_id=789,
                               attempt=1, ciphertext_sha256=sha(self.cipher),
                               scope_granted=False)
        # Construct expected certificate independently from production mapper.
        self.cert = dict(
            issuer='https://token.actions.githubusercontent.com',
            subjectAlternativeName='https://github.com/fixture/project/.github/workflows/trusted.yml@refs/heads/main',
            buildSignerURI='https://github.com/fixture/project/.github/workflows/trusted.yml@refs/heads/main',
            buildSignerDigest='b'*40, runnerEnvironment='github-hosted',
            sourceRepositoryURI='https://github.com/fixture/project',
            sourceRepositoryDigest='a'*40, sourceRepositoryRef='refs/heads/main',
            sourceRepositoryIdentifier='123', sourceRepositoryOwnerURI='https://github.com/fixture',
            sourceRepositoryOwnerIdentifier='456',
            buildConfigURI='https://github.com/fixture/project/.github/workflows/build.yml@refs/heads/main',
            buildConfigDigest='e'*40, buildTrigger='workflow_dispatch',
            runInvocationURI='https://github.com/fixture/project/actions/runs/789/attempts/1')
        self.projection = dict(kind='j0-unsigned-certificate-projection', schema=1,
                               certificate=self.cert,
                               predicate_type='https://slsa.dev/provenance/v1',
                               subjects=dict(descriptor=sha(wire(self.descriptor)),
                                             ciphertext=sha(self.cipher)))

    def inspect(self, projection=None, policy=None, descriptor=None, cipher=None):
        return P.inspect_projection(wire(self.projection if projection is None else projection),
                                    wire(self.policy if policy is None else policy),
                                    wire(self.descriptor if descriptor is None else descriptor),
                                    self.cipher if cipher is None else cipher)

    def rejected(self, function, reason=None):
        with self.assertRaises(P.Hold) as caught:
            function()
        self.assertEqual(caught.exception.args, ())
        self.assertIn(caught.exception.reason, P.REASONS)
        if reason:
            self.assertEqual(caught.exception.reason, reason)

    def test_perfect_match_never_authenticates(self):
        result = self.inspect()
        self.assertEqual(result['state'], 'MATCHED_UNAUTHENTICATED')
        self.assertEqual(result['projection_sha256'], sha(wire(self.projection)))
        for key in ('provenance_authenticated', 'tool_authenticated', 'scope_granted',
                    'secret_release_authorized', 'j0_ready', 'r1_complete', 'r2_authorized'):
            self.assertIs(result[key], False)

    def test_each_certificate_claim_mismatch(self):
        for field in self.cert:
            with self.subTest(field=field):
                value = copy.deepcopy(self.projection)
                value['certificate'][field] += '-PRIVATE_VALUE'
                self.rejected(lambda: self.inspect(projection=value), 'CLAIM')

    def test_each_certificate_claim_required(self):
        for field in self.cert:
            with self.subTest(field=field):
                value = copy.deepcopy(self.projection)
                del value['certificate'][field]
                self.rejected(lambda: self.inspect(projection=value), 'SCHEMA')

    def test_unsigned_predicate_cannot_fill_missing_certificate(self):
        value = copy.deepcopy(self.projection)
        del value['certificate']['runInvocationURI']
        value['predicate'] = {'runInvocationURI': self.cert['runInvocationURI']}
        self.rejected(lambda: self.inspect(projection=value), 'SCHEMA')

    def test_replay_attempt_and_run(self):
        for uri in ('https://github.com/fixture/project/actions/runs/789/attempts/2',
                    'https://github.com/fixture/project/actions/runs/790/attempts/1',
                    'https://github.com/fixture/project/actions/runs/789'):
            value = copy.deepcopy(self.projection)
            value['certificate']['runInvocationURI'] = uri
            self.rejected(lambda: self.inspect(projection=value), 'CLAIM')

    def test_workflow_prefix_and_ref_suffix_attack(self):
        for field in ('subjectAlternativeName', 'buildSignerURI', 'buildConfigURI'):
            for suffix in ('.attacker.yml', '@refs/heads/attacker', '/extra'):
                value = copy.deepcopy(self.projection)
                value['certificate'][field] += suffix
                self.rejected(lambda: self.inspect(projection=value), 'CLAIM')

    def test_renamed_repository_identifier_mismatch(self):
        value = copy.deepcopy(self.projection)
        value['certificate']['sourceRepositoryIdentifier'] = '999'
        self.rejected(lambda: self.inspect(projection=value), 'CLAIM')

    def test_caller_authentication_flags_rejected(self):
        for key in ('verified', 'provenance_authenticated', 'success', 'scope_granted'):
            value = copy.deepcopy(self.projection)
            value[key] = True
            self.rejected(lambda: self.inspect(projection=value), 'SCHEMA')

    def test_both_subjects_required(self):
        for name in ('descriptor', 'ciphertext'):
            value = copy.deepcopy(self.projection)
            del value['subjects'][name]
            self.rejected(lambda: self.inspect(projection=value), 'SCHEMA')

    def test_subject_substitution_and_wrong_predicate(self):
        for name in ('descriptor', 'ciphertext'):
            value = copy.deepcopy(self.projection)
            value['subjects'][name] = 'f'*64
            self.rejected(lambda: self.inspect(projection=value), 'SUBJECT')
        value = copy.deepcopy(self.projection)
        value['predicate_type'] = 'https://attacker.invalid/predicate'
        self.rejected(lambda: self.inspect(projection=value), 'CLAIM')

    def test_changed_actual_bytes(self):
        self.rejected(lambda: self.inspect(cipher=self.cipher+b'changed'), 'SUBJECT')
        value = copy.deepcopy(self.descriptor)
        value['scope_granted'] = True
        self.rejected(lambda: self.inspect(descriptor=value), 'SCHEMA')

    def test_descriptor_context_rebound_hash_still_rejects(self):
        for field in ('generation', 'lock_sha256', 'run_id', 'attempt'):
            d = copy.deepcopy(self.descriptor)
            d[field] = 42 if type(d[field]) is int else 'e'*len(d[field])
            x = copy.deepcopy(self.projection)
            x['subjects']['descriptor'] = sha(wire(d))
            self.rejected(lambda: self.inspect(projection=x, descriptor=d), 'CONTEXT')

    def test_duplicate_float_nonfinite_and_oversize(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.0}',
                    b'{"a":Infinity}', b' '*65537, b'{"a":'+b'1'*100+b'}',
                    b'{"a":"\xff"}', b'{} trailing'):
            self.rejected(lambda: P.record(raw), 'INPUT')

    def test_nesting_bound_before_json_parse(self):
        self.rejected(lambda: P.record(b'{"x":'+b'['*13+b'0'+b']'*13+b'}'), 'INPUT')
        self.assertEqual(P.record(b'{"s":"[[[[[[[[[[[[[[[["}')['s'], '['*16)

    def test_bool_not_integer_and_closed_policy(self):
        for field in ('repository_id', 'owner_id', 'run_id', 'attempt', 'schema'):
            value = copy.deepcopy(self.policy)
            value[field] = True
            self.rejected(lambda: self.inspect(policy=value), 'SCHEMA')
        value = copy.deepcopy(self.policy)
        value['private_path'] = '/PRIVATE/path'
        self.rejected(lambda: self.inspect(policy=value), 'SCHEMA')

    def test_production_and_raw_gh_classes_rejected(self):
        value = copy.deepcopy(self.projection)
        value['kind'] = 'j0-authenticated-provenance-v1'
        self.rejected(lambda: self.inspect(projection=value), 'SCHEMA')
        self.rejected(lambda: P.inspect_projection(b'[{"verificationResult":{}}]',
                                                   wire(self.policy), wire(self.descriptor),
                                                   self.cipher), 'SCHEMA')

    def test_tool_equality_never_authenticates_or_executes(self):
        result = P.compare_tool_object(b'synthetic tool', sha(b'synthetic tool'), 14)
        self.assertEqual(result['state'], 'DIGEST_EQUAL_UNAUTHENTICATED')
        self.assertIs(result['tool_authenticated'], False)
        self.assertIs(result['execution_authorized'], False)

    def test_tool_mutations_fail_closed(self):
        for digest, size in ((sha(b'wrong'), 4), (sha(b'tool'), 5),
                             (sha(b'tool'), True), ('NOT_A_DIGEST', 4)):
            self.rejected(lambda: P.compare_tool_object(b'tool', digest, size))
        self.rejected(lambda: P.compare_tool_object(b'', sha(b''), 0))

    def test_policy_ref_and_identity_types(self):
        for field, value in (('ref', 'refs/pull/1/merge'),
                             ('workflow', '.github/workflows/../bad.yml'),
                             ('source_sha', 'A'*40), ('attempt', 0)):
            p = copy.deepcopy(self.policy)
            p[field] = value
            self.rejected(lambda: self.inspect(policy=p))

    def test_import_and_action_audit(self):
        tree = ast.parse((ROOT/'provenance_preflight.py').read_text())
        self.assertEqual([n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)],
                         ['hashlib', 'json', 're'])
        self.assertFalse(any(isinstance(n, ast.ImportFrom) for n in ast.walk(tree)))
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                             and n.func.id in {'open', 'eval', 'exec', '__import__'}
                             for n in ast.walk(tree)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
