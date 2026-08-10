#!/usr/bin/env python3
"""
build_qb_grades.py -- joins the QB coaches' per-play grading CSV (Footwork/
Eyes/Decision/Timing/Accuracy/Notes) with the main practice CSV for the same
day, by row order (both files are 1:1, same play order, verified against
Fall Camp Practice #1: zero mismatches on '#'/Play Call across 36 rows).

Produces one flat list of per-rep grade records, each tagged with the
concept name and WARP-play name it belongs to (using the SAME concept_name()
/ WARP_EXCLUDE logic as build_period_variant.py, so drill-downs in the QB
profile line up with the Pass Concepts / WARP Plays tables elsewhere on the
site) and which period (TEAM/SKELLY) it happened in, so the QB profile can
respect the same rep-filter as the rest of self-scout.html.

Aggregation (category averages, per-concept/per-warp breakdowns, cumulative-
across-days totals) happens client-side in JS from these raw records --
there are too many concept/warp/category/day-range combinations to
usefully pre-aggregate in Python.

Usage:
  python3 build_qb_grades.py <grades_csv> <practice_csv> <day_key> [output_dir]
Example:
  python3 build_qb_grades.py "QB DATA FALL CAMP #1.csv" "FALL CAMP #1 DATA.csv" fall_1 ./output/
"""
import csv, json, re, sys, os

if len(sys.argv) < 4:
    print("Usage: python3 build_qb_grades.py <grades_csv> <practice_csv> <day_key> [output_dir]")
    sys.exit(1)

grades_path = sys.argv[1]
practice_path = sys.argv[2]
day_key = sys.argv[3]
out_dir = sys.argv[4] if len(sys.argv) > 4 else './output'
os.makedirs(out_dir, exist_ok=True)

with open(grades_path, encoding='utf-8-sig') as f:
    grade_rows = list(csv.DictReader(f))
with open(practice_path, encoding='utf-8-sig') as f:
    practice_rows = list(csv.DictReader(f))

if len(grade_rows) != len(practice_rows):
    print(f"ERROR: row count mismatch -- grades has {len(grade_rows)} rows, practice has "
          f"{len(practice_rows)} rows. These must be 1:1 (same plays, same order). Aborting "
          f"rather than guessing at a join.")
    sys.exit(1)

# ── same helpers/rules as build_period_variant.py -- keep in sync ───────
def period_of(r):
    comp = r.get('COMPETITIVE', '').strip().upper()
    if comp == 'SKELLY': return 'SKELLY'
    if comp: return 'TEAM'
    name = r.get('Name', '')
    if re.search(r'\bSKELLY\b', name, re.I): return 'SKELLY'
    if re.search(r'\bTEAM\b', name, re.I): return 'TEAM'
    return 'TEAM'

# 6MAN/5MAN/QG are protection/tempo tags, not route concepts -- kept in sync
# with build_period_variant.py's concept_name(). A rep tagged only with one
# of these in Play, with no Primary/Reset or Full Concept charted, is a
# charting gap, not a legitimate standalone "concept" (confirmed with Matt
# after "6MAN" wrongly showed up as its own concept in the QB Profile's By
# Concept table, Fall Camp Practice #2 data) -- flagged instead of silently
# using the bare tag as the concept name.
_PROTECTION_ONLY_TAGS = {'6MAN', '5MAN', 'QG'}
def concept_name(r):
    primary = r['Primary'].strip(); reset = r['Reset'].strip()
    if primary: return primary + (' / ' + reset if reset else '')
    full = r['Full Concept'].strip()
    if full: return full
    play = r['Play'].strip()
    if play.upper() in _PROTECTION_ONLY_TAGS:
        return 'NEEDS CONCEPT (' + play.upper() + ')'
    return play or '(unknown)'

WARP_EXCLUDE = {'RAP', 'MVMT', 'SCREEN', '6MAN', '5MAN', 'QG', 'WZ', 'TZ', 'GAP', 'MZ'}
def warp_name(r):
    # Kept in sync with build_period_variant.py's warp_map: WARP plays
    # include named/coded run-play calls (e.g. HEDGEHOG, BLOODHOUND), not
    # just pass reps -- no longer gated on Run Family being blank. But
    # WZ/TZ/GAP/MZ are generic run-family shorthand, not real play names,
    # so they stay excluded same as RAP/MVMT/SCREEN/6MAN/5MAN/QG.
    nm = r['Play'].strip() or '(unknown)'
    if nm in WARP_EXCLUDE: return None
    return nm

# Kept in sync with build_period_variant.py's is_pass()/is_eff(): is_pass is
# the "was this rep actually a pass attempt" signal (Run Family blank), used
# by the QB profile's per-concept table (added after Fall Camp Practice #3)
# to decide which graded reps count toward a concept's REPS/EFF%/COMPOSITE
# row -- same definition already used for WARP Plays' comp%/route-thrown
# columns (isp=[r for r in items if is_pass(r)]), so an RPO's pass-look rep
# (e.g. CYCLONE thrown) counts as a pass attempt under its own name/concept,
# while the same play's handoff reps don't show up in that table at all.
# Also excludes PEN/NP rows -- build_period_variant.py drops these entirely
# before computing is_pass there, and unlike that script, build_qb_grades.py
# intentionally does NOT filter PEN rows out of `records` (its row-order join
# needs every row to stay 1:1 with the grading CSV), so this table's own
# is_pass flag has to do that exclusion itself rather than assume it already
# happened.
def is_pass(r):
    # 'NO PLAY' (spelled out, first seen in Fall Camp Practice #4) is the
    # same "No Play" concept as 'NP', just a different export spelling --
    # kept in sync with build_period_variant.py's row-drop filter.
    if r['pff_RUNPASS'].strip().upper() in ('PEN', 'NP', 'NO PLAY'): return False
    return r['Run Family'].strip() == ''
def is_eff(r): return r['Efficient'].strip() == 'Y'

def jint(val):
    if val is None: return None
    s = str(val).strip()
    if s in ('', '-', 'N/A', 'n/a'): return None
    if s[:1] in ('O', 'o'): s = s[1:]
    try: return int(s)
    except: return None

def grade_val(s):
    s = (s or '').strip()
    if s == '': return None
    try: return float(s)
    except: return None

CATEGORIES = ['footwork', 'eyes', 'decision', 'timing', 'accuracy']
CSV_COLS = {'footwork': 'Footwork', 'eyes': 'Eyes', 'decision': 'Decision',
            'timing': 'Timing', 'accuracy': 'Accuracy'}

records = []
skipped_no_qb = 0
for g, p in zip(grade_rows, practice_rows):
    # Trust the grading CSV's own QB column (clean int, no 'O' prefix) as the
    # primary source; fall back to the practice row's pff_QB if it's blank.
    jersey = jint(g.get('QB')) if jint(g.get('QB')) is not None else jint(p.get('pff_QB'))
    if jersey is None:
        skipped_no_qb += 1
        continue
    rec = {
        'num': g.get('#', '').strip(),
        'qb': jersey,
        'period': period_of(p),
        'concept': concept_name(p),
        'warp': warp_name(p),
        'play_call': p.get('Play Call', '').strip(),
        'notes': g.get('Notes', '').strip(),
        'is_pass': is_pass(p),
        'eff': is_eff(p),
    }
    for key in CATEGORIES:
        rec[key] = grade_val(g.get(CSV_COLS[key]))
    records.append(rec)

if skipped_no_qb:
    print(f"WARNING: {skipped_no_qb} row(s) had no resolvable QB jersey (blank in both the "
          f"grading CSV's QB column and the practice CSV's pff_QB) and were skipped.")

data = {'day_key': day_key, 'records': records}
out_path = os.path.join(out_dir, f'{day_key}_qb_grades.json')
with open(out_path, 'w') as f:
    json.dump(data, f)

qb_counts = {}
for r in records:
    qb_counts[r['qb']] = qb_counts.get(r['qb'], 0) + 1
print(f"Wrote {out_path}: {len(records)} graded reps across {len(qb_counts)} QB(s): {qb_counts}")

_needs_concept = [r for r in records if (r['concept'] or '').startswith('NEEDS CONCEPT')]
if _needs_concept:
    print(f"WARNING: {len(_needs_concept)} graded rep(s) have a protection/tempo-only concept "
          f"({', '.join(sorted(set(r['concept'] for r in _needs_concept)))}) -- flagged instead of "
          f"used as a real concept. Affected reps:")
    for r in _needs_concept:
        print(f"    # {r['num']}  QB {r['qb']}  Play Call='{r['play_call']}'  is_pass={r['is_pass']}")
