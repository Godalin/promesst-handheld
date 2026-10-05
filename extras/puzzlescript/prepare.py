#!/usr/bin/env python3
"""Fetch pinned original games and build private ArkOS / PuzzleScript PM packs."""
import argparse
import hashlib
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = json.loads(Path(__file__).with_name('upstream.lock.json').read_text())
MAX_BYTES = 2 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url, expected, cache, offline=False):
    if cache.is_file():
        data = cache.read_bytes()
    elif offline:
        raise ValueError('Missing offline file: ' + str(cache))
    else:
        request = urllib.request.Request(url, headers={'User-Agent': 'handheld-puzzlescript/1'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('Download too large: ' + url)
    if sha256(data) != expected:
        raise ValueError('SHA-256 mismatch: ' + str(cache))
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        temp = cache.with_name(cache.name + '.tmp')
        temp.write_bytes(data)
        temp.replace(cache)
    return data


def extract_source(data, kind):
    if kind == 'standalone_html':
        # Parse a string literal, never execute the downloaded JavaScript.
        match = re.search(r'var sourceCode\s*=\s*("(?:[^"\\]|\\.)*")\s*;', data.decode('utf-8'))
        if not match:
            raise ValueError('Original standalone sourceCode literal not found')
        return json.loads(match.group(1)).replace('\\n', '\n').encode('utf-8')
    return data


def build_pack(mode, games, manifest):
    dest = ROOT / 'dist' / ('sinking-star-predecessors.' + mode + '.local.zip')
    dest.parent.mkdir(exist_ok=True)
    if mode == 'arkos':
        install = '''ArkOS PuzzleScript local trial pack

Copy the puzzlescript/ folder to your active ROM card's ROM root (EASYROMS).
Files should end up in /roms/puzzlescript/ or /roms2/puzzlescript/.
Refresh the game list / restart EmulationStation, then launch PuzzleScript.
Requires the lr-puzzlescript core provided by supported ArkOS firmware.
XF40H firmware variants may differ; this pack does not modify firmware.

Use RetroArch Quick Menu > Save State before exiting. Load State to resume.
Automatic progress saving is not guaranteed by the core's default settings.
RetroPad: D-pad movement, A action, Y undo, Start restart, L title screen.
Bindings can be reviewed in RetroArch Quick Menu > Controls.

These are original games, not native SDL2 rewrites. No emulator is bundled.
Source download hashes are in SOURCES.json. Original redistribution
permission has not been established: keep this generated pack for local use.
See extras/puzzlescript/README.md in the adaptation repository.
'''
    else:
        install = '''PuzzleScript PM local addon pack

Install "PuzzleScript PM" through PortMaster first.
Copy puzzlescriptpm/ into your active ports/ directory, merging folders.
Launch the existing PuzzleScript PM entry and select one of the five games.
This is an addon: it does not include the engine or its launch script.
Files use a sinkingstar_ prefix so existing games and saves are preserved.

PortMaster upstream controls: D-pad movement, X action, B undo,
R1 restart, Select quit. Firmware mappings may differ.
The engine saves completed-level progress and checkpoints, not every move.
Skipping Stones uses checkpoints; Mirror Isles / Heroes use level progress.
For a full mid-level save, use the ArkOS package and RetroArch Save State.

Source download hashes are in SOURCES.json. Original redistribution
permission has not been established: keep this generated pack for local use.
See extras/puzzlescript/README.md in the adaptation repository.
'''
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr('INSTALL.txt', install)
        package.writestr('SOURCES.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        for game, source in games:
            if mode == 'arkos':
                name = 'puzzlescript/' + game['rom_name'] + '.pz'
            else:
                name = 'puzzlescriptpm/games/sinkingstar_' + game['id'] + '.txt'
            package.writestr(name, source)
    # Verify the actual ZIP contents, including hashes and expected game count.
    with zipfile.ZipFile(dest) as package:
        if package.testzip() is not None or len(package.namelist()) != len(games) + 2:
            raise ValueError('Invalid ZIP: ' + str(dest))
        for game, source in games:
            suffix = game['rom_name'] + '.pz' if mode == 'arkos' else 'sinkingstar_' + game['id'] + '.txt'
            names = [name for name in package.namelist() if name.endswith('/' + suffix)]
            if len(names) != 1 or sha256(package.read(names[0])) != game['source_sha256']:
                raise ValueError('Pack source differs from original: ' + game['id'])
    digest = sha256(dest.read_bytes())
    dest.with_name(dest.name + '.sha256').write_text(digest + '  ' + dest.name + '\n')
    print(str(dest) + ': ' + str(dest.stat().st_size) + ' bytes; ZIP and all five source hashes verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', type=Path, help='Offline files with the names in upstream.lock.json')
    args = parser.parse_args()
    cache = args.archive_dir or ROOT / 'downloads' / 'puzzlescript'
    sources = ROOT / 'upstream' / 'puzzlescript' / 'games'
    sources.mkdir(parents=True, exist_ok=True)
    games = []
    for game in LOCK['games']:
        data = fetch(game['url'], game['download_sha256'], cache / game['archive_name'], bool(args.archive_dir))
        source = extract_source(data, game['format'])
        if sha256(source) != game['source_sha256']:
            raise ValueError('Extracted source hash mismatch: ' + game['id'])
        text = source.decode('utf-8')
        if not re.search(r'^title\s+' + re.escape(game['title']) + r'\s*$', text, re.M):
            raise ValueError('Unexpected title: ' + game['id'])
        (sources / (game['id'] + '.pz')).write_bytes(source)
        games.append((game, source))
        print(game['title'] + ': original source verified')
    manifest = {'games': LOCK['games'], 'original_rules_modified': False, 'hardware_tested': False}
    for mode in ('arkos', 'portmaster-addon'):
        build_pack(mode, games, manifest)


if __name__ == '__main__':
    main()
