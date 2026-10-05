#!/usr/bin/env python3
"""Apply small, checked adaptations to locally obtained official source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'scripts/upstream.lock.json').read_text())

LOAD = r'''static int hh_valid_state(const player_state *s)
{
   return s->player_x < NUM_X*SIZE_X && s->player_y < NUM_Y*SIZE_Y && s->player_z < 2;
}

static void load_game(void)
{
   FILE *f = fopen(get_savegame_path(), "rb");
   gamestate current, saved_checkpoint;
   roomsave_big *head = NULL, **tail = &head;
   char magic[8];
   if (!f) return;
   if (fread(magic, 1, 8, f) != 8 || memcmp(magic, HH_SAVE_MAGIC, 8) ||
       fread(&current, sizeof(current), 1, f) != 1 ||
       fread(&saved_checkpoint, sizeof(saved_checkpoint), 1, f) != 1 ||
       !hh_valid_state(&current.state) || !hh_valid_state(&saved_checkpoint.state)) goto invalid;
   for (int count = 0;; count++) {
      roomsave_big disk;
      size_t bytes = fread(&disk, 1, sizeof(disk), f);
      if (!bytes && feof(f)) break;
      if (bytes != sizeof(disk) || count >= 100000 || disk.room_x >= NUM_X ||
          disk.room_y >= NUM_Y || disk.room_z >= 2 || !hh_valid_state(&disk.state)) goto invalid;
      for (int y = 0; y < SIZE_Y; y++) if (disk.doors[y] & ~((1 << SIZE_X) - 1)) goto invalid;
      roomsave_big *node = malloc(sizeof(*node));
      if (!node) goto invalid;
      *node = disk; node->next = NULL; *tail = node; tail = &node->next;
   }
   fclose(f);
   loaded_game = current; checkpoint = saved_checkpoint;
   flush_undo(); undo_chain = head;
   restore_map(&loaded_game); game_started = 1;
   return;
invalid:
   fclose(f);
   while (head) { roomsave_big *next = head->next; free(head); head = next; }
   fprintf(stderr, "Save rejected (wrong version, truncated or invalid): %s\n", get_savegame_path());
}
'''

SAVE = r'''static void save_game(void)
{
   if (!game_started) return;
   FILE *f = hh_save_open();
   if (!f) return;
   save_map(&loaded_game);
   fwrite(HH_SAVE_MAGIC, 1, 8, f);
   fwrite(&loaded_game, sizeof(loaded_game), 1, f);
   fwrite(&checkpoint, sizeof(checkpoint), 1, f);
   for (roomsave_big *r = undo_chain; r; r = r->next) {
      roomsave_big disk = *r;
      disk.next = NULL;
      fwrite(&disk, sizeof(disk), 1, f);
   }
   hh_save_commit(f);
}
'''

REPORT = r'''
void hh_game_cleanup(void)
{
   flush_undo();
   free(colordata); colordata = NULL;
}

/* Diagnostic state output; invoked only when --report is supplied. */
void hh_report(FILE *f, int frame)
{
   uint32_t hash = 2166136261u;
   const unsigned char *maps[] = {(const unsigned char *)tilemap, (const unsigned char *)objmap};
   size_t sizes[] = {sizeof(tilemap), sizeof(objmap)};
   for (int n = 0; n < 2; n++) for (size_t i = 0; i < sizes[n]; i++) hash = (hash ^ maps[n][i]) * 16777619u;
   int depth = 0;
   for (roomsave_big *r = undo_chain; r; r = r->next) depth++;
   fprintf(f, "{\"frame\":%d,\"mode\":%d,\"x\":%d,\"y\":%d,\"z\":%d,\"gems\":%d,\"wand\":%d,\"undo\":%d,\"world\":%u}\n",
       frame, main_mode, px, py, pz, state.num_gems, state.has_wand, depth, hash);
}
'''


def replace_function(source, name, replacement, count=1):
    expression = r'static (?:char \*|void )' + re.escape(name) + r'\(void\)\n\{.*?\n\}'
    result, found = re.subn(expression, lambda _: replacement.rstrip(), source, flags=re.S)
    if found != count:
        raise ValueError(f'Unexpected source layout for {name}: {found} matches')
    return result


def prepare(game, output, baseline=False):
    spec = LOCK[game]
    original = ROOT / 'upstream' / game / 'source'
    if not (original / 'main.c').exists():
        raise SystemExit('Obtain original sources first: python3 scripts/fetch_upstream.py')
    output.mkdir(parents=True, exist_ok=True)
    source = (original / 'main.c').read_text()
    for filename, digest in spec.get('source_sha256', {}).items():
        if hashlib.sha256((original / filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f'{game}: original {filename} changed; reimport the pinned release')
    for old in ['#include "stb_sdl2graph.h"', '#include "stb_gl.h"']:
        if source.count(old) != 1:
            raise ValueError('Unexpected include layout: ' + old)
    source = source.replace('#include "stb_sdl2graph.h"', '#include "handheld.h"')
    source = source.replace('#include "stb_gl.h"', '/* Rectangles are rendered by the shared SDL2 backend. */')
    source = re.sub(r'^#pragma warning.*\n', '', source, flags=re.M)
    source = replace_function(source, 'get_savegame_path',
                              'static char *get_savegame_path(void)\n{\n   return hh_save_path();\n}',
                              2 if game == 'promesst2' else 1)
    if not baseline:
        source = replace_function(source, 'load_game', LOAD)
        source = replace_function(source, 'save_game', SAVE)
    # Request RGBA explicitly: the original indexes its atlas using four bytes per pixel.
    source = source.replace('&w,&h,0,0)', '&w,&h,0,4)')
    source = source.replace('   tex = stbgl_TexImage2D',
                            '   if (!colordata) hh_fail("Sprite atlas load failed");\n   tex = stbgl_TexImage2D')
    # Original one has inactive directions (-1) in this loop; do not index powers[-1].
    unsafe = 'draw_sprite(x+1,y+1, 4+(d&1), 5, &powers[light_for_dir[my][mx][d]], flicker * 0.25);'
    source = source.replace(unsafe, 'if (light_for_dir[my][mx][d] >= 0) ' + unsafe)
    # Rover animation uses zero offsets during the stationary part of its cycle.
    source = source.replace('int ds,sx,sy, t;', 'int ds,sx=0,sy=0, t;')
    source = source.replace('int ds,dt=0,sx,sy, t;', 'int ds,dt=0,sx=0,sy=0, t;')
    labels = {'ESC FOR MENU': 'START MENU', 'BACKSPACE TO': 'R1 TO',
              'Z TO FIRE': 'SOUTH FIRE', 'X TO GET/PUT': 'EAST GET/PUT',
              'C TO GET/PUT': 'WEST GET/PUT'}
    for old, new in labels.items():
        source = source.replace(old, new)
    source += REPORT
    (output / 'main.c').write_text(source)
    decoder = (original / 'stb_image.c').read_text()
    # Preserve the decoder's bitstream behavior without signed-shift UB.
    decoder = decoder.replace('zget8(z) << z->num_bits', '(unsigned int)zget8(z) << z->num_bits')
    (output / 'stb_image.c').write_text(decoder)
    print(f'{game}: generated platform-adapted source in {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/generated')
    parser.add_argument('--baseline', action='store_true', help='Keep original persistence for reference comparison')
    args = parser.parse_args()
    for game in LOCK:
        prepare(game, args.output / game, args.baseline)


if __name__ == '__main__':
    main()
