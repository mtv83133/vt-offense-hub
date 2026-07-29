const fs = require('fs');
const { JSDOM } = require('jsdom');

let html = fs.readFileSync('/tmp/vt-offense-hub/_source/self-scout.html', 'utf8');
html = html.replace(
  /<script src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/Chart\.js\/[^"]*"><\/script>/,
  `<script>window.Chart = class Chart { constructor(){} destroy(){} update(){} }; window.Chart.defaults = { font: {}, color: '' };</script>`
);

const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  resources: 'usable',
  pretendToBeVisual: true,
  url: 'https://mtv83133.github.io/vt-offense-hub/self-scout.html',
  virtualConsole: (() => {
    const { VirtualConsole } = require('jsdom');
    const vc = new VirtualConsole();
    vc.on('jsdomError', (e) => errors.push('jsdomError: ' + e.message));
    return vc;
  })(),
});
const { window } = dom;
window.addEventListener('error', (e) => errors.push('window error: ' + (e.error ? e.error.message : e.message)));

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  await wait(400);
  const results = [];
  const assert = (cond, msg) => results.push({ ok: !!cond, msg });

  // 1. Spring team variant should have OL lineups with plays baked in
  const springOl = window.eval('SPRING_VARIANTS.team.PLAYER_DATA.ol_lineups');
  assert(Array.isArray(springOl) && springOl.length > 0, `Spring team ol_lineups is a non-empty array (n=${springOl && springOl.length})`);
  assert(springOl.every(o => Array.isArray(o.plays)), 'Every spring OL combo has a plays array');
  assert(springOl.some(o => o.plays.length > 0), 'At least one spring OL combo has non-empty plays');
  assert(springOl.every(o => o.plays.every(p => p.type === 'RUN')), 'All baked OL combo plays are tagged RUN');

  // 2. Spring skelly variant should have zero OL lineups (no run plays in skelly CSV rows)
  const skellyOl = window.eval('SPRING_VARIANTS.skelly.PLAYER_DATA.ol_lineups');
  assert(Array.isArray(skellyOl) && skellyOl.length === 0, `Spring skelly ol_lineups is empty (n=${skellyOl && skellyOl.length})`);

  // 3. Render _buildOLLineups directly and inspect output HTML
  const rendered = window.eval('_buildOLLineups(SPRING_VARIANTS.team.PLAYER_DATA.ol_lineups)');
  assert(typeof rendered === 'string' && rendered.length > 0, '_buildOLLineups returns non-empty HTML string');
  assert(rendered.includes('lineup-ol-table'), 'Rendered output still includes the summary table');
  assert(rendered.includes('Run Plays'), 'Table header renamed to "Run Plays"');
  assert(rendered.includes('Top Run Plays'), 'Rendered output includes the new Top Run Plays section');
  assert(rendered.includes('lp-play-badge run'), 'Rendered output includes RUN play badges');
  assert(rendered.includes('lineup-card'), 'Rendered output uses lineup-card styling for combo detail blocks');

  // 4. Sanity: parse the rendered HTML into a detached container and check card count <= 5
  const div = window.document.createElement('div');
  div.innerHTML = rendered;
  const cards = div.querySelectorAll('.lineup-card');
  assert(cards.length > 0 && cards.length <= 5, `Detail card count is between 1 and 5 (found ${cards.length})`);
  const playRows = div.querySelectorAll('.lp-play-row');
  assert(playRows.length > 0, `Found play rows inside cards (${playRows.length})`);

  // 5. Empty input should return empty string (no blank section)
  const emptyRendered = window.eval('_buildOLLineups([])');
  assert(emptyRendered === '', 'Empty ol_lineups input renders nothing');
  const skellyRendered = window.eval('_buildOLLineups(SPRING_VARIANTS.skelly.PLAYER_DATA.ol_lineups)');
  assert(skellyRendered === '', 'Skelly (no run OL data) renders nothing');

  // 6. Fall camp fall_1 data sanity
  const fallTeamOl = window.eval("FALL_DATA.days[0].variants.team.ol_lineups");
  assert(Array.isArray(fallTeamOl) && fallTeamOl.length > 0, `Fall camp team ol_lineups non-empty (n=${fallTeamOl && fallTeamOl.length})`);
  assert(fallTeamOl.every(o => Array.isArray(o.plays)), 'Every fall camp OL combo has a plays array');

  for (const r of results) console.log((r.ok ? 'PASS' : 'FAIL') + ' - ' + r.msg);
  const fails = results.filter(r => !r.ok);
  console.log(`\n${results.length - fails.length}/${results.length} checks passed.`);
  if (errors.length) {
    console.log(`${errors.length} runtime errors:`);
    errors.forEach(e => console.log('  ' + e));
  } else {
    console.log('No runtime/console errors captured.');
  }
  process.exit(fails.length || errors.length ? 1 : 0);
}
main().catch(e => { console.error('TEST THREW:', e); process.exit(1); });
