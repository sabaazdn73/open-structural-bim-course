/* Runs the course checker (checker/bimcheck, the same Python code as the command line) in the browser.
   Python comes from Pyodide and IfcOpenShell from its official WebAssembly build. Files stay in the browser. */
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';
const IFCOPENSHELL = 'https://ifcopenshell.github.io/wasm-wheels/ifcopenshell-0.8.5-cp313-cp313-pyodide_2025_0_wasm32.whl';

let py = null;
let loading = null;
let ready = false;
let hasPdf = false;

function say(msg) { postMessage({ type: 'status', msg }); }

async function load(base) {
  say('Downloading Python (about 30 MB the first time, then it is cached)...');
  importScripts(PYODIDE + 'pyodide.js');
  py = await loadPyodide({ indexURL: PYODIDE });
  say('Loading NumPy...');
  await py.loadPackage(['micropip', 'numpy']);
  say('Loading IfcOpenShell...');
  py.globals.set('IFC_WHEEL', IFCOPENSHELL);
  await py.runPythonAsync('import micropip\nawait micropip.install(IFC_WHEEL)');
  say('Loading the checker...');
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

def _run(eid, paths):
    try:
        res = REGISTRY[eid]['fn'](*paths)
    except SystemExit as e:
        return json.dumps({'error': str(e)})
    except Exception as e:
        return json.dumps({'error': 'The checker could not read this file (' + type(e).__name__ + ': ' + str(e)[:300] + '). Check that you exported an IFC file.'})
    ok, n = res.score()
    return json.dumps({'title': res.title, 'ok': ok, 'n': n, 'passed': res.passed,
                       'items': [{'ok': i.ok, 'text': i.text, 'hint': i.hint} for i in res.items]})
`);
  ready = true;
  say('');
}

onmessage = async (ev) => {
  const m = ev.data;
  try {
    if (!loading) loading = load(m.base);
    await loading;
    if (m.type === 'warm') { postMessage({ type: 'ready' }); return; }
    const dir = '/run/' + m.id;
    py.FS.mkdirTree(dir);
    const paths = [];
    m.files.forEach((f, i) => {
      const safe = f.name.replace(/[^A-Za-z0-9._-]/g, '_');
      const p = `${dir}/${i}_${safe}`;
      py.FS.writeFile(p, new Uint8Array(f.data));
      paths.push(p);
    });
    if (!hasPdf && m.files.some(f => /\.pdf$/i.test(f.name))) {
      say('Loading the PDF reader...');
      await py.runPythonAsync("import micropip\nawait micropip.install('pypdf')");
      hasPdf = true;
    }
    say('Checking...');
    py.globals.set('EID', m.eid);
    py.globals.set('PATHS', py.toPy(paths));
    const out = JSON.parse(await py.runPythonAsync('_run(EID, list(PATHS))'));
    for (const p of paths) { try { py.FS.unlink(p); } catch (_) { /* already gone */ } }
    say('');
    postMessage({ type: 'result', id: m.id, result: out });
  } catch (e) {
    if (!ready) loading = null;
    postMessage({ type: 'error', id: m.id, msg: String(e && e.message || e).slice(0, 500) });
  }
};
