"""Linux offline checkpoint store. Private root is explicitly supplied by caller."""
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
import stat
import sys

from checkpoint import Hold, MAX_BYTES, need, validate

APP_ID = 0x48434631
DB = 'checkpoints.sqlite3'
SQL = (
    'CREATE TABLE checkpoints (checkpoint_id TEXT PRIMARY KEY, chain_id TEXT NOT NULL, generation INTEGER NOT NULL, digest TEXT NOT NULL, envelope BLOB NOT NULL, UNIQUE(chain_id,generation))',
    'CREATE TABLE heads (chain_id TEXT PRIMARY KEY, generation INTEGER NOT NULL, digest TEXT NOT NULL, checkpoint_id TEXT NOT NULL)')


def _commit(connection):
    connection.execute('COMMIT')


class Store:
    def __init__(self, root, max_rows=256):
        self.fd = None
        need(sys.platform == 'linux', 'STORE_UNAVAILABLE')
        need(type(max_rows) is int and 1 <= max_rows <= 4096, 'BUDGET_EXHAUSTED')
        self.max_rows = max_rows
        try:
            path = Path(root)
            need(path.is_absolute() and '..' not in path.parts, 'STORE_UNAVAILABLE')
            fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
            try:
                for component in path.parts[1:]:
                    child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    os.close(fd)
                    fd = child
                self.fd, fd = fd, None
            finally:
                if fd is not None:
                    os.close(fd)
            self._root()
            try:
                new = os.open(DB, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
            except FileExistsError:
                pass
            else:
                os.close(new)
                os.fsync(self.fd)
            with self._connect() as db:
                db.execute('BEGIN IMMEDIATE')
                try:
                    tables = db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
                    if not tables and db.execute('PRAGMA application_id').fetchone()[0] == 0:
                        for sql in SQL:
                            db.execute(sql)
                        db.execute(f'PRAGMA application_id={APP_ID}')
                        db.execute('PRAGMA user_version=1')
                    else:
                        self._schema(db)
                    _commit(db)
                except BaseException:
                    db.execute('ROLLBACK')
                    raise
        except BaseException as error:
            self.close()
            if isinstance(error, Hold):
                raise
            if isinstance(error, (OSError, sqlite3.Error, ValueError, TypeError)):
                raise Hold('STORE_UNAVAILABLE') from None
            raise

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def _root(self):
        need(self.fd is not None, 'STORE_UNAVAILABLE')
        info = os.fstat(self.fd)
        need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
             and stat.S_IMODE(info.st_mode) == 0o700, 'STORE_UNAVAILABLE')

    def _schema(self, db):
        need(db.execute('PRAGMA application_id').fetchone()[0] == APP_ID
             and db.execute('PRAGMA user_version').fetchone()[0] == 1, 'STORE_UNAVAILABLE')
        rows = db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        expected = [('table', 'checkpoints', SQL[0]), ('table', 'heads', SQL[1])]
        need(rows == expected, 'STORE_UNAVAILABLE')

    @contextmanager
    def _connect(self):
        db = None
        try:
            self._root()
            for name in (DB, DB+'-journal', DB+'-wal', DB+'-shm'):
                try:
                    info = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
                except FileNotFoundError:
                    need(name != DB, 'STORE_UNAVAILABLE')
                    continue
                need(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                     and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
                     and info.st_size <= 320*1024**2,
                     'STORE_UNAVAILABLE')
                need(name not in (DB+'-wal', DB+'-shm'), 'STORE_UNAVAILABLE')
            db = sqlite3.connect(f'/proc/self/fd/{self.fd}/{DB}', isolation_level=None, timeout=2)
            db.execute('PRAGMA trusted_schema=OFF')
            need(db.execute('PRAGMA journal_mode').fetchone()[0] == 'delete', 'STORE_UNAVAILABLE')
            db.execute('PRAGMA synchronous=FULL')
            yield db
        except (OSError, sqlite3.Error, ValueError):
            raise Hold('STORE_UNAVAILABLE') from None
        finally:
            if db is not None:
                db.close()

    def append(self, raw, expected_generation=0, expected_digest=None):
        envelope = validate(raw)  # Reject input before opening a transaction.
        p = envelope['payload']
        need(type(expected_generation) is int and expected_generation >= 0)
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                self._schema(db)
                row = db.execute('SELECT generation,digest FROM heads WHERE chain_id=?', (p['chain_id'],)).fetchone()
                need(row == (expected_generation, expected_digest) if row else
                     expected_generation == 0 and expected_digest is None, 'CONCURRENT_UPDATE')
                need(p['generation'] == expected_generation+1 and p['parent_sha256'] == expected_digest,
                     'STALE_GENERATION')
                need(db.execute('SELECT count(*) FROM checkpoints').fetchone()[0] < self.max_rows,
                     'BUDGET_EXHAUSTED')
                need(not db.execute('SELECT 1 FROM checkpoints WHERE checkpoint_id=?', (p['checkpoint_id'],)).fetchone(),
                     'CONCURRENT_UPDATE')
                db.execute('INSERT INTO checkpoints VALUES (?,?,?,?,?)',
                           (p['checkpoint_id'], p['chain_id'], p['generation'], envelope['payload_sha256'], raw))
                if row:
                    changed = db.execute('UPDATE heads SET generation=?,digest=?,checkpoint_id=? WHERE chain_id=? AND generation=? AND digest=?',
                        (p['generation'], envelope['payload_sha256'], p['checkpoint_id'], p['chain_id'], expected_generation, expected_digest)).rowcount
                    need(changed == 1, 'CONCURRENT_UPDATE')
                else:
                    db.execute('INSERT INTO heads VALUES (?,?,?,?)', (p['chain_id'], p['generation'], envelope['payload_sha256'], p['checkpoint_id']))
                _commit(db)
                return p['generation'], envelope['payload_sha256']
            except BaseException:
                if db.in_transaction:
                    db.execute('ROLLBACK')
                raise

    def head(self, chain_id):
        need(type(chain_id) is str)
        with self._connect() as db:
            db.execute('BEGIN')
            self._schema(db)
            row = db.execute('SELECT h.generation,h.digest,h.checkpoint_id,substr(c.envelope,1,?) FROM heads h LEFT JOIN checkpoints c ON c.checkpoint_id=h.checkpoint_id WHERE h.chain_id=?',
                             (MAX_BYTES+1, chain_id)).fetchone()
            need(row is not None, 'STALE_GENERATION')
            envelope = validate(row[3])
            p = envelope['payload']
            need((p['chain_id'], p['generation'], envelope['payload_sha256'], p['checkpoint_id']) ==
                 (chain_id, row[0], row[1], row[2]), 'CHECKSUM_MISMATCH')
            # Check predecessor chain within the same committed read snapshot.
            need(p['generation'] <= self.max_rows, 'BUDGET_EXHAUSTED')
            generation, parent = p['generation']-1, p['parent_sha256']
            while generation:
                previous = db.execute('SELECT digest,substr(envelope,1,?) FROM checkpoints WHERE chain_id=? AND generation=?',
                                      (MAX_BYTES+1, chain_id, generation)).fetchone()
                need(previous is not None and previous[0] == parent, 'CHECKSUM_MISMATCH')
                older = validate(previous[1])
                op = older['payload']
                need((op['chain_id'], op['generation'], older['payload_sha256']) ==
                     (chain_id, generation, parent), 'CHECKSUM_MISMATCH')
                parent = op['parent_sha256']
                generation -= 1
            need(parent is None, 'CHECKSUM_MISMATCH')
            return envelope
