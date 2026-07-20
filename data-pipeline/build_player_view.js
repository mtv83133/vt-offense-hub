#!/usr/bin/env node
/*
 * build_player_view.js -- derives the curated, position-grouped
 * PLAYER_VIEW_DATA blob for player-view.html from the SAME source data
 * that powers the coach's advance-scout.html. advance-scout.html's
 * per-team consts (VMI_DATA / ODU_DATA / MARYLAND_DATA / ...) remain the
 * single source of truth -- this script re-derives player-view.html's
 * data every time it's run, so the two pages never drift out of sync.
 *
 * Usage:
 *   node build_player_view.js <path-to-_source-advance-scout.html> <path-to-_source-player-view.html>
 *
 * Splices a fresh `const PLAYER_VIEW_DATA = {...};` into player-view.html,
 * replacing only that block (same brace-matched splice technique used
 * elsewhere in this pipeline). Everything else in player-view.html
 * (markup, CSS, render JS) is left untouched.
 */
const fs = require('fs');

const [,, advPath, pvPath] = process.argv;
if (!advPath || !pvPath) {
  console.error('Usage: node build_player_view.js <_source/advance-scout.html> <_source/player-view.html>');
  process.exit(1);
}

const advSrc = fs.readFileSync(advPath, 'utf8');

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
  // Evaluate as a JS object literal (handles both strict JSON and the
  // unquoted-key/single-quoted-string style MARYLAND_DATA uses).
  return (0, eval)('(' + text + ')');
}

const TEAMS = {
  VMI: extractConst('VMI_DATA', advSrc),
  ODU: extractConst('ODU_DATA', advSrc),
  MARYLAND: extractConst('MARYLAND_DATA', advSrc),
};

function curateTeam(D, teamKey) {
  if (!D) return null;
  const exploits = (D.exploits || []).map(e => e.text);
  const fastFacts = D.fastFacts || [];
  const sitRef = D.sitRef || [];
  const depthChart = D.depthChart || { secondary: [], dline: [] };

  return {
    meta: D.meta,
    weeklyNotes: D.weeklyNotes || '',
    keys: { exploits, fastFacts },
    sitRef,
    depthChart,
    // QB: what shells/pressure/RZ coverage to expect
    qb: {
      ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
      ndFormationChart: D.ndFormationChart ? { labels: D.ndFormationChart.labels, blitz: D.ndFormationChart.blitz } : null,
      cdFormationChart: D.cdFormationChart ? { labels: D.cdFormationChart.labels, blitz: D.cdFormationChart.blitz } : null,
    },
    // OL: fronts + pressure tells
    ol: {
      ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
      ndFormationChart: D.ndFormationChart ? { labels: D.ndFormationChart.labels, blitz: D.ndFormationChart.blitz } : null,
      cdFormationChart: D.cdFormationChart ? { labels: D.cdFormationChart.labels, blitz: D.cdFormationChart.blitz } : null,
    },
    // RB: fronts + run family efficiency + blitz (pass pro context)
    rb: {
      ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
      runFamilies: D.runFamilies,
      ndFormationChart: D.ndFormationChart ? { labels: D.ndFormationChart.labels, blitz: D.ndFormationChart.blitz } : null,
    },
    // WR: coverage + RZ
    wr: {
      ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
    },
    // TE: coverage (as a pass catcher) + fronts (as a blocker)
    te: {
      ndCovDonut: D.ndCovDonut, cdCovDonut: D.cdCovDonut,
      ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    },
  };
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
// consume trailing semicolon if present
let end = i;
if (pvSrc[end] === ';') end++;

const updated = pvSrc.slice(0, start) + newBlock + pvSrc.slice(end);
fs.writeFileSync(pvPath, updated, 'utf8');
console.log(`Spliced PLAYER_VIEW_DATA (${Object.keys(PLAYER_VIEW_DATA).length} teams) into ${pvPath}`);
for (const [k,v] of Object.entries(PLAYER_VIEW_DATA)) {
  console.log(`  ${k}: ${v ? 'OK' : 'MISSING'}`);
}
