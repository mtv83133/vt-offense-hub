const fs = require('fs');
const { JSDOM } = require('jsdom');

const path = '/tmp/vt-offense-hub/_source/advance-scout.html';
let html = fs.readFileSync(path, 'utf8');

// Replace the external Chart.js CDN script tag with a lightweight in-page stub
// (jsdom can't render canvas / we don't need real charts for this logic test).
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
  // Give the page's own load/init scripts (setTimeout-based initCharts etc.) a moment to run.
  await wait(300);

  const results = [];
  const assert = (cond, msg) => results.push({ ok: !!cond, msg });

  // Basic sanity: page loaded, key globals exist
  assert(typeof window.eval('TEAMS_DATA') === 'object', 'TEAMS_DATA exists');
  assert(typeof window.selectTeam === 'function', 'selectTeam() exists');
  assert(typeof window.show === 'function', 'show() exists');
  assert(typeof window.switchTmMode === 'function', 'switchTmMode() exists');
  assert(typeof window.switchTmSub === 'function', 'switchTmSub() exists');
  assert(typeof window.tmStab === 'function', 'tmStab() exists');
  assert(typeof window.switchStab === 'function', 'switchStab() exists');
  const deepSections = window.eval('DEEP_SECTIONS');
  assert(deepSections && deepSections.includes('tm') && deepSections.includes('fm'), 'DEEP_SECTIONS includes tm and fm');

  for (const team of ['MARYLAND', 'VMI', 'ODU']) {
    window.selectTeam(team);
    await wait(80);
    assert(window.eval('currentTmMode') === 'eog', `${team}: currentTmMode resets to eog after selectTeam`);

    // Show the 2 MIN and 4 MIN sections
    window.show('tm');
    await wait(80);
    const tmSec = window.document.getElementById('sec-tm');
    assert(tmSec && tmSec.classList.contains('on'), `${team}: sec-tm becomes visible via show('tm')`);

    window.show('fm');
    await wait(80);
    const fmSec = window.document.getElementById('sec-fm');
    assert(fmSec && fmSec.classList.contains('on'), `${team}: sec-fm becomes visible via show('fm')`);

    // Back to tm to test the EOG/EOH toggle
    window.show('tm');
    await wait(80);
    const eogWrap = window.document.getElementById('tm-eog-wrap');
    const eohWrap = window.document.getElementById('tm-eoh-wrap');
    assert(eogWrap && eohWrap, `${team}: tm-eog-wrap and tm-eoh-wrap both exist in DOM`);
    assert(eogWrap && eogWrap.classList.contains('on'), `${team}: EOG wrap starts active`);
    assert(eohWrap && !eohWrap.classList.contains('on'), `${team}: EOH wrap starts inactive`);

    window.switchTmMode('eoh');
    await wait(30);
    assert(window.eval('currentTmMode') === 'eoh', `${team}: switchTmMode('eoh') updates currentTmMode`);
    assert(eohWrap.classList.contains('on'), `${team}: EOH wrap active after switchTmMode('eoh')`);
    assert(!eogWrap.classList.contains('on'), `${team}: EOG wrap inactive after switchTmMode('eoh')`);

    window.switchTmMode('eog');
    await wait(30);

    // Sub-tab switching (formations/fronts/coverage/blitz) within tm
    for (const sub of ['formations', 'fronts', 'coverage', 'blitz']) {
      window.tmStab(sub);
      await wait(20);
    }
    results.push({ ok: true, msg: `${team}: tmStab cycled through all 4 sub-tabs without throwing` });

    // fm sub-tabs via switchStab
    window.show('fm');
    await wait(50);
    for (const sub of ['formations', 'fronts', 'coverage', 'blitz']) {
      window.switchStab('fm', sub);
      await wait(20);
    }
    results.push({ ok: true, msg: `${team}: switchStab('fm', ...) cycled through all 4 sub-tabs without throwing` });

    // Data-layer checks
    const D = window.eval('TEAMS_DATA')[team];
    const fields = ['tmEogFormationChart','tmEogFrontsDonut','tmEogCovDonut','tmEohFormationChart','tmEohFrontsDonut','tmEohCovDonut','fmFormationChart','fmFrontsDonut','fmCovDonut'];
    for (const f of fields) {
      assert(D[f] && typeof D[f] === 'object', `${team}: TEAMS_DATA.${f} present`);
    }
  }

  // Field-position secondary-breakpoint callout: should stay hidden for all
  // 3 currently-loaded teams (the analysis legitimately found nothing
  // significant beyond the RZ for any of them this season), and should show
  // up correctly if TEAMS_DATA did have a value (synthetic check, since
  // real data has none right now).
  for (const team of ['MARYLAND', 'VMI', 'ODU']) {
    window.selectTeam(team);
    await wait(50);
    const cb = window.document.getElementById('field-breakpoint-callout');
    assert(cb && cb.style.display === 'none', `${team}: field-breakpoint callout hidden when no data`);
  }
  window.eval("TEAMS_DATA.MARYLAND.fieldBreakpoint = 'TEST BREAKPOINT NARRATIVE';");
  window.selectTeam('MARYLAND');
  await wait(50);
  const cbShown = window.document.getElementById('field-breakpoint-callout');
  assert(cbShown && cbShown.style.display !== 'none' && cbShown.innerHTML.includes('TEST BREAKPOINT NARRATIVE'),
    'MARYLAND: field-breakpoint callout shows when TEAMS_DATA has a value');
  window.eval("TEAMS_DATA.MARYLAND.fieldBreakpoint = null;");

  // ODU 4 MIN should be an empty bucket (n=0, no '4' tag in their data) -- check placeholder text present
  window.selectTeam('ODU');
  await wait(80);
  window.show('fm');
  await wait(80);
  const fmBody = window.document.getElementById('sec-fm-body');
  const hasPlaceholder = fmBody && /No .*data charted yet/i.test(fmBody.textContent);
  assert(hasPlaceholder, 'ODU: 4 MIN tab shows "no data yet" placeholder (0 tagged plays)');

  // Report
  const fails = results.filter(r => !r.ok);
  for (const r of results) {
    console.log((r.ok ? 'PASS' : 'FAIL') + ' - ' + r.msg);
  }
  console.log(`\n${results.length - fails.length}/${results.length} checks passed.`);
  if (errors.length) {
    console.log(`\n${errors.length} runtime error(s) captured:`);
    errors.forEach(e => console.log('  ' + e));
  } else {
    console.log('\nNo runtime/console errors captured.');
  }
  process.exit(fails.length || errors.length ? 1 : 0);
}

main().catch(e => { console.error('TEST SCRIPT THREW:', e); process.exit(1); });
