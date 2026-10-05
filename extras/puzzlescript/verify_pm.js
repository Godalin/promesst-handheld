#!/usr/bin/env node
'use strict';
// Validate unchanged game data with the pinned official PM engine. Hardware I/O
// is disabled; rules, compiler, input handlers, renderer and storage stay intact.
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const {spawnSync} = require('child_process');
const Module = require('module');
const root = path.resolve(__dirname, '../..');
const lock = JSON.parse(fs.readFileSync(path.join(__dirname, 'upstream.lock.json')));
const engine = path.join(root, 'build/puzzlescript/pm-engine');
const output = path.join(root, 'build/puzzlescript/validation');

if (process.argv[2] !== '--child') {
  fs.mkdirSync(output, {recursive: true});
  for (const game of lock.games) {
    const result = spawnSync(process.execPath, [__filename, '--child', game.id], {
      encoding: 'utf8', timeout: 120000,
      env: {...process.env, SDL2FB: '1', DISPLAY_WIDTH: '720', DISPLAY_HEIGHT: '720'}
    });
    if (result.status !== 0) {
      process.stderr.write(result.stderr || String(result.error));
      process.exit(1);
    }
    process.stdout.write(result.stdout);
  }
  process.exit(0);
}

const game = lock.games.find(item => item.id === process.argv[3]);
assert(game, 'Unknown game');
const resume = process.argv[4] === '--resume';
const work = path.join(output, game.id);
if (!resume) fs.rmSync(work, {recursive: true, force: true});
fs.mkdirSync(path.join(work, 'conf'), {recursive: true});
const source = path.join(root, 'upstream/puzzlescript/games', game.id + '.pz');
process.argv = [process.execPath, path.join(engine, 'main.js'), source];

let program = fs.readFileSync(path.join(engine, 'main.js'), 'utf8');
const marker = '// main loop\n';
assert(program.includes(marker), 'Pinned runtime structure changed');
program = program.slice(0, program.indexOf(marker));
// Keep each test's save separate from downloaded engine files.
program = program.replace("const savePath = runtimeDir + '../conf/saves.json';",
  'const savePath = ' + JSON.stringify(path.join(work, 'conf/saves.json')) + ';');
// Silence audio during host validation; audio/hardware are outside this check.
program = program.replace('levelString = __gameSource;\ncompile(',
  'playSound = function() {};\nlevelString = __gameSource;\ncompile(');
program += '\nrequire(' + JSON.stringify(__filename) + ').verify({processKey, flushSaves, framebuffer: __framebuf});\n';

exports.verify = function(runtime) {
  const vm = require('vm');
  const ev = code => vm.runInThisContext(code);
  const snapshot = () => Array.from(ev('level.objects'));
  assert.strictEqual(ev('errorCount'), 0, 'Original game must compile without errors');
  assert.strictEqual(ev('state.metadata.title'), game.title);
  if (resume) {
    const expected = JSON.parse(fs.readFileSync(path.join(work, 'expected.json')));
    assert(ev('titleScreen && curlevelTarget !== null'), 'Saved fixture missing from continue menu');
    ev('nextLevel(); canvasResize();');
    assert.strictEqual(ev('curlevel'), expected.level);
    assert.deepStrictEqual(snapshot(), expected.board, 'New process failed to restore checkpoint fixture');
    process.stdout.write(game.title + ': checkpoint fixture persisted and restored in a new process\n');
    return;
  }

  // All original boards must load, execute start rules and render without edits.
  const boardIndices = ev('state.levels.map((item,index)=>item.message === undefined ? index : -1).filter(index=>index>=0)');
  assert(boardIndices.length > 0);
  for (const index of boardIndices) {
    ev('titleScreen=false; textMode=false; loadLevelFromState(state,' + index + ',"handheld-trial"); canvasResize();');
    assert(ev('level.width > 0 && level.height > 0 && level.objects.length === level.width * level.height * STRIDE_OBJ'));
    assert(runtime.framebuffer.some(byte => byte !== 0), 'Empty rendering');
  }

  const first = boardIndices[0];
  function reset() {
    ev('titleScreen=false; textMode=false; loadLevelFromState(state,' + first + ',"handheld-trial"); canvasResize();');
  }
  let moves = 0;
  for (const direction of [0, 1, 2, 3, 4]) {
    reset();
    const before = snapshot();
    ev('processInput(' + direction + ',true);');
    if (JSON.stringify(snapshot()) !== JSON.stringify(before)) {
      moves++;
      ev('DoUndo(true,true);');
      assert.deepStrictEqual(snapshot(), before, 'Undo must restore original board');
    }
  }
  assert(moves > 0, 'No playable move/action on the first board');

  reset();
  const initial = snapshot();
  for (const code of [106, 108, 105, 103, 45]) runtime.processKey(code);
  ev('DoRestart(true);');
  // Restart executes start rules; some games have automatic visual transitions.
  assert.strictEqual(snapshot().length, initial.length);
  assert(ev('getPlayerPositions().length > 0'), 'Restart lost player');

  // Exercise the PM time/update path, including Skipping Stones' realtime rules.
  reset();
  for (let frame = 0; frame < 300; frame++) {
    if (frame % 30 === 0) runtime.processKey([106, 108, 105, 103, 45][Math.floor(frame / 30) % 5]);
    ev('deltatime=33; update();');
  }

  // Serialize an actual board via the engine format and restore it unchanged.
  reset();
  ev('globalThis.__trialSave = level4Serialization();');
  const saved = snapshot();
  ev('processInput(3,true); loadLevelFromStateTarget(state,' + first + ',globalThis.__trialSave,"handheld-trial");');
  assert.deepStrictEqual(snapshot(), saved, 'Checkpoint restore changed board');
  ev('canvasResize();');

  // Save screenshot from the actual PM framebuffer (RGBA) as a top-down BMP.
  const pixels = Buffer.from(runtime.framebuffer);
  for (let i = 0; i < pixels.length; i += 4) {
    const red = pixels[i]; pixels[i] = pixels[i+2]; pixels[i+2] = red;
  }
  const header = Buffer.alloc(54);
  header.write('BM'); header.writeUInt32LE(54 + pixels.length, 2);
  header.writeUInt32LE(54, 10); header.writeUInt32LE(40, 14);
  header.writeInt32LE(720, 18); header.writeInt32LE(-720, 22);
  header.writeUInt16LE(1, 26); header.writeUInt16LE(32, 28);
  header.writeUInt32LE(pixels.length, 34);
  fs.writeFileSync(path.join(work, 'game.bmp'), Buffer.concat([header, pixels]));
  // This deliberately establishes a checkpoint fixture, not a checkpoint reached
  // by solving a puzzle. It verifies the unmodified runtime's disk/continue path.
  ev('storage_set(document.URL,curlevel); storage_set(document.URL+"_checkpoint",JSON.stringify(level4Serialization()));');
  runtime.flushSaves();
  fs.writeFileSync(path.join(work, 'expected.json'), JSON.stringify({level: ev('curlevel'), board: snapshot()}));
  const reload = spawnSync(process.execPath, [__filename, '--child', game.id, '--resume'], {
    encoding: 'utf8', timeout: 120000, env: process.env
  });
  assert.strictEqual(reload.status, 0, reload.stderr || String(reload.error));
  process.stdout.write(reload.stdout);
  process.stdout.write(game.title + ': ' + boardIndices.length + ' boards loaded/rendered; movement, action handler, undo, restart and 300 updates passed\n');
};

const runtimeModule = new Module(path.join(engine, 'main.js'), module);
runtimeModule.filename = path.join(engine, 'main.js');
runtimeModule.paths = Module._nodeModulePaths(engine);
runtimeModule._compile(program, runtimeModule.filename);
