"""Test-only P1 transport fixture; disposable registry, no configured backend.

The reserved create label injects a reader error only around that real create.
It is not a production command or a natural storage failure. Missing/locked
scenarios instead exercise actual SQLite read failures. Every other backend
operation is rejected by stubs; their local status is synthetic, not health.
"""
import argparse
from contextlib import nullcontext
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import server
from contexts import ContextError, ContextRegistry
from stdio_guard import run_stdio_guarded

FAULT_LABEL = 'P1_FIXTURE_CREATE_READ_FAILURE'


class NoBackend:
    def start_watchdog(self):
        # The real server calls this hook; this fixture starts no native worker.
        pass

    def local_status(self):
        return {'fixture_only': True, 'backend_initialized': False}

    def __getattr__(self, name):
        raise ContextError('Fixture backend operations are disabled.')


class FixtureAudit:
    def record(self, *args):
        pass


class FixtureRegistry(ContextRegistry):
    def create(self, label):
        fault = (patch('context_read.registry_reader',
                       side_effect=sqlite3.OperationalError('PRIVATE_FIXTURE_STORAGE_ERROR'))
                 if label == FAULT_LABEL else nullcontext())
        with fault:
            # Actual durable create/status/observation and production error filtering.
            return super().create(label)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=('healthy', 'missing', 'locked'), default='healthy')
    scenario = parser.parse_args().scenario
    with tempfile.TemporaryDirectory(prefix='context-p1-transport-') as tmp:
        contexts = FixtureRegistry(Path(tmp), FixtureAudit(), soft_cap=3)
        lock = None
        try:
            if scenario == 'missing':
                contexts.path.unlink()
            elif scenario == 'locked':
                lock = sqlite3.connect(contexts.path)
                lock.execute('BEGIN EXCLUSIVE')
            backend = NoBackend()
            run_stdio_guarded(server(backend, backend, backend, contexts))
        finally:
            if lock is not None:
                lock.rollback()
                lock.close()


if __name__ == '__main__':
    main()
