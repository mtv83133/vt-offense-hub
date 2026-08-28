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
    """Load rows, dropping blank-Name rows and deduping on Name (keep first occurrence).
    Some opponent exports repeat the exact same play under multiple '#' row-sequence values
    (confirmed with Matt on VMI's 2026-08-23 upload: 'there are plays that are included
    multiple times, only count it once, do not double count anything') -- Name is the
    reliable per-play identifier (it embeds the source game + play number), so any row
    sharing an already-seen Name is a duplicate of the same play, not a new one."""
    with open(path, newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=delim)
        rows = [row for row in r if (row.get('Name') or '').strip()]
    seen = {}
    for row in rows:
        key = row['Name'].strip()
        if key not in seen:
            seen[key] = row
    return list(seen.values())

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
        if name in ('', 'UNKNOWN', 'NAN', '?') or cnt < min_count:
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

# ---- Run Defense tab (run-scheme family efficiency + DL technique/DE reaction
# breakdowns), per Matt's 2026-08-28 direction. "PlayType" is the run-scheme
# tag column (WZ/TZ/MZ/GAP/DRAW/SPEED OPTION); "REMEMBER THIS FOREVER" fallback
# for opponents where PlayType is blank: the leading digit of the dressed Run
# Play call indicates family via VT's hole-number convention --
# 0/1 = Tite Zone, 4/5 = Mid Zone, 6/7 = Gap, 8/9 = Wide Zone.
RUN_FAMILY_MAP = {
    "WZ": "WIDE ZONE", "TZ": "TITE ZONE", "MZ": "MID ZONE", "MZ FLIP": "MID ZONE",
    "GAP": "GAP", "DRAW": "DRAW", "SPEED OPTION": "OPTION", "OPTION": "OPTION",
}
RUN_NUM_PREFIX_MAP = {
    '0': "TITE ZONE", '1': "TITE ZONE",
    '4': "MID ZONE", '5': "MID ZONE",
    '6': "GAP", '7': "GAP",
    '8': "WIDE ZONE", '9': "WIDE ZONE",
}
RUN_FAMILY_ORDER = ["WIDE ZONE", "MID ZONE", "TITE ZONE", "GAP", "DRAW", "OPTION"]

def run_family_of(row):
    fam = RUN_FAMILY_MAP.get(upper(row.get('PlayType')))
    if fam:
        return fam
    m = re.match(r'\s*(\d)', norm(row.get('Run Play')))
    if m:
        return RUN_NUM_PREFIX_MAP.get(m.group(1))
    return None

def is_clean_tag(v):
    """A trailing '?' means the charter wasn't confident in the tag; 'EMPTY'
    isn't a real alignment/reaction value. Both are excluded from the DL
    Technique / DE Reaction breakdown tables (established VMI/ODU convention:
    only confidently-charted tags are counted)."""
    v = norm(v)
    return bool(v) and not v.endswith('?') and v.upper() != 'EMPTY'

def compute_run_tab(rows):
    """Run Defense tab: run-family efficiency (WIDE ZONE/MID ZONE/TITE ZONE/
    GAP/DRAW/OPTION), DL 3-Tech alignment (RB side), and DE Reaction (P.O.A. /
    Read) breakdowns, aggregated across every charted run snap (not down-
    bucketed -- matches the existing shipped Run tab's full-season scope)."""
    run_rows = [r for r in rows if upper(r.get('pff_RUNPASS')) == 'R']

    fam_n, fam_eff = Counter(), Counter()
    for r in run_rows:
        fam = run_family_of(r)
        if not fam:
            continue
        fam_n[fam] += 1
        if upper(r.get('pff_VAPI_EFFICIENT')) == 'Y':
            fam_eff[fam] += 1

    families = []
    for fam in RUN_FAMILY_ORDER:
        n = fam_n.get(fam, 0)
        if n == 0:
            continue
        families.append({"name": fam, "plays": n, "eff": round(fam_eff.get(fam, 0) / n * 100)})
    families.sort(key=lambda x: -x["plays"])

    total_n = sum(f["plays"] for f in families)
    total_eff_n = sum(fam_eff.get(f["name"], 0) for f in families)
    overall_pct = round(total_eff_n / total_n * 100) if total_n else 0

    by_eff = sorted(families, key=lambda x: -x["eff"])
    narrative = None
    if len(by_eff) >= 2:
        worst, best = by_eff[0], by_eff[-1]
        middle = [f for f in by_eff if f is not worst and f is not best]
        text = (f'Overall Run Efficiency Allowed: {overall_pct}% ({total_eff_n}/{total_n} qualifying snaps) — '
                f'{worst["name"].title()} is their most vulnerable at {worst["eff"]}%. '
                f'{best["name"].title()} is defended best at {best["eff"]}%.')
        if middle:
            names = " and ".join(f["name"].title() for f in middle)
            pcts = " and ".join(f'{f["eff"]}%' for f in middle)
            verb = "sit" if len(middle) > 1 else "sits"
            text += f' {names} {verb} in between at {pcts}.'
        narrative = text
    elif len(by_eff) == 1:
        f = by_eff[0]
        narrative = f'Overall Run Efficiency Allowed: {overall_pct}% ({total_eff_n}/{total_n} qualifying snaps) — {f["name"].title()} only, at {f["eff"]}%.'

    def tally(field):
        c = Counter(upper(r.get(field)) for r in run_rows if is_clean_tag(r.get(field)))
        return [{"label": k, "n": v} for k, v in sorted(c.items(), key=lambda kv: -kv[1])]

    return {
        "n": total_n, "effN": total_eff_n, "effPct": overall_pct,
        "families": families, "narrative": narrative,
        "threeTech": tally('3TECH (TO/AWAY)'),
        "dePoa": tally('DE REACTION(P.O.A)'),
        "deRead": tally('DE REACTION ( READ)'),
    }

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
    """Finds the single yard line where the defense's CoverFamily distribution
    shifts most sharply, scanning EVERY yard line (not just multiples of 5)
    from +1 out to +35.

    2026-08-28 rewrite, per Matt's direct challenge ("scan every yard line,
    not just 5/10/15/20/25") after he questioned why ODU and Maryland both
    independently landed on exactly +5 under the old coarse-grid version.
    Investigation confirmed the coarse grid itself wasn't cheating -- +5
    legitimately beat +10/+15/+20/+25 for all 3 currently-loaded opponents --
    but a full 1-yard-increment scan exposed a real flaw underneath: with the
    "inside" group as small as 8-15 plays, cover_family_score() (an
    un-normalized total-variation distance, see its docstring) is dominated
    by small-sample noise, so the raw per-yard-line argmax jumps around
    unstably (ODU +4, MARYLAND +2, VMI +1 -- each on an "inside" n of 8-14,
    each easily explained by 2-3 plays landing a certain way by chance, NOT a
    real scheme change). Verified empirically: once the "inside" sample floor
    is raised enough to escape that noise regime (tested every floor 8-30 for
    all 3 teams), the best-scoring yard line stops moving and stabilizes --
    the stabilization point lands consistently in the n>=15 range across all
    3 teams (ODU stabilizes at inside-n>=16, MARYLAND at >=12, VMI at >=13).
    15 is therefore used as the floor: large enough that every team's answer
    is past its own noise-driven instability point, small enough to still
    resolve a genuinely tight-radius shift rather than forcing every opponent
    toward the same wide default. Re-validate this floor choice (rerun the
    stability sweep above) if a future opponent's answer looks suspiciously
    unstable or suspiciously identical to another team's."""
    best_thresh, best_score = 15, 0
    MIN_INSIDE = 15
    for thresh in range(1, 36):
        inside = [r for r in rp_rows if field_pos(r) is not None and 1 <= field_pos(r) <= thresh]
        outside = [r for r in rp_rows if field_pos(r) is not None and not (1 <= field_pos(r) <= thresh)]
        if len(inside) < MIN_INSIDE or len(outside) < 10:
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

def is_red_zone(row):
    """Standard red zone: opponent's 20-yard-line and in. CORRECTED 2026-08-24:
    this dataset's pff_FIELDPOSITION convention is POSITIVE = opponent territory
    (distance-to-goal), confirmed directly against goal-to-go rows in VMI's raw
    export (field_pos=1/distance=1, field_pos=2/distance=2, field_pos=3/distance=3,
    etc. -- exact match only holds if positive field_pos IS yards-to-opponent-goal).
    An earlier pass on this same date incorrectly assumed the opposite sign and
    excluded the wrong 13 plays (own-territory snaps near midfield) while leaving
    the real ~72 red-zone snaps in the Bible -- this fixes that. RZ = 1 <= field_pos
    <= 20. Per Matt's 2026-08-24 direction, the Bible (NDD cheat-sheet) should
    exclude RZ snaps entirely -- it's meant to reflect the base-field normal-downs
    picture, with RZ handled by its own dedicated tab/section."""
    fp = field_pos(row)
    return fp is not None and 1 <= fp <= 20

def is_fully_charted(row):
    """A play only belongs in the Bible if it has real data in all three of
    Formation (FinalForm), Coverage (CoverFamily), and Front (Front Family).
    Per Matt's 2026-08-24 direction: a play charted with only some of those
    columns filled in (e.g. Formation logged but Coverage/Front never charted)
    should be excluded outright, not shown as a labeled 'UNCHARTED' row."""
    return bool(upper(row.get('FinalForm'))) and bool(upper(row.get('CoverFamily'))) and bool(upper(row.get('Front Family')))

def compute_bible(rows, allowed_games=None):
    """Normal-Downs coverage cross-tab reference ('Bible' tab), matching the staff's
    own 'NDD Bible' cheat-sheet format: coverage broken out against offensive personnel,
    fronts, defensive personnel, formation, FIB, WARP tempo, and Base/Nickel. rows should
    already be the Normal Downs bucket (down 1-2, non-2min/4min) -- this function further
    excludes Red Zone snaps (see is_red_zone) and any play not fully charted across
    Formation/Coverage/Front (see is_fully_charted), so the Bible reflects only complete,
    base-field normal-downs data. Returns None if empty.

    allowed_games: optional list of substrings to match against each row's Name field,
    restricting the Bible to only specific games. Per Matt's 2026-08-24 direction: not
    every charted game has normal downs charted to the same completeness -- some games
    only got 3rd/4th down, RZ, and 2-min/4-min situational snaps charted (used elsewhere
    -- CD/RZ/TM/FM all still use every game), while normal-downs-open-field charting was
    only done thoroughly for a subset of games. Every game DOES have some down-1/2 rows
    tagged (so this can't be auto-detected from down distribution alone -- confirmed by
    inspecting VMI's raw CSV: e.g. Harvard has 23 down-1/2 rows, not zero, yet still isn't
    one of the fully-charted games) -- so the game list has to come from Matt directly
    rather than being inferred. Pass None (default) for opponents where every game is
    fully charted for normal downs."""
    if allowed_games:
        rows = [r for r in rows if any(g in (r.get('Name') or '') for g in allowed_games)]
    rows = [r for r in rows if not is_red_zone(r) and is_fully_charted(r)]

    # FIB ('FIB REACTION' / motion-into-boundary-type situational tag) plays get
    # their own dedicated "Coverage to FIB" card further down -- they were being
    # double-counted into every other table (Overall Coverage, Coverage by Off
    # Personnel, Coverage to Formation Group, etc.) too, which is what caused counts
    # there to run higher than Matt's own cutup counts. Fixed 2026-08-24, confirmed
    # against Matt's TRIPS cutup (Book2.xlsx): his 18 real TRIPS plays are exactly
    # the FIB-blank subset of the 34 FIB-blank-or-YES plays my query originally
    # returned. fib_rows (computed below, for the FIB card) still comes from the
    # full RZ-excluded/fully-charted/allowed-games pool -- only the FIB=YES rows are
    # pulled OUT of `rows` itself so every other table reflects base, non-FIB snaps.
    fib_rows = [r for r in rows if upper(r.get('FIB')) == 'YES']
    rows = [r for r in rows if upper(r.get('FIB')) != 'YES']
    total = len(rows)
    if total == 0:
        return None

    def cov_breakdown(sub):
        c = Counter(upper(r.get('CoverFamily')) for r in sub)
        return topN_pct(c, len(sub), n=16)

    def front_breakdown(sub):
        c = Counter(upper(r.get('Front Family')) for r in sub)
        return topN_pct(c, len(sub), n=16)

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

    # ---- 4. Coverage to FIB (fib_rows computed above, before FIB=YES rows were
    # pulled out of `rows`) ----
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

    # ---- 10. Coverage to Formation Group (FinalForm -- named formation, e.g. 'TRIPS',
    # 'DUO', 'DOS' -- per Matt's 2026-08-23 direction, replacing the old FORMATION GROUP
    # OFF 3X1/2X2-style generic bucket. Used as-is/verbatim, no regex bucketing -- FORMATION
    # GROUP OFF itself is left untouched everywhere else in this file.) ----
    def form_group_bucket(r):
        return upper(r.get('FinalForm'))
    form_groups = defaultdict(list)
    for r in rows:
        f = form_group_bucket(r)
        if f:
            form_groups[f].append(r)
    form_total = sum(len(v) for v in form_groups.values())
    coverage_to_form_family = [{
        "form": f, "n": len(grp), "pct": round(len(grp)/form_total*100) if form_total else 0,
        "coverage": cov_breakdown(grp),
    } for f, grp in sorted(form_groups.items(), key=lambda kv: -len(kv[1]))]

    # ---- 11. Normal Downs Breakdown by Formation (PREPARE FOR / REACT TO / MIXERS /
    # PRESSURE) -- reuses the same form_groups grouping as #10 above (FinalForm), just
    # reshaped into the staff's "Michigan Breakdown"-style situational-card format
    # instead of a flat cross-tab list. PREPARE FOR = the single most common coverage
    # family; REACT TO = the 2nd most common; MIXERS = up to 2 additional coverage
    # families that still clear MIXER_MIN_COUNT (secondary/notable tags, not just
    # single-snap noise); PRESSURE = blitz rate, with BLITZ_LOOK_MIN clearing enough
    # snaps to name a specific blitz look (e.g. "MISSILE") rather than just a %.
    # Matt flagged (2026-08-26) he'll likely want these thresholds tuned once he's
    # seen it live -- MIXER_MIN_COUNT/BLITZ_LOOK_MIN/MIN_FORM_N are the knobs to
    # adjust. MIN_FORM_N keeps the grid from being swamped by 1-2-snap formations
    # (e.g. VMI's FinalForm column has ~16 formations with only 1 charted snap) --
    # anything below it is rolled into a single "Small Sample" summary card instead
    # of silently dropped.
    MIXER_MIN_COUNT = 2
    BLITZ_LOOK_MIN = 2
    MIN_FORM_N = 3

    def prm_group(sub):
        n = len(sub)
        cov_top = cov_breakdown(sub)
        prepare_for = cov_top[0] if len(cov_top) > 0 else None
        react_to = cov_top[1] if len(cov_top) > 1 else None
        mixers = [c for c in cov_top[2:4] if c["count"] >= MIXER_MIN_COUNT]
        blitz_sub = [r for r in sub if is_blitz(r)]
        blitz_n = len(blitz_sub)
        blitz_c = Counter(upper(r.get('Blitz')) for r in blitz_sub if upper(r.get('Blitz')))
        blitz_looks = topN_pct(blitz_c, blitz_n, n=2, min_count=BLITZ_LOOK_MIN) if blitz_n else []
        return {
            "n": n,
            "prepareFor": prepare_for,
            "reactTo": react_to,
            "mixers": mixers,
            "blitzLooks": blitz_looks,
            "pressurePct": round(blitz_n/n*100) if n else 0,
            "pressureN": blitz_n,
        }

    form_groups_sorted = sorted(form_groups.items(), key=lambda kv: -len(kv[1]))
    nd_formation_breakdown = [
        {"form": f, **prm_group(grp)}
        for f, grp in form_groups_sorted if len(grp) >= MIN_FORM_N
    ]
    small_sample_groups = [(f, grp) for f, grp in form_groups_sorted if len(grp) < MIN_FORM_N]
    nd_formation_small_sample = None
    if small_sample_groups:
        small_n = sum(len(grp) for _, grp in small_sample_groups)
        nd_formation_small_sample = {
            "forms": [f for f, _ in small_sample_groups],
            "count": len(small_sample_groups),
            "n": small_n,
        }

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
        "ndFormationBreakdown": nd_formation_breakdown,
        "ndFormationSmallSample": nd_formation_small_sample,
    }

RZ_ZONE_DEFS = [
    ("outer", "+27 to +13 (Outer RZ)", "outer", 13, 27),
    ("score", "+12 to +4 (Score Zone)", "score", 4, 12),
    ("gl", "Goal Line +3 to +1", "gl", 1, 3),
]

def _rz_situational(sub):
    """Down-based situational breakdown (Plays, Blitz%) for one RZ zone --
    generic across zones (unlike the old hand-built per-zone situational
    buckets) so it stays accurate as new data comes in."""
    out = []
    for label, pred in [
        ("1st Down", lambda r: down_of(r) == 1),
        ("2nd Down", lambda r: down_of(r) == 2),
        ("3rd Down", lambda r: down_of(r) == 3),
        ("4th Down", lambda r: down_of(r) == 4),
    ]:
        grp = [r for r in sub if pred(r)]
        n = len(grp)
        if n == 0:
            continue
        blitz_n = sum(1 for r in grp if is_blitz(r))
        out.append({"label": label, "n": n, "blitzPct": round(blitz_n/n*100) if n else 0})
    return out

def rz_demarcation(rows):
    """Surfaces the data-driven RZ 'line of demarcation' -- the yard line
    where the defense's front/coverage/blitz tendencies shift most sharply --
    as its own finding on the RZ tab. This threshold was already being
    COMPUTED by find_rz_line_of_demarcation() above, but only ever used as a
    silent input to find_secondary_breakpoint() (a rarer, conservative
    finding for a SECOND shift beyond the red zone); the line-of-demarcation
    yard line itself was never shown on its own. Per Matt's 2026-08-26
    direction, both the coach's and player's RZ tab should call out this
    specific yard line explicitly. Returns None if there isn't enough data on
    both sides of the candidate line to say anything reliable yet.

    2026-08-26 addendum, per Matt's follow-up ("double check ... another yard
    line ... where the scheme changes significantly"): direct analysis
    confirmed there is NOT a second, separate breakpoint inside the red
    zone -- what's actually happening is one continuous, broad tightening
    effect as the defense nears its own goal line, not two discrete steps.
    Every yard line from the primary line out to roughly the +15 clears the
    same strict shift-and-corroboration bar find_secondary_breakpoint() uses,
    then it fades out smoothly. So the callout should describe a GRADIENT
    ("tightens progressively inside the +N, sharpest inside the +{lod}"),
    not imply a single hard on/off switch -- while still naming the +{lod}
    headline number, which remains the single sharpest point in that curve."""
    rp_rows = [r for r in rows if is_run_pass(r) and field_pos(r) is not None]
    if len(rp_rows) < 40:
        return None
    lod = find_rz_line_of_demarcation(rp_rows)
    inside = [r for r in rp_rows if 1 <= field_pos(r) <= lod]
    outside = [r for r in rp_rows if not (1 <= field_pos(r) <= lod)]
    if len(inside) < 8 or len(outside) < 10:
        return None

    def top_label(grp, field):
        c = Counter(upper(r.get(field)) for r in grp if upper(r.get(field)) not in ('', 'UNKNOWN', 'NAN'))
        return c.most_common(1)[0][0] if c else None

    cov_in, cov_out = top_label(inside, 'CoverFamily'), top_label(outside, 'CoverFamily')
    front_in, front_out = top_label(inside, 'Front Family'), top_label(outside, 'Front Family')
    blitz_in = sum(1 for r in inside if is_blitz(r)) / len(inside) * 100
    blitz_out = sum(1 for r in outside if is_blitz(r)) / len(outside) * 100

    parts = []
    if cov_in and cov_out and cov_in != cov_out:
        parts.append(f'top coverage flips from {cov_out} to {cov_in}')
    if front_in and front_out and front_in != front_out:
        parts.append(f'top front flips from {front_out} to {front_in}')
    if abs(blitz_in - blitz_out) >= 8:
        parts.append(f'blitz rate moves from {round(blitz_out)}% to {round(blitz_in)}%')
    if not parts:
        return None
    detail = "; ".join(parts)
    detail = detail[0].upper() + detail[1:]

    # Scan outward from the primary line to find how far the same shift
    # stays statistically "live" (clears find_secondary_breakpoint()'s exact
    # bar: covScore >= 0.45, corroborated by frontScore >= 0.25 or a blitz
    # swing >= 12 points). Stops at the first yard line that no longer
    # clears -- this deliberately does NOT keep scanning past a gap (the
    # RZ-boundary vs rest-of-field comparison re-triggers the bar again out
    # around +25/+26, which is really just re-detecting "red zone vs not,"
    # not a genuine continuation of this shift).
    outer_edge = lod
    for thresh in range(lod + 1, 27):
        cand_in = [r for r in rp_rows if 1 <= field_pos(r) <= thresh]
        cand_out = [r for r in rp_rows if not (1 <= field_pos(r) <= thresh)]
        if len(cand_in) < 15 or len(cand_out) < 15:
            continue
        cov_score = cover_family_score(cand_in, cand_out)
        front_score = front_family_score(cand_in, cand_out)
        bi = sum(1 for r in cand_in if is_blitz(r)) / len(cand_in) * 100
        bo = sum(1 for r in cand_out if is_blitz(r)) / len(cand_out) * 100
        if cov_score >= 0.45 and (front_score >= 0.25 or abs(bi - bo) >= 12):
            outer_edge = thresh
        else:
            break

    if outer_edge > lod:
        text = (
            f'{detail} inside the +{lod}. The tightening is gradual, not a single hard switch -- '
            f'it\'s measurable as far out as the +{outer_edge}, sharpest inside the +{lod}.'
        )
    else:
        text = f'{detail} once the ball crosses the +{lod}.'

    return {
        "yardLine": lod, "outerEdge": outer_edge, "text": text,
        "nInside": len(inside), "nOutside": len(outside),
    }

def compute_rz(rows):
    """Red Zone tab: breaks opponent-territory snaps (pff_FIELDPOSITION 1-27,
    i.e. inside their own 27) into 3 zones -- Outer RZ (+27 to +13), Score Zone
    (+12 to +4), Goal Line (+3 to +1) -- matching the staff's existing RZ tab
    format. rows should be the full non-garbage play set for the opponent (all
    downs -- RZ tendencies aren't limited to normal downs). Rebuilt 2026-08-24
    from the current raw CSV; no prior version of this function existed, so
    this is a from-scratch, fully data-driven build (no hand-authored zone
    boundaries or narrative -- everything below is computed from real rows).
    Returns None if there's no RZ data at all yet."""
    RZ_MIXER_MIN_COUNT = 2
    RZ_BLITZ_LOOK_MIN = 2

    zones = []
    for key, label, cls, lo, hi in RZ_ZONE_DEFS:
        sub = [r for r in rows if field_pos(r) is not None and lo <= field_pos(r) <= hi]
        n = len(sub)
        front_c = Counter(upper(r.get('Front Family')) for r in sub)
        cov_c = Counter(upper(r.get('CoverFamily')) for r in sub)
        blitz_sub = [r for r in sub if is_blitz(r)]
        blitz_n = len(blitz_sub)
        five_n, _ = compute_pressure_schemes(blitz_sub, 5, blitz_n) if blitz_n else (0, [])
        six_n, _ = compute_pressure_schemes(blitz_sub, 6, blitz_n) if blitz_n else (0, [])
        cov_top = topN_pct(cov_c, n, n=4)
        blitz_look_c = Counter(upper(r.get('Blitz')) for r in blitz_sub if upper(r.get('Blitz')))
        zones.append({
            "key": key, "label": label, "cls": cls, "n": n,
            "front": topN_pct(front_c, n, n=4),
            "coverage": cov_top,
            "blitzCount": blitz_n, "blitzPct": round(blitz_n/n*100) if n else 0,
            "fiveManPct": round(five_n/blitz_n*100) if blitz_n else 0,
            "sixManPct": round(six_n/blitz_n*100) if blitz_n else 0,
            "situational": _rz_situational(sub),
            # PREPARE FOR / REACT TO / MIXERS / PRESSURE breakdown, same shape and
            # same tunable thresholds as compute_bible()'s ndFormationBreakdown --
            # see the comment there for why these two knobs exist.
            "prepareFor": cov_top[0] if len(cov_top) > 0 else None,
            "reactTo": cov_top[1] if len(cov_top) > 1 else None,
            "mixers": [c for c in cov_top[2:4] if c["count"] >= RZ_MIXER_MIN_COUNT],
            "blitzLooks": topN_pct(blitz_look_c, blitz_n, n=2, min_count=RZ_BLITZ_LOOK_MIN) if blitz_n else [],
        })

    total_n = sum(z["n"] for z in zones)
    if total_n == 0:
        return None
    total_blitz = sum(z["blitzCount"] for z in zones)

    gl = next(z for z in zones if z["key"] == "gl")
    top_cov_gl = gl["coverage"][0] if gl["coverage"] else None
    top_front_gl = gl["front"][0] if gl["front"] else None
    gl_six_man_universal = gl["blitzCount"] > 0 and gl["sixManPct"] == 100

    # ---- Data-driven callout: describe the biggest front/coverage swings
    # between the widest (Outer) and tightest (Goal Line) zones, using the
    # same cover/front-family shift-score helpers as the secondary-breakpoint
    # scanner. Only claims a shift if the zones actually have decent samples;
    # otherwise falls back to a plain "not enough plays yet" note. ----
    outer = zones[0]
    callout = None
    if outer["n"] >= 15 and gl["n"] >= 5:
        outer_rows = [r for r in rows if field_pos(r) is not None and 13 <= field_pos(r) <= 27]
        gl_rows = [r for r in rows if field_pos(r) is not None and 1 <= field_pos(r) <= 3]
        cov_shift = cover_family_score(outer_rows, gl_rows)
        front_shift = front_family_score(outer_rows, gl_rows)
        parts = []
        if top_front_gl and outer["front"]:
            of = {f["label"]: f["pct"] for f in outer["front"]}
            gf_pct = top_front_gl["pct"]
            of_pct = of.get(top_front_gl["label"], 0)
            if gf_pct > of_pct:
                parts.append(f'{top_front_gl["label"]} front rises from {of_pct}% in the Outer RZ to {gf_pct}% at the Goal Line')
        if top_cov_gl:
            oc = {c["label"]: c["pct"] for c in outer["coverage"]}
            oc_pct = oc.get(top_cov_gl["label"], 0)
            if top_cov_gl["pct"] != oc_pct:
                parts.append(f'{top_cov_gl["label"]} coverage moves from {oc_pct}% in the Outer RZ to {top_cov_gl["pct"]}% at the Goal Line')
        if outer["blitzPct"] != gl["blitzPct"]:
            parts.append(f'blitz rate shifts from {outer["blitzPct"]}% in the Outer RZ to {gl["blitzPct"]}% at the Goal Line')
        if parts:
            joined = "; ".join(parts)
            callout = joined[0].upper() + joined[1:] + "."
        if cov_shift < 0.2 and front_shift < 0.2 and not callout:
            callout = None

    return {
        "n": total_n,
        "blitzPct": round(total_blitz/total_n*100) if total_n else 0,
        "blitzCount": total_blitz,
        "zones": zones,
        "topCoverageGL": top_cov_gl,
        "topFrontGL": top_front_gl,
        "glSixManUniversal": gl_six_man_universal,
        "callout": callout,
        "lineOfDemarcation": rz_demarcation(rows),
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

# Per Matt's 2026-08-24 direction: only these 4 Cornell games were fully charted
# for normal-downs/open-field snaps (the other 6 games only got 3rd/4th down, RZ,
# and 2-min/4-min situational snaps charted, not a complete normal-downs sample).
# CD/RZ/TM/FM all still pull from every game -- this restriction is Bible-only.
BIBLE_GAME_ALLOWLIST = {
    "VMI": ["vs Princeton", "vs Pennsylvania", "vs Dartmouth", "vs Columbia"],
    # Per Matt's 2026-08-28 direction: only these 7 ODU games were fully charted
    # for normal-downs/open-field snaps -- the other 6 (Indiana, NC Central,
    # Liberty, Coastal Carolina, Georgia State, Georgia Southern) only got 3rd
    # down, RZ, 2-min EOG/EOH, and 4-min situational snaps charted.
    "ODU": ["vs Virginia Tech", "vs Marshall", "vs James Madison", "vs Louisiana-Monroe",
            "vs South Florida", "vs Appalachian State", "vs Troy"],
    # Per Matt's 2026-08-28 direction: only these 6 Maryland games were fully
    # charted for normal-downs/open-field snaps -- the other 6 (Northern
    # Illinois, UCLA, Wisconsin, Florida Atlantic, Nebraska, Towson) only got
    # RZ, 3rd down, 2-min EOH/EOG, and 4-min situational snaps charted.
    "MARYLAND": ["vs Washington", "vs Michigan", "vs Indiana", "vs Illinois",
                 "vs Michigan State", "vs Rutgers"],
}

def compute_gl_detail(rows):
    """Standalone Goal Line tab (#sec-gl / tmpl-gl-<TEAM>) -- a richer,
    down-split view of the same Goal Line zone (field_pos 1-3) already
    surfaced as one of the 3 zone cards in compute_rz(). This is a SEPARATE
    top-level nav tab from the RZ tab, with its own Front Families, Front &
    Blitz by Down, Coverage, and 5/6/7-Man Blitz Summary (with actual blitz
    package names, not just man-count %s).

    Rebuilt from scratch 2026-08-27: the previous tmpl-gl-<TEAM> content was
    a one-off hand-authored block (including a hardcoded "Cornell faced 9
    Goal Line possessions last season..." sentence) that predated the
    coverage-family correction pipeline and was never wired into it, so it
    drifted out of sync with the RZ tab's own (correct) Goal Line zone
    numbers for the identical situation -- confirmed on VMI: old tab said 18
    plays / BEAR 39% / GL 0 28% / 44% blitz, RZ zone card (already correct)
    says 17 plays / BEAR 47% / ZERO 76% / 41% blitz. This function makes the
    standalone tab fully data-driven like every other tab, using the same
    Front Family / CoverFamily grouped labels as the rest of the site
    (rather than the old tab's raw, unlabeled Coverage-column text) so it
    can never silently drift out of sync with the RZ tab again.

    Returns None if there's no Goal Line data yet."""
    sub = [r for r in rows if field_pos(r) is not None and 1 <= field_pos(r) <= 3]
    n = len(sub)
    if n == 0:
        return None

    front_c = Counter(upper(r.get('Front Family')) for r in sub)
    front_family = topN_pct(front_c, n, n=6)

    cov_c = Counter(upper(r.get('CoverFamily')) for r in sub)
    coverage = topN_pct(cov_c, n, n=6)

    # Front & Blitz by Down -- 1st / 2nd / 3rd&4th combined (matches the
    # original tab's 3-row grouping).
    down_groups = [
        ("1st Down", lambda r: down_of(r) == 1),
        ("2nd Down", lambda r: down_of(r) == 2),
        ("3rd & 4th", lambda r: down_of(r) in (3, 4)),
    ]
    by_down = []
    for label, pred in down_groups:
        grp = [r for r in sub if pred(r)]
        gn = len(grp)
        if gn == 0:
            continue
        fc = Counter(upper(r.get('Front Family')) for r in grp if upper(r.get('Front Family')) not in ('', 'UNKNOWN', 'NAN', '?'))
        top = fc.most_common()
        if top:
            top_count = top[0][1]
            top_fronts = ' / '.join(f for f, c in top if c == top_count)
        else:
            top_fronts = '--'
        gb = sum(1 for r in grp if is_blitz(r))
        by_down.append({
            "label": f"{label} (n={gn})", "topFront": top_fronts,
            "blitzPct": round(gb/gn*100) if gn else 0,
        })

    blitz_sub = [r for r in sub if is_blitz(r)]
    blitz_n = len(blitz_sub)
    five_n, five_pkgs = compute_pressure_schemes(blitz_sub, 5, blitz_n) if blitz_n else (0, [])
    six_n, six_pkgs = compute_pressure_schemes(blitz_sub, 6, blitz_n) if blitz_n else (0, [])
    seven_n, seven_pkgs = compute_pressure_schemes(blitz_sub, 7, blitz_n) if blitz_n else (0, [])

    # Data-driven package-dominance callout (replaces the old hand-typed
    # "M WRAP (6-man) is the only blitz package used" sentence -- confirmed
    # on VMI that sentence is no longer true post-correction: 4 of 7 Goal
    # Line blitzes are M WRAP, not all of them, though all 7 are still
    # 6-man).
    pkg_callout = None
    if blitz_n:
        pkg_c = Counter(upper(r.get('Blitz')) for r in blitz_sub if upper(r.get('Blitz')) not in ('', 'UNKNOWN', 'NAN'))
        if pkg_c:
            top_pkg, top_pkg_n = pkg_c.most_common(1)[0]
            man_counts = set(rushers_of(r) for r in blitz_sub if upper(r.get('Blitz')) == top_pkg)
            man_label = f"{man_counts.pop()}-man" if len(man_counts) == 1 and next(iter(man_counts), None) else None
            if top_pkg_n == blitz_n:
                pkg_callout = f'{top_pkg}{f" ({man_label})" if man_label else ""} is the only blitz package used at the Goal Line -- every pressure look is {man_label or "the same package"}.'
            elif top_pkg_n / blitz_n >= 0.5:
                pct = round(top_pkg_n/blitz_n*100)
                pkg_callout = f'{top_pkg} is the primary blitz package at the Goal Line ({pct}% of pressure looks, {top_pkg_n} of {blitz_n}).'
        all_man_counts = set(rushers_of(r) for r in blitz_sub if rushers_of(r))
        if len(all_man_counts) == 1:
            only_man = next(iter(all_man_counts))
            man_note = f'Every Goal Line pressure look is {only_man}-man ({blitz_n} of {blitz_n}).'
            pkg_callout = f'{pkg_callout} {man_note}' if pkg_callout else man_note

    return {
        "n": n,
        "frontFamily": front_family,
        "byDown": by_down,
        "coverage": coverage,
        "blitzCount": blitz_n, "blitzPct": round(blitz_n/n*100) if n else 0,
        "fiveManN": five_n, "fivePkgs": five_pkgs,
        "sixManN": six_n, "sixPkgs": six_pkgs,
        "sevenManN": seven_n, "sevenPkgs": seven_pkgs,
        "pkgCallout": pkg_callout,
    }

def main():
    team, path, delim = sys.argv[1], sys.argv[2], sys.argv[3]
    delim = '\t' if delim == 'tab' else delim
    rows = load(path, delim)
    rows = [r for r in rows if upper(r.get('SituationO')) != GARBAGE]

    # Per Matt's 2026-08-25 direction: the general Normal Downs card (Fronts,
    # Formations, Coverage, Blitz -- compute_bucket(nd_rows) below, NOT just
    # the Bible tab) must be 1st/2nd down, OPEN FIELD only -- exclude Red
    # Zone (which covers Goal Line as a subset, field_pos 1-20 under the
    # confirmed sign convention, see is_red_zone()/§2a of the skill) in
    # addition to the existing 2min/4min exclusion. Confirmed on VMI: this
    # removes 72 RZ snaps that were previously polluting the open-field ND
    # numbers (244 -> 172). compute_bible() already applied this same RZ
    # exclusion internally on top of nd_rows, so Bible tab numbers are
    # unaffected by this change -- this only fixes the separate general ND
    # summary card that every team's advance-scout page shows.
    nd_rows = [r for r in rows if down_of(r) in (1,2) and upper(r.get('SituationO')) not in EXCLUDE_FROM_ND_CD and not is_red_zone(r)]
    # Same RZ exclusion as nd_rows above, applied to CD -- per Matt's explicit
    # 2026-08-26 rule restatement: "RZ, 4 MIN, 2 EOG & 2 EOH & 3RD/4TH DOWN ALL
    # IN THEIR OWN SECTIONS." CD (3rd/4th down) is meant to be OPEN FIELD only,
    # same as ND -- a 3rd/4th down snap inside the red zone belongs exclusively
    # to the RZ tab, not also counted in Conversion Downs. This mirrors the ND
    # fix above (which already excludes RZ) but had never been applied to CD.
    cd_rows = [r for r in rows if down_of(r) in (3,4) and upper(r.get('SituationO')) not in EXCLUDE_FROM_ND_CD and not is_red_zone(r)]
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
        "bible": compute_bible(nd_rows, allowed_games=BIBLE_GAME_ALLOWLIST.get(team)),
        "rz": compute_rz(rows),
        "gl": compute_gl_detail(rows),
        "runTab": compute_run_tab(rows),
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
