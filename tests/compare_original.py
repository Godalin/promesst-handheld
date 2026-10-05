#!/usr/bin/env python3
"""Compare complete diagnostic traces against original rules and persistence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('build_dir', type=Path)
    args = parser.parse_args()
    build = args.build_dir.resolve()
    output = build / 'original-comparison'
    output.mkdir(parents=True, exist_ok=True)
    # Fixed navigation and action sequence, without enabling debug/cheat paths.
    actions = ['w', 'w', 'a', 's', 'd', 'd', 'x', 'z', 'c', 'undo', 's', 'a', 'w', 'd'] * 4
    script = '5:south,15:south,' + ','.join(f'{40 + n * 15}:{key}' for n, key in enumerate(actions))
    for game in ['promesst', 'promesst2']:
        traces = []
        for kind, suffix in [('adapted', ''), ('original', '_reference')]:
            saves = output / (game + '-' + kind)
            if saves.exists():
                shutil.rmtree(saves)
            env = os.environ.copy()
            env.update(PROMESST_ASSET_DIR=str(ROOT / 'assets' / game), PROMESST_SAVE_DIR=str(saves))
            trace = output / (game + '-' + kind + '.jsonl')
            subprocess.run([str(build / (game + suffix)), '--headless', '--frames', '1000',
                            '--input', script, '--report', str(trace)], env=env, check=True, timeout=60)
            traces.append([json.loads(line) for line in trace.read_text().splitlines()])
        assert traces[0] == traces[1], game + ': original and adapted states differ'
        print(game + ': 1,000-frame original/adapted traces identical (movement, actions, room undo)')


if __name__ == '__main__':
    main()
