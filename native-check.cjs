// Validação independente: não importa nem inicializa o aplicativo privado.
const assert = require('node:assert/strict');
const path = require('node:path');
const { createRequire } = require('node:module');
const load = createRequire(path.join(process.cwd(), 'package.json'));
assert.equal(process.versions.electron, '33.4.11');
const Database = load('better-sqlite3');
const database = new Database(':memory:');
assert.equal(database.prepare('select 40 + 2 as result').get().result, 42);
database.close();
load('keytar'); // Carrega o módulo; não lê nem grava segredos.
const pty = load('node-pty').spawn('/usr/bin/printf', ['PTY_OK'], {
  name: 'xterm', cols: 80, rows: 24, cwd: process.cwd(), env: process.env,
});
let output = '';
const timeout = setTimeout(() => { pty.kill(); process.exit(1); }, 10000);
pty.onData(data => { output += data; });
pty.onExit(({ exitCode }) => {
  clearTimeout(timeout);
  assert.equal(exitCode, 0);
  assert.match(output, /PTY_OK/);
  console.log(JSON.stringify({electron: process.versions.electron,
    node: process.version, abi: process.versions.modules,
    sqlite: 'OK', keytar_load: 'OK', pty: 'PTY_OK'}));
});
