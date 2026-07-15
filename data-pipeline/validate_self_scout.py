#!/usr/bin/env python3
"""
validate_self_scout.py -- run this after ANY edit to self-scout.html's baked
JSON data, before committing/pushing. It catches every bug class we hit
building the Skelly/Team/Combined rep-filter for Spring 2026 + Fall Camp:

  1. JSON syntax errors in `const SPRING_VARIANTS = {...}` and any
     `var <PERIOD>_DATA = {...}` blob (FALL_DATA, INSEASON_DATA, ...).
  2. JS syntax errors in the page's largest <script> block (requires `node`
     on PATH).
  3. HTML well-formedness.
  4. The "both-or-neither" rule: a run_sub/pass_sub sub-breakdown must
     either have BOTH keys or NEITHER. Seeing only one means a play that
     was 100% run or 100% pass got a redundant/misleading sub-breakdown.
  5. Known-bad WARP entry names -- protection calls (6MAN, 5MAN) and
     run-scheme/category abbreviations (WZ, TZ, GAP, MZ, RAP, MVMT,
     SCREEN, QG) should never appear as a WARP play name. If a NEW one
     shows up that isn't obviously a real play-call name, don't guess --
     ask Matt before excluding or keeping it (see README.md).
  6. WARP-total consistency: PW_DATA.warp.total.n (and each tempo
     procedure's total.n) must equal the sum of its own entries, and must
     be <= pass_ov.n <= overall.n. A mismatch here means `total` was
     computed over the wrong row set again.

Usage:
  python3 validate_self_scout.py path/to/self-scout.html
Exits non-zero (and prints every problem found) if anything fails.
"""
import json, re, subprocess, sys, tempfile
from html.parser import HTMLParser

BAD_WARP_NAMES = {'6MAN', '5MAN', 'RAP', 'MVMT', 'SCREEN', 'WZ', 'TZ', 'GAP', 'MZ', 'QG'}


def extract_js_object(html, prefix):
    start = html.find(prefix)
    if start == -1:
        return None
    start += len(prefix)
    depth = 0
    started = False
    for j in range(start, len(html)):
        c = html[j]
        if c == '{':
            depth += 1
            started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                return json.loads(html[start:j + 1])
    return None


def check_html(html, problems):
    class P(HTMLParser):
        def error(self, msg):
            problems.append(f"HTML parse error: {msg}")
    P().feed(html)


def check_node_syntax(html, problems):
    scripts = re.findall(r'<script(?:(?!src)[^>])*>(.*?)</script>', html, re.S)
    if not scripts:
        return
    biggest = max(scripts, key=len)
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write(biggest)
        path = f.name
    try:
        r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"JS syntax error in largest <script> block:\n{r.stderr}")
    except FileNotFoundError:
        problems.append("WARNING: `node` not found on PATH, skipped JS syntax check.")


def both_or_neither(path_label, e, problems):
    hb = ('run_sub' in e) and ('pass_sub' in e)
    he = ('run_sub' in e) or ('pass_sub' in e)
    if he and not hb:
        problems.append(f"both-or-neither violation at {path_label}: has only one of run_sub/pass_sub -> {e}")


def check_spring_variants(sv, problems):
    for variant, vdata in sv.items():
        d = vdata.get('D', {})
        rd = vdata.get('RUN_DATA', {})
        pw = vdata.get('PW_DATA', {})

        for fam in rd.get('families', []):
            both_or_neither(f"{variant}/RUN_DATA.families/{fam.get('name')}", fam, problems)
            for sc in fam.get('schemes', []):
                both_or_neither(f"{variant}/RUN_DATA.families/{fam.get('name')}/schemes/{sc.get('name')}", sc, problems)

        for e in d.get('warp', []):
            both_or_neither(f"{variant}/D.warp/{e.get('name')}", e, problems)
            if e.get('name') in BAD_WARP_NAMES:
                problems.append(f"BAD WARP NAME in {variant}/D.warp: '{e.get('name')}' -- protection/category tag, not a real play name")

        warp = pw.get('warp', {})
        ts = warp.get('total_section', [])
        for e in ts:
            both_or_neither(f"{variant}/PW_DATA.warp.total_section/{e.get('name')}", e, problems)
            if e.get('name') in BAD_WARP_NAMES:
                problems.append(f"BAD WARP NAME in {variant}/PW_DATA.warp.total_section: '{e.get('name')}'")

        sum_ts = sum(e['n'] for e in ts)
        tot = warp.get('total', {}).get('n')
        pass_n = d.get('pass_ov', {}).get('n')
        overall_n = d.get('overall', {}).get('n')
        if tot is not None and tot != sum_ts:
            problems.append(f"WARP TOTAL MISMATCH in {variant}: warp.total.n={tot} but sum(total_section)={sum_ts}")
        if tot is not None and pass_n is not None and tot > pass_n:
            problems.append(f"WARP TOTAL TOO BIG in {variant}: warp.total.n={tot} > pass_ov.n={pass_n}")
        if pass_n is not None and overall_n is not None and pass_n > overall_n:
            problems.append(f"pass_ov.n ({pass_n}) > overall.n ({overall_n}) in {variant} -- impossible")

        for pk, plist in warp.get('procedures', {}).items():
            psum = sum(p['n'] for p in plist.get('plays', []))
            ptot = plist.get('total', {}).get('n')
            if ptot is not None and ptot != psum:
                problems.append(f"WARP PROCEDURE TOTAL MISMATCH in {variant}/{pk}: total.n={ptot} but sum(plays)={psum}")
            for e in plist.get('plays', []):
                both_or_neither(f"{variant}/PW_DATA.warp.procedures/{pk}/{e.get('name')}", e, problems)
                if e.get('name') in BAD_WARP_NAMES:
                    problems.append(f"BAD WARP NAME in {variant}/PW_DATA.warp.procedures/{pk}: '{e.get('name')}'")


def check_period_data(label, fd, problems):
    days = fd.get('days', [])
    for day in days:
        for variant, vdata in day.get('variants', {}).items():
            for fam in vdata.get('run_families', []):
                both_or_neither(f"{label}/{day.get('key')}/{variant}/run_families/{fam.get('name')}", fam, problems)
                for sc in fam.get('schemes', []):
                    both_or_neither(f"{label}/{day.get('key')}/{variant}/run_families/{fam.get('name')}/schemes/{sc.get('name')}", sc, problems)
            for e in vdata.get('warp_plays', []):
                if e.get('name') in BAD_WARP_NAMES:
                    problems.append(f"BAD WARP NAME in {label}/{day.get('key')}/{variant}/warp_plays: '{e.get('name')}'")
            pn = vdata.get('n_pass'); on = vdata.get('n')
            if pn is not None and on is not None and pn > on:
                problems.append(f"n_pass ({pn}) > n ({on}) in {label}/{day.get('key')}/{variant} -- impossible")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    html_path = sys.argv[1]
    html = open(html_path, encoding='utf-8').read()
    problems = []

    check_html(html, problems)
    check_node_syntax(html, problems)

    sv = extract_js_object(html, 'const SPRING_VARIANTS = ')
    if sv is not None:
        check_spring_variants(sv, problems)
    else:
        print("(no SPRING_VARIANTS found -- skipping spring checks)")

    for var_name in ['FALL_DATA', 'INSEASON_DATA']:
        fd = extract_js_object(html, f'var {var_name} = ')
        if fd is not None:
            check_period_data(var_name, fd, problems)

    if problems:
        print(f"\n{len(problems)} PROBLEM(S) FOUND:\n")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    else:
        print("All checks passed: JSON/JS/HTML valid, no both-or-neither violations, no bad WARP names, WARP totals internally consistent.")


if __name__ == '__main__':
    main()
