/**
 * VT Offense Hub -- AI Search proxy (Cloudflare Worker)
 *
 * Holds the Anthropic API key server-side so it never reaches the browser.
 * advance-scout.html POSTs a question + the currently-selected team's data
 * (static context + raw queryPlays) here; this Worker calls Claude with a
 * `query_plays` tool (matchesFilters/topBreakdown below) that filters and
 * counts the real per-play data, so every number Claude reports is counted
 * by real code, never guessed/hallucinated from reading raw JSON. Claude
 * only ever gets to (a) read the small "static context" object directly
 * (depth chart, roster, matchups, prose, etc.) and (b) call query_plays as
 * many times as it needs against the full raw play list to answer
 * situational/statistical questions.
 *
 * Deploy: see SETUP.md in this same folder for step-by-step instructions.
 * Required secrets (set via `wrangler secret put` or the dashboard):
 *   ANTHROPIC_API_KEY  -- your Anthropic Console API key
 *   APP_SECRET         -- any random string you also paste into
 *                         advance-scout.html's AI_SEARCH_APP_SECRET constant
 * Required var: ALLOWED_ORIGIN (e.g. "https://mtv83133.github.io")
 */

const ANTHROPIC_VERSION = '2023-06-01';
const MODEL = 'claude-sonnet-5';
const MAX_TOOL_ITERATIONS = 8;

// 2026-09-28: the rest of the site (RZ line-of-demarcation, Bible tab small-
// sample flags, etc.) treats a group under 5 charted reps as too thin to call
// a real tendency -- topBreakdown() below now tags each breakdown entry (and
// the overall filtered set) with this same floor as a machine-readable
// `trusted` boolean, instead of relying purely on the system prompt telling
// Claude to "say so if it's under ~5." Groups under 2 are still dropped
// entirely (not even 1 real snap is noise, not a pattern); 2-4 are kept but
// marked untrusted so Claude can still surface a genuinely rare event while
// being honest about the sample size.
const SAMPLE_FLOOR = 5;
const MIN_BREAKDOWN_COUNT = 2;

// Retry/backoff for transient Anthropic API failures (rate limits, 5xx, the
// "overloaded" 529) -- a single dropped request used to immediately 502 the
// whole coach-facing answer. Never retries a 4xx (bad request, auth failure,
// etc.) since those won't succeed on retry.
const MAX_API_RETRIES = 2;
const RETRY_BASE_MS = 400;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function backoffMs(attempt) {
  return RETRY_BASE_MS * (2 ** attempt) + Math.floor(Math.random() * 200);
}

const TOOL_DEF = {
  name: 'query_plays',
  description:
    "Filter the opponent's raw charted plays and count them, grouped by a chosen field. " +
    'This is the ONLY reliable way to get an exact count/percentage -- always use this tool ' +
    'for any question about frequency, rate, or "most common X" rather than eyeballing the ' +
    'static context. You may call it multiple times (e.g. once per situation you want to ' +
    'compare, or to sweep a range like field position in chunks) before giving your final ' +
    'answer. A VOCABULARY LEGEND of every real value seen in this team\'s charted data is ' +
    'included at the end of the system prompt -- always check it before guessing a spelling ' +
    'for front/formation/coverage/personnel/scheme/etc; a filter value that doesn\'t exactly ' +
    "match the legend will silently return 0 matches, which is NOT the same as \"they never do " +
    'this" -- if a filtered count comes back 0 for a value you typed from memory, re-check the ' +
    'legend before concluding anything.',
  input_schema: {
    type: 'object',
    properties: {
      down: { type: 'string', enum: ['1', '2', '3', '4', 'any'], description: "Down, or 'any'." },
      distance: {
        type: 'string',
        enum: ['short', 'med', 'long', 'any'],
        description: "short = 1-3 yds, med = 4-6 yds, long = 7+ yds, or 'any'. For an exact " +
          "distance (e.g. '3rd and 1' specifically), use distance_exact instead and leave this 'any'.",
      },
      distance_exact: {
        type: 'string',
        description: "Exact yards-to-go as a string (e.g. '1' for 3rd-and-1), or 'any'. Overrides " +
          "the distance bucket when set to something other than 'any'.",
      },
      situation: {
        type: 'string',
        enum: ['any', 'nd', 'cd', 'rz', '2min', '4min'],
        description:
          "nd = Normal Downs (1st/2nd, excludes Red Zone/2-min/4-min), " +
          "cd = Conversion Downs (3rd/4th, excludes Red Zone/2-min/4-min), " +
          'rz = Red Zone (inside the 20), 2min = end of half/game 2-minute situations, ' +
          "4min = 4-minute offense, or 'any' for every play with no situational filter.",
      },
      snap_type: {
        type: 'string',
        enum: ['run', 'pass', 'any'],
        description: "Whether the play was a run or a pass call, or 'any' for both.",
      },
      scheme: {
        type: 'string',
        description:
          "The play's run-scheme/pass-concept-family tag (e.g. 'GAP', 'MZ', 'TZ', 'DRAW', " +
          "'PAP', 'QK GAME', 'WZ'). Check the vocabulary legend for the real list. 'any' for no filter.",
      },
      front: {
        type: 'string',
        description: "Defensive front -- matches either the exact raw call (e.g. 'CUB') or the " +
          "front FAMILY (e.g. 'EVEN', 'ODD', 'BEAR', 'KC', 'OVERLOAD') -- check the legend for both " +
          "lists. Use a family name to combine all its raw variants in one count. 'any' for no filter.",
      },
      formation: {
        type: 'string',
        description: "Offensive formation -- matches either the exact raw formation name (e.g. " +
          "'TRIPS') or the formation GROUP (e.g. '3X1 11P', '2X2 12P', 'EMPTY', 'UNB') -- check the " +
          "legend for both lists. Use a group to combine all formations sharing that alignment. 'any' for no filter.",
      },
      personnel: { type: 'string', description: "Offensive personnel grouping (e.g. '11', '12'), or 'any'." },
      coverage: {
        type: 'string',
        description: "Coverage call -- matches either the exact raw call (e.g. '3 WEAK') or the " +
          "coverage FAMILY (e.g. '1HZ', 'QTRS', 'ZERO') -- check the legend for both lists. 'any' for no filter.",
      },
      blitz_call: {
        type: 'string',
        description: "Exact raw blitz call name (e.g. 'BAM', 'MISSILE INSIDE'), for isolating a " +
          "specific blitz. 'any' for no filter (includes non-blitz snaps too).",
      },
      pressure_direction: {
        type: 'string',
        enum: ['I', 'F', 'D', 'B', 'any'],
        description: 'I = Internal, F = Field, D = Double Edge, B = Boundary.',
      },
      rusher_count: { type: 'string', description: "Number of rushers as a string, e.g. '5', or 'any'." },
      hash: { type: 'string', enum: ['L', 'M', 'R', 'any'] },
      field_position_min: {
        type: 'string',
        description:
          "Lower bound (inclusive) of field position, on a 1-99 scale where 1 = the " +
          "opponent's goal line and 99 = our own goal line (so 50 is exactly midfield). " +
          "E.g. to answer 'once we cross the 50' (i.e. we're in opponent territory), use " +
          "min='1', max='49'. Red Zone is 1-20 (use situation='rz' instead, it's equivalent). " +
          "Use 'any' for no lower bound.",
      },
      field_position_max: {
        type: 'string',
        description: "Upper bound (inclusive) of field position on the same 1-99 scale as field_position_min, or 'any' for no upper bound.",
      },
      success: {
        type: 'string',
        enum: ['successful', 'unsuccessful', 'any'],
        description:
          "Whether the play was 'successful' by down-and-distance standard (1st down needs 40%+ " +
          "of distance gained, 2nd needs 50%+, 3rd/4th need the full conversion), if yardage data " +
          "is available for this team. 'any' for no filter.",
      },
      yards_min: { type: 'string', description: "Minimum yards gained (inclusive), or 'any'. For explosive plays specifically, prefer the explosive filter below (it already applies the correct run-vs-pass threshold)." },
      yards_max: { type: 'string', description: "Maximum yards gained (inclusive), e.g. '0' or negative for stuffed/lost-yardage plays, or 'any'." },
      explosive: {
        type: 'string',
        enum: ['explosive', 'non_explosive', 'any'],
        description:
          "Whether the play was explosive by this team's standard: a RUN gaining 12+ yards, or " +
          "a PASS gaining 15+ yards (the two thresholds are applied automatically based on the " +
          "play's own run/pass type -- you don't need to combine this with snap_type or yards_min " +
          "yourself). Use this for any question about explosive/chunk/big plays. 'any' for no filter.",
      },
      dl_technique: {
        type: 'string',
        description: "Defensive line 3-technique alignment relative to the play's strength: " +
          "'TO' (to the call), 'AWAY' (away from the call), or 'PST' (post). Only populated on " +
          "charted plays where a confident alignment was recorded. 'any' for no filter.",
      },
      dl_technique_side: {
        type: 'string',
        description: "Defensive line 3-technique side: 'BND' (boundary) or 'FLD' (field). Only " +
          "populated for run-defense-charted plays. 'any' for no filter.",
      },
      de_reaction_poa: {
        type: 'string',
        description: "Defensive end's point-of-attack reaction on run plays (e.g. 'BOX', 'DENT', " +
          "'SPILL'). Only populated for run-defense-charted plays. 'any' for no filter.",
      },
      de_reaction_read: {
        type: 'string',
        description: "Defensive end's read-and-react technique on run plays (e.g. 'SIT', " +
          "'SQUEEZE', 'SURF', 'UPFIELD', 'MESH CHARGE'). Only populated for run-defense-charted " +
          "plays. 'any' for no filter.",
      },
      opponent: {
        type: 'string',
        description: "Filter to plays charted against one specific opponent (e.g. 'Cincinnati') -- " +
          "matches as a case-insensitive substring against the charted game label, so a partial " +
          "name works. Check the legend for the real list of opponents charted. 'any' for every " +
          "opponent combined (the normal case -- most questions should leave this 'any' unless the " +
          "coach names a specific team).",
      },
      breakdown_by: {
        type: 'string',
        enum: [
          'covFam', 'cov', 'frontFam', 'front', 'blitz', 'pers', 'fbi', 'hash',
          'form', 'formGrp', 'rp', 'playType', 'rush', 'dlTech', 'dlTechSide',
          'deReactPOA', 'deReactRead', 'opp',
        ],
        description:
          'Which field to group the matching plays by and count. covFam/cov = coverage family / ' +
          'raw call, frontFam/front = front family / raw call, blitz = raw blitz call, pers = ' +
          'personnel, fbi = pressure direction, hash = hash location, form/formGrp = formation ' +
          'name / group, rp = run vs pass, playType = scheme/concept tag, rush = rusher count, ' +
          'dlTech/dlTechSide = DL 3-tech alignment/side, deReactPOA/deReactRead = DE reaction ' +
          'type, opp = opponent.',
      },
    },
    required: [
      'down', 'distance', 'distance_exact', 'situation', 'snap_type', 'scheme',
      'front', 'formation', 'personnel', 'coverage', 'blitz_call',
      'pressure_direction', 'rusher_count', 'hash', 'field_position_min',
      'field_position_max', 'success', 'yards_min', 'yards_max', 'explosive',
      'dl_technique', 'dl_technique_side', 'de_reaction_poa', 'de_reaction_read',
      'opponent', 'breakdown_by',
    ],
  },
};

// 2026-09-28, task #796: a SECOND, independent tool over a SECOND raw dataset
// -- Matt's PFF play-by-play export (pff-data/*.parquet), which turned out to
// cover exactly one charted Pitt defensive game (Week 1 vs Miami OH, 693
// defender-snap rows across 31 players -- see build_pitt_pff_defense.py for
// how it was built and why it's scoped this narrowly). This is individual-
// defender PFF-graded EVENT data (missed tackles, pressures, sacks, coverage
// results, per-snap grade) -- a different axis entirely from query_plays'
// hand-charted SCHEME data. Deliberately a separate tool/dataset rather than
// merged into queryPlays, since the two have almost no overlapping fields and
// merging them would just make both harder to filter correctly.
const PFF_TOOL_DEF = {
  name: 'query_pff_defense',
  description:
    "Filter Pitt's PFF-graded individual-defender snap data and see event counts (missed " +
    'tackles, pressures, sacks, coverage results, etc.) and average PFF grade, optionally broken ' +
    'down per player, per position, or per game. Use this for any question about an INDIVIDUAL ' +
    'DEFENDER\'S performance, reliability, or grade (e.g. "who misses the most tackles", "how ' +
    'does the SS grade in coverage", "which LB generates the most pressure", "how did the ' +
    'defense play against Syracuse") -- query_plays cannot answer these since it has no ' +
    'player-level grading. This tool currently covers every Pitt game charted so far this season ' +
    '(check the games list returned by an unfiltered call, or filter to a single game with the ' +
    "game parameter) -- still always note it's PFF-charted data, not the full hand-charted " +
    'scheme dataset. If this tool errors or says no data is available, that means this team has ' +
    'no PFF individual-defender data loaded (only Pitt does right now) -- fall back to ' +
    'query_plays and the static context instead.',
  input_schema: {
    type: 'object',
    properties: {
      player: { type: 'string', description: "Exact player name (e.g. 'Josh Guerrier'), or 'any' for every defender." },
      position: { type: 'string', description: "Position code as charted by PFF (e.g. 'FS', 'RLB', 'DLT'), or 'any'." },
      down: { type: 'string', enum: ['1', '2', '3', '4', 'any'] },
      run_pass: { type: 'string', enum: ['run', 'pass', 'any'], description: "Whether the play was a run or pass, or 'any'." },
      game: {
        type: 'string',
        description: "Exact game label to isolate one game (matches as a case-insensitive " +
          "substring, e.g. 'Syracuse' or 'Week 3'), or 'any' for every game charted so far " +
          "combined. Check a broad unfiltered call's returned game list for the real labels " +
          "before filtering to a specific one.",
      },
      event: {
        type: 'string',
        enum: [
          'any', 'tackle', 'assist', 'missed_tackle', 'pressure', 'hurry', 'sack', 'hit',
          'interception', 'batted_pass', 'penalty', 'catch_allowed', 'contested_target',
          'contested_catch', 'stop', 'beaten_by_defender',
        ],
        description: "Only include snaps where this specific event happened (e.g. 'missed_tackle' " +
          "to isolate every missed-tackle snap), or 'any' for no event filter.",
      },
      breakdown_by: {
        type: 'string',
        enum: ['player', 'position', 'game', 'none'],
        description: "Group the matching snaps by player, position, or game and show each " +
          "group's own event counts/avg grade, or 'none' to just get one aggregate total for the " +
          "whole filtered set.",
      },
    },
    required: ['player', 'position', 'down', 'run_pass', 'game', 'event', 'breakdown_by'],
  },
};

const PFF_EVENT_FIELDS = [
  'tackle', 'assist', 'missed_tackle', 'pressure', 'hurry', 'sack', 'hit', 'interception',
  'batted_pass', 'penalty', 'catch_allowed', 'contested_target', 'contested_catch', 'stop',
  'beaten_by_defender',
];

// Sums each boolean event field across a group of PFF snap-rows and averages
// the PFF `grade` field (when present) -- mirrors statsFor()'s "only report a
// stat when real data backs it" convention, never a misleading 0.
function pffEventSummary(rows) {
  const out = { n: rows.length };
  for (const f of PFF_EVENT_FIELDS) {
    const c = rows.filter((r) => r[f] === true).length;
    if (c > 0) out[f] = c;
  }
  const graded = rows.filter((r) => typeof r.grade === 'number');
  if (graded.length) {
    out.avg_grade = Math.round((graded.reduce((s, r) => s + r.grade, 0) / graded.length) * 10) / 10;
  }
  out.trusted = rows.length >= SAMPLE_FLOOR;
  return out;
}

function groupPffBy(rows, field) {
  const groups = {};
  for (const r of rows) {
    const v = r[field];
    if (!v) continue;
    (groups[v] = groups[v] || []).push(r);
  }
  return Object.entries(groups)
    .filter(([, group]) => group.length >= MIN_BREAKDOWN_COUNT)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([label, group]) => ({ label, ...pffEventSummary(group) }));
}

// field param: 'player' | 'pos' | 'game' -- game breakdown uses the same
// grouping helper since each row's `game` string is already a clean label.
function pffGroupField(breakdownBy) {
  if (breakdownBy === 'player') return 'player';
  if (breakdownBy === 'game') return 'game';
  return 'pos';
}

function runPffDefenseTool(input, pffDefensePlays) {
  if (!Array.isArray(pffDefensePlays) || !pffDefensePlays.length) {
    return { error: 'No PFF individual-defender data is loaded for this team. Fall back to query_plays and the static context.' };
  }
  const gamesCharted = Array.from(new Set(pffDefensePlays.map((r) => r.game).filter(Boolean)));
  const filtered = pffDefensePlays.filter((r) => {
    if (input.player !== 'any' && r.player !== input.player) return false;
    if (input.position !== 'any' && r.pos !== input.position) return false;
    if (input.down !== 'any' && String(r.down) !== input.down) return false;
    if (input.run_pass === 'run' && r.rp !== 'R') return false;
    if (input.run_pass === 'pass' && r.rp !== 'P') return false;
    if (input.game && input.game !== 'any') {
      if (!r.game || !r.game.toLowerCase().includes(String(input.game).toLowerCase())) return false;
    }
    if (input.event !== 'any' && r[input.event] !== true) return false;
    return true;
  });

  const result = {
    note: 'PFF-charted individual-defender data, covering every Pitt game charted so far this ' +
      'season (see games_charted below) -- still a different, narrower dataset than the full ' +
      'hand-charted scheme data in query_plays. `trusted` (n >= ' + SAMPLE_FLOOR + ') follows the ' +
      'same floor as query_plays; treat an untrusted count as too thin to call a real tendency.',
    games_charted: gamesCharted,
    total_matching_snaps: filtered.length,
  };
  if (input.breakdown_by === 'none') {
    Object.assign(result, pffEventSummary(filtered));
  } else {
    result.breakdown_field = input.breakdown_by;
    result.breakdown = groupPffBy(filtered, pffGroupField(input.breakdown_by));
  }
  return result;
}

const FBI_LABELS = { I: 'Internal', F: 'Field', D: 'Dbl Edge', B: 'Boundary' };
const EXCLUDE_ND_CD = new Set(['2 EOG', '2 EOH', '4']);

function isRedZone(p) { return p.fp != null && p.fp >= 1 && p.fp <= 20; }
function isND(p) { return (p.down === 1 || p.down === 2) && !EXCLUDE_ND_CD.has(p.sit) && !isRedZone(p); }
function isCD(p) { return (p.down === 3 || p.down === 4) && !EXCLUDE_ND_CD.has(p.sit) && !isRedZone(p); }
function pct(n, d) { return d ? Math.round((n / d) * 100) : 0; }

// D.queryPlays stores field position as a SIGNED scoreboard-style yard line
// (-49 to +49): positive = opponent territory (fp=1 is their goal line, fp=49
// is just shy of midfield), negative = our own territory (fp=-1 is pinned on
// our own 1, fp=-49 is just shy of midfield). That's convenient for isRedZone
// above (1-20 works directly) but not how coaches phrase field-position
// questions ("once we cross the 50", "backed up inside our own 10"). This
// converts to the same unsigned 1-99 "distance to opponent's goal line" scale
// the rest of the site (RZ/Bible tabs, compute_situational.py's field_pos())
// already uses, so field_position_min/max filters line up with that.
function unsignedFieldPos(p) {
  if (p.fp == null) return null;
  return p.fp > 0 ? p.fp : (100 - Math.abs(p.fp));
}

// Run/pass-aware explosive-play threshold: 12+ yards on a run, 15+ on a pass.
// Computed on the fly from p.rp/p.yards rather than requiring a precomputed
// field, so it works as soon as yardage data exists on a play regardless of
// how the data pipeline built it.
function isExplosive(p) {
  if (p.yards == null || !p.rp) return null;
  if (p.rp === 'R') return p.yards >= 12;
  if (p.rp === 'P') return p.yards >= 15;
  return null;
}

function matchesFilters(p, f) {
  if (f.down !== 'any' && String(p.down) !== f.down) return false;
  if (f.distance === 'short' && !(p.dist != null && p.dist >= 1 && p.dist <= 3)) return false;
  if (f.distance === 'med' && !(p.dist != null && p.dist >= 4 && p.dist <= 6)) return false;
  if (f.distance === 'long' && !(p.dist != null && p.dist >= 7)) return false;
  if (f.distance_exact !== 'any' && String(p.dist) !== f.distance_exact) return false;
  if (f.situation === 'nd' && !isND(p)) return false;
  if (f.situation === 'cd' && !isCD(p)) return false;
  if (f.situation === 'rz' && !isRedZone(p)) return false;
  if (f.situation === '2min' && !(p.sit === '2 EOG' || p.sit === '2 EOH')) return false;
  if (f.situation === '4min' && p.sit !== '4') return false;
  if (f.snap_type === 'run' && p.rp !== 'R') return false;
  if (f.snap_type === 'pass' && p.rp !== 'P') return false;
  if (f.scheme !== 'any' && p.playType !== f.scheme) return false;
  // front/formation/coverage each match against EITHER the raw call or its
  // family/group tag, so Claude can filter by a family name (e.g. 'EVEN',
  // '3X1 11P', 'QTRS') to combine all its raw variants in one count, without
  // needing a second dedicated filter parameter.
  if (f.front !== 'any' && p.front !== f.front && p.frontFam !== f.front) return false;
  if (f.formation !== 'any' && p.form !== f.formation && p.formGrp !== f.formation) return false;
  if (f.coverage !== 'any' && p.cov !== f.coverage && p.covFam !== f.coverage) return false;
  if (f.blitz_call !== 'any' && p.blitz !== f.blitz_call) return false;
  if (f.personnel !== 'any' && p.pers !== f.personnel) return false;
  if (f.pressure_direction !== 'any' && p.fbi !== f.pressure_direction) return false;
  if (f.rusher_count !== 'any' && String(p.rush) !== f.rusher_count) return false;
  if (f.hash !== 'any' && p.hash !== f.hash) return false;
  if (f.field_position_min !== 'any' || f.field_position_max !== 'any') {
    const ufp = unsignedFieldPos(p);
    if (ufp == null) return false;
    if (f.field_position_min !== 'any' && ufp < Number(f.field_position_min)) return false;
    if (f.field_position_max !== 'any' && ufp > Number(f.field_position_max)) return false;
  }
  if (f.success !== 'any') {
    if (p.success == null) return false;
    const wasSuccessful = p.success === 'Y' || p.success === true;
    if (f.success === 'successful' && !wasSuccessful) return false;
    if (f.success === 'unsuccessful' && wasSuccessful) return false;
  }
  if (f.yards_min !== 'any' && !(p.yards != null && p.yards >= Number(f.yards_min))) return false;
  if (f.yards_max !== 'any' && !(p.yards != null && p.yards <= Number(f.yards_max))) return false;
  if (f.explosive !== 'any') {
    const exp = isExplosive(p);
    if (exp == null) return false;
    if (f.explosive === 'explosive' && !exp) return false;
    if (f.explosive === 'non_explosive' && exp) return false;
  }
  if (f.dl_technique !== 'any' && p.dlTech !== f.dl_technique) return false;
  if (f.dl_technique_side !== 'any' && p.dlTechSide !== f.dl_technique_side) return false;
  if (f.de_reaction_poa !== 'any' && p.deReactPOA !== f.de_reaction_poa) return false;
  if (f.de_reaction_read !== 'any' && p.deReactRead !== f.de_reaction_read) return false;
  if (f.opponent !== 'any') {
    if (!p.opp || !p.opp.toLowerCase().includes(String(f.opponent).toLowerCase())) return false;
  }
  return true;
}

// Yardage-derived efficiency stats (avg yards, success rate, explosive rate)
// for a given set of plays -- used BOTH for the overall filtered-set totals
// AND, critically, for each individual breakdown group below, so a question
// like "which run scheme has been most productive" can be answered from a
// SINGLE tool call (breakdown_by=playType) instead of requiring one call per
// scheme value. Omits a stat entirely when no play in the group has that
// data charted, rather than reporting a misleading 0.
function statsFor(rows) {
  const out = {};
  const withYards = rows.filter((p) => p.yards != null);
  if (withYards.length) {
    out.avg_yards_gained = Math.round((withYards.reduce((s, p) => s + p.yards, 0) / withYards.length) * 10) / 10;
    const explosiveCount = withYards.filter((p) => isExplosive(p) === true).length;
    out.explosive_play_pct = pct(explosiveCount, withYards.length);
  }
  const withSuccess = rows.filter((p) => p.success != null);
  if (withSuccess.length) {
    const successCount = withSuccess.filter((p) => p.success === 'Y' || p.success === true).length;
    out.success_rate_pct = pct(successCount, withSuccess.length);
  }
  return out;
}

// Mirrors advance-scout.html's qeTopBreakdown() for count/pct (min-count
// floor of MIN_BREAKDOWN_COUNT, blanks/UNKNOWN dropped) so this tool can
// never report a number the shipped Stat Explorer UI would disagree with --
// but ALSO attaches each group's own avg_yards_gained/success_rate_pct/
// explosive_play_pct (see statsFor above), which qeTopBreakdown does not do,
// since this tool's job is answering "which X is most productive/efficient"
// in one shot. Each entry also now carries `trusted` (n >= SAMPLE_FLOOR, the
// same floor the rest of the site uses) so Claude has a machine-readable
// signal instead of having to eyeball `count` against a number in the prompt.
function topBreakdown(rows, field, minCount) {
  const groups = {};
  for (const r of rows) {
    const v = r[field];
    if (!v || v === 'UNKNOWN' || v === 'NAN' || v === '?') continue;
    (groups[v] = groups[v] || []).push(r);
  }
  const total = rows.length;
  return Object.entries(groups)
    .filter(([, group]) => group.length >= minCount)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([label, group]) => ({
      label: field === 'fbi' ? (FBI_LABELS[label] || label) : label,
      count: group.length,
      pct: pct(group.length, total),
      trusted: group.length >= SAMPLE_FLOOR,
      ...statsFor(group),
    }));
}

function runQueryPlaysTool(input, queryPlays) {
  const filtered = queryPlays.filter((p) => matchesFilters(p, input));
  const breakdown = topBreakdown(filtered, input.breakdown_by, MIN_BREAKDOWN_COUNT);
  const result = {
    total_matching_plays: filtered.length,
    trusted: filtered.length >= SAMPLE_FLOOR,
    breakdown_field: input.breakdown_by,
    note: `breakdown only includes values charted ${MIN_BREAKDOWN_COUNT}+ times (blank/uncharted ` +
      'values excluded); total_matching_plays and each breakdown entry carry a `trusted` boolean ' +
      `(true when n >= ${SAMPLE_FLOOR}, the same small-sample floor the rest of this site uses) -- ` +
      'when trusted is false, treat that count/pct as too thin to call a real tendency and say so ' +
      'plainly rather than stating it with confidence, even if it looks like a clean number. Each ' +
      'breakdown entry also carries its OWN avg_yards_gained/success_rate_pct/explosive_play_pct ' +
      'when yardage data exists for that group, so you can directly compare which value is most ' +
      'productive/efficient without a separate call per value',
    breakdown,
    ...statsFor(filtered),
  };
  return result;
}

// Computes, once per request, the real set of values this team's charted
// data actually uses for every free-text/vocabulary-dependent field. This
// gets embedded in the system prompt so Claude never has to guess a
// spelling (e.g. 'OVER SH' vs 'over front') -- it can look up the real
// charted vocabulary before filtering, instead of silently getting a
// 0-match result and mistaking that for "they never do this."
const VOCAB_FIELDS = [
  ['front', 'Defensive fronts (raw calls)'],
  ['frontFam', 'Defensive front families'],
  ['form', 'Offensive formations (raw names)'],
  ['formGrp', 'Formation groups'],
  ['pers', 'Personnel groupings'],
  ['cov', 'Coverage calls (raw)'],
  ['covFam', 'Coverage families'],
  ['blitz', 'Blitz calls'],
  ['playType', 'Run-scheme/pass-concept tags'],
  ['dlTech', 'DL 3-tech alignment values'],
  ['dlTechSide', 'DL 3-tech side values'],
  ['deReactPOA', 'DE point-of-attack reaction values'],
  ['deReactRead', 'DE read-and-react values'],
  ['opp', 'Opponents charted'],
];

function buildVocabLegend(queryPlays) {
  const lines = [];
  for (const [field, label] of VOCAB_FIELDS) {
    const vals = new Set();
    for (const p of queryPlays) {
      const v = p[field];
      if (v && v !== 'UNKNOWN' && v !== 'NAN' && v !== '?') vals.add(v);
    }
    if (vals.size) lines.push(`${label} (${field}): ${Array.from(vals).sort().join(', ')}`);
  }
  return lines.join('\n');
}

function corsHeaders(origin, allowedOrigin) {
  const h = {
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-app-secret',
    'Access-Control-Max-Age': '86400',
  };
  if (origin === allowedOrigin) h['Access-Control-Allow-Origin'] = allowedOrigin;
  return h;
}

// Retries a transient failure (network error, 429 rate limit, 5xx, or
// Anthropic's 529 "overloaded") up to MAX_API_RETRIES times with exponential
// backoff before giving up -- previously a single blip here immediately 502'd
// the coach's whole question. A 4xx client error (bad request, auth failure)
// is never retried since trying again won't change the outcome.
async function callClaude(env, system, messages, tools) {
  let lastErr;
  for (let attempt = 0; attempt <= MAX_API_RETRIES; attempt++) {
    let resp;
    try {
      resp = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-api-key': env.ANTHROPIC_API_KEY,
          'anthropic-version': ANTHROPIC_VERSION,
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 1536,
          system,
          tools,
          messages,
        }),
      });
    } catch (networkErr) {
      lastErr = networkErr;
      if (attempt < MAX_API_RETRIES) {
        await sleep(backoffMs(attempt));
        continue;
      }
      throw networkErr;
    }

    if (resp.ok) return resp.json();

    const errText = await resp.text();
    lastErr = new Error(`Anthropic API error ${resp.status}: ${errText}`);
    const transient = resp.status === 429 || resp.status === 529 || resp.status >= 500;
    if (transient && attempt < MAX_API_RETRIES) {
      await sleep(backoffMs(attempt));
      continue;
    }
    throw lastErr;
  }
  throw lastErr;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const allowedOrigin = env.ALLOWED_ORIGIN || '';

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(origin, allowedOrigin) });
    }
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const cors = corsHeaders(origin, allowedOrigin);
    if (origin !== allowedOrigin) {
      return new Response(JSON.stringify({ error: 'Origin not allowed.' }), {
        status: 403,
        headers: { 'content-type': 'application/json', ...cors },
      });
    }

    const appSecret = request.headers.get('x-app-secret') || '';
    if (!env.APP_SECRET || appSecret !== env.APP_SECRET) {
      return new Response(JSON.stringify({ error: 'Unauthorized.' }), {
        status: 401,
        headers: { 'content-type': 'application/json', ...cors },
      });
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify({ error: 'Invalid JSON body.' }), {
        status: 400,
        headers: { 'content-type': 'application/json', ...cors },
      });
    }

    const { question, teamData, queryPlays, pffDefensePlays, teamLabel } = body || {};
    if (!question || typeof question !== 'string') {
      return new Response(JSON.stringify({ error: 'Missing "question".' }), {
        status: 400,
        headers: { 'content-type': 'application/json', ...cors },
      });
    }
    if (!Array.isArray(queryPlays) || !queryPlays.length) {
      return new Response(JSON.stringify({ error: 'Missing or empty "queryPlays".' }), {
        status: 400,
        headers: { 'content-type': 'application/json', ...cors },
      });
    }

    const vocabLegend = buildVocabLegend(queryPlays);
    const hasPffData = Array.isArray(pffDefensePlays) && pffDefensePlays.length > 0;
    const tools = hasPffData ? [TOOL_DEF, PFF_TOOL_DEF] : [TOOL_DEF];

    const system =
      `You are a football scouting assistant embedded in a coach-only VT Offense Hub page for ` +
      `${teamLabel || 'the opponent'}. Answer the coach's question using ONLY: (1) the static ` +
      `context JSON below (depth chart, roster, matchups, coach-written notes, run families, ` +
      `man/zone splits, stat leaders), (2) the query_plays tool for anything involving a ` +
      `count, rate, percentage, "most common", success rate, or explosive-play claim about ` +
      `play-level SCHEME tendencies (formations/fronts/coverages/blitzes across the full season)` +
      (hasPffData
        ? `, and (3) the query_pff_defense tool for anything about an INDIVIDUAL DEFENDER'S grade ` +
          `or events (missed tackles, pressures, sacks, coverage results) -- query_plays has no ` +
          `player-level data, query_pff_defense has no scheme data, use whichever one the question ` +
          `is actually about. query_pff_defense's results always include a games_charted list -- ` +
          `use it to know how many games back the numbers, and mention that scope when relevant`
        : '') +
      `. Never invent or estimate a number -- if it requires counting plays, ` +
      `call the tool.\n\n` +
      `HOW TO BE THOROUGH:\n` +
      `- Many real questions need more than one tool call to answer well -- e.g. a "how does X ` +
      `change by down" question needs one call per down; a field-position trend needs a sweep in ` +
      `chunks (e.g. 1-20, 21-40, 41-60...); a "compare A vs B" question needs one call per side. ` +
      `Make as many calls as the question actually needs (up to the iteration limit) before ` +
      `answering -- don't settle for a single generic call when the question implies a comparison ` +
      `or a breakdown across a dimension.\n` +
      `- Before typing any front/formation/coverage/personnel/scheme/opponent value into a filter, ` +
      `check the VOCABULARY LEGEND at the end of this prompt for the real charted spelling. A ` +
      `filter value that doesn't exactly match the legend returns 0 matches -- that is NOT the ` +
      `same thing as "they never do this," it usually means a typo or a value that isn't in the ` +
      `data. If a filtered count comes back 0 and you're not sure why, re-check the legend (or ` +
      `retry with the family/group version of the field) before telling the coach they never do ` +
      `something.\n` +
      `- Small samples are common with charted data. total_matching_plays and every breakdown ` +
      `entry carry a \`trusted\` boolean (true only when n >= ${SAMPLE_FLOOR}, the site's own ` +
      `small-sample floor). When trusted is false, say so explicitly rather than presenting that ` +
      `percentage as if it were a reliable tendency -- e.g. "only 2 plays charted here, too small ` +
      `to call a tendency" beats a misleadingly precise "50%." Never state an untrusted number ` +
      `with the same confidence as a trusted one.\n` +
      `- query_plays automatically returns avg_yards_gained / explosive_play_pct / ` +
      `success_rate_pct for the OVERALL filtered set, AND separately for EACH individual entry in ` +
      `the breakdown array, whenever yardage data exists -- use these instead of re-deriving them ` +
      `yourself, and mention them when they're relevant to the question even if not explicitly asked ` +
      `(a coach asking about a blitz almost always also wants to know if it's actually effective). ` +
      `Critically: for any "which X is most productive/effective/efficient" question (most productive ` +
      `run scheme, most efficient formation, best coverage to bring pressure from, etc.), do NOT loop ` +
      `calling the tool once per value of X -- set breakdown_by to that field and make ONE call; each ` +
      `returned breakdown entry already carries its own avg_yards_gained/success_rate_pct so you can ` +
      `directly compare them and name a winner without extra round-trips.\n\n` +
      `Keep answers tight and coach-readable: lead with the direct answer, then supporting ` +
      `numbers. If the data genuinely doesn't support an answer, say so plainly rather than ` +
      `guessing.\n\n` +
      `STATIC CONTEXT:\n${JSON.stringify(teamData || {})}\n\n` +
      `VOCABULARY LEGEND (the real values charted for this team -- use these exact spellings):\n${vocabLegend}`;

    let messages = [{ role: 'user', content: question }];

    try {
      for (let i = 0; i < MAX_TOOL_ITERATIONS; i++) {
        const resp = await callClaude(env, system, messages, tools);

        if (resp.stop_reason !== 'tool_use') {
          const text = (resp.content || [])
            .filter((b) => b.type === 'text')
            .map((b) => b.text)
            .join('\n')
            .trim();
          return new Response(JSON.stringify({ answer: text || '(no answer produced)' }), {
            headers: { 'content-type': 'application/json', ...cors },
          });
        }

        messages.push({ role: 'assistant', content: resp.content });
        const toolResults = [];
        for (const block of resp.content) {
          if (block.type !== 'tool_use') continue;
          let result;
          try {
            if (block.name === 'query_pff_defense') {
              result = runPffDefenseTool(block.input, pffDefensePlays);
            } else {
              result = runQueryPlaysTool(block.input, queryPlays);
            }
          } catch (e) {
            result = { error: String(e) };
          }
          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: JSON.stringify(result),
          });
        }
        messages.push({ role: 'user', content: toolResults });
      }

      return new Response(
        JSON.stringify({ answer: "I wasn't able to settle on an answer within the tool-call limit -- try rephrasing or narrowing the question." }),
        { headers: { 'content-type': 'application/json', ...cors } },
      );
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e && e.message || e) }), {
        status: 502,
        headers: { 'content-type': 'application/json', ...cors },
      });
    }
  },
};
