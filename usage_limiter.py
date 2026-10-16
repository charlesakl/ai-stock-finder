"""SQLite daily quota for a single trusted local deployment.
Public paid access is disabled by default. SQLite on ephemeral cloud disks is NOT
suitable for durable multi-instance public quotas.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

LIMITS = {'Free Research': None, 'AI Research': 5, 'Advanced AI Research': 2}
GLOBAL_DAILY_LIMIT = int(os.getenv('GLOBAL_DAILY_LIMIT', '20'))
DB = Path(os.getenv('USAGE_DB_PATH', str(Path(__file__).parent / '.usage_limits.sqlite3')))


def paid_enabled():
    return os.getenv('ENABLE_PAID_AI', 'false').lower() == 'true'


def _connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB), timeout=20, isolation_level=None)
    con.execute('PRAGMA busy_timeout=20000')
    con.execute('CREATE TABLE IF NOT EXISTS usage (day TEXT NOT NULL, user_id TEXT NOT NULL, mode TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(day,user_id,mode))')
    return con


def remaining(user_id, mode):
    limit = LIMITS[mode]
    if limit is None:
        return None
    today = datetime.now(timezone.utc).date().isoformat()
    with _connect() as con:
        row = con.execute('SELECT count FROM usage WHERE day=? AND user_id=? AND mode=?', (today,user_id,mode)).fetchone()
    return max(0, limit - (row[0] if row else 0))


def reserve(user_id, mode):
    """Atomically reserve a paid workflow before any model calls. No automatic refund."""
    if mode not in LIMITS or LIMITS[mode] is None:
        raise ValueError('Not a paid research mode')
    if not paid_enabled():
        return False, 'Paid AI is disabled on this deployment.'
    day = datetime.now(timezone.utc).date().isoformat()
    with _connect() as con:
        try:
            con.execute('BEGIN IMMEDIATE')
            used = con.execute('SELECT COALESCE(SUM(count),0) FROM usage WHERE day=?', (day,)).fetchone()[0]
            individual = con.execute('SELECT count FROM usage WHERE day=? AND user_id=? AND mode=?', (day,user_id,mode)).fetchone()
            if used >= GLOBAL_DAILY_LIMIT:
                con.execute('ROLLBACK')
                return False, 'The daily AI request allowance for this deployment has been reached.'
            if individual and individual[0] >= LIMITS[mode]:
                con.execute('ROLLBACK')
                return False, f'Daily {mode} limit reached. Try again tomorrow (UTC).'
            con.execute('INSERT INTO usage(day,user_id,mode,count) VALUES(?,?,?,1) ON CONFLICT(day,user_id,mode) DO UPDATE SET count=count+1', (day,user_id,mode))
            con.execute('COMMIT')
            return True, ''
        except Exception:
            con.execute('ROLLBACK')
            raise
