/* Runs the course checker (checker/bimcheck, the same Python code as the command line) in the browser.
   Python comes from Pyodide and IfcOpenShell from its official WebAssembly build. Files stay in the browser.
   Messages are handled one at a time. If anything fails, the page throws this worker away and starts a new one. */
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';
const IFCOPENSHELL = 'https://ifcopenshell.github.io/wasm-wheels/ifcopenshell-0.8.5-cp313-cp313-pyodide_2025_0_wasm32.whl';
const PYPDF = 'pypdf==7.0.0';

let py = null;
let run = null;          // the Python function _run(eid, paths)
let hasPdf = false;
let queue = Promise.resolve();

function say(msg) { postMessage({ type: 'status', msg }); }

async function load(base) {
  say('Loading the checker: Python, NumPy and IfcOpenShell (about 40 MB the first time, then cached by the browser)...');
  importScripts(PYODIDE + 'pyodide.js');
  py = await loadPyodide({ indexURL: PYODIDE });
  await py.loadPackage(['micropip', 'numpy']);
  say('Loading IfcOpenShell...');
  py.globals.set('IFC_WHEEL', IFCOPENSHELL);
  await py.runPythonAsync('import micropip\nawait micropip.install(IFC_WHEEL)');
  const files = await fetch(base + 'data/bimcheck.json').then(r => {
    if (!r.ok) throw new Error('could not read data/bimcheck.json');
    return r.json();
  });
  for (const [rel, text] of Object.entries(files)) {
    const path = '/checker/bimcheck/' + rel;
    py.FS.mkdirTree(path.slice(0, path.lastIndexOf('/')));
    py.FS.writeFile(path, text);
  }
  await py.runPythonAsync(`
import sys, json
sys.path.insert(0, '/checker')
from bimcheck.exercises import REGISTRY

KINDS = {'.ifc': 'an IFC model', '.svg': 'an SVG drawing', '.pdf': 'a PDF drawing', '.csv': 'a CSV schedule'}

def _run(eid, paths):
    paths = [p for p in paths]
    try:
        res = REGISTRY[eid]['fn'](*paths)
    except SystemExit as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        kinds = ', '.join(KINDS.get('.' + str(p).rsplit('.', 1)[-1].lower(), 'the right file') for p in paths if p)
        return json.dumps({'error': 'The checker could not read your file (' + type(e).__name__ + ': ' + str(e)[:300]
                           + '). Check that you gave ' + kinds + ' exported from your program.'})
    ok, n = res.score()
    return json.dumps({'title': res.title, 'ok': ok, 'n': n, 'passed': res.passed,
                       'items': [{'ok': i.ok, 'text': i.text, 'hint': i.hint} for i in res.items]})
`);
  run = py.globals.get('_run');
  say('');
}

async function handle(m) {
  if (!run) await load(m.base);
  if (m.type === 'warm') { postMessage({ type: 'ready', id: m.id }); return; }
  const dir = '/run/' + m.id;
  py.FS.mkdirTree(dir);
  const paths = [];
  try {
    m.files.forEach((f, i) => {
      if (!f) { paths.push(null); return; }
      const p = `${dir}/${i}_${f.name.replace(/[^A-Za-z0-9._-]/g, '_')}`;
      py.FS.writeFile(p, new Uint8Array(f.data));
      paths.push(p);
    });
    if (!hasPdf && m.files.some(f => f && /\.pdf$/i.test(f.name))) {
      say('Loading the PDF reader...');
      py.globals.set('PYPDF', PYPDF);
      await py.runPythonAsync('import micropip\nawait micropip.install(PYPDF)');
      hasPdf = true;
    }
    say('Checking...');
    const out = JSON.parse(run(m.eid, paths));
    postMessage({ type: 'result', id: m.id, result: out });
  } finally {
    for (const p of paths) { if (p) { try { py.FS.unlink(p); } catch (_) { /* already gone */ } } }
  }
}

onmessage = (ev) => {
  const m = ev.data;
  queue = queue.then(() => handle(m)).catch((e) => {
    postMessage({ type: 'error', id: m.id, fatal: true, msg: String((e && e.message) || e).slice(0, 500) });
  });
};
