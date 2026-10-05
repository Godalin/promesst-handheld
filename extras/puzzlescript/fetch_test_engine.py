#!/usr/bin/env python3
"""Fetch pinned official PuzzleScript PM JS files for host-side validation only."""
import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = json.loads(Path(__file__).with_name('upstream.lock.json').read_text())['pm_test_engine']
DEST = ROOT / 'build' / 'puzzlescript' / 'pm-engine'


def fetch_file(item):
    name, expected = item
    path = DEST / name
    if path.is_file():
        data = path.read_bytes()
    else:
        url = 'https://raw.githubusercontent.com/{repository}/{commit}/{path}/'.format(**ENGINE) + name
        request = urllib.request.Request(url, headers={'User-Agent': 'handheld-puzzlescript/1'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ValueError('Test engine file too large: ' + name)
    git_blob = b'blob ' + str(len(data)).encode() + b'\0' + data
    if hashlib.sha1(git_blob).hexdigest() != expected:
        raise ValueError('Pinned Git blob mismatch: ' + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return name


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(fetch_file, ENGINE['files'].items()))
    print(str(DEST) + ': ' + str(len(files)) + ' official JS files verified at ' + ENGINE['commit'])
