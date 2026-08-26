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
// Per Matt's 2026-08-26 direction: OL doesn't need offensive-formation
// frequency info at all (that's a playcaller/coordinator concern, not
// relevant to a lineman's job) -- OL is the only position group with
// 'formations' dropped from its nd/cd stabs. Everyone else unchanged.
const STAB_MAP = {
  qb: { run: true, nd: ['formations', 'fronts', 'coverage', 'blitz'], cd: ['formations', 'fronts', 'coverage', 'blitz'], rz: true, gl: true },
  te: { run: true, nd: ['formations', 'fronts', 'coverage', 'blitz'], cd: ['formations', 'fronts', 'coverage', 'blitz'], rz: true, gl: true },
  ol: { run: true, nd: ['fronts', 'blitz'], cd: ['fronts', 'blitz'], rz: true, gl: true },
  rb: { run: true, nd: ['formations', 'fronts', 'blitz'], cd: ['formations', 'fronts', 'blitz'], rz: true, gl: true },
  wr: { run: false, nd: ['formations', 'coverage'], cd: ['formations', 'coverage'], rz: true, gl: true },
};

// ---------- "Personnel info" (right under Need to Know) ----------
// Per Matt's 2026-08-26 direction (revised from the first pass, which pulled
// the full "X by Personnel" TABLES over -- too much raw data for players):
// this section should be (1) short bullet-point "key notes" summarizing the
// same by-personnel numbers as plain sentences instead of tables, plus
// (2) the box-style ("pcard") visualizations -- Field/Boundary blitz-hash
// tendency, and the Red Zone stat boxes -- kept exactly as-is, since those
// are already a compact, scannable format, not a table.
const PERSONNEL_HEADING = { fronts: 'Fronts by Personnel', coverage: 'Coverage by Personnel', blitz: 'Blitz by Personnel' };

function extractCardByHeading(html, heading) {
  if (!html) return null;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  const cards = Array.from(root.querySelectorAll('.card'));
  const match = cards.find(c => {
    const hd = c.querySelector('.card-hd');
    return hd && hd.textContent.trim() === heading;
  });
  return match ? match.outerHTML : null;
}

// Grabs the box-style ".pcard" row (e.g. the Field/Boundary blitz-hash boxes,
// or the Red Zone Blitz Rate / Top Coverage at GL / Top Front at GL / 6-man
// boxes) -- returns the whole wrapping grid div's outerHTML, or null.
function extractPcardBoxes(html) {
  if (!html) return null;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  const firstPcard = root.querySelector('.pcard');
  if (!firstPcard) return null;
  const wrap = firstPcard.parentElement;
  return wrap ? wrap.outerHTML : null;
}

function parseTableRows(cardHtml) {
  if (!cardHtml) return [];
  const doc = fragDoc(cardHtml);
  const root = doc.getElementById('root');
  return Array.from(root.querySelectorAll('tbody tr')).map(tr =>
    Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim())
  );
}

// Turns the same per-personnel-group numbers that used to fill a table into
// short bullet sentences instead.
function summarizeByPersonnel(cardHtml, kind) {
  const rows = parseTableRows(cardHtml);
  if (!rows.length) return [];
  return rows.map(r => {
    const [pers, plays, val1, val2] = r;
    if (kind === 'fronts') return `vs <b>${pers}</b> personnel (${plays} plays): <b>${val1}</b> front, ${val2} of the time`;
    if (kind === 'coverage') return `vs <b>${pers}</b> personnel (${plays} plays): <b>${val1}</b> coverage, ${val2} of the time`;
    if (kind === 'blitz') return `vs <b>${pers}</b> personnel (${plays} plays): blitzes ${val2} of the time`;
    return null;
  }).filter(Boolean);
}

function buildPersonnelInfo(deepCurated) {
  const notes = {};
  ['nd', 'cd'].forEach(sec => {
    if (!deepCurated[sec]) return;
    Object.keys(PERSONNEL_HEADING).forEach(stabName => {
      const stabHTML = deepCurated[sec][stabName];
      if (!stabHTML) return;
      const card = extractCardByHeading(stabHTML, PERSONNEL_HEADING[stabName]);
      if (!card) return;
      const bullets = summarizeByPersonnel(card, stabName);
      if (bullets.length) {
        notes[sec] = notes[sec] || {};
        notes[sec][stabName] = bullets;
      }
    });
  });

  const blitzBoxesND = deepCurated.nd && deepCurated.nd.blitz ? extractPcardBoxes(deepCurated.nd.blitz) : null;
  const blitzBoxesCD = deepCurated.cd && deepCurated.cd.blitz ? extractPcardBoxes(deepCurated.cd.blitz) : null;
  const rzBoxes = deepCurated.rz ? extractPcardBoxes(deepCurated.rz) : null;

  const hasAnything = Object.keys(notes).length || blitzBoxesND || blitzBoxesCD || rzBoxes;
  if (!hasAnything) return null;
  return { notes, blitzBoxesND, blitzBoxesCD, rzBoxes };
}

// ---------- Matchups (best/toughest/superlatives), filtered per position ----------
// Per Matt's 2026-08-26 direction:
//   QB   -> all players
//   RB/OL -> DL & LBs only
//   TE   -> DL, LB, SS, FS (safeties, not corners)
//   WR   -> Secondary & Nickel/Sam (the whole DB group)
// Plus: the "WR - Q. Brown (#3)" entry is excluded from the player-facing
// version entirely, regardless of position (stays intact in the coach's
// advance-scout.html copy -- this filtering only affects player-view.html).
const EXCLUDE_MATCHUP_VT = ['WR - Q. Brown (#3)'];

function matchupUnits(text) {
  const t = String(text || '');
  // "s?" on every alternative -- free-text descriptions use plurals a lot
  // ("DBs", "LBs (#43 + #21)") and \b...\b doesn't match across a trailing
  // "s" (no word-boundary between "B" and "s"), so without this the regex
  // silently misses plural mentions and the entry falls through to the
  // "unclassifiable -> include for everyone" default below.
  const units = new Set();
  if (/\b(DTs?|DEs?|NTs?|RUSH(ES)?|IDLs?|DLs?)\b/i.test(t)) units.add('DL');
  if (/\b(LBs?|WILLs?|MIKEs?|MLBs?|WLBs?|WOLFs?|NICKELs?|SAMs?|N\/S)\b/i.test(t)) units.add('LB');
  if (/\b(DBs?|CBs?|SAFs?|SSs?|FSs?|NKLs?|FCs?|BCs?|Secondary)\b/i.test(t)) units.add('DB');
  if (/back\s*7/i.test(t)) { units.add('LB'); units.add('DB'); }
  return units;
}

function posAllowsUnits(posKey, units) {
  if (!units.size) return true; // unclassifiable free text -- err on including it
  if (posKey === 'qb') return true;
  if (posKey === 'ol' || posKey === 'rb') return units.has('DL') || units.has('LB');
  if (posKey === 'te') return units.has('DL') || units.has('LB') || units.has('DB');
  if (posKey === 'wr') return units.has('DB');
  return true;
}

function posAllowsGroup(posKey, group) {
  const g = String(group || '').toUpperCase();
  if (posKey === 'qb') return true;
  if (posKey === 'ol' || posKey === 'rb') return g === 'IDL' || g === 'DE' || g === 'LB';
  if (posKey === 'te') return g === 'IDL' || g === 'DE' || g === 'LB' || g === 'DB';
  if (posKey === 'wr') return g === 'DB';
  return true;
}

function filterMatchupsForPosition(matchups, posKey) {
  if (!matchups) return null;
  const dropExcluded = (rows) => (rows || []).filter(r => !EXCLUDE_MATCHUP_VT.includes(r.vt));

  const best = dropExcluded(matchups.best).filter(r => posAllowsUnits(posKey, matchupUnits(r.opp)));
  const toughest = dropExcluded(matchups.toughest).filter(r => posAllowsUnits(posKey, matchupUnits(r.opp)));

  const superlatives = (matchups.superlatives || []).map(g => {
    if (!posAllowsGroup(posKey, g.group)) return null;
    let rows = g.rows || [];
    // TE's spec is DL/LB/SS/FS -- within the DB group specifically, keep only
    // safety rows (player text starts with "SAF"), drop corner/nickel rows.
    if (posKey === 'te' && String(g.group).toUpperCase() === 'DB') {
      rows = rows.filter(r => /^SAF\b/i.test(r.player || ''));
    }
    return rows.length ? { group: g.group, rows } : null;
  }).filter(Boolean);

  if (!best.length && !toughest.length && !superlatives.length) return null;
  return { best, toughest, superlatives };
}

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
  const fastFacts = D.fastFacts || [];
  const sitRef = D.sitRef || [];
  const depthChart = D.depthChart || { secondary: [], dline: [] };
  const deep = getDeepForTeam(teamKey);

  const fc = (d) => d ? { labels: d.labels, freq: d.freq, blitz: d.blitz } : null;

  const base = {
    meta: D.meta,
    weeklyNotes: D.weeklyNotes || '',
    keys: { fastFacts },
    sitRef,
    depthChart,
  };

  const deepQb = curateDeepForPosition(deep, 'qb');
  const deepOl = curateDeepForPosition(deep, 'ol');
  const deepRb = curateDeepForPosition(deep, 'rb');
  const deepWr = curateDeepForPosition(deep, 'wr');
  const deepTe = curateDeepForPosition(deep, 'te');

  base.qb = {
    ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: deepQb, personnel: buildPersonnelInfo(deepQb),
    matchups: filterMatchupsForPosition(D.matchups, 'qb'),
  };
  base.ol = {
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    // ndFormationChart/cdFormationChart are kept (not shown as a chart/bars --
    // only used to compute the aggregate "overall pressure rate" Need to Know
    // bullet, which is a plain %, not formation-specific info) per Matt's
    // "exclude any formation info from OL page" direction.
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: deepOl, personnel: buildPersonnelInfo(deepOl),
    matchups: filterMatchupsForPosition(D.matchups, 'ol'),
  };
  base.rb = {
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    runFamilies: D.runFamilies,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: deepRb, personnel: buildPersonnelInfo(deepRb),
    matchups: filterMatchupsForPosition(D.matchups, 'rb'),
  };
  base.wr = {
    ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: deepWr, personnel: buildPersonnelInfo(deepWr),
    matchups: filterMatchupsForPosition(D.matchups, 'wr'),
  };
  base.te = {
    ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    deep: deepTe, personnel: buildPersonnelInfo(deepTe),
    matchups: filterMatchupsForPosition(D.matchups, 'te'),
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
