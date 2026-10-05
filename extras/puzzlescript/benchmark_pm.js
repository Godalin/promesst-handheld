#!/usr/bin/env node
'use strict';
// Measure rules/rendering in the pinned PM engine, without display/audio I/O.
// These timings are CPU measurements, not end-to-end controller latency.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const Module = require('module');
const assert = require('assert');
const os = require('os');
const root = path.resolve(__dirname, '../..');
const engine = path.join(root, 'build/puzzlescript/pm-engine');
const source = path.join(root, 'upstream/puzzlescript/games/skipping_stones.pz');
const ev = code => vm.runInThisContext(code);

process.env.SDL2FB = '1';
process.env.DISPLAY_WIDTH = '720';
process.env.DISPLAY_HEIGHT = '720';
process.argv = [process.execPath, path.join(engine, 'main.js'), source];
let program = fs.readFileSync(path.join(engine, 'main.js'), 'utf8');
const marker = '// main loop\n';
assert(program.includes(marker), 'Pinned runtime structure changed');
program = program.slice(0, program.indexOf(marker));
// Do not open input devices or use a player's persisted progress.
const inputStart = program.indexOf('// open input devices\n');
const inputEnd = program.indexOf('// input reading utility\n');
assert(inputStart >= 0 && inputEnd > inputStart, 'Pinned input structure changed');
program = program.slice(0, inputStart) + 'const inputFds = [];\n' + program.slice(inputEnd);
program = program.replace("const savePath = runtimeDir + '../conf/saves.json';",
  'const savePath = ' + JSON.stringify(path.join(os.tmpdir(), 'puzzlescript-benchmark-' + process.pid + '.json')) + ';');
program = program.replace('levelString = __gameSource;\ncompile(',
  'playSound = function() {};\nlevelString = __gameSource;\ncompile(');
const runtime = new Module(path.join(engine, 'main.js'), module);
runtime.filename = path.join(engine, 'main.js');
runtime.paths = Module._nodeModulePaths(engine);
runtime._compile(program, runtime.filename);
assert.strictEqual(ev('errorCount'), 0, 'Original source must compile');
const first = ev('state.levels.findIndex(item => item.message === undefined)');
assert(first >= 0);
const reset = () => ev('titleScreen=false; textMode=false; loadLevelFromState(state,' + first + ',"benchmark"); canvasResize();');
reset();
const dimensions = ev('[level.width, level.height]');
const tick = ev('(function() { processInput(-1); })');
const move = ev('(function(direction) { processInput(direction, true); redraw(); })');
const redrawBoard = ev('(function() { redraw(); })');

function measure(operation, count) {
  const times = [];
  for (let index = 0; index < count; index++) {
    reset(); // Loading/rendering the initial board is outside the timed region.
    const start = process.hrtime.bigint();
    operation(index % 4);
    times.push(Number(process.hrtime.bigint() - start) / 1e6);
  }
  times.sort((a, b) => a - b);
  return {
    samples: count,
    median_ms: +times[Math.floor(count / 2)].toFixed(3),
    p95_ms: +times[Math.ceil(count * 0.95) - 1].toFixed(3),
    max_ms: +times[count - 1].toFixed(3)
  };
}
// Warm the generated rule functions before collecting steady-state samples.
for (let index = 0; index < 40; index++) {
  reset();
  tick();
  move(index % 4);
}
const result = {
  game: 'Skipping Stones to Lonely Homes',
  node: process.version,
  platform: process.platform + '/' + process.arch,
  cpu: os.cpus()[0].model,
  map: dimensions,
  viewport: [19, 14],
  screen: [720, 720],
  idle_rules: measure(tick, 80),
  direction_rules_and_redraw: measure(move, 80),
  redraw_only: measure(redrawBoard, 80),
  limitation: 'Initial board only; excludes input polling, framebuffer output, audio, OS scheduling and later game states. Development-host timings do not predict XF40H latency.'
};
console.log(JSON.stringify(result, null, 2));
