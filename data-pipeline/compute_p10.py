#!/usr/bin/env python3
"""
Computes the "P&10" (1st Play of Every Drive) tab from a dedicated, purpose-
extracted CSV of just those snaps -- same 59-column schema as the main XOS
per-opponent export, but pre-filtered by the charter to exactly the first
play of each offensive drive (always 1st & 10, so there's no down-distance
splits table the way ND/CD have one).

Per Matt's 2026-08-31 request: "add another section above Normal Downs...
P&10... obviously we do not need the D/D tables since it is all 1st & 10,
first possession of a drive."

Reuses compute_situational.py's compute_bucket() directly for the Formations/
Fronts/Coverage/Blitz breakdown (formation frequency, front family, coverage
family, blitz rate [5+ rushers] + sim/total pressure, 5/6/7-man pressure
schemes, blitz/fronts/coverage by personnel, coverage-on-blitz, front-on-
blitz) -- it already produces everything build_breakdown_section() needs, no
bespoke P&10-only logic required for that part.

Adds two things compute_bucket() doesn't cover, both used by the Quick
Summary pcard bar at the top of the tab (see build_p10_summary() in
gen_html.py):
  - Def personnel (Nickel/Base) split, via the same defpers_bucket() used
    elsewhere -- compute_bucket() doesn't track this since ND/CD show it
    differently (formation-level, not a single headline number).
  - Man/Zone coverage split, via compute_man_zone_bucket() -- also spliced
    into the opponent's manZone dict as a new "p10" key for data-completeness/
    future reuse, even though the P&10 tab surfaces it via its own Quick
    Summary bar rather than the shared top-of-tab MAN_ZONE_CALLOUTS mechanism
    (that mechanism is for ND/CD/RZ/TM/FM; duplicating it here would just be
    a second copy of the same number already in the Quick Summary bar).

Garbage-row handling: the source CSV is expected to be 100% down=1/distance=10
rows plus, in practice, the occasional export artifact (confirmed on VMI's
first P&10 file: one row where a coverage-call tag ("4 CLAMP MAX") ended up
in the Name field with every other column blank -- a column-shift artifact,
not a real play). Filtering to down_of(row)==1 and distance_of(row)==10 drops
that row for free (down_of/distance_of return None on blank), no special-case
needed.

Usage: python3 compute_p10.py <team_key> <csv_path> <delimiter>
Prints one JSON object to stdout: {"team", "totalRowsLoaded", "p10": {...
compute_bucket() fields ..., "defPersonnel": {...}, "manZoneP10": {...}}}
"""
import json, sys

from compute_situational import (
    load, upper, down_of, distance_of, defpers_bucket,
    compute_bucket, compute_man_zone_bucket, topN_pct,
)
from collections import Counter


def compute_def_personnel(rows):
    """Nickel/Base split (defpers_bucket buckets pff_DEFPERSONNEL's DB count:
    5+ DBs = NICKEL, <=4 = BASE; unparseable/blank rows are excluded, same
    convention as everywhere else this helper is used)."""
    c = Counter(defpers_bucket(r) for r in rows)
    nickel = c.get('NICKEL', 0)
    base = c.get('BASE', 0)
    n = nickel + base
    return {
        "n": n, "nickel": nickel, "base": base,
        "nickelPct": round(nickel / n * 100) if n else 0,
        "basePct": round(base / n * 100) if n else 0,
    }


def main():
    team, path, delim = sys.argv[1], sys.argv[2], sys.argv[3]
    delim = '\t' if delim == 'tab' else delim
    rows = load(path, delim)
    # P&10 file is purpose-extracted (already just opening-drive snaps), but
    # filter to real 1st & 10 rows anyway -- drops the 1 known column-shift
    # garbage row for free and guards against any similar artifact in a
    # future opponent's P&10 export.
    p10_rows = [r for r in rows if down_of(r) == 1 and distance_of(r) == 10]

    bucket = compute_bucket(p10_rows)
    bucket["defPersonnel"] = compute_def_personnel(p10_rows)
    bucket["manZoneP10"] = compute_man_zone_bucket(p10_rows)

    result = {
        "team": team,
        "totalRowsLoaded": len(rows),
        "p10RowsUsed": len(p10_rows),
        "p10": bucket,
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
