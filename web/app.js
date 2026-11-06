/* BIM practice panel: lessons, brief and an in-browser checker for the Open Structural BIM Course. */
(function () {
  'use strict';

  const BASE = new URL('./', location.href.split('#')[0]).href;
  const $ = (sel, el) => (el || document).querySelector(sel);
  let C = null;              // course.json
  let worker = null;
  let workerReady = false;
  let runId = 0;
  const pending = {};
  const chosen = {};         // eid -> [File|null per input]

  // ------------------------------------------------------------ storage (per viewer, optional)
  const store = {
    get(k, d) { try { const v = localStorage.getItem('osbc.' + k); return v === null ? d : JSON.parse(v); } catch (_) { return d; } },
    set(k, v) { try { localStorage.setItem('osbc.' + k, JSON.stringify(v)); } catch (_) { /* private mode */ } },
  };
  const done = new Set(store.get('done', []));
  let tool = store.get('tool', 'freecad');

  // ------------------------------------------------------------ helpers
  function el(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'html') e.innerHTML = v;            // only for course.json, which this repository generates
      else if (k === 'text') e.textContent = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? '' : v);
    }
    for (const k of kids.flat()) if (k !== null && k !== undefined && k !== false) e.append(k);
    return e;
  }
  const ids = () => C.sections.flatMap(s => s.exercises);
  const sectionOf = eid => C.sections.find(s => s.id === eid.split('.')[0]);

  // ------------------------------------------------------------ theme
  function applyTheme(t) {
    if (t) document.documentElement.setAttribute('data-theme', t);
    else document.documentElement.removeAttribute('data-theme');
  }
  applyTheme(store.get('theme', null));
  $('#theme').addEventListener('click', () => {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark' ||
      (!document.documentElement.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
    const t = dark ? 'light' : 'dark';
    applyTheme(t); store.set('theme', t);
  });

  if (/(^|\.)tnega\.app$/.test(location.hostname)) {
    $('#host').append(el('a', { href: '/', text: 'Tnega' }), ' · ');
  }
  $('#menu').addEventListener('click', () => {
    const open = $('#toc').classList.toggle('open');
    $('#menu').setAttribute('aria-expanded', String(open));
  });

  // ------------------------------------------------------------ table of contents
  function renderToc(current) {
    const toc = $('#toc');
    toc.textContent = '';
    for (const s of C.sections) {
      toc.append(el('h2', { text: `${s.id}. ${s.title.split(':')[0]}` }));
      toc.append(el('ol', null, s.exercises.map(eid => el('li', null,
        el('a', { href: `#/ex/${eid}`, 'aria-current': eid === current ? 'page' : null },
          el('span', { class: 'n', text: eid }),
          el('span', { text: C.exercises[eid].title }),
          el('span', { class: 'ok', text: done.has(eid) ? '✓' : '', 'aria-label': done.has(eid) ? 'done' : null }))))));
    }
    const n = ids().filter(e => done.has(e)).length;
    $('#bar').style.width = `${(100 * n) / ids().length}%`;
    $('#count').textContent = `${n} of ${ids().length} done`;
  }

  // ------------------------------------------------------------ checker (web worker)
  function setStatus(msg, err) {
    const s = $('#status');
    if (!s) return;
    s.textContent = msg;
    s.classList.toggle('err', !!err);
  }
  function dropWorker(msg) {
    if (worker) worker.terminate();
    worker = null;
    workerReady = false;
    warming = false;
    for (const k of Object.keys(pending)) { pending[k]({ type: 'error', msg }); delete pending[k]; }
  }
  function getWorker() {
    if (worker) return worker;
    worker = new Worker(BASE + 'worker.js');
    worker.onmessage = (ev) => {
      const m = ev.data;
      if (m.type === 'status') setStatus(m.msg, false);
      else if (m.type === 'ready') { workerReady = true; warming = false; }
      else if (m.type === 'result') {
        workerReady = true;
        const p = pending[m.id]; delete pending[m.id];
        if (p) p(m);
      } else if (m.type === 'error') {
        const p = pending[m.id]; delete pending[m.id];
        dropWorker(m.msg);           // a fresh worker next time
        if (p) p(m);
        else setStatus(`The checker could not load (${m.msg}). Try again, or run it on your computer.`, true);
      }
    };
    worker.onerror = (e) => { e.preventDefault(); dropWorker(e.message || 'the checker stopped'); };
    return worker;
  }
  let warming = false;
  function warm() {
    if (workerReady || warming) return;
    warming = true;
    getWorker().postMessage({ type: 'warm', id: ++runId, base: BASE });
  }
  function check(eid, files) {
    const id = ++runId;
    return new Promise(resolve => {
      pending[id] = resolve;
      getWorker().postMessage({ type: 'check', id, eid, base: BASE, files }, files.filter(Boolean).map(f => f.data));
    });
  }
  async function asPayload(item) {
    if (!item) return null;
    if (item instanceof File) {
      try { return { name: item.name, data: await item.arrayBuffer() }; }
      catch (err) { throw new Error(`${item.name} changed since you chose it (for example, you exported it again). Choose or drop it again.`); }
    }
    const r = await fetch(BASE + item);
    if (!r.ok) throw new Error('Could not download ' + item.split('/').pop() + '. Check your connection and try again.');
    return { name: item.split('/').pop(), data: await r.arrayBuffer() };
  }
  const currentEid = () => (location.hash.match(/^#\/ex\/([\d.]+)$/) || [])[1] || null;

  // ------------------------------------------------------------ pages
  function page(...kids) {
    const v = $('#view');
    v.textContent = '';
    v.append(...kids);
    v.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }

  function startPage() {
    renderToc(null);
    document.title = 'BIM Practice';
    page(
      el('p', { class: 'crumb', text: 'Free and open source' }),
      el('h1', { text: 'Practise structural BIM without paying for software' }),
      el('p', { class: 'lead', text: 'You model one small reinforced concrete building, TB-01, from levels and grids to the issued model, in 32 exercises. Every exercise tells you what to build and how, step by step, in FreeCAD or in Bonsai. When you are done, drop your file here (the IFC model, or the drawing or schedule you exported) and the checker tells you, line by line, what is right and what is not.' }),
      el('ol', { class: 'how' },
        el('li', null, el('b', { text: 'Install a free BIM program' }), 'FreeCAD or Blender with the Bonsai add-on. Both are free and open source and export IFC, the open BIM standard.'),
        el('li', null, el('b', { text: 'Follow the exercise' }), 'Each exercise has the numbers from the project brief and the steps for both programs.'),
        el('li', null, el('b', { text: 'Check your file here' }), 'The checker runs in your browser. Your file is not uploaded anywhere.')),
      el('p', null, el('a', { class: 'btn primary', href: '#/ex/1.1', text: 'Start with exercise 1.1' }), ' ',
        el('a', { class: 'btn', href: '#/brief', text: 'Read the project brief' })),
      el('h2', { text: 'What you need' }),
      el('div', { html: C.need }),
      el('p', { class: 'note', text: 'Python and Git are only needed if you want to run the checker on your own computer, and for exercise 7.3. In this panel the checker runs in the browser.' }),
      el('h2', { text: 'Starting files' }),
      el('p', null, 'Some exercises start from files the course gives you. They are all on the ', el('a', { href: '#/files', text: 'Files' }), ' page.'),
      el('h2', { text: 'If you know Revit' }),
      el('div', { html: C.revit }),
    );
  }

  function briefPage() {
    renderToc(null);
    document.title = 'Project brief · BIM Practice';
    const div = el('div', { class: 'brief', html: C.brief });
    const drawings = el('div', { class: 'drawings' }, ...[...div.querySelectorAll('a[href^="files/drawings/"]')].map(a =>
      el('a', { href: a.getAttribute('href'), target: '_blank', rel: 'noopener' },
        el('img', { src: a.getAttribute('href'), alt: a.textContent, loading: 'lazy' }), a.textContent)));
    const h1 = div.querySelector('h1');
    if (h1) h1.after(drawings); else div.prepend(drawings);
    page(el('p', { class: 'crumb', text: 'Project brief' }), div);
  }

  function filesPage() {
    renderToc(null);
    document.title = 'Files · BIM Practice';
    page(
      el('p', { class: 'crumb', text: 'Files' }),
      el('h1', { text: 'Starting files and drawings' }),
      el('p', { text: 'Download these when an exercise asks for them. Your own model, tb01.ifc, you make yourself from exercise 1.1 on.' }),
      el('h2', { text: 'Datasets' }),
      el('ul', { class: 'files' }, C.datasets.map(d => el('li', null,
        el('a', { href: d.href, download: d.name, text: d.name }), el('span', { class: 'muted small', text: d.about })))),
      el('h2', { text: 'Brief drawings' }),
      el('ul', { class: 'files' }, ['TB-01_brief_level1_framing_plan.svg', 'TB-01_brief_section_grid2.svg', 'TB-01_brief_foundation_plan.svg'].map(n =>
        el('li', null, el('a', { href: 'files/drawings/' + n, target: '_blank', rel: 'noopener', text: n })))),
      el('p', { class: 'note' }, 'Everything is also in the ', el('a', { href: C.repo, target: '_blank', rel: 'noopener', text: 'GitHub repository' }), ', with the checker for the command line.'),
    );
  }

  function stepsBlock(e) {
    const box = el('div', { class: 'steps', id: 'steps', role: 'tabpanel', tabindex: '0' });
    const show = (t, focus) => {
      tool = t; store.set('tool', t);
      tabs.querySelectorAll('button').forEach(b => {
        const on = b.dataset.t === t;
        b.setAttribute('aria-selected', String(on));
        b.tabIndex = on ? 0 : -1;
        if (on) { box.setAttribute('aria-labelledby', b.id); if (focus) b.focus(); }
      });
      box.innerHTML = e.steps[t] || '<p class="muted">Steps for this program are not written yet.</p>';
    };
    const names = [['freecad', 'FreeCAD'], ['bonsai', 'Bonsai']];
    const tabs = el('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Program',
      onkeydown: (ev) => {
        if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
        ev.preventDefault();
        const i = names.findIndex(([t]) => t === tool);
        show(names[(i + (ev.key === 'ArrowRight' ? 1 : names.length - 1)) % names.length][0], true);
      } },
      names.map(([t, label]) =>
        el('button', { type: 'button', role: 'tab', id: 'tab-' + t, 'data-t': t, 'aria-controls': 'steps', onclick: () => show(t), text: label })));
    show(tool);
    return [tabs, box];
  }

  function checkCard(eid, e) {
    const card = el('section', { class: 'card sticky', 'aria-labelledby': 'chk' });
    card.append(el('h2', { id: 'chk', text: 'Check your work' }));
    if (e.inputs.some(i => i.kind === 'folder')) {
      card.append(el('p', { text: 'This check reads a Git repository, which a browser cannot open. Run it on your computer from the course folder:' }),
        el('pre', null, el('code', { text: e.check })),
        el('p', { class: 'note' }, 'How to install the checker: ', el('a', { href: C.repo + '#quick-start', target: '_blank', rel: 'noopener', text: 'Quick start' }), '.'),
        el('button', { class: 'btn', type: 'button', text: done.has(eid) ? 'Marked as done' : 'Mark as done', onclick: (ev) => { done.add(eid); store.set('done', [...done]); ev.target.textContent = 'Marked as done'; renderToc(currentEid()); } }));
      return card;
    }
    card.append(el('p', { class: 'note', text: `Save or export your work as ${e.save}, then drop it below.` }));
    const files = chosen[eid] || (chosen[eid] = e.inputs.map(() => null));
    const run = el('button', { class: 'btn primary', type: 'button', text: 'Check' });
    const refBtn = e.reference ? el('button', { class: 'btn link', type: 'button', text: 'Try it on the reference answer' }) : null;
    const status = el('p', { id: 'status', class: 'status', role: 'status' });
    const say = (msg, err) => { status.textContent = msg; status.classList.toggle('err', !!err); };
    const results = el('div');
    let busy = false;
    const refresh = () => {
      run.disabled = busy || e.inputs.some((inp, i) => !inp.optional && !inp.course_file && !files[i]);
      if (refBtn) refBtn.disabled = busy;
    };

    e.inputs.forEach((inp, i) => {
      const input = el('input', { type: 'file', accept: inp.accept });
      const val = el('span', { class: 'val' });
      const slot = el('label', { class: 'slot' }, el('span', { class: 'lab', text: inp.label }), val, input);
      const showVal = () => {
        if (files[i]) { val.textContent = files[i].name; slot.classList.add('has'); }
        else if (inp.course_file) { val.textContent = `The course file ${inp.name} is used. Drop another file to replace it.`; slot.classList.remove('has'); }
        else { val.textContent = inp.optional ? 'Optional. Drop a file or click to choose.' : 'Drop the file here or click to choose.'; slot.classList.remove('has'); }
      };
      const take = (f) => {
        if (!f) return;
        const exts = inp.accept.split(',');
        const ok = exts.some(x => f.name.toLowerCase().endsWith(x));
        if (!ok) { say(`Choose a ${exts.join(' or ')} file.`, true); return; }
        files[i] = f; showVal(); refresh(); say('', false); warm();
      };
      input.addEventListener('change', () => { take(input.files[0]); input.value = ''; });
      slot.addEventListener('dragover', (ev) => { ev.preventDefault(); slot.classList.add('over'); });
      slot.addEventListener('dragleave', () => slot.classList.remove('over'));
      slot.addEventListener('drop', (ev) => { ev.preventDefault(); slot.classList.remove('over'); take(ev.dataTransfer.files[0]); });
      showVal();
      card.append(slot);
    });

    async function go(list, label) {
      if (busy) return;
      busy = true; refresh();
      results.textContent = '';
      say(workerReady ? 'Checking...' : 'Starting the checker...', false);
      let m;
      try {
        const payload = await Promise.all(list.map(asPayload));
        m = await check(eid, payload);
      } catch (err) {
        m = { type: 'input', msg: String(err.message || err) };
      }
      busy = false; refresh();
      if (m.type === 'input') { say(m.msg, true); return; }
      if (m.type === 'error') {
        say(`The checker stopped (${m.msg}). Press Check to try again, or run it on your computer: ${e.check}`, true);
        return;
      }
      if (m.result.error) { say(m.result.error, true); return; }
      const r = m.result;
      say(`${r.ok} of ${r.n} checks passed.` + (r.passed ? ' Exercise complete.' : ''), false);
      if (label) results.append(el('p', { class: 'note', text: label }));
      results.append(el('ul', { class: 'results' }, r.items.map(it => el('li', null,
        el('span', { class: 'pill ' + (it.ok ? 'pass' : 'fail'), text: it.ok ? 'PASS' : 'FAIL' }),
        el('span', null, it.text, it.hint && !it.ok ? el('span', { class: 'hint', text: it.hint }) : null)))));
      results.append(el('p', { class: 'score' + (r.passed ? ' done' : ''), text: `${r.ok} of ${r.n} checks passed.` + (r.passed ? ' Exercise complete.' : '') }));
      if (r.passed && !label) {
        done.add(eid); store.set('done', [...done]); renderToc(currentEid());
        const next = ids()[ids().indexOf(eid) + 1];
        if (next) results.append(el('a', { class: 'btn primary', href: `#/ex/${next}`, text: `Next: ${next} ${C.exercises[next].title}` }));
      }
    }

    run.addEventListener('click', () => go(e.inputs.map((inp, i) => files[i] || inp.course_file || null), null));
    const actions = el('div', { class: 'actions' }, run);
    if (refBtn) {
      refBtn.addEventListener('click', () => go(e.reference, 'Reference answer from the course (try the exercise yourself first):'));
      actions.append(refBtn);
    }
    card.append(actions, status, results,
      el('p', { class: 'note' }, 'On your computer: ', el('code', { class: 'cmd', text: e.check })));
    refresh();
    return card;
  }

  function exercisePage(eid) {
    const e = C.exercises[eid];
    if (!e) return startPage();
    renderToc(eid);
    $('#toc').classList.remove('open');
    $('#menu').setAttribute('aria-expanded', 'false');
    document.title = `${eid} ${e.title} · BIM Practice`;
    const s = sectionOf(eid);
    const all = ids();
    const i = all.indexOf(eid);
    const prev = all[i - 1], next = all[i + 1];
    page(
      el('p', { class: 'crumb', text: `Section ${s.id} · ${s.title.split(':')[0]}` }),
      el('h1', { text: `${eid} ${e.title}` }),
      el('p', { class: 'goal', html: e.goal }),
      el('div', { class: 'cols' },
        el('div', null,
          el('section', { class: 'card' }, el('h2', { text: 'What you build' }),
            el('ul', { class: 'build' }, e.build.map(b => el('li', { html: b }))),
            eid.startsWith('7.')
              ? el('p', { class: 'note' }, 'Section 7 adds a few numbers that are not in the ', el('a', { href: '#/brief', text: 'project brief' }), '; they are given above. Starting files are on the ', el('a', { href: '#/files', text: 'Files' }), ' page.')
              : el('p', { class: 'note' }, 'All numbers come from the ', el('a', { href: '#/brief', text: 'project brief' }), '. Starting files are on the ', el('a', { href: '#/files', text: 'Files' }), ' page.')),
          ...stepsBlock(e),
          el('details', { class: 'why' }, el('summary', { text: 'Why this matters' }), el('div', { html: e.why }))),
        checkCard(eid, e)),
      el('nav', { class: 'pager', 'aria-label': 'Exercises' },
        prev ? el('a', { href: `#/ex/${prev}`, text: `← ${prev} ${C.exercises[prev].title}` }) : el('span'),
        next ? el('a', { href: `#/ex/${next}`, text: `${next} ${C.exercises[next].title} →` }) : el('span')),
    );
  }

  function route() {
    if (location.hash && !location.hash.startsWith('#/')) return;   // e.g. the skip link
    const h = location.hash.replace(/^#\/?/, '');
    if (h.startsWith('ex/')) exercisePage(h.slice(3));
    else if (h === 'brief') briefPage();
    else if (h === 'files') filesPage();
    else startPage();
  }

  // A file dropped outside a slot must not make the browser open it instead of the panel.
  window.addEventListener('dragover', (ev) => ev.preventDefault());
  window.addEventListener('drop', (ev) => ev.preventDefault());

  fetch(BASE + 'data/course.json').then(r => r.json()).then(c => {
    C = c;
    $('#repo').href = C.repo;
    window.addEventListener('hashchange', route);
    if (location.hash && !location.hash.startsWith('#/')) startPage(); else route();
  }).catch(() => {
    $('#view').textContent = 'The course could not be loaded. Please reload the page.';
  });
})();
