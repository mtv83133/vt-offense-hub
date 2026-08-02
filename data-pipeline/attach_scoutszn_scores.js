#!/usr/bin/env node
/*
 * attach_scoutszn_scores.js -- fetches a team's ScoutSZN depth chart page
 * (https://scoutszn.com/team/<name>) and attaches {score, scoutszn} fields
 * to the matching players already present in that team's depthChart inside
 * advance-scout.html, matched by exact player name.
 *
 * ScoutSZN grades every FBS prospect 0-10. It does NOT cover FCS programs
 * (e.g. VMI) -- for those opponents this script will report zero matches
 * and leave the depth chart untouched. That's expected, not a bug.
 *
 * This only annotates players ALREADY in depthChart (added by hand from the
 * opponent's roster/depth chart) -- it never adds new players on its own.
 *
 * Usage:
 *   node attach_scoutszn_scores.js <TEAM_KEY> "<ScoutSZN team name>" <path-to-_source-advance-scout.html>
 * Example:
 *   node attach_scoutszn_scores.js ODU "Old Dominion" DO-NOT-SHARE-plaintext-source/advance-scout.html
 *   node attach_scoutszn_scores.js BOSTON_COLLEGE "Boston College" DO-NOT-SHARE-plaintext-source/advance-scout.html
 *
 * The ScoutSZN team name must match their URL slug (see https://scoutszn.com/teams
 * for the exact spelling per school -- usually the plain school name, e.g.
 * "Boston College", "Old Dominion", "Georgia Tech").
 */
const fs = require('fs');

const [, , teamKey, scoutsznName, advPath] = process.argv;
if (!teamKey || !scoutsznName || !advPath) {
  console.error('Usage: node attach_scoutszn_scores.js <TEAM_KEY> "<ScoutSZN team name>" <path-to-_source-advance-scout.html>');
  process.exit(1);
}

async function main() {
  const url = `https://scoutszn.com/team/${encodeURIComponent(scoutsznName)}`;
  const res = await fetch(url);
  if (!res.ok) { console.error(`Fetch failed: ${res.status} ${url}`); process.exit(1); }
  const html = await res.text();

  if (!html.includes('Depth Chart')) {
    console.log(`No depth chart section found for "${scoutsznName}" on ScoutSZN -- likely not covered `
      + `(FCS opponents like VMI aren't graded). Nothing to attach; leaving depthChart untouched.`);
    process.exit(0);
  }

  const scoreMap = {}; // name -> {score, id}

  // Starters, e.g.:
  // <a class="dc-chip" href="/player/12399">
  //   <span class="dc-grade grade-bg-y3">4.2</span>
  //   <span class="dc-body"><span class="dc-nm">Quinn Henicle</span> ...
  const starterRe = /<a class="dc-chip" href="\/player\/(\d+)">\s*<span class="dc-grade[^"]*">([\d.]+)<\/span>[\s\S]*?<span class="dc-nm">([^<]+)<\/span>/g;
  let m;
  while ((m = starterRe.exec(html))) {
    const [, id, score, name] = m;
    scoreMap[name.trim()] = { score: parseFloat(score), id };
  }
  // Reserves, e.g.: <a class="dc-res-chip" href="/player/12476">Jaxon Potter <b class="grade-txt-yellow">3.5</b></a>
  const reserveRe = /<a class="dc-res-chip" href="\/player\/(\d+)">([^<]+?)\s*<b class="grade-txt-\w+">([\d.]+)<\/b><\/a>/g;
  while ((m = reserveRe.exec(html))) {
    const [, id, name, score] = m;
    scoreMap[name.trim()] = { score: parseFloat(score), id };
  }

  console.log(`Parsed ${Object.keys(scoreMap).length} graded players from ScoutSZN for ${scoutsznName}.`);

  // Case/apostrophe-insensitive lookup -- ScoutSZN and our own hand-entered depth
  // chart don't always agree on capitalization (e.g. "DeAndre" vs "Deandre") or
  // curly vs straight apostrophes ("Ja’Mez" vs "Ja'Mez"). Normalize both sides
  // the same way rather than requiring byte-for-byte matches.
  function norm(s) { return s.toLowerCase().replace(/[‘’']/g, "'").trim(); }
  const normMap = {};
  Object.keys(scoreMap).forEach(k => { normMap[norm(k)] = scoreMap[k]; });

  // ---- load advance-scout.html, find <TEAM>_DATA, patch depthChart in place ----
  const advSrc = fs.readFileSync(advPath, 'utf8');
  const marker = `const ${teamKey}_DATA = `;
  const start = advSrc.indexOf(marker);
  if (start === -1) { console.error(`Could not find "${marker}" in ${advPath}`); process.exit(1); }
  let i = start + marker.length;
  if (advSrc[i] !== '{') throw new Error('expected { after marker');
  let depth = 0, inStr = false, strCh = null, esc = false;
  const objStart = i;
  for (; i < advSrc.length; i++) {
    const c = advSrc[i];
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
  const objEnd = i;
  const objText = advSrc.slice(objStart, objEnd);
  const data = (0, eval)('(' + objText + ')');

  if (!data.depthChart) { console.error(`${teamKey}_DATA has no depthChart -- add depth chart entries by hand first.`); process.exit(1); }

  let matched = 0;
  const unmatched = [];
  ['secondary', 'dline'].forEach(grp => {
    (data.depthChart[grp] || []).forEach(posGroup => {
      (posGroup.players || []).forEach(p => {
        const hit = scoreMap[p.name] || normMap[norm(p.name)];
        if (hit) {
          p.score = hit.score;
          p.scoutszn = `https://scoutszn.com/player/${hit.id}`;
          matched++;
        } else {
          unmatched.push(p.name);
        }
      });
    });
  });

  console.log(`Matched ${matched} players.`);
  if (unmatched.length) {
    console.log(`Unmatched (no exact ScoutSZN name match -- check spelling, or the player may be a walk-on `
      + `ScoutSZN hasn't graded): ${unmatched.join(', ')}`);
  }

  // NOTE: this rewrites the object with JSON.stringify (double-quoted keys). If teamKey's
  // const was originally written with unquoted keys (MARYLAND_DATA historically was), this
  // will normalize it to quoted-key style -- functionally identical JS, just a formatting
  // change on first run. Not a bug.
  const newBlob = JSON.stringify(data);
  const newSrc = advSrc.slice(0, objStart) + newBlob + advSrc.slice(objEnd);
  fs.writeFileSync(advPath, newSrc, 'utf8');
  console.log(`Wrote ${advPath}`);
}

main().catch(e => { console.error('THREW:', e); process.exit(1); });
