#!/usr/bin/env python3
"""Create separate ArkOS ZIPs. Full assets are an explicit local-build option."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from bmp_to_png import convert


def package(game, build, full):
    title = 'Promesst' if game == 'promesst' else 'Promesst 2'
    data_name = 'data' if game == 'promesst' else 'data2'
    binary = build / game
    elf = binary.read_bytes()
    if elf[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', elf, 18)[0] != 183:
        raise ValueError(f'{binary} is not a little-endian AArch64 ELF binary')
    mode = 'local-full' if full else 'assets-required'
    package_root = ROOT / 'staging' / mode / 'port' / game
    if package_root.exists():
        shutil.rmtree(package_root)
    game_dir = package_root / game
    game_dir.mkdir(parents=True)
    executable = game_dir / (game + '.aarch64')
    shutil.copy2(binary, executable)
    executable.chmod(0o755)
    launcher = (ROOT / 'packaging/portmaster/launch.sh.in').read_text()
    launcher = launcher.replace('@GAME@', game).replace('@DATA@', data_name)
    launch_name = title + '.sh'
    launch_path = package_root / launch_name
    launch_path.write_text(launcher)
    launch_path.chmod(0o755)
    shutil.copy2(ROOT / 'packaging/portmaster/controls.gptk', game_dir / 'controls.gptk')
    shutil.copytree(ROOT / 'licenses', game_dir / 'licenses', ignore=shutil.ignore_patterns('.gitkeep'))
    originals = ROOT / 'upstream' / game
    for readme in originals.glob('*.txt'):
        shutil.copy2(readme, game_dir / 'licenses' / readme.name)
    if full:
        shutil.copytree(ROOT / 'assets' / game / data_name, game_dir / data_name)
    instructions = f'''{title} — XF40H / ArkOS local build

Install: extract this ZIP into the ports directory used by your ArkOS system.
Keep {launch_name} beside the {game}/ folder. PortMaster must already be installed.
Open Ports and select {title}. This build needs aarch64 Linux and SDL2 >= 2.0.8.
Assets included: {"yes (personal local build)" if full else "no"}.
If absent: obtain the official game from https://silverspaceship.com/{game}/
and copy its {data_name}/ folder into ports/{game}/. Do not copy PC executables.

Controls (physical position, regardless of printed A/B labels):
D-pad / left stick: move. South: Z action / confirm menu.
East: X action. West: C action (Promesst 2).
R1: undo one room. Start: menu. North: toggle integer / fit scaling.
Select + Start: save and exit with native controls.
Keyboard: arrows/WASD, Z/X/C, Backspace, Escape, Enter; F2 toggles scaling.
The optional PortMaster keyboard fallback uses its system exit shortcut.

Progress: {game}/saves/save.dat. Settings: {game}/conf/.
Updating: replace program and assets; keep saves/ and conf/.
Saves use this port's versioned 64-bit layout; PC or 32-bit saves are not imported.
If launch fails, inspect {game}/log.txt. All paths support spaces and second-card ROMs.
Device validation: ARM64 container checks passed; XF40H hardware is not yet tested.
This is a local personal build, not an authorized public redistribution of the game.
Credits: Sean Barrett (game), David Gow (Linux port); original credits are preserved.
'''
    (game_dir / 'INSTALL.txt').write_text(instructions)
    (package_root / 'README.md').write_text(instructions)
    (game_dir / 'BUILD.json').write_text(json.dumps({
        'game': game, 'target': 'aarch64', 'device': 'XF40H', 'hardware_tested': False,
        'assets_included': full, 'upstream': json.loads((ROOT / 'scripts/upstream.lock.json').read_text())[game],
        'binary_sha256': hashlib.sha256(elf).hexdigest(),
        'glibc_build_environment': 'Ubuntu 18.04 / glibc 2.27', 'sdl_minimum': '2.0.8'
    }, indent=2) + '\n')
    (package_root / 'port.json').write_text(json.dumps({
        'version': 4, 'name': game + '.zip', 'items': [launch_name, game], 'items_opt': [],
        'attr': {'title': title, 'porter': ['Local build'], 'desc': 'Sean Barrett puzzle game, handheld adaptation.',
                 'desc_md': None, 'inst': instructions, 'inst_md': None, 'genres': ['puzzle'], 'image': None,
                 'rtr': False, 'exp': True, 'runtime': [], 'store': [],
                 'availability': 'full' if full else 'files', 'reqs': [], 'arch': ['aarch64'], 'min_glibc': '2.27'}
    }, indent=2) + '\n')
    # Capture gameplay at 4:3 for the PortMaster submission layout. It is local
    # derived imagery, kept alongside generated artifacts, not in Git.
    screenshot = build / 'smoke' / (game + '-catalog.bmp')
    if screenshot.exists():
        convert(screenshot, package_root / 'screenshot.png')
        shutil.copy2(package_root / 'screenshot.png', game_dir / 'screenshot.png')
    info = ET.Element('gameList')
    entry = ET.SubElement(info, 'game')
    for tag, value in [('path', './' + launch_name), ('name', title), ('desc', 'A puzzle game by Sean Barrett.'),
                       ('developer', 'Sean Barrett'), ('genre', 'Puzzle'), ('image', './' + game + '/screenshot.png')]:
        ET.SubElement(entry, tag).text = value
    ET.ElementTree(info).write(package_root / 'gameinfo.xml', encoding='utf-8', xml_declaration=True)
    output = ROOT / 'dist' / f'{game}.aarch64.{mode}.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_root.rglob('*')):
            relative = path.relative_to(package_root)
            if path.is_file() and path.name != '.gitkeep' and relative.parts[0] in {launch_name, game}:
                archive.write(path, relative)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + '.sha256').write_text(digest + '  ' + output.name + '\n')
    print(f'{output}: {output.stat().st_size} bytes, sha256={digest}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/aarch64')
    parser.add_argument('--local-full', action='store_true', help='Include original assets for a personal local build')
    args = parser.parse_args()
    for game in ['promesst', 'promesst2']:
        package(game, args.build_dir.resolve(), args.local_full)


if __name__ == '__main__':
    main()
