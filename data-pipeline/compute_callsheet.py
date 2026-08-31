#!/usr/bin/env python3
"""
Joins a week's CALLSHEET_STRUCTURE (see vmi_callsheet_v1.py) against that
week's aggregated Install Tracker data (compute_install_tracker.py's
all_install, i.e. every rep charted across every practice day that week) to
produce the data behind the Install Tracker's "Callsheet" pill: every
gameplanned play, grouped by category, with how many times (and what % of
the week's total reps) it's actually been called in practice.

Matching is exact (case/whitespace-normalized) against the Play Call field
charted in practice -- a callsheet entry that hasn't been run yet in
practice simply shows 0 reps / 0%, which is exactly the "not installed
enough yet" signal Matt wants this for.

Usage: python3 compute_callsheet.py <callsheet_module_name_without_.py>
Reads the week's all_install JSON from stdin, prints the joined
{"total": int, "categories": [...]} JSON to stdout.
"""
import sys, json, re, importlib

def norm(s):
    return ' '.join((s or '').strip().upper().split())

def strip_dressing(s):
    """Practice CSVs chart the full dressed huddle call, which often carries
    a leading formation/personnel tag (W17, W-27, 11A...) not present on the
    master callsheet's base play name, plus bracketed situational suffixes
    ([ON ORG], [ON QK]). Strip both before comparing to the callsheet."""
    s = re.sub(r'\[.*?\]', '', s)
    s = re.sub(r'^\s*[A-Z]*\d+\S*\s+', '', s)
    return norm(s)

def strip_parens(s):
    return norm(re.sub(r'[()]', '', s))

def build_call_rows(all_install):
    """One row per distinct charted Play Call, with both its cleaned
    (dressing-stripped) form and its raw normalized form, for exact +
    contains + whole-word matching."""
    rows = []
    for c in (all_install or {}).get('calls', []):
        rows.append({"raw": norm(c['call']), "clean": strip_dressing(c['call']), "n": c['n']})
    return rows

def match_warp(name, rows):
    needle = strip_parens(name)
    pat = re.compile(r'(?<!\w)' + re.escape(needle) + r'(?!\w)')
    return sum(r['n'] for r in rows if pat.search(strip_parens(r['raw'])))

def match_dressed(name, rows):
    needle = norm(name)
    total = sum(r['n'] for r in rows if r['clean'] == needle)
    if total:
        return total
    # Fallback for future callsheet wording drift: substring containment.
    return sum(r['n'] for r in rows if needle in r['clean'] or r['clean'] in needle)

def join_play(play, rows, total):
    if play.get('warp'):
        n = match_warp(play['call'], rows)
        pct = round(n / total * 100, 1) if total else 0
        out = {"label": play['label'], "warp": True, "n": n, "pct": pct,
               "calls": [{"dir": None, "call": play['call'], "n": n}]}
    else:
        lt_n = match_dressed(play['lt'], rows)
        rt_n = match_dressed(play['rt'], rows)
        n = lt_n + rt_n
        pct = round(n / total * 100, 1) if total else 0
        out = {"label": play['label'], "warp": False, "n": n, "pct": pct,
               "calls": [{"dir": "LT", "call": play['lt'], "n": lt_n},
                         {"dir": "RT", "call": play['rt'], "n": rt_n}]}
    if play.get('note'):
        out['note'] = play['note']
    return out

def build_callsheet(structure, all_install):
    total = all_install.get('n', 0) if all_install else 0
    rows = build_call_rows(all_install)
    categories = []
    for cat in structure:
        plays = [join_play(p, rows, total) for p in cat['plays']]
        categories.append({"group": cat['group'], "name": cat['name'], "plays": plays})
    return {"total": total, "categories": categories}

def main():
    module_name = sys.argv[1]
    mod = importlib.import_module(module_name)
    all_install = json.load(sys.stdin)
    result = build_callsheet(mod.CALLSHEET_STRUCTURE, all_install)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
