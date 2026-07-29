const fs = require('fs');
const { JSDOM } = require('jsdom');

const path = '/tmp/vt-offense-hub/_source/advance-scout.html';
let html = fs.readFileSync(path, 'utf8');

html = html.replace(
  '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>',
  `<script>
    window.Chart = class Chart {
      constructor(el, config) { this.el = el; this.config = config; this.data = config && config.data; }
      destroy() {}
      update() {}
    };
  </script>`
);

const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  resources: 'usable',
  pretendToBeVisual: true,
  url: 'https://mtv83133.github.io/vt-offense-hub/advance-scout.html',
  virtualConsole: (() => {
    const { VirtualConsole } = require('jsdom');
    const vc = new VirtualConsole();
    vc.on('jsdomError', (e) => errors.push('jsdomError: ' + e.message));
    vc.on('error', (...args) => errors.push('console.error: ' + args.join(' ')));
    return vc;
  })(),
});
const { window } = dom;
function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  await wait(300);
  const results = [];
  const assert = (cond, msg) => results.push({ ok: !!cond, msg });

  const deepSections = window.eval('DEEP_SECTIONS');
  assert(deepSections && deepSections.includes('bible'), 'DEEP_SECTIONS includes "bible"');

  const navBtn = Array.from(window.document.querySelectorAll('.nav')).find(n => n.textContent.includes('Bible'));
  assert(!!navBtn, 'Sidebar has a Bible nav item');

  const secBible = window.document.getElementById('sec-bible');
  assert(!!secBible, 'sec-bible element exists');
  const bodyBible = window.document.getElementById('sec-bible-body');
  assert(!!bodyBible, 'sec-bible-body element exists');

  // show('bible') should toggle visibility without throwing
  window.show('bible');
  await wait(50);
  assert(secBible.classList.contains('on'), "show('bible') marks sec-bible as active");

  // Default (Maryland) content should have real Base/Nickel data, not the empty-state callout
  assert(bodyBible.innerHTML.includes('Base Personnel'), 'MARYLAND (default) Bible body includes Base Personnel card');
  assert(bodyBible.innerHTML.includes('Nickel Personnel'), 'MARYLAND (default) Bible body includes Nickel Personnel card');
  assert(!bodyBible.innerHTML.includes('No defensive personnel data tagged'), 'MARYLAND (default) Bible body is NOT the empty state');

  // ODU: has real (if thin) Base/Nickel data
  window.selectTeam('ODU');
  await wait(80);
  assert(bodyBible.innerHTML.includes('Base Personnel'), 'ODU Bible body includes Base Personnel card');
  assert(bodyBible.innerHTML.includes('Nickel Personnel'), 'ODU Bible body includes Nickel Personnel card');
  assert(!bodyBible.innerHTML.includes('No defensive personnel data tagged'), 'ODU Bible body is NOT the empty state');

  // VMI: no pff_DEFPERSONNEL data at all -> should show the empty state, not a blank/broken table
  window.selectTeam('VMI');
  await wait(80);
  assert(bodyBible.innerHTML.includes('No defensive personnel data tagged'), 'VMI Bible body correctly shows the empty state (no source data)');
  assert(!bodyBible.innerHTML.includes('Base Personnel'), 'VMI Bible body does NOT render a Base Personnel card');

  // Switching back to MARYLAND restores its own Bible content (not stuck on VMI's empty state)
  window.selectTeam('MARYLAND');
  await wait(80);
  assert(bodyBible.innerHTML.includes('Base Personnel'), 'MARYLAND Bible body restores after switching away and back');

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
