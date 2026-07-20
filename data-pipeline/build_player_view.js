#!/usr/bin/env node
/*
 * build_player_view.js -- derives the curated, position-grouped
 * PLAYER_VIEW_DATA blob for player-view.html from the SAME source data
 * that powers the coach's advance-scout.html. advance-scout.html's
 * per-team consts (VMI_DATA / ODU_DATA / MARYLAND_DATA / ...) AND its
 * hand-written "deep" sections (Run Defense / Normal Downs / Conversion
 * Downs / Red Zone / Goal Line -- the tmpl-<sec>-<TEAM> blocks, or the
 * live DOM content for Maryland) remain the single source of truth --
 * this script re-derives player-view.html's data every time it's run,
 * so the two pages never drift out of sync.
 *
 * Usage:
 *   node build_player_view.js <path-to-_source-advance-scout.html> <path-to-_source-player-view.html>
 */
const fs = require('fs');
const { JSDOM } = require('jsdom');

const [,, advPath, pvPath] = process.argv;
if (!advPath || !pvPath) {
  console.error('Usage: node build_player_view.js <_source/advance-scout.html> <_source/player-view.html>');
  process.exit(1);
}

const advSrc = fs.readFileSync(advPath, 'utf8');

// ---------- extract the JS consts (VMI_DATA / ODU_DATA / MARYLAND_DATA) ----------
function extractConst(varName, src) {
  const marker = `const ${varName} = `;
  const start = src.indexOf(marker);
  if (start === -1) return null;
  let i = start + marker.length;
  if (src[i] !== '{') throw new Error(`${varName}: expected { at position ${i}`);
  let depth = 0, inStr = false, strCh = null, esc = false;
  const objStart = i;
  for (; i < src.length; i++) {
    const c = src[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === '\\') esc = true;
      else if (c === strCh) inStr = false;
    } else {
      if (c === '"' || c === "'") { inStr = true; strCh = c; }
      else if (c === '{') depth++;
      else if (c === '}') { depth--; if (depth === 0) { i++; break; } }
    }
  }
  const text = src.slice(objStart, i);
  return (0, eval)('(' + text + ')');
}

const TEAMS = {
  VMI: extractConst('VMI_DATA', advSrc),
  ODU: extractConst('ODU_DATA', advSrc),
  MARYLAND: extractConst('MARYLAND_DATA', advSrc),
};

// ---------- extract the hand-written "deep" sections (run/nd/cd/rz/gl) ----------
const DEEP_SECTIONS = ['run', 'nd', 'cd', 'rz', 'gl'];
const parseDom = new JSDOM(advSrc);
const parseDoc = parseDom.window.document;

function getDeepSectionHTML(sec, team) {
  if (team === 'MARYLAND') {
    const el = parseDoc.getElementById('sec-' + sec + '-body');
    return el ? el.innerHTML : null;
  }
  const tmpl = parseDoc.getElementById('tmpl-' + sec + '-' + team);
  return tmpl ? tmpl.innerHTML : null;
}

function fragDoc(html) {
  return new JSDOM('<div id="root">' + (html || '') + '</div>').window.document;
}

function extractStab(sectionHTML, sec, stabName) {
  if (!sectionHTML) return null;
  const doc = fragDoc(sectionHTML);
  const el = doc.getElementById(sec + '-' + stabName);
  return el ? el.innerHTML : null;
}

// Remove chart canvases (and their wrapping card, if the card is just a
// chart with a heading) from an HTML fragment -- player-view renders its
// own charts from the JSON data instead, fed by the SAME source numbers,
// so we don't want a dead, unrendered canvas left behind.
function stripCharts(html) {
  if (!html) return html;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  root.querySelectorAll('canvas').forEach(c => {
    const wrap = c.closest('.ch-lg, .ch-sm, .ch') || c;
    const card = wrap.closest('.card');
    if (card && card.querySelectorAll('canvas').length && card.children.length <= 2) {
      card.remove();
    } else {
      wrap.remove();
    }
  });
  return root.innerHTML.trim();
}

// Run section: drop the run-eff-bars/chart card (player-view already
// renders this itself from D.runFamilies) and any other canvases; keep
// the DL Techniques + Run Game Reactions tables, which are genuinely new
// hand-written detail not available anywhere else.
function stripRunEffCard(html) {
  if (!html) return html;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  const runEffBars = root.querySelector('#run-eff-bars');
  if (runEffBars) {
    const card = runEffBars.closest('.card');
    if (card) card.remove();
  }
  root.querySelectorAll('canvas').forEach(c => {
    const wrap = c.closest('.ch-lg, .ch-sm, .ch') || c;
    const card = wrap.closest('.card');
    if (card) card.remove(); else wrap.remove();
  });
  return root.innerHTML.trim();
}

function getDeepForTeam(team) {
  const out = {};
  DEEP_SECTIONS.forEach(sec => { out[sec] = getDeepSectionHTML(sec, team); });
  return out;
}

// Which deep-section detail each position group sees. QB (and TE, given
// the position's dual run/pass-catching role) get everything; other
// groups get the stabs that are actually relevant to their job.
const STAB_MAP = {
  qb: { run: true, nd: ['formations', 'fronts', 'coverage', 'blitz'], cd: ['formations', 'fronts', 'coverage', 'blitz'], rz: true, gl: true },
  te: { run: true, nd: ['formations', 'fronts', 'coverage', 'blitz'], cd: ['formations', 'fronts', 'coverage', 'blitz'], rz: true, gl: true },
  ol: { run: true, nd: ['formations', 'fronts', 'blitz'], cd: ['formations', 'fronts', 'blitz'], rz: true, gl: true },
  rb: { run: true, nd: ['formations', 'fronts', 'blitz'], cd: ['formations', 'fronts', 'blitz'], rz: true, gl: true },
  wr: { run: false, nd: ['formations', 'coverage'], cd: ['formations', 'coverage'], rz: true, gl: true },
};

function curateDeepForPosition(deep, posKey) {
  const map = STAB_MAP[posKey];
  const result = {};
  if (map.run && deep.run) {
    const stripped = stripRunEffCard(deep.run);
    if (stripped) result.run = stripped;
  }
  ['nd', 'cd'].forEach(sec => {
    if (map[sec] && deep[sec]) {
      const stabs = {};
      let any = false;
      map[sec].forEach(stabName => {
        const raw = extractStab(deep[sec], sec, stabName);
        const cleaned = stripCharts(raw);
        if (cleaned) { stabs[stabName] = cleaned; any = true; }
      });
      if (any) result[sec] = stabs;
    }
  });
  if (map.rz && deep.rz) {
    const cleaned = stripCharts(deep.rz);
    if (cleaned) result.rz = cleaned;
  }
  if (map.gl && deep.gl) {
    const cleaned = stripCharts(deep.gl);
    if (cleaned) result.gl = cleaned;
  }
  return result;
}

function curateTeam(D, teamKey) {
  if (!D) return null;
  const exploits = (D.exploits || []).map(e => e.text);
  const fastFacts = D.fastFacts || [];
  const sitRef = D.sitRef || [];
  const depthChart = D.depthChart || { secondary: [], dline: [] };
  const deep = getDeepForTeam(teamKey);

  const fc = (d) => d ? { labels: d.labels, freq: d.freq, blitz: d.blitz } : null;

  const base = {
    meta: D.meta,
    weeklyNotes: D.weeklyNotes || '',
    keys: { exploits, fastFacts },
    sitRef,
    depthChart,
  };

  base.qb = {
    ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: curateDeepForPosition(deep, 'qb'),
  };
  base.ol = {
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: curateDeepForPosition(deep, 'ol'),
  };
  base.rb = {
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    runFamilies: D.runFamilies,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: curateDeepForPosition(deep, 'rb'),
  };
  base.wr = {
    ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: curateDeepForPosition(deep, 'wr'),
  };
  base.te = {
    ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    deep: curateDeepForPosition(deep, 'te'),
  };

  return base;
}

const PLAYER_VIEW_DATA = {};
for (const [key, D] of Object.entries(TEAMS)) {
  PLAYER_VIEW_DATA[key] = curateTeam(D, key);
}

const jsonBlob = JSON.stringify(PLAYER_VIEW_DATA);
const newBlock = `const PLAYER_VIEW_DATA = ${jsonBlob};`;

let pvSrc;
try {
  pvSrc = fs.readFileSync(pvPath, 'utf8');
} catch (e) {
  console.error(`Could not read ${pvPath} -- create the page shell first, this script only updates the data block.`);
  process.exit(1);
}

const marker = 'const PLAYER_VIEW_DATA = ';
const start = pvSrc.indexOf(marker);
if (start === -1) {
  console.error(`No "const PLAYER_VIEW_DATA = " block found in ${pvPath} -- add a placeholder first.`);
  process.exit(1);
}
let i = start + marker.length;
if (pvSrc[i] !== '{') throw new Error('expected { after marker');
let depth = 0, inStr = false, strCh = null, esc = false;
for (; i < pvSrc.length; i++) {
  const c = pvSrc[i];
  if (inStr) {
    if (esc) esc = false;
    else if (c === '\\') esc = true;
    else if (c === strCh) inStr = false;
  } else {
    if (c === '"' || c === "'") { inStr = true; strCh = c; }
    else if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) { i++; break; } }
  }
}
let end = i;
if (pvSrc[end] === ';') end++;

const updated = pvSrc.slice(0, start) + newBlock + pvSrc.slice(end);
fs.writeFileSync(pvPath, updated, 'utf8');
console.log(`Spliced PLAYER_VIEW_DATA (${Object.keys(PLAYER_VIEW_DATA).length} teams) into ${pvPath}`);
for (const [k, v] of Object.entries(PLAYER_VIEW_DATA)) {
  if (!v) { console.log(`  ${k}: MISSING`); continue; }
  const deepCounts = ['qb','ol','rb','wr','te'].map(p => `${p}=${Object.keys(v[p].deep || {}).length}`).join(' ');
  console.log(`  ${k}: OK (deep sections per position: ${deepCounts})`);
}
