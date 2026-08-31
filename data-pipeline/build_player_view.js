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

// ---------- extract the hand-written "deep" sections (run/nd/cd/rz/gl/bible) ----------
// 'bible' added 2026-08-26 for the Normal Downs Breakdown by Formation cards
// (PREPARE FOR/REACT TO/MIXERS/PRESSURE) -- only that one card is pulled out of
// the much bigger Bible tab, via extractFormationBreakdown() below, not the
// whole coach-only coverage cross-tab.
const DEEP_SECTIONS = ['run', 'nd', 'cd', 'rz', 'gl', 'bible'];
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
// 'bible' (Normal Downs Breakdown by Formation) follows the same gating as the
// 'coverage' nd/cd stab -- it's fundamentally coverage-family/pressure-look
// info by offensive formation, so only QB/WR/TE (the positions that already
// see Coverage) get it; OL/RB don't, same reasoning as the existing split.
const STAB_MAP = {
  qb: { run: true, nd: ['formations', 'fronts', 'coverage', 'blitz'], cd: ['formations', 'fronts', 'coverage', 'blitz'], rz: true, gl: true, bible: true },
  te: { run: true, nd: ['formations', 'fronts', 'coverage', 'blitz'], cd: ['formations', 'fronts', 'coverage', 'blitz'], rz: true, gl: true, bible: true },
  ol: { run: true, nd: ['fronts', 'blitz'], cd: ['fronts', 'blitz'], rz: true, gl: true },
  rb: { run: true, nd: ['formations', 'fronts', 'blitz'], cd: ['formations', 'fronts', 'blitz'], rz: true, gl: true },
  wr: { run: false, nd: ['formations', 'coverage'], cd: ['formations', 'coverage'], rz: true, gl: true, bible: true },
};

// ---------- "Personnel info" (right under Need to Know) ----------
// Per Matt's 2026-08-26 direction: drop the by-personnel bullet-point "key
// notes" entirely (both stages of that feature -- the original raw tables
// AND the summarized-sentence revision) -- too much granular detail for the
// player-facing page. Keep ONLY the box-style ("pcard") visualizations --
// Field/Boundary blitz-hash tendency for Blitz, and the Red Zone stat boxes
// -- exactly as they appear on the coach's advance-scout.html.
function extractPcardBoxes(html) {
  if (!html) return null;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  const firstPcard = root.querySelector('.pcard');
  if (!firstPcard) return null;
  const wrap = firstPcard.parentElement;
  return wrap ? wrap.outerHTML : null;
}

// Grabs the qualitative ".callout" note that sits alongside the pcard box
// row on the coach's page -- Blitz's rate header (e.g. "36% Blitz Rate on
// Conversion Downs (56/155 plays)") or Red Zone's "OUTER RZ -> GOAL LINE
// SHIFTS" note -- returns its outerHTML, or null.
function extractCallout(html) {
  if (!html) return null;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  // Grab ALL .callout elements, not just the first -- Red Zone now has TWO
  // (the new "LINE OF DEMARCATION" note plus the existing "OUTER RZ -> GOAL
  // LINE SHIFTS" note), and both should carry over to player-view.html in
  // the same order they appear on the coach's page.
  const callouts = Array.from(root.querySelectorAll('.callout'));
  return callouts.length ? callouts.map(c => c.outerHTML).join('') : null;
}

// Blitz on the coach's page shows the rate callout ABOVE the boxes; Red
// Zone shows its shift-note callout BELOW the boxes -- match that exact
// order here so player-view looks identical to advance-scout.html.
function combineBoxesAndCallout(stabHtml, calloutFirst) {
  if (!stabHtml) return null;
  const boxes = extractPcardBoxes(stabHtml);
  const callout = extractCallout(stabHtml);
  if (!boxes && !callout) return null;
  return calloutFirst ? (callout || '') + (boxes || '') : (boxes || '') + (callout || '');
}

// Grabs the 3-zone breakdown cards (Outer RZ / Score Zone / Goal Line --
// each with Front/Coverage/Blitz text + a Down/Plays/Blitz% table) that sit
// below the RZ callouts on the coach's page. Per Matt's 2026-08-26 direction
// these should show on EVERY position's Red Zone section on player-view.html
// too, unfiltered -- unlike the by-personnel notes that were removed
// earlier, these are the specific tables Matt asked to have included.
function extractZoneCards(html) {
  if (!html) return null;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  const firstZcard = root.querySelector('.zcard');
  if (!firstZcard) return null;
  const wrap = firstZcard.parentElement;
  return wrap ? wrap.outerHTML : null;
}

// Grabs just the "Normal Downs Breakdown by Formation" PREPARE FOR/REACT
// TO/MIXERS/PRESSURE card out of the much bigger Bible tab -- the rest of
// the Bible tab (coverage cross-tabs by personnel/front/def-personnel) is
// coach-only detail, not meant for the player-facing page. Matches the
// extractZoneCards() pattern above: find the first .prm-grid, grab its
// containing .bib-card2 card.
function extractFormationBreakdown(html) {
  if (!html) return null;
  const doc = fragDoc(html);
  const root = doc.getElementById('root');
  const grid = root.querySelector('.prm-grid');
  if (!grid) return null;
  const card = grid.closest('.bib-card2') || grid.parentElement;
  return card ? card.outerHTML : null;
}

function buildPersonnelInfo(deepCurated) {
  const blitzBoxesND = deepCurated.nd && deepCurated.nd.blitz ? combineBoxesAndCallout(deepCurated.nd.blitz, true) : null;
  const blitzBoxesCD = deepCurated.cd && deepCurated.cd.blitz ? combineBoxesAndCallout(deepCurated.cd.blitz, true) : null;
  const rzBoxes = deepCurated.rz ? combineBoxesAndCallout(deepCurated.rz, false) : null;
  const rzZoneCards = deepCurated.rz ? extractZoneCards(deepCurated.rz) : null;

  if (!blitzBoxesND && !blitzBoxesCD && !rzBoxes && !rzZoneCards) return null;
  return { blitzBoxesND, blitzBoxesCD, rzBoxes, rzZoneCards };
}

// ---------- Matchups (best/toughest/superlatives) ----------
// Per Matt's 2026-08-26 direction, Matchups no longer lives on each position
// page -- it moved to the single shared "Keys to the Game" tab, so it's no
// longer filtered by position (there's no one "current position" in that
// tab). It stays team-level and unfiltered except for one standing
// exclusion: the "WR - Q. Brown (#3)" entry is dropped from the
// player-facing version entirely (stays intact in the coach's
// advance-scout.html copy -- this only affects player-view.html).
const EXCLUDE_MATCHUP_VT = ['WR - Q. Brown (#3)'];

function filterMatchupsUnfiltered(matchups) {
  if (!matchups) return null;
  const dropExcluded = (rows) => (rows || []).filter(r => !EXCLUDE_MATCHUP_VT.includes(r.vt));
  const best = dropExcluded(matchups.best);
  const toughest = dropExcluded(matchups.toughest);
  const superlatives = matchups.superlatives || [];
  if (!best.length && !toughest.length && !superlatives.length) return null;
  return { best, toughest, superlatives };
}

// ---------- "Top players you'll face" (Need to Know), from Depth Chart ----------
// Per Matt's 2026-08-26 direction: sourced from the Depth Chart (the starter
// at each relevant defensive slot), filtered by the SAME position-relevance
// rule used for matchups before:
//   QB    -> all defensive position groups
//   RB/OL -> DL & LBs (incl. Nickel/Sam)
//   TE    -> DL, LB, Nickel/Sam, & Safeties (not corners)
//   WR    -> Secondary (all 4 DB slots) & Nickel/Sam
// DEPTH_POS_UNIT maps each depth-chart position CODE (the exact `pos`
// strings used in DC_GROUP_ORDER on the player-view page) to a finer-grained
// unit than the 3-way secondary/lb/dl split, because Nickel/Sam and
// corners-vs-safeties need to be told apart from their neighbors.
const DEPTH_POS_UNIT = {
  BC: 'DB', FC: 'DB', FS: 'SAF', SS: 'SAF',
  WILL: 'LB', MIKE: 'LB', 'NICKEL / SAM': 'NICKEL', 'N/S': 'NICKEL',
  RUSH: 'DL', DT: 'DL', NT: 'DL', DE: 'DL',
};
const UNIT_LABEL = { DL: 'D-Line', LB: 'Linebackers', NICKEL: 'Nickel/Sam', SAF: 'Safeties', DB: 'Secondary' };

function depthUnitsForPosition(posKey) {
  if (posKey === 'qb') return ['DL', 'LB', 'NICKEL', 'SAF', 'DB'];
  if (posKey === 'ol' || posKey === 'rb') return ['DL', 'LB', 'NICKEL'];
  if (posKey === 'te') return ['DL', 'LB', 'NICKEL', 'SAF'];
  if (posKey === 'wr') return ['DB', 'SAF', 'NICKEL'];
  return [];
}

function buildTopPlayers(depthChart, posKey) {
  if (!depthChart) return null;
  const allGroups = [].concat(depthChart.secondary || [], depthChart.dline || []);
  const units = depthUnitsForPosition(posKey);
  const players = [];
  allGroups.forEach(g => {
    const unit = DEPTH_POS_UNIT[g.pos];
    if (unit && !units.includes(unit)) return; // recognized code, not relevant to this position
    const starter = (g.players || []).find(p => p.starter) || (g.players || [])[0];
    if (starter) players.push(Object.assign({ pos: g.pos }, starter));
  });
  if (!players.length) return null;
  const legend = units.map(u => UNIT_LABEL[u]).join(', ');
  return { players, legend };
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
  if (map.bible && deep.bible) {
    const cleaned = extractFormationBreakdown(deep.bible);
    if (cleaned) result.bible = cleaned;
  }
  return result;
}

// Per Matt 2026-08-28: on player-view ONLY, coverage-family donut slices
// that differ solely by a trailing " MAX" (depth/alignment variant of the
// same shell -- QTRS/QTRS MAX, 1HZ/1HZ MAX, 1HM/1HM MAX, 2HM/2HM MAX,
// 2HZ/2HZ MAX, ZERO/ZERO MAX, and any future family that gets a MAX tag)
// are combined into one slice, since that's the level of detail players
// need for a "what coverage are they in" read. This is a GENERIC rule (not
// a hardcoded list of family names) so a brand-new opponent's MAX variant
// folds in automatically without any manual per-team work.
//
// "P"-suffix pattern-match variants (1HMP/1HZP/2HZP) are explicitly NOT
// touched -- pattern-match is a real technique difference, not just a
// depth tweak, so those stay their own separate slices per Matt's direction.
//
// IMPORTANT: this runs ONLY on the copy of the donut object embedded into
// PLAYER_VIEW_DATA below -- it never modifies D.ndCovDonut/D.cdCovDonut
// themselves (those came from advance-scout.html's own TEAMS_DATA/<TEAM>_DATA
// and are left completely untouched), so the coach's advance-scout.html view
// keeps showing every family split out exactly as charted. This function
// only takes an already-extracted {labels,data} object and returns a new
// one -- it never writes back to advance-scout.html or its source data.
//
// Situational/down-and-distance coverage breakdowns (Bible, RZ zone cards,
// personnel/formation cross-tabs, the "Full Coach Breakdown" detail sections)
// are untouched by this function and stay fully granular on player-view too
// -- only the top-level ND/CD Coverage donuts go through this.
function groupCoverageDonutForPlayers(donut) {
  if (!donut || !donut.labels || !donut.labels.length) return donut;
  const order = [];
  const groups = new Map(); // base family label -> { pct, hadMax }
  donut.labels.forEach((label, i) => {
    const pct = donut.data[i];
    const m = label.match(/^(.*)\s\d+%$/);
    const fam = m ? m[1] : label;
    const isMax = /\sMAX$/.test(fam);
    const base = isMax ? fam.replace(/\sMAX$/, '') : fam;
    if (!groups.has(base)) { groups.set(base, { pct: 0, hadMax: false }); order.push(base); }
    const g = groups.get(base);
    g.pct += pct;
    if (isMax) g.hadMax = true;
  });
  order.sort((a, b) => groups.get(b).pct - groups.get(a).pct);
  const labels = order.map(f => `${f}${groups.get(f).hadMax ? '*' : ''} ${groups.get(f).pct}%`);
  const data = order.map(f => groups.get(f).pct);
  const mergedFamilies = order.filter(f => groups.get(f).hadMax);
  const note = mergedFamilies.length
    ? `* ${mergedFamilies.map(f => `${f} + ${f} MAX`).join(', ')} combined for clarity -- coaches see the full breakdown.`
    : null;
  return { labels, data, note };
}

// ── Top Team Stats (Keys tab, sits above Superlatives) ──
// Per Matt's 2026-08-29 direction: replaces nothing, ADDS a new section above
// Superlatives showing (1) team-level stat categories where the opponent
// ranks Top 25 nationally OR Top 2 in their conference, and (2) individual
// roster players with standout stats Top 10 in their conference. A team with
// no qualifying rows in either bucket gets no section at all (e.g. expected
// for VMI going into a rebuild year -- though see note below, VMI actually
// clears the bar in one category on real 2025 data).
//
// TEAM-LEVEL data source: `D.stats` already carries `conf`/`nat` rank for
// every opponent (Total/Scoring/Run/Pass Defense, Takeaways, 3rd Down Def.,
// Red Zone Def.) -- this is the SAME data already shown as rank chips on the
// coach's advance-scout.html Overview tab, sourced from each team's real
// final-2025-season official stats. No new research needed for this half.
// Matt approved Total Defense/Scoring Defense/Rush Defense/Pass Defense/
// Sacks/Turnover Margin as the category set -- `D.stats` has the first four
// under those exact (or equivalent -- "Run Defense" = Rush Defense) labels.
// It does NOT have team-total Sacks or true Turnover Margin (net, not just
// takeaways) anywhere in the pipeline -- "Takeaways" is included as the
// closest already-available proxy, labeled honestly as "Takeaways" rather
// than mislabeled "Turnover Margin". Flagged to Matt 2026-08-29; add real
// Sacks/Turnover Margin team totals to the source data if he wants those
// two included for real later.
//
// PLAYER-LEVEL data (`D.teamStatsPlayers`, optional array of
// {name, pos, category, conferenceRank, value}) requires genuine per-
// conference-leaderboard research (SoCon/Sun Belt/Big Ten stat pages) that
// isn't in this pipeline at all -- left for Matt to ask for per-opponent,
// same "look it up when building/updating that week" cadence as everything
// else here. Not populated as of 2026-08-29 (search-snippet results weren't
// reliable enough to hand-enter real ranks without risking a wrong number).
const TEAM_STAT_CATEGORIES = ['Total Defense', 'Scoring Defense', 'Run Defense', 'Pass Defense', 'Takeaways'];
const TS_NAT_MAX = 25, TS_CONF_MAX = 2;
function buildTeamStats(D) {
  const statRows = (D.stats || [])
    .filter(s => TEAM_STAT_CATEGORIES.includes(s.label))
    .filter(s => (s.nat != null && s.nat <= TS_NAT_MAX) || (s.conf != null && s.conf <= TS_CONF_MAX))
    .map(s => ({ category: s.label, value: s.val, nationalRank: s.nat, conferenceRank: s.conf }));
  const players = (D.teamStatsPlayers || []).filter(p => p.conferenceRank != null && p.conferenceRank <= 10);
  if (!statRows.length && !players.length) return null;
  return { team: statRows, players };
}

// ── True overall ND blitz rate (Need to Know bullet), 2026-08-29 fix ──
// Per Matt: player-view's "Overall blitz rate, early downs" Need to Know
// bullet was showing 42% for VMI while the coach's page shows 40%. Root
// cause: the bullet was computed via avgBlitz(d.ndFormationChart) -- a
// play-frequency-weighted average across only the ND Formation Frequency
// chart's TOP 8 formations. That chart's `freq` values don't sum to 100
// (VMI's ND freq sums to 76) because it's a top-N display list, not the
// full formation set -- so ~24% of VMI's real ND snaps (whatever formation
// they came from, outside the top 8) were silently excluded from the
// average, skewing 40% -> 42%. The TRUE number (69/172 = 40% for VMI) is
// already computed once, correctly, from the FULL raw dataset by
// compute_situational.py/gen_html.py, and is already rendered verbatim on
// the coach's advance-scout.html page as the ND Blitz stab's callout:
// `<strong>40% Blitz Rate</strong> on Normal Downs (69/172 plays)`.
// Rather than re-deriving that number a second, less-accurate way, this
// pulls the EXACT same rendered number back out of that HTML (already
// available in `deep.nd`, the full ND section HTML, before
// curateDeepForPosition() trims it down per position) via regex -- same
// "extract from already-generated HTML" pattern already used throughout
// this file (extractPcardBoxes/extractCallout/extractZoneCards etc.).
// Guarantees byte-for-byte agreement with the coach's page by construction,
// for any team/week, without needing compute_situational.py to expose a
// separate clean JSON field.
function extractBlitzPct(sectionHtml, label) {
  if (!sectionHtml) return null;
  const re = new RegExp(`(\\d+)%\\s*Blitz Rate<\\/strong>\\s*on\\s*${label}\\s*\\((\\d+)\\/(\\d+)\\s*plays\\)`, 'i');
  const m = sectionHtml.match(re);
  if (!m) return null;
  return parseInt(m[1], 10);
}

function curateTeam(D, teamKey) {
  if (!D) return null;
  const fastFacts = D.fastFacts || [];
  const sitRef = D.sitRef || [];
  const depthChart = D.depthChart || { secondary: [], dline: [] };
  const deep = getDeepForTeam(teamKey);
  // True overall ND blitz rate, matching the coach's page exactly -- see
  // extractBlitzPct() docs above. Computed once from the FULL (pre-position-
  // trim) deep.nd HTML, then reused across every position below (the number
  // itself doesn't vary by position, same as the coach's page).
  const ndBlitzPct = extractBlitzPct(deep.nd, 'Normal Downs');

  const fc = (d) => d ? { labels: d.labels, freq: d.freq, blitz: d.blitz } : null;
  const cov = (d) => groupCoverageDonutForPlayers(d);

  const base = {
    meta: D.meta,
    weeklyNotes: D.weeklyNotes || '',
    keys: { fastFacts },
    sitRef,
    depthChart,
    // Team-level, shown once in the "Keys to the Game" tab -- no longer
    // filtered per position (see filterMatchupsUnfiltered above).
    matchups: filterMatchupsUnfiltered(D.matchups),
    // Team-level, shown once in the Keys tab ABOVE Superlatives -- see
    // buildTeamStats() above for the qualification rules and data-source notes.
    teamStats: buildTeamStats(D),
  };

  const deepQb = curateDeepForPosition(deep, 'qb');
  const deepOl = curateDeepForPosition(deep, 'ol');
  const deepRb = curateDeepForPosition(deep, 'rb');
  const deepWr = curateDeepForPosition(deep, 'wr');
  const deepTe = curateDeepForPosition(deep, 'te');

  // manZone ({nd,cd,rz,tm,fm,overall}, each {n,man,zone,manPct,zonePct,unmapped})
  // is passed through verbatim from D.manZone -- team-wide, not position-
  // specific (same as ndBlitzPct above), same object reused across QB/WR/TE.
  // Per Matt 2026-08-31: only QB/WR/TE get it (not OL/RB) -- coverage reads
  // matter most for the positions that actually run/defend routes.
  const manZone = D.manZone || null;

  base.qb = {
    ndCovDonut: cov(D.ndCovDonut), cdCovDonut: cov(D.cdCovDonut),
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    ndBlitzPct, manZone,
    deep: deepQb, personnel: buildPersonnelInfo(deepQb),
    topPlayers: buildTopPlayers(depthChart, 'qb'),
  };
  base.ol = {
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    // ndFormationChart/cdFormationChart are kept (not shown as a chart/bars --
    // only used to compute the aggregate "overall pressure rate" Need to Know
    // bullet, which is a plain %, not formation-specific info) per Matt's
    // "exclude any formation info from OL page" direction.
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    ndBlitzPct,
    deep: deepOl, personnel: buildPersonnelInfo(deepOl),
    topPlayers: buildTopPlayers(depthChart, 'ol'),
  };
  base.rb = {
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    runFamilies: D.runFamilies,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    ndBlitzPct,
    deep: deepRb, personnel: buildPersonnelInfo(deepRb),
    topPlayers: buildTopPlayers(depthChart, 'rb'),
  };
  base.wr = {
    ndCovDonut: cov(D.ndCovDonut), cdCovDonut: cov(D.cdCovDonut),
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    ndBlitzPct, manZone,
    deep: deepWr, personnel: buildPersonnelInfo(deepWr),
    topPlayers: buildTopPlayers(depthChart, 'wr'),
  };
  base.te = {
    ndCovDonut: cov(D.ndCovDonut), cdCovDonut: cov(D.cdCovDonut),
    ndFrontsDonut: D.ndFrontsDonut, cdFrontsDonut: D.cdFrontsDonut,
    ndFormationChart: fc(D.ndFormationChart), cdFormationChart: fc(D.cdFormationChart),
    ndBlitzPct, manZone,
    deep: deepTe, personnel: buildPersonnelInfo(deepTe),
    topPlayers: buildTopPlayers(depthChart, 'te'),
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
