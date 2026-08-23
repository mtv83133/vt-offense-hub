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
  const bodyBible = window.document.getElementById('sec-bible-body');
  assert(!!secBible, 'sec-bible element exists');
  assert(!!bodyBible, 'sec-bible-body element exists');

  window.show('bible');
  await wait(50);
  assert(secBible.classList.contains('on'), "show('bible') marks sec-bible as active");

  // MARYLAND (default): full cross-tab set, all sections present, real ND-play counts
  assert(bodyBible.innerHTML.includes('Normal Downs Bible'), 'MARYLAND Bible header shows "Normal Downs Bible"');
  assert(bodyBible.innerHTML.includes('Overall Coverage'), 'MARYLAND: Overall Coverage card present');
  assert(bodyBible.innerHTML.includes('Coverage by Off Personnel'), 'MARYLAND: Coverage by Off Personnel card present');
  assert(bodyBible.innerHTML.includes('Fronts by Off Personnel'), 'MARYLAND: Fronts by Off Personnel card present');
  assert(bodyBible.innerHTML.includes('Coverage by Big Bucket Defensive Personnel'), 'MARYLAND: Big Bucket (Base/Nickel) card present');
  assert(bodyBible.innerHTML.includes('O Personnel vs D Personnel'), 'MARYLAND: O Pers vs D Pers card present (has pff_DEFPERSONNEL)');
  assert(bodyBible.innerHTML.includes('Coverage by Def Personnel'), 'MARYLAND: Coverage by Def Personnel card present');
  assert(bodyBible.innerHTML.includes('Coverage by Pers by Front'), 'MARYLAND: Coverage by Pers by Front card present');
  assert(bodyBible.innerHTML.includes('Coverage to Formation Group'), 'MARYLAND: Coverage to Formation Group card present');
  assert(bodyBible.innerHTML.includes('>3X1<') || bodyBible.innerHTML.includes('3X1'), 'MARYLAND: Formation Group uses 3X1/2X2-style buckets, not named formations');
  assert(/class="bib-pct p-(hot|warm|mild|cool)"/.test(bodyBible.innerHTML), 'MARYLAND: percentage cells carry a conditional-formatting heat class');
  assert(bodyBible.innerHTML.includes('bib-notes'), 'MARYLAND: editable notes textarea present');
  assert(!bodyBible.innerHTML.includes('No Normal Downs data available'), 'MARYLAND is NOT the empty state');

  // ODU: has pff_DEFPERSONNEL too -> same full section set
  window.selectTeam('ODU');
  await wait(80);
  assert(bodyBible.innerHTML.includes('O Personnel vs D Personnel'), 'ODU: O Pers vs D Pers card present');
  assert(bodyBible.innerHTML.includes('Coverage by Big Bucket Defensive Personnel'), 'ODU: Big Bucket (Base/Nickel) card present');
  assert(!bodyBible.innerHTML.includes('No Normal Downs data available'), 'ODU is NOT the empty state');

  // VMI: as of 2026-08-23, the raw CSV was reuploaded with pff_DEFPERSONNEL and FinalForm
  // populated, so the full card set now renders (previously these were correctly omitted
  // when the source data lacked pff_DEFPERSONNEL -- that gap is now closed, not a regression).
  window.selectTeam('VMI');
  await wait(80);
  assert(bodyBible.innerHTML.includes('Overall Coverage'), 'VMI: Overall Coverage still renders (no D-personnel dependency)');
  assert(bodyBible.innerHTML.includes('Coverage by Off Personnel'), 'VMI: Coverage by Off Personnel still renders');
  assert(bodyBible.innerHTML.includes('O Personnel vs D Personnel'), 'VMI: O Pers vs D Pers card now present (source data has pff_DEFPERSONNEL)');
  assert(bodyBible.innerHTML.includes('Coverage by Big Bucket Defensive Personnel'), 'VMI: Big Bucket card now present (source data has pff_DEFPERSONNEL)');
  assert(bodyBible.innerHTML.includes('Coverage by Def Personnel'), 'VMI: Coverage by Def Personnel card now present (source data has pff_DEFPERSONNEL)');
  assert(bodyBible.innerHTML.includes('Coverage to Formation Group'), 'VMI: Coverage to Formation Group card present (now sourced from FinalForm)');

  // Switching back to MARYLAND restores its own full content
  window.selectTeam('MARYLAND');
  await wait(80);
  assert(bodyBible.innerHTML.includes('O Personnel vs D Personnel'), 'MARYLAND Bible body restores after switching away and back');

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
