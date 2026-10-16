"""Local, time-limited JSON cache for paid AI model responses. No API keys stored."""
import hashlib
import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / '.ai_cache'
TTL_SECONDS = int(os.getenv('AI_CACHE_HOURS', '168')) * 3600
# Remove retrieval-only timestamps; retain substantive evidence and dates.
VOLATILE = {'retrieved_at', 'generated_at', 'asof'}

def _normalized(value):
    if isinstance(value, dict):
        return {k: _normalized(v) for k, v in sorted(value.items()) if k not in VOLATILE}
    if isinstance(value, list):
        return [_normalized(v) for v in value]
    return value

def key_for(kind, model, instructions, payload):
    encoded = json.dumps({'kind': kind, 'model': model, 'instructions': instructions,
                          'payload': _normalized(payload)}, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()

def load(key):
    if TTL_SECONDS <= 0:
        return None
    path = CACHE_DIR / (key + '.json')
    try:
        if time.time() - path.stat().st_mtime > TTL_SECONDS:
            return None
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None

def save(key, value):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / (key + '.json')
    temp = CACHE_DIR / (key + '.tmp')
    temp.write_text(json.dumps(value, default=str), encoding='utf-8')
    os.replace(temp, path)
