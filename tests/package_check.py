#!/usr/bin/env python3
"""Check ZIPs and run launchers with isolated PortMaster mocks."""
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def launcher_check(game, script, fallback):
    with tempfile.TemporaryDirectory(prefix='promesst-launch-') as temp:
        base = Path(temp)
        ports = base / 'second card with spaces' / 'ports'
        folder = ports / game
        data = folder / ('data' if game == 'promesst' else 'data2')
        data.mkdir(parents=True)
        for name in ['sprites.png', 'title.png', 'sss_logo.png']:
            (data / name).touch()
        launcher = ports / ('Promesst.sh' if game == 'promesst' else 'Promesst 2.sh')
        launcher.write_text(script)
        subprocess.run(['bash', '-n', str(launcher)], check=True)
        binary = folder / (game + '.aarch64')
        binary.write_text('''#!/usr/bin/env bash
if [[ -f request-fallback && -z "${PROMESST_KEYBOARD_ONLY:-}" ]]; then exit 78; fi
printf '%s\n' "$PROMESST_ASSET_DIR" "$PROMESST_SAVE_DIR" "$PROMESST_CONFIG_DIR" "$SDL_GAMECONTROLLERCONFIG" "${PROMESST_KEYBOARD_ONLY:-}" > launch-record.txt
exit 0
''')
        binary.chmod(0o755)
        if fallback:
            (folder / 'request-fallback').touch()
        pm = base / 'xdg' / 'PortMaster'
        pm.mkdir(parents=True)
        mapper = base / 'mapper'
        mapper.write_text('#!/usr/bin/env bash\nexec sleep 60\n')
        mapper.chmod(0o755)
        (pm / 'control.txt').write_text(f'''CFW_NAME=TEST
DEVICE_ARCH=aarch64
directory=roms2
GPTOKEYB='{mapper}'
get_controls() {{ sdl_controllerconfig='test-mapping'; }}
pm_message() {{ echo "$*"; }}
pm_platform_helper() {{ :; }}
pm_finish() {{ echo finished > "$game_dir/finish-record.txt"; }}
''')
        env = os.environ.copy()
        env['XDG_DATA_HOME'] = str(base / 'xdg')
        env.pop('PROMESST_KEYBOARD_ONLY', None)
        subprocess.run(['bash', str(launcher)], env=env, check=True, timeout=10,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines = (folder / 'launch-record.txt').read_text().splitlines()
        assert lines[:4] == [str(folder), str(folder / 'saves'), str(folder / 'conf'), 'test-mapping']
        assert lines[4] == ('1' if fallback else '')
        assert (folder / 'finish-record.txt').exists()


def main():
    for game in ['promesst', 'promesst2']:
        path = ROOT / 'dist' / (game + '.aarch64.local-full.zip')
        with zipfile.ZipFile(path) as package:
            assert package.testzip() is None
            names = package.namelist()
            launcher = 'Promesst.sh' if game == 'promesst' else 'Promesst 2.sh'
            for name in [launcher, game + '/' + game + '.aarch64', game + '/INSTALL.txt', game + '/screenshot.png']:
                assert name in names, name
            assert not any('/saves/' in name or '/conf/' in name or name.endswith('.c') for name in names)
            metadata = json.loads((ROOT / 'staging/local-full/port' / game / 'port.json').read_text())
            assert metadata['items'] == [launcher, game]
            assert not metadata['attr']['rtr'] and metadata['attr']['exp']
            assert package.getinfo(launcher).external_attr >> 16 & 0o111
            assert package.getinfo(game + '/' + game + '.aarch64').external_attr >> 16 & 0o111
            assert all(name.split('/')[0] in {launcher, game} for name in names), 'Cross-game install collision'
            png = package.read(game + '/screenshot.png')
            assert struct.unpack_from('>II', png, 16) == (640, 480)
            binary = package.read(game + '/' + game + '.aarch64')
            assert struct.unpack_from('<H', binary, 18)[0] == 183
            script = package.read(launcher).decode()
            launcher_check(game, script, False)
            launcher_check(game, script, True)
        print(game + ': ZIP, permissions, 4:3 screenshot, paths with spaces and keyboard fallback passed')


if __name__ == '__main__':
    main()
