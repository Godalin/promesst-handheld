#!/usr/bin/env python3
"""Exercise built executables, including menu controls and a second process reload."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(binary, game, save_dir, output, name, inputs, size='720x720'):
    env = os.environ.copy()
    env.update(PROMESST_ASSET_DIR=str(ROOT / 'assets' / game), PROMESST_SAVE_DIR=str(save_dir))
    report = output / (name + '.jsonl')
    command = [str(binary), '--headless', '--integer', '--size', size, '--frames', '180', '--report', str(report),
               '--screenshot', str(output / (name + '.bmp'))]
    if inputs:
        command += ['--input', inputs]
    subprocess.run(command, env=env, check=True, timeout=60)
    rows = [json.loads(line) for line in report.read_text().splitlines()]
    assert len(rows) == 180
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir', type=Path)
    args = parser.parse_args()
    output = args.build_dir.resolve() / 'smoke'
    output.mkdir(parents=True, exist_ok=True)
    for game in ['promesst', 'promesst2']:
        saves = output / ('save-' + game)
        if saves.exists():
            shutil.rmtree(saves)
        binary = args.build_dir.resolve() / game
        first = run(binary, game, saves, output, game,
                    '5:south,15:south,40:w,60:d,80:east,100:west')
        assert first[5]['mode'] == 1, 'South button must open menu from logo'
        assert first[15]['mode'] == 3, 'South button must confirm New Game'
        assert (first[-1]['x'], first[-1]['y']) != (first[0]['x'], first[0]['y'])
        save_file = saves / 'save.dat'
        assert save_file.read_bytes()[:8] == (b'PMSTHH01' if game == 'promesst' else b'PMSTHH02')
        assert not (saves / 'save.dat.tmp').exists()
        second = run(binary, game, saves, output, game + '-reload', None)
        for field in ['x', 'y', 'z', 'gems', 'wand', 'world', 'undo']:
            assert second[0][field] == first[-1][field], (game, field, second[0], first[-1])
        menu = run(binary, game, saves, output, game + '-menu', '5:south,15:south,100:menu')
        assert menu[-1]['mode'] == 1, 'Start must return to menu'
        run(binary, game, saves, output, game + '-catalog', '5:south,15:south', '640x480')
        print(game + ': actual startup, gameplay, controller action mapping, graceful save, reload and menu passed')


if __name__ == '__main__':
    main()
