#!/usr/bin/env python3
"""
Computes ND/CD (exclusion-corrected) + 2MIN-EOG / 2MIN-EOH / 4MIN aggregate
data for one opponent's raw XOS play-by-play CSV, matching the schema
already used in advance-scout.html's TEAMS_DATA (formation tendencies table,
front family donut+table, coverage family donut+table, blitz rate, RB blitz
tendency, down-distance splits, blitz scheme tables).

Rules (per Matt, July 2026):
  - SituationO == 'G' (garbage time) is dropped from EVERY bucket, always.
  - SituationO in {'2 EOG','2 EOH','4'} (End of Game / End of Half / 4-minute
    offense) is excluded from Normal Downs (down 1-2) and Conversion Downs
    (down 3-4), and instead becomes its own bucket.
  - OT and '2 PT' are left alone (not part of this request) -- they still
    count toward ND/CD via normal down bucketing same as before.
  - Blitz definition: non-blank 'Blitz' field (matches build_odu_charts.py's
    HAS_BLITZ = df['Blitz'].ne('')).
  - Blitz pressure DIRECTION (Internal/Field/Dbl Edge/Boundary) comes from
    the 'FBI' column (I/F/D/B, sometimes combo values like 'F/I' -- we take
    the first letter as the primary direction).
  - 5/6/7-Man Pressure Schemes = 'Blitz' field value, grouped by 'RUSHERS'
    count, with % shown relative to the bucket's TOTAL blitz count (not the
    rusher-count subgroup) -- verified against the site's existing baked-in
    numbers, e.g. Maryland ND "5-Man ... (127 plays)" and "6-Man ... (127
    plays)" share the same denominator, and each row's % = count/127.
  - Blitz by Personnel % IS relative to that personnel group's own total
    plays in the bucket (blitz penetration rate per personnel), not to
    overall blitz count.
  - Down-distance splits (Fronts/Coverage/Stunts) use the SAME percent
    denominator as their own bucket (e.g. % of "3rd & 6-10" plays).

Usage: python3 compute_situational.py <team_key> <csv_path> <delimiter>
Prints one JSON object to stdout.
"""
import csv, json, re, sys
from collections import Counter, defaultdict

EXCLUDE_FROM_ND_CD = {'2 EOG', '2 EOH', '4'}
GARBAGE = 'G'

def load(path, delim):
    with open(path, newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=delim)
        return [row for row in r if (row.get('Name') or '').strip()]

def norm(v):
    return (v or '').strip()

def upper(v):
    return norm(v).upper()

def down_of(row):
    try:
        return int(norm(row.get('pff_DOWN')))
    except (ValueError, TypeError):
        return None

def distance_of(row):
    try:
        return int(norm(row.get('pff_DISTANCE')))
    except (ValueError, TypeError):
        return None

def is_blitz(row):
    return bool(norm(row.get('Blitz')))

def is_stunt(row):
    return bool(norm(row.get('Stunt')))

def rushers_of(row):
    return norm(row.get('RUSHERS'))

FBI_ALIASES = {
    'I': 'I', 'F': 'F', 'B': 'B', 'D': 'D',
    'DBL EDGE': 'D', 'DBL-EDGE': 'D', 'DBLE DGE': 'D',  # observed typo variant
    'INTERNAL': 'I', 'FIELD': 'F', 'BOUNDARY': 'B',
}

def fbi_primary(row):
    """First (primary) direction token from the FBI column, normalized via
    FBI_ALIASES -- values are inconsistently charted across teams/sessions
    (single letters 'I'/'F'/'D'/'B', combo values like 'F/I', and occasional
    spelled-out/typo'd variants like 'DBL EDGE/I' or 'DBLE DGE')."""
    v = upper(row.get('FBI'))
    if not v:
        return ''
    first = v.split('/')[0].strip()
    return FBI_ALIASES.get(first, '')

FBI_LABELS = {'I': 'Internal', 'F': 'Field', 'D': 'Dbl Edge', 'B': 'Boundary'}
FBI_CLASS = {'I': 'int', 'F': 'fld', 'D': 'dbl', 'B': 'bnd'}

def parse_formation(row):
    final_form = upper(row.get('FinalForm'))
    grp = upper(row.get('FORMATION GROUP OFF'))
    if not final_form:
        final_form = grp or 'UNKNOWN'
    if grp == 'EMPTY' or final_form == 'EMPTY':
        return 'EMPTY', 'EMPTY'
    m = re.match(r'^(\dX\d)\s+(\S+)$', grp)
    if m:
        recv_set = m.group(1).replace('X', '×')
        pers = m.group(2)
        return f"{final_form} {recv_set}", pers
    if grp:
        return final_form, grp
    return final_form, ''

def topN_pct(counter, total, n, min_count=1):
    out = []
    for name, cnt in counter.most_common():
        if name in ('', 'UNKNOWN', 'NAN') or cnt < min_count:
            continue
        out.append({"label": name, "count": cnt, "pct": round(cnt/total*100) if total else 0})
        if len(out) >= n:
            break
    return out

def compute_pcards(blitz_rows):
    c = Counter(fbi_primary(r) for r in blitz_rows if fbi_primary(r) in FBI_LABELS)
    total = len(blitz_rows)
    cards = []
    for code, cnt in c.most_common():
        cards.append({
            "code": code, "label": FBI_LABELS[code], "cls": FBI_CLASS[code],
            "count": cnt, "pct": round(cnt/total*100) if total else 0,
        })
    return cards

def compute_pressure_schemes(blitz_rows, rusher_count, blitz_total, n=8):
    sub = [r for r in blitz_rows if rushers_of(r) == str(rusher_count)]
    c = Counter(upper(r.get('Blitz')) for r in sub)
    return len(sub), topN_pct(c, blitz_total, n=n)

def is_run_pass(row):
    return upper(row.get('pff_RUNPASS')) in ('R', 'P')

def field_pos(row):
    try:
        return int(norm(row.get('pff_FIELDPOSITION')))
    except (ValueError, TypeError):
        return None

def cover_family_score(inside, outside):
    """Total-variation-style distance between two groups' CoverFamily
    distributions -- same metric the original RZ line-of-demarcation
    finder used. 0 = identical distributions, up to 2 = totally disjoint."""
    n_in, n_out = max(len(inside), 1), max(len(outside), 1)
    c_in = Counter(upper(r.get('CoverFamily')) for r in inside if upper(r.get('CoverFamily')) not in ('', 'UNKNOWN', 'NAN'))
    c_out = Counter(upper(r.get('CoverFamily')) for r in outside if upper(r.get('CoverFamily')) not in ('', 'UNKNOWN', 'NAN'))
    all_c = set(c_in) | set(c_out)
    return sum(abs(c_in.get(c, 0)/n_in - c_out.get(c, 0)/n_out) for c in all_c)

def front_family_score(inside, outside):
    n_in, n_out = max(len(inside), 1), max(len(outside), 1)
    f_in = Counter(upper(r.get('Front Family')) for r in inside if upper(r.get('Front Family')) not in ('', 'UNKNOWN', 'NAN'))
    f_out = Counter(upper(r.get('Front Family')) for r in outside if upper(r.get('Front Family')) not in ('', 'UNKNOWN', 'NAN'))
    all_f = set(f_in) | set(f_out)
    return sum(abs(f_in.get(f, 0)/n_in - f_out.get(f, 0)/n_out) for f in all_f)

def find_rz_line_of_demarcation(rp_rows):
    """Replicates the existing RZ 'line of demarcation' method (generate_report.py)
    so the secondary-breakpoint scanner below knows which yardage is ALREADY
    covered by that analysis and doesn't rediscover it under a new label."""
    best_thresh, best_score = 15, 0
    for thresh in [5, 10, 15, 20, 25]:
        inside = [r for r in rp_rows if field_pos(r) is not None and 1 <= field_pos(r) <= thresh]
        outside = [r for r in rp_rows if field_pos(r) is not None and not (1 <= field_pos(r) <= thresh)]
        if len(inside) < 8 or len(outside) < 10:
            continue
        score = cover_family_score(inside, outside)
        if score > best_score:
            best_score, best_thresh = score, thresh
    if best_score < 0.08:
        for thresh in [30, 35]:
            inside = [r for r in rp_rows if field_pos(r) is not None and 1 <= field_pos(r) <= thresh]
            outside = [r for r in rp_rows if field_pos(r) is not None and not (1 <= field_pos(r) <= thresh)]
            if len(inside) < 8 or len(outside) < 10:
                continue
            score = cover_family_score(inside, outside)
            if score > best_score:
                best_score, best_thresh = score, thresh
    return best_thresh

def find_secondary_breakpoint(rows):
    """Looks for a SECOND field-position 'breaking point' beyond the already-
    identified RZ line of demarcation -- specifically in the range a coach
    would recognize as landmarks (approaching FG range around the +35, out to
    midfield). Deliberately conservative: requires (1) adequate sample size on
    both sides of the candidate line, (2) the candidate to be a genuine LOCAL
    MAXIMUM in the coverage-family shift score (not just a point on the decay
    curve trailing off the RZ effect), (3) that local max to clear a high
    absolute bar (0.45 -- comparable in magnitude to genuine RZ-level shifts,
    which run 0.5-1.0), and (4) a SECOND, independent corroborating signal
    (front-family shift also locally peaking, or a double-digit blitz-rate
    swing) so a single noisy metric can't trigger a false finding on its own.
    Returns None if nothing clears this bar -- callers should not force a
    callout when this returns None.
    """
    rp_rows = [r for r in rows if is_run_pass(r) and field_pos(r) is not None]
    if len(rp_rows) < 60:
        return None

    # The RZ effect's shoulder (elevated but decaying shift score) extends well
    # beyond the single "line of demarcation" yard line itself -- comparing
    # against a boundary that's too shallow lets that decaying tail get
    # mistaken for an independent second breakpoint. Floor the exclusion at
    # +25 (validated against this season's data: shift scores stay clearly
    # RZ-dominated through the +25 for all 3 currently-loaded opponents)
    # regardless of how tight the single-yard-line RZ finding comes back.
    lod = max(find_rz_line_of_demarcation(rp_rows), 25)
    candidates = [t for t in [28, 30, 32, 35, 38, 40, 42, 45, 48, 50] if t > lod]

    results = []
    for thresh in candidates:
        inside = [r for r in rp_rows if lod < field_pos(r) <= thresh]
        outside = [r for r in rp_rows if not (lod < field_pos(r) <= thresh)]
        if len(inside) < 15 or len(outside) < 15:
            results.append(None)
            continue
        cov_score = cover_family_score(inside, outside)
        front_score = front_family_score(inside, outside)
        blitz_in = sum(1 for r in inside if is_blitz(r)) / len(inside)
        blitz_out = sum(1 for r in outside if is_blitz(r)) / len(outside)
        results.append({
            "thresh": thresh, "n_in": len(inside), "n_out": len(outside),
            "covScore": cov_score, "frontScore": front_score,
            "blitzIn": round(blitz_in*100), "blitzOut": round(blitz_out*100),
            "blitzDeltaAbs": abs(blitz_in - blitz_out) * 100,
        })

    best = None
    for i, r in enumerate(results):
        if r is None:
            continue
        prev_score = results[i-1]["covScore"] if i > 0 and results[i-1] else -1
        next_score = results[i+1]["covScore"] if i < len(results)-1 and results[i+1] else -1
        is_local_max = r["covScore"] >= prev_score and r["covScore"] >= next_score
        if not is_local_max or r["covScore"] < 0.45:
            continue
        corroborated = r["frontScore"] >= 0.25 or r["blitzDeltaAbs"] >= 12
        if not corroborated:
            continue
        if best is None or r["covScore"] > best["covScore"]:
            best = r

    if best is None:
        return None

    return {
        "thresh": best["thresh"], "rzLine": lod,
        "nInside": best["n_in"], "nOutside": best["n_out"],
        "covScorePct": round(best["covScore"] * 100),
        "blitzIn": best["blitzIn"], "blitzOut": best["blitzOut"],
    }

def compute_bucket(rows):
    total = len(rows)
    if total == 0:
        return {
            "n": 0, "formations": [], "frontFamily": [], "covFamily": [],
            "blitzPct": 0, "blitzCount": 0, "rbBlitzTendency": [],
            "pcards": [], "pressureFive": [], "pressureFiveN": 0,
            "pressureSix": [], "pressureSixN": 0,
            "pressureSeven": [], "pressureSevenN": 0,
            "blitzByPersonnel": [], "coverageOnBlitz": [], "frontOnBlitz": [],
            "frontsByPersonnel": [], "coverageByPersonnel": [],
        }

    # ---- Formation Tendencies table ----
    form_groups = defaultdict(list)
    for row in rows:
        disp, pers = parse_formation(row)
        form_groups[(disp, pers)].append(row)

    formations = []
    for (disp, pers), grp in sorted(form_groups.items(), key=lambda kv: -len(kv[1])):
        n = len(grp)
        blitz_n = sum(1 for r in grp if is_blitz(r))
        front_c = Counter(upper(r.get('Front')) for r in grp)
        cov_c = Counter(upper(r.get('Coverage')) for r in grp)
        def top1(counter, grp_n):
            for name, cnt in counter.most_common():
                if name in ('', 'UNKNOWN', 'NAN'):
                    continue
                return f"{name} ({round(cnt/grp_n*100)}%)"
            return "—"
        formations.append({
            "formation": disp, "pers": pers, "plays": n,
            "pct": round(n/total*100),
            "blitzPct": round(blitz_n/n*100) if n else 0,
            "topFront": top1(front_c, n),
            "topCoverage": top1(cov_c, n),
        })
    formations = formations[:8]

    # ---- Front Family donut ----
    front_fam_c = Counter(upper(r.get('Front Family')) for r in rows)
    front_family = topN_pct(front_fam_c, total, n=6)

    # ---- Coverage Family donut ----
    cov_fam_c = Counter(upper(r.get('CoverFamily')) for r in rows)
    cov_family = topN_pct(cov_fam_c, total, n=8)

    # ---- Blitz rate + RB tendency ----
    blitz_rows = [r for r in rows if is_blitz(r)]
    blitz_count = len(blitz_rows)
    blitz_pct = round(blitz_count/total*100) if total else 0
    rb_c = Counter(upper(r.get('RBTENDBLITZ')) for r in blitz_rows)
    rb_tendency = topN_pct(rb_c, blitz_count, n=5)

    # ---- Pressure direction cards (Internal/Field/Dbl Edge/Boundary) ----
    pcards = compute_pcards(blitz_rows)

    # ---- 5/6/7-Man Pressure Schemes (% relative to total blitz count) ----
    five_n, pressure_five = compute_pressure_schemes(blitz_rows, 5, blitz_count)
    six_n, pressure_six = compute_pressure_schemes(blitz_rows, 6, blitz_count)
    seven_n, pressure_seven = compute_pressure_schemes(blitz_rows, 7, blitz_count)

    # ---- Personnel groups (shared by Blitz/Fronts/Coverage "by Personnel" tables) ----
    pers_groups = defaultdict(list)
    for r in rows:
        p = upper(r.get('PERS(O)'))
        if p:
            pers_groups[p].append(r)
    pers_sorted = [(pers, grp) for pers, grp in sorted(pers_groups.items(), key=lambda kv: -len(kv[1])) if len(grp) >= 3][:6]

    def top1_label_pct(counter, grp_n):
        for name, cnt in counter.most_common():
            if name in ('', 'UNKNOWN', 'NAN'):
                continue
            return name, round(cnt/grp_n*100) if grp_n else 0
        return None, 0

    # ---- Blitz by Personnel (% relative to that personnel group's own plays) ----
    blitz_by_personnel = []
    for pers, grp in pers_sorted:
        gn = len(grp)
        gb = sum(1 for r in grp if is_blitz(r))
        blitz_by_personnel.append({
            "pers": pers, "plays": gn, "blitz": gb,
            "blitzPct": round(gb/gn*100) if gn else 0,
        })

    # ---- Fronts by Personnel (top front + % within that personnel group) ----
    fronts_by_personnel = []
    for pers, grp in pers_sorted:
        gn = len(grp)
        front_c = Counter(upper(r.get('Front')) for r in grp)
        top_front, top_pct = top1_label_pct(front_c, gn)
        if top_front is None:
            continue
        fronts_by_personnel.append({
            "pers": pers, "plays": gn, "topFront": top_front, "topFrontPct": top_pct,
        })

    # ---- Coverage by Personnel (top coverage + % within that personnel group) ----
    coverage_by_personnel = []
    for pers, grp in pers_sorted:
        gn = len(grp)
        cov_c = Counter(upper(r.get('Coverage')) for r in grp)
        top_cov, top_pct = top1_label_pct(cov_c, gn)
        if top_cov is None:
            continue
        coverage_by_personnel.append({
            "pers": pers, "plays": gn, "topCoverage": top_cov, "topCoveragePct": top_pct,
        })

    # ---- Coverage on Blitz (% relative to total blitz count) ----
    cov_on_blitz_c = Counter(upper(r.get('Coverage')) for r in blitz_rows)
    coverage_on_blitz = topN_pct(cov_on_blitz_c, blitz_count, n=6)

    # ---- Front on Blitz (Front Family, % relative to total blitz count) ----
    front_on_blitz_c = Counter(upper(r.get('Front Family')) for r in blitz_rows)
    front_on_blitz = topN_pct(front_on_blitz_c, blitz_count, n=6)

    return {
        "n": total, "formations": formations,
        "frontFamily": front_family, "covFamily": cov_family,
        "blitzPct": blitz_pct, "blitzCount": blitz_count,
        "rbBlitzTendency": rb_tendency,
        "pcards": pcards,
        "pressureFive": pressure_five, "pressureFiveN": five_n,
        "pressureSix": pressure_six, "pressureSixN": six_n,
        "pressureSeven": pressure_seven, "pressureSevenN": seven_n,
        "blitzByPersonnel": blitz_by_personnel,
        "coverageOnBlitz": coverage_on_blitz,
        "frontOnBlitz": front_on_blitz,
        "frontsByPersonnel": fronts_by_personnel,
        "coverageByPersonnel": coverage_by_personnel,
    }

def compute_down_splits(rows, defs):
    """defs: list of (label, predicate(row)->bool). Returns list of
    {label, n, fronts:[...], coverage:[...], stuntCount, stuntPct}."""
    out = []
    for label, pred in defs:
        sub = [r for r in rows if pred(r)]
        n = len(sub)
        front_c = Counter(upper(r.get('Front')) for r in sub)
        cov_c = Counter(upper(r.get('Coverage')) for r in sub)
        stunt_n = sum(1 for r in sub if is_stunt(r))
        out.append({
            "label": label, "n": n,
            "fronts": topN_pct(front_c, n, n=6),
            "coverage": topN_pct(cov_c, n, n=6),
            "stuntCount": stunt_n,
            "stuntPct": round(stunt_n/n*100) if n else 0,
        })
    return out

def defpers_bucket(row):
    """Bucket a defensive personnel string like '2-4-5' (DL-LB-DB) into BASE/NICKEL
    off the DB count (last number): 5 or more -> NICKEL, 4 or fewer -> BASE.
    Unparseable/blank values (e.g. '12 Men', 'X-X-X', '') return None and are excluded."""
    v = (row.get('pff_DEFPERSONNEL') or '').strip()
    if not v:
        return None
    parts = v.split('-')
    if len(parts) != 3:
        return None
    try:
        db = int(parts[2])
    except (TypeError, ValueError):
        return None
    return 'NICKEL' if db >= 5 else 'BASE'

def compute_bible(rows):
    """Normal-Downs coverage cross-tab reference ('Bible' tab), matching the staff's
    own 'NDD Bible' cheat-sheet format: coverage broken out against offensive personnel,
    fronts, defensive personnel, formation, FIB, WARP tempo, and Base/Nickel. rows should
    already be the Normal Downs bucket (down 1-2, non-2min/4min). Returns None if empty."""
    total = len(rows)
    if total == 0:
        return None

    def cov_breakdown(sub):
        c = Counter(upper(r.get('CoverFamily')) for r in sub)
        return topN_pct(c, len(sub), n=15)

    def front_breakdown(sub):
        c = Counter(upper(r.get('Front Family')) for r in sub)
        return topN_pct(c, len(sub), n=15)

    def off_pers_of(r):
        return (r.get('PERS(O)') or '').strip().upper()

    pers_groups = defaultdict(list)
    for r in rows:
        p = off_pers_of(r)
        if p:
            pers_groups[p].append(r)
    pers_sorted = sorted(pers_groups.items(), key=lambda kv: -len(kv[1]))

    # ---- 1. Overall Coverage ----
    overall_coverage = cov_breakdown(rows)

    # ---- 2. Coverage by Off Pers ----
    coverage_by_off_pers = [{
        "pers": pers, "n": len(grp), "pct": round(len(grp)/total*100),
        "coverage": cov_breakdown(grp),
    } for pers, grp in pers_sorted]

    # ---- 3. Front by Off Pers ----
    front_by_off_pers = [{
        "pers": pers, "n": len(grp), "pct": round(len(grp)/total*100),
        "fronts": front_breakdown(grp),
    } for pers, grp in pers_sorted]

    # ---- 4. Coverage to FIB ----
    fib_rows = [r for r in rows if upper(r.get('FIB')) == 'YES']
    coverage_to_fib = cov_breakdown(fib_rows) if fib_rows else []

    # ---- 5. Coverage to Tempo (WARP = pff_TEMPO == '1') ----
    warp_rows = [r for r in rows if (r.get('pff_TEMPO') or '').strip() == '1']
    warp_pers_groups = defaultdict(list)
    for r in warp_rows:
        p = off_pers_of(r)
        if p:
            warp_pers_groups[p].append(r)
    coverage_to_tempo = [{
        "pers": pers, "n": len(grp), "coverage": cov_breakdown(grp),
    } for pers, grp in sorted(warp_pers_groups.items(), key=lambda kv: -len(kv[1]))]

    # ---- 6. Coverage by Big Bucket Defensive Pers (Base/Nickel) ----
    base_rows = [r for r in rows if defpers_bucket(r) == 'BASE']
    nickel_rows = [r for r in rows if defpers_bucket(r) == 'NICKEL']
    bucket_total = len(base_rows) + len(nickel_rows)
    coverage_by_bucket = None
    if bucket_total:
        coverage_by_bucket = {
            "total": bucket_total,
            "nickel": {"n": len(nickel_rows), "pct": round(len(nickel_rows)/bucket_total*100) if bucket_total else 0,
                       "coverage": cov_breakdown(nickel_rows)},
            "base": {"n": len(base_rows), "pct": round(len(base_rows)/bucket_total*100) if bucket_total else 0,
                     "coverage": cov_breakdown(base_rows)},
        }

    # ---- 7 & 8. O Pers vs D Pers / Coverage by Def Pers (raw pff_DEFPERSONNEL string) ----
    defpers_present = [r for r in rows if (r.get('pff_DEFPERSONNEL') or '').strip()]
    o_vs_d = None
    coverage_by_def_pers = None
    if defpers_present:
        o_vs_d = []
        for pers, grp in pers_sorted:
            dgrp = defaultdict(list)
            for r in grp:
                dp = (r.get('pff_DEFPERSONNEL') or '').strip()
                if dp:
                    dgrp[dp].append(r)
            if not dgrp:
                continue
            dn = sum(len(v) for v in dgrp.values())
            entries = [{"label": dp, "count": len(v), "pct": round(len(v)/dn*100)}
                       for dp, v in sorted(dgrp.items(), key=lambda kv: -len(kv[1]))]
            o_vs_d.append({"pers": pers, "n": dn, "defpers": entries})

        dpers_groups = defaultdict(list)
        for r in defpers_present:
            dpers_groups[(r.get('pff_DEFPERSONNEL') or '').strip()].append(r)
        dtotal = len(defpers_present)
        coverage_by_def_pers = [{
            "defpers": dp, "n": len(grp), "pct": round(len(grp)/dtotal*100),
            "coverage": cov_breakdown(grp),
        } for dp, grp in sorted(dpers_groups.items(), key=lambda kv: -len(kv[1]))]

    # ---- 9. Coverage by Pers by Front (PERS(O) -> Front Family -> Cov Fam) ----
    coverage_by_pers_by_front = []
    for pers, grp in pers_sorted:
        fgroups = defaultdict(list)
        for r in grp:
            f = upper(r.get('Front Family'))
            if f:
                fgroups[f].append(r)
        if not fgroups:
            continue
        fn = sum(len(v) for v in fgroups.values())
        fronts = [{
            "front": f, "n": len(fg), "pct": round(len(fg)/fn*100),
            "coverage": cov_breakdown(fg),
        } for f, fg in sorted(fgroups.items(), key=lambda kv: -len(kv[1]))]
        coverage_by_pers_by_front.append({"pers": pers, "n": fn, "fronts": fronts})

    # ---- 10. Coverage to Form Family (FinalForm) ----
    form_groups = defaultdict(list)
    for r in rows:
        f = upper(r.get('FinalForm'))
        if f:
            form_groups[f].append(r)
    form_total = sum(len(v) for v in form_groups.values())
    coverage_to_form_family = [{
        "form": f, "n": len(grp), "pct": round(len(grp)/form_total*100) if form_total else 0,
        "coverage": cov_breakdown(grp),
    } for f, grp in sorted(form_groups.items(), key=lambda kv: -len(kv[1]))]

    return {
        "n": total,
        "overallCoverage": overall_coverage,
        "coverageByOffPers": coverage_by_off_pers,
        "frontByOffPers": front_by_off_pers,
        "coverageToFib": coverage_to_fib, "fibN": len(fib_rows),
        "coverageToTempo": coverage_to_tempo, "warpN": len(warp_rows),
        "coverageByBucket": coverage_by_bucket,
        "oVsD": o_vs_d,
        "coverageByDefPers": coverage_by_def_pers,
        "coverageByPersByFront": coverage_by_pers_by_front,
        "coverageToFormFamily": coverage_to_form_family,
    }

ND_SPLIT_DEFS = [
    ("1st Down", lambda r: down_of(r) == 1),
    ("2nd & Short (1-3)", lambda r: down_of(r) == 2 and distance_of(r) is not None and 1 <= distance_of(r) <= 3),
    ("2nd & Med (4-6)", lambda r: down_of(r) == 2 and distance_of(r) is not None and 4 <= distance_of(r) <= 6),
    ("2nd & Long (7+)", lambda r: down_of(r) == 2 and distance_of(r) is not None and distance_of(r) >= 7),
]

CD_SPLIT_DEFS = [
    ("3rd & 1", lambda r: down_of(r) == 3 and distance_of(r) == 1),
    ("3rd & 2", lambda r: down_of(r) == 3 and distance_of(r) == 2),
    ("3rd & 3-5", lambda r: down_of(r) == 3 and distance_of(r) is not None and 3 <= distance_of(r) <= 5),
    ("3rd & 6-10", lambda r: down_of(r) == 3 and distance_of(r) is not None and 6 <= distance_of(r) <= 10),
    ("3rd & 11+", lambda r: down_of(r) == 3 and distance_of(r) is not None and distance_of(r) >= 11),
    ("4th Down (All)", lambda r: down_of(r) == 4),
]

def main():
    team, path, delim = sys.argv[1], sys.argv[2], sys.argv[3]
    delim = '\t' if delim == 'tab' else delim
    rows = load(path, delim)
    rows = [r for r in rows if upper(r.get('SituationO')) != GARBAGE]

    nd_rows = [r for r in rows if down_of(r) in (1,2) and upper(r.get('SituationO')) not in EXCLUDE_FROM_ND_CD]
    cd_rows = [r for r in rows if down_of(r) in (3,4) and upper(r.get('SituationO')) not in EXCLUDE_FROM_ND_CD]
    tm_eog_rows = [r for r in rows if upper(r.get('SituationO')) == '2 EOG']
    tm_eoh_rows = [r for r in rows if upper(r.get('SituationO')) == '2 EOH']
    fm_rows = [r for r in rows if upper(r.get('SituationO')) == '4']

    result = {
        "team": team,
        "totalRowsLoaded": len(rows),
        "nd": compute_bucket(nd_rows),
        "cd": compute_bucket(cd_rows),
        "tmEog": compute_bucket(tm_eog_rows),
        "tmEoh": compute_bucket(tm_eoh_rows),
        "fm": compute_bucket(fm_rows),
        "ndSplits": compute_down_splits(nd_rows, ND_SPLIT_DEFS),
        "cdSplits": compute_down_splits(cd_rows, CD_SPLIT_DEFS),
        "secondaryBreakpoint": find_secondary_breakpoint(rows),
        "bible": compute_bible(nd_rows),
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
