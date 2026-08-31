#!/usr/bin/env python3
"""
Computes the "Install Tracker" for one Season Practices day -- a rep-count
and defensive-look log of every play call run in Team-vs-scout-team periods
during a game-week practice, WITHOUT the normal efficiency/grade stats self-
scout otherwise shows. Per Matt's 2026-08-27 direction: starting with VMI
week, in-season Team periods are run against a scout-team defense coached to
mimic that week's opponent, and he wants to verify (a) gameplanned plays are
getting reps, and (b) they're getting reps against the right looks -- NOT the
normal concept/player efficiency breakdown Fall Camp practices get. The CSV
for these practices is charted minimally on purpose: just Play Call + the
scout defense's Front/Blitz Name/Coverage (no Full Concept/Run Family/PERS/
grades -- those columns are blank), confirmed against VMI BONUS WEDNESDAY
DATA.csv (2026-08-27 upload, 41 rows, 3 periods, all "vs VMI D-SQUAD").

Usage: python3 compute_install_tracker.py <csv_path> <delimiter>
Prints one JSON object to stdout: {"n": int, "periods": [...], "calls": [...]}
"""
import csv, json, re, sys
from collections import defaultdict

def load(path, delim):
    """Same dedupe-by-Name convention as compute_situational.py's load().

    Also drops rows where NOTHING was actually charted -- Play Call,
    pff_RUNPASS, and pff_PASSRESULT all blank. These are scripted-but-
    never-run reps (the period ended before that Play # was reached), not
    real snaps. First seen in VMI BONUS SATURDAY DATA.csv (2026-08-31
    upload): 19/48 rows were entirely blank across every column (no Play
    Call, no notes, no result, no gain) -- confirmed by inspection, not
    just a missing field. Without this filter they'd show up as a bogus
    "(blank call)" entry inflating that day's install n by 19. VMI BONUS
    WEDNESDAY DATA.csv had zero such rows, so this filter is a no-op there."""
    with open(path, newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=delim)
        rows = [row for row in r if (row.get('Name') or '').strip()]
        rows = [row for row in rows if (
            (row.get('Play Call') or '').strip()
            or (row.get('pff_RUNPASS') or '').strip()
            or (row.get('pff_PASSRESULT') or '').strip()
        )]
    seen = {}
    for row in rows:
        key = row['Name'].strip()
        if key not in seen:
            seen[key] = row
    return list(seen.values())

def norm(v):
    return (v or '').strip()

# Matches e.g. "26-08-26 09. OFF TEAM 1 - NORMAL DOWNS vs VMI D-SQUAD IC, Play 001"
# -> captures "09. OFF TEAM 1 - NORMAL DOWNS vs VMI D-SQUAD IC"
NAME_PERIOD_RE = re.compile(r'^\S+\s+(.*?),\s*Play\s*\d+\s*$')

def period_label(name):
    m = NAME_PERIOD_RE.match(norm(name))
    if not m:
        return 'Unlabeled Period'
    label = m.group(1).strip()
    # Drop the leading period-sequence number ("09. ") -- not meaningful
    # outside the original script order, just clutter here.
    label = re.sub(r'^\d+\.\s*', '', label)
    return label

def compute_install(rows):
    total = len(rows)
    if total == 0:
        return None

    period_c = defaultdict(int)
    call_groups = defaultdict(list)

    for r in rows:
        call = norm(r.get('Play Call')) or '(blank call)'
        period = period_label(r.get('Name'))
        period_c[period] += 1
        call_groups[call].append({
            "period": period,
            "front": norm(r.get('Front')),
            "blitz": norm(r.get('Blitz Name')),
            "coverage": norm(r.get('Coverage')),
            "down": norm(r.get('pff_DOWN')),
            "distance": norm(r.get('pff_DISTANCE')),
        })

    calls = [
        {"call": call, "n": len(reps), "reps": reps}
        for call, reps in sorted(call_groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]
    periods = [
        {"label": label, "n": n}
        for label, n in sorted(period_c.items(), key=lambda kv: -kv[1])
    ]

    return {"n": total, "periods": periods, "calls": calls}

def aggregate_installs(installs):
    """Merge multiple per-day install dicts (as returned by compute_install)
    into one combined view -- used for a game-week's "All Practices" pill
    once a week has more than one charted day."""
    total = 0
    period_c = defaultdict(int)
    call_groups = defaultdict(list)
    for inst in installs:
        if not inst:
            continue
        total += inst['n']
        for p in inst['periods']:
            period_c[p['label']] += p['n']
        for c in inst['calls']:
            call_groups[c['call']].extend(c['reps'])
    calls = [
        {"call": call, "n": len(reps), "reps": reps}
        for call, reps in sorted(call_groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]
    periods = [
        {"label": label, "n": n}
        for label, n in sorted(period_c.items(), key=lambda kv: -kv[1])
    ]
    return {"n": total, "periods": periods, "calls": calls}

def main():
    path, delim = sys.argv[1], sys.argv[2]
    delim = '\t' if delim == 'tab' else delim
    rows = load(path, delim)
    result = compute_install(rows)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
