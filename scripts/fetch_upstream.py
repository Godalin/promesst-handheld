#!/usr/bin/env python3
"""Download pinned official releases; import only source, documentation and assets."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'scripts/upstream.lock.json').read_text())


def relative(name, prefix):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe archive member: ' + name)
    return path.relative_to(prefix)


def import_release(game, archive):
    spec = LOCK[game]
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != spec['sha256']:
        raise ValueError(f'{game}: checksum mismatch: {digest}')
    destination = ROOT / 'upstream' / game
    with tarfile.open(archive) as outer:
        for member in outer.getmembers():
            if not member.isfile():
                continue
            rel = relative(member.name, spec['prefix'])
            if not (str(rel) == spec['source_archive'] or rel.suffix == '.txt'
                    or rel.parts[0] == spec['assets']):
                continue
            target = destination / str(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(outer.extractfile(member).read())
    inner_path = destination / spec['source_archive']
    source = destination / 'source'
    source.mkdir(parents=True, exist_ok=True)
    if inner_path.suffix == '.zip':
        with zipfile.ZipFile(inner_path) as inner:
            for member in inner.infolist():
                if member.is_dir():
                    continue
                rel = relative(member.filename, spec['source_prefix'])
                target = source / str(rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(inner.read(member))
    else:
        with tarfile.open(inner_path) as inner:
            for member in inner.getmembers():
                if not member.isfile():
                    continue
                rel = relative(member.name, spec['source_prefix'])
                target = source / str(rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(inner.extractfile(member).read())
    assets = ROOT / 'assets' / game / spec['assets']
    shutil.copytree(destination / spec['assets'], assets, dirs_exist_ok=True)
    print(f'{game} {spec["version"]}: verified and imported ({digest})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', type=Path,
                        help='Use previously downloaded official archives, without network access')
    parser.add_argument('--game', choices=list(LOCK), help='Only import one game')
    args = parser.parse_args()
    for game in ([args.game] if args.game else LOCK):
        spec = LOCK[game]
        if args.archive_dir:
            archive = args.archive_dir / spec['archive']
        else:
            archive = ROOT / 'downloads' / spec['archive']
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                request = urllib.request.Request(spec['url'], headers={'User-Agent': 'Promesst-handheld-builder'})
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = response.read(16 * 1024 * 1024 + 1)
                if len(payload) > 16 * 1024 * 1024:
                    raise ValueError('Unexpectedly large release archive')
                if hashlib.sha256(payload).hexdigest() != spec['sha256']:
                    raise ValueError('Downloaded archive does not match pinned checksum')
                archive.write_bytes(payload)
        import_release(game, archive)


if __name__ == '__main__':
    main()
