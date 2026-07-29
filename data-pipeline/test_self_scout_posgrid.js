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

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  await wait(400);
  const results = [];
  const assert = (cond, msg) => results.push({ ok: !!cond, msg });

  const posGrid = window.document.getElementById('posGrid');
  assert(posGrid, 'posGrid element exists');
  const cards = posGrid ? posGrid.querySelectorAll('.pos-card') : [];
  assert(cards.length > 0, `posGrid has cards (found ${cards.length})`);

  let hasQ = false;
  let pctSum = 0;
  cards.forEach(c => {
    const badge = c.querySelector('.pos-badge');
    if (badge && badge.textContent.trim() === 'Q') hasQ = true;
    const big = c.querySelector('.big');
    if (big) {
      const v = parseFloat(big.textContent);
      if (!isNaN(v)) pctSum += v;
    }
  });
  assert(!hasQ, 'No QB (Q) card rendered in posGrid');
  assert(pctSum > 95 && pctSum < 105, `Remaining position percentages sum close to 100% (got ${pctSum.toFixed(1)}%)`);

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
