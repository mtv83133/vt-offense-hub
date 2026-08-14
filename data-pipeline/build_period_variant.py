import csv, json, re, sys, os

if len(sys.argv) < 4:
    print("Usage: python3 build_fall_variant.py <team|skelly|combined> <path_to_csv> <day_key> [output_dir]")
    print("  day_key becomes the output filename prefix, e.g. 'fall_2' -> fall_2_team.json")
    print("  output_dir defaults to './output' (created if missing)")
    sys.exit(1)

variant = sys.argv[1]  # team, skelly, combined
csv_path = sys.argv[2]
day_key = sys.argv[3]
out_dir = sys.argv[4] if len(sys.argv) > 4 else './output'
os.makedirs(out_dir, exist_ok=True)

with open(csv_path, encoding='utf-8-sig') as f:
    rd = csv.DictReader(f)
    rows = list(rd)
# 'NO PLAY' (spelled out) first appeared in Fall Camp Practice #4's export --
# same "No Play" concept as the abbreviated 'NP', just a different export
# spelling (same pattern as pff_PASSRESULT's C/COMPLETE variance). Treated
# as equivalent and excluded here; flagged to Matt rather than silently
# assumed to be something else, since it wasn't in the format before.
rows = [r for r in rows if r['pff_RUNPASS'].strip().upper() not in ('PEN','NP','NO PLAY','')]

# ── Team vs. Skelly period detection ────────────────────────────────────
# Older exports populate COMPETITIVE directly ('SKELLY' or blank/other).
# Newer exports leave COMPETITIVE blank entirely and instead embed the
# period type in the Name column, e.g. "...16. SKELLY NORMAL DOWNS OFF IC,
# Play 001" vs "...20. TEAM NORMAL DOWNS OFF IC, Play 009". Prefer the
# explicit COMPETITIVE tag when present; fall back to parsing Name.
def period_of(r):
    comp = r.get('COMPETITIVE', '').strip().upper()
    if comp == 'SKELLY': return 'SKELLY'
    if comp: return 'TEAM'
    name = r.get('Name', '')
    if re.search(r'\bSKELLY\b', name, re.I): return 'SKELLY'
    if re.search(r'\bTEAM\b', name, re.I): return 'TEAM'
    return 'TEAM'  # unrecognized/blank Name: default to team so it isn't silently dropped

if variant == 'team':
    rows = [r for r in rows if period_of(r) != 'SKELLY']
elif variant == 'skelly':
    rows = [r for r in rows if period_of(r) == 'SKELLY']
print(f"[{variant}] usable rows:", len(rows))

def gain(r):
    s = r['pff_GAINLOSS'].strip()
    if s in ('', 'NP'): return 0.0
    try: return float(s)
    except: return 0.0

# ── Pass-result normalization ───────────────────────────────────────────
# Some exports code pff_PASSRESULT with single letters (C/I/D/S/X/Q), others
# spell it out (COMPLETE/INCOMPLETE/DROP/INTERCEPTION/SCRAMBLE DRILL) and
# tag sacks via pff_RUNPASS='SACK' with a blank result instead of 'S'.
# presult() normalizes either form to a single internal code so the rest of
# the stat logic doesn't care which export style produced the row.
# Legend: C=Complete I=Incomplete D=Drop S=Sack X=Interception Q=Scramble
# Drill TA=Throwaway (new; tracked as its own stat, not folded into comp%).
_PRESULT_MAP = {
    'COMPLETE':'C','INCOMPLETE':'I','DROP':'D','INTERCEPTION':'X',
    'SCRAMBLE DRILL':'Q','THROWAWAY':'TA','SACK':'S',
    'C':'C','I':'I','D':'D','S':'S','X':'X','Q':'Q','R':'R',
    # 'SCRAMBLE' (no "DRILL") and 'SCRAMLBE DRILL' (typo transposition of
    # "SCRAMBLE DRILL") both first appeared in Fall Camp Practice #5's
    # export -- same underlying outcome as 'SCRAMBLE DRILL' (QB left
    # structure / scrambled), just a different spelling, so both normalize
    # to the same 'Q' code rather than falling through unmatched (which
    # would silently exclude these reps from scramble_pct/RT SCRM and any
    # other Q-keyed stat).
    'SCRAMBLE':'Q','SCRAMLBE DRILL':'Q',
}
def presult(r):
    rp = r['pff_RUNPASS'].strip().upper()
    if rp == 'SACK': return 'S'
    raw = r['pff_PASSRESULT'].strip().upper()
    return _PRESULT_MAP.get(raw, raw)

def is_sack(r): return presult(r)=='S'
def is_comp(r): return presult(r)=='C'
def is_drop(r): return presult(r)=='D'
def is_scramble(r): return presult(r)=='Q'
def is_throwaway(r): return presult(r)=='TA'
def is_int(r): return presult(r)=='X'
def is_eff(r): return r['Efficient'].strip()=='Y'
def is_expl(r): return r['EXPLOSIVE'].strip()=='Y'
# Run vs. pass is decided by Run Family being non-blank -- EXCEPT Fall Camp
# Practice #5's export had Run Family completely blank for every single row
# (88/88), including 28 rows clearly marked pff_RUNPASS='R' with a real
# RunScheme populated (e.g. '28*29 KEY', '16*17 OPTION TOSS') and a real
# yardage gain -- a charting gap for the whole practice, not a genuine
# passing week. Left unhandled, every one of those 28 designed runs would
# get miscounted as a pass attempt (inflating n_pass, polluting the Pass
# Concepts table with fake "concept" rows for run play names like FREIBURG/
# FOGBOW/KOBE, and leaving the Run Family/Scheme table completely empty for
# the week even though 28 real runs happened). Fixed by falling back to
# pff_RUNPASS=='R' as a run signal whenever Run Family is blank -- this is
# a safe, well-grounded fallback (not a guess: pff_RUNPASS is a separate,
# reliably-populated column that already directly says "this was a run").
# The Run Family/Scheme BREAKDOWN table itself (fam_rows/fam_map below) is
# backfilled separately via run_family_of()/family_from_scheme() -- Matt
# supplied the actual RunScheme-number-to-family mapping after Practice #5
# (see the comment above _SCHEME_DIGIT_FAMILY near fam_rows) -- so that
# table now also populates correctly for a day where Run Family wasn't
# charted, as long as RunScheme was. If a future day has BOTH Run Family
# blank AND RunScheme unparseable (no digit pattern, no 'PAINT'), a run rep
# still counts correctly toward n_run/n_pass via this pff_RUNPASS fallback,
# but won't appear in the Run Family/Scheme breakdown table -- flag that
# specific gap to Matt rather than guessing a family for it.
def is_run(r):
    if r['Run Family'].strip()!='': return True
    return r['pff_RUNPASS'].strip().upper()=='R'
def is_pass(r): return not is_run(r)
# NOTE: an earlier version of this file forced CYCLONE/KOBE/HEDGEHOG to
# always be is_run_sub=True/is_pass_sub=False (never splitting a PASS
# sub-row in WARP Plays/Run Family). Matt corrected that: these ARE RPOs
# ("run plays with an option to throw the ball") and DO want the normal
# RUN/PASS sub-section split in WARP Plays whenever a rep actually got
# thrown -- same as MARKER. What he actually wants suppressed is these
# plays showing up as their own row in the separate PASS CONCEPTS table
# (see RPO_RUN_PLAYS / pc_pass_rows below), not the WARP sub-breakdown.
# So is_run_sub/is_pass_sub are back to the original presult()/RUNPASS-
# based logic, unmodified by play name.
def is_run_sub(r):
    pr = presult(r)
    if pr == 'R': return True
    if pr == '': return r['pff_RUNPASS'].strip().upper() == 'R'  # blank result: fall back to the called tag, don't assume
    return False
def is_pass_sub(r):
    pr = presult(r)
    return pr in ('C','I','S','D','X','TA','Q')
def is_neg(r): return gain(r) < 0 or is_sack(r)
def is_rz(r):
    fp = r['pff_FIELDPOSITION'].strip()
    if fp.startswith('+'):
        try: return int(fp[1:]) <= 12
        except: return False
    return False
def pct(cnt,total): return round(cnt/total*1000)/10 if total else 0.0
def avgy(items): return round(sum(gain(r) for r in items)/len(items)*10)/10 if items else 0.0
# Targeted attempts for completion% purposes: complete/incomplete/drop/
# interception -- an INT is charted like it would count in a real game
# (a failed pass attempt, hurting comp%). Scrambles and throwaways are
# NOT folded in here -- they get their own scramble_pct/throwaway_pct
# instead of diluting true target/completion numbers.
def targeted(items): return [r for r in items if presult(r) in ('C','I','D','X')]
def comp_pct(items):
    ta = targeted(items)
    return pct(sum(1 for r in ta if is_comp(r)), len(ta))
def stat_block(items):
    n=len(items)
    return {'n':n,'avg':avgy(items),'eff':pct(sum(1 for r in items if is_eff(r)),n),
            'expl':pct(sum(1 for r in items if is_expl(r)),n),'neg':pct(sum(1 for r in items if is_neg(r)),n),
            'scramble_pct':pct(sum(1 for r in items if is_scramble(r)),n),
            'throwaway_pct':pct(sum(1 for r in items if is_throwaway(r)),n)}

# ── Route Thrown breakdown (read progression) ───────────────────────────
# The 'Route Thrown' column tags which read/route got the ball on a given
# pass rep: '1'/'2'/'3'/'4' = 1st/2nd/3rd/4th read, 'O' = out/checkdown,
# 'A' = alert route, 'Q' = scramble (QB left structure). Starting Fall Camp
# Practice #2, a throwaway rep is also tagged 'TA' in this column
# (previously it just fell through with no route-thrown tag at all).
# Starting Fall Camp Practice #3: a 4th-read rep appeared for the first
# time ('4', added as its own RT 4TH column), and some rows spelled the
# alert route out as 'ALERT' instead of the usual 'A' -- _RT_NORMALIZE
# folds that spelling into 'A' before matching so it isn't silently
# dropped from RT ALRT. These power the RT 1ST/RT 2ND/RT 3RD/RT 4TH/
# RT OUT/RT ALRT/RT SCRM/RT TA columns on the Pass Concepts table -- a
# read-progression tag, independent of the scramble_pct/throwaway_pct
# outcome-based stats above (kept for WARP Plays/QB tables, which have no
# RT breakdown of their own). Per Matt's direction after Practice #3, the
# Pass Concepts table's own TA % column (throwaway_pct) was dropped as
# redundant now that RT TA exists there -- throwaway_pct itself is still
# computed/kept in stat_block for WARP Plays and the QB stats table, which
# still rely on it.
_ROUTE_THROWN_CODES = {'rt1':'1','rt2':'2','rt3':'3','rt4':'4','rto':'O','rta':'A','rts':'Q','rtta':'TA'}
_RT_NORMALIZE = {'ALERT':'A'}
def rt_code(r):
    v = r['Route Thrown'].strip().upper()
    return _RT_NORMALIZE.get(v, v)
def route_thrown_block(items):
    n=len(items)
    return {k: pct(sum(1 for r in items if rt_code(r)==code), n)
            for k, code in _ROUTE_THROWN_CODES.items()}
def pass_block(items):
    b=stat_block(items); b['comp']=comp_pct(items); b.update(route_thrown_block(items)); return b
# 6MAN/5MAN/QG are protection/tempo tags, not route concepts (same category
# as RAP/MVMT/SCREEN -- see WARP_EXCLUDE below). A rep tagged only with one
# of these in the Play column, with no Primary/Reset or Full Concept also
# charted, is a charting gap: the coach still needs to note the actual route
# concept run under that protection call. Confirmed with Matt after "6MAN"
# wrongly showed up as its own standalone "concept" in Fall Camp Practice #2
# data (3 pass reps, Day 2 Skelly) -- it should never be treated as if it
# were a resolved concept. concept_name() now returns a clearly-flagged
# placeholder instead of silently using the bare protection tag, and
# validate_self_scout.py hard-warns whenever this placeholder shows up so it
# can't ship unnoticed again -- see that script's NEEDS_CONCEPT check.
_PROTECTION_ONLY_TAGS={'6MAN','5MAN','QG'}
# Screen plays are charted with Play='SCREEN' (a generic category tag, same
# idea as MVMT/RAP) and the ACTUAL screen call name lives in the Protection
# column instead -- e.g. Protection='50*51 INMATE' or '58*59 HANDCUFF' (the
# leading NN*NN is the numbered protection call for playside*backside, not
# part of the screen's name) or a bare 'PRISON'/'PRISON*JAIL'. Left alone,
# every screen rep collapses into one bare "SCREEN" bucket no matter which
# actual screen was run -- confirmed wrong by Matt (Fall Camp Practice #3+4
# data): each distinct screen call must show up as its own concept
# (JAIL/PRISON, INMATE, HANDCUFF, ...), same as any other named concept.
# JAIL and PRISON are the same underlying screen call (just two names/sides
# for it) and are always merged into one canonical "JAIL/PRISON" bucket --
# confirmed by Matt grouping a bare 'PRISON' and a combined 'PRISON*JAIL'
# under the same "JAIL/PRISON" label. Any other screen name passes through
# unchanged. If Protection doesn't resolve to a name (blank, or only
# numbers), this flags NEEDS CONCEPT (SCREEN) instead of guessing -- same
# "flag, don't guess" pattern as the 6MAN/5MAN/QG protection-tag fix.
_SCREEN_NAME_ALIASES={'JAIL':'JAIL/PRISON','PRISON':'JAIL/PRISON'}
# Direction/motion words that show up alongside a screen's real name in the
# Protection column (e.g. "SPRINT RT*LT WATERFALL", first seen Fall Camp
# Practice #7 -- confirmed against that rep's full Play Call text, which
# literally read "...Y-WATERFALL SCREEN", i.e. WATERFALL is the real name and
# "SPRINT RT"/"LT" are just protection/motion-direction tags, same role as
# the NN*NN numeric prefix). Stripped the same way numeric tokens are.
_SCREEN_DIRECTION_WORDS={'RT','LT','SPRINT'}
def screen_name(protection_raw):
    prot=(protection_raw or '').strip().upper()
    if not prot: return None
    names=[]
    for part in prot.split('*'):
        toks=[t for t in part.split() if not re.match(r'^\d+[A-Z]?$', t)
              and t not in _SCREEN_DIRECTION_WORDS]
        # A part that still has 2+ tokens after stripping numeric prefixes
        # and known direction words doesn't match any known shape -- joining
        # the words would guess at a name. Flag as unresolved (NEEDS CONCEPT)
        # instead; ask Matt what the real screen name is for this pattern.
        if len(toks)>1:
            return None
        if toks:
            nm=toks[0]
            names.append(_SCREEN_NAME_ALIASES.get(nm, nm))
    names=sorted(set(n for n in names if n))
    return '/'.join(names) if names else None
def concept_name(r):
    primary=r['Primary'].strip(); reset=r['Reset'].strip()
    if primary: return primary+(' / '+reset if reset else '')
    full=r['Full Concept'].strip()
    if full: return full
    play=r['Play'].strip()
    if play.upper()=='SCREEN':
        sn=screen_name(r.get('Protection',''))
        return sn if sn else 'NEEDS CONCEPT (SCREEN)'
    if play.upper() in _PROTECTION_ONLY_TAGS:
        return 'NEEDS CONCEPT ('+play.upper()+')'
    return play or '(unknown)'

ROSTER = {
 12:('K. Ryan','QB'),17:('Grunkemeyer','QB'),14:('T. Huhn','QB'),22:('B. Baker','QB'),
 16:('J. Overton Jr.','RB'),23:('T. Mason','RB'),35:('J. Buetow','RB'),
 46:('D. Taylor','RB'),27:('M. Hawkins','RB'),32:('B. Davis','RB'),
 26:('M. Mickens','RB'),49:('G. Peterson','RB'),50:('D. Taylor','RB'),
 36:('B. Jones','TE'),82:('B. Gosnell','TE'),13:('Ja. Hairston','TE'),
 87:('H. St. Germain','TE'),99:('C. Reemsnyder','TE'),
 44:('M. Henderson','TE'),85:('L. Reynolds','TE'),
 2:('T. Heath','WR'),6:('B. Adams','WR'),7:('C. Wiggins','WR'),
 0:('A. Greene','WR'),81:('I. Hairston','WR'),80:('L.J. Booker','WR'),
 18:('A.J. Brand','WR'),86:('J. Hobbs','WR'),15:('S. Peterkin','WR'),
 83:('L. Stuewe','WR'),28:('D. Hube','WR'),3:('Q. Brown','WR'),
 19:('T. Denmark','WR'),20:('J. Exinor Jr.','WR'),5:('M. Jackson','WR'),
 11:('D. Brown','WR'),
 51:('Haughawout','OL'),56:('Ghannam','OL'),66:('Cunningham','OL'),
 77:('B. Meadows','OL'),79:('J. Garrett','OL'),76:('A. Lynch','OL'),
 53:('T. Ricard','OL'),57:('L. Austin','OL'),62:('K. Altuner','OL'),
 71:('G. Crawford','OL'),61:('J. Bell','OL'),74:('M. Bright','OL'),
 75:('B. Eziuka','OL'),70:('L. Howland','OL'),65:('T. Simpson','OL'),
 72:('J. Terry','OL'),54:('M. Troutman III','OL'),52:('B. Wegdam','OL'),
 88:('P. Petersohn','TE'),
 89:('H. Zell','WR'),60:('M. Cochrane','OL'),55:('T. Wilder','OL'),
 58:('R. Lubintus','OL'),
}
def jint(val):
    if val is None: return None
    s=str(val).strip()
    if s in ('','-','N/A','n/a'): return None
    if s[:1] in ('O','o'): s=s[1:]
    try: return int(s)
    except: return None

FAM_ORDER=['WIDE ZONE','TITE ZONE','MID ZONE','GAP','DRAW']
# Some exports (e.g. Fall Camp Practice #3) chart Run Family using the same
# abbreviated shorthand as WARP_EXCLUDE (WZ/TZ/MZ) instead of the full name
# other weeks use (WIDE ZONE/TITE ZONE/MID ZONE) -- same underlying scheme,
# different spelling. Left unnormalized, a multi-day merge (all_variants)
# would split one real family into two separate rows (e.g. "WIDE ZONE" from
# one week + "WZ" from another) instead of combining them. Normalize to the
# full name so every week's data lands in the same bucket regardless of
# which shorthand that export happened to use.
_RUN_FAMILY_NORMALIZE={'WZ':'WIDE ZONE','TZ':'TITE ZONE','MZ':'MID ZONE'}
# Fall Camp Practice #5 had Run Family blank for the ENTIRE practice (see
# is_run/is_pass above) -- originally left the Run Family/Scheme breakdown
# table empty for that day rather than guess at a mapping. Matt then gave
# the actual rule: RunScheme's leading playside*backside number pair (e.g.
# '28*29 KEY', '0*1 FAN', '16*17 OPTION TOSS') uses the same 0-9 hole-
# numbering system used elsewhere in the CSV (Protection/screen calls) --
# the family is keyed off the LAST digit of the first number (if it's a
# two-digit call like '28' or '16', take the ones digit -- '28'->'8',
# '16'->'6'; a one-digit call like '0' or '4' is used directly). Confirmed
# against real Practice #5 data: '28*29 KEY' (digit 8) -> WIDE ZONE,
# '24*25 COWBOY' (digit 4) -> MID ZONE, matching the digit map below built
# from Matt's direct examples (TZ=0*1, MZ=4*5, GAP=6*7, WZ=8*9). DRAW has
# no number -- it's the literal word 'PAINT' instead (Matt: "DRAW = PAINT").
# This ONLY supplies a family when the CSV's own Run Family column is blank
# -- a charted Run Family value always wins, this is purely a backfill for
# the charting-gap scenario, not a general override.
_SCHEME_DIGIT_FAMILY={'0':'TITE ZONE','1':'TITE ZONE','4':'MID ZONE','5':'MID ZONE',
                      '6':'GAP','7':'GAP','8':'WIDE ZONE','9':'WIDE ZONE'}
def family_from_scheme(scheme_raw):
    s=(scheme_raw or '').strip().upper()
    if not s: return None
    if 'PAINT' in s: return 'DRAW'
    m=re.search(r'(\d+)\s*\*\s*\d+', s)
    if not m: return None
    digit=m.group(1)[-1]
    return _SCHEME_DIGIT_FAMILY.get(digit)
def run_family_of(r):
    fam=r['Run Family'].strip().upper()
    fam=_RUN_FAMILY_NORMALIZE.get(fam, fam)
    if fam: return fam
    return family_from_scheme(r.get('RunScheme','')) or ''

run_rows=[r for r in rows if is_run(r)]
pass_rows=[r for r in rows if is_pass(r)]
# Restrict to actual RUN reps (is_run(r)) even though run_family_of() can
# resolve a family from RunScheme alone -- a couple of Practice #5 rows
# have BOTH a RunScheme value charted AND a real pass result (an RPO-style
# rep where the scheme was called but the ball was thrown), and those must
# stay out of the Run Family/Scheme breakdown table the same way they
# always have (that table is runs only) -- confirmed 3 such rows (#45, #53,
# #60, all pff_RUNPASS='P' with a populated RunScheme) would otherwise have
# been double-counted into both n_pass and a run family bucket.
fam_rows=[r for r in rows if is_run(r) and run_family_of(r)]
n=len(rows); n_run=len(run_rows); n_pass=len(pass_rows)

fam_map={}
for r in fam_rows:
    fam=run_family_of(r)
    sch=r['RunScheme'].strip() or '(unnamed)'
    fam_map.setdefault(fam, {}).setdefault(sch, []).append(r)
run_families=[]
for fam, schemes in sorted(fam_map.items(), key=lambda kv: -sum(len(v) for v in kv[1].values())):
    all_fam_rows=[r for sr in schemes.values() for r in sr]
    fobj=stat_block(all_fam_rows); fobj['name']=fam
    fr=[r for r in all_fam_rows if is_run_sub(r)]; fp=[r for r in all_fam_rows if is_pass_sub(r)]
    if fr and fp:
        fobj['run_sub']=stat_block(fr)
        fobj['pass_sub']=stat_block(fp)
    scheme_list=[]
    for sch, sr in sorted(schemes.items(), key=lambda kv:-len(kv[1])):
        sobj=stat_block(sr); sobj['name']=sch
        sr_run=[r for r in sr if is_run_sub(r)]; sr_pass=[r for r in sr if is_pass_sub(r)]
        if sr_run and sr_pass:
            sobj['run_sub']=stat_block(sr_run)
            sobj['pass_sub']=stat_block(sr_pass)
        scheme_list.append(sobj)
    fobj['schemes']=scheme_list
    run_families.append(fobj)

rz_rows=[r for r in pass_rows if is_rz(r)]

# RPO run plays (named WARP run-play calls with a built-in pass option) do
# NOT belong in the Pass Concepts table -- confirmed with Matt: they're run
# plays first, already broken out with their own RUN/PASS sub-split in the
# WARP Plays table, and showing up here too (usually as a bare play-name
# row like "CYCLONE" since these reps have no real Primary/Full Concept
# tagged) just duplicates/confuses that. This ONLY filters what feeds the
# Pass Concepts table (legacy flat pass_concepts + pass_groups below) --
# it deliberately does NOT touch the broader pass_rows used for QB/receiver
# stats, sacks, or overall pass_overall, since a ball genuinely thrown on
# one of these reps still counts as a real pass attempt for those. If a
# new RPO-style run play with a pass option shows up, don't guess -- ask
# before adding it here.
RPO_RUN_PLAYS={'CYCLONE','KOBE','HEDGEHOG','MARKER'}
pc_pass_rows=[r for r in pass_rows if r['Play'].strip().upper() not in RPO_RUN_PLAYS]

gm_all={}
for r in pc_pass_rows: gm_all.setdefault(concept_name(r), []).append(r)
pass_concepts=[]
for nm, items in sorted(gm_all.items(), key=lambda kv:-len(kv[1])):
    c=pass_block(items); c['name']=nm; pass_concepts.append(c)

# WARP plays = named play-calls pulled from the raw 'Play' column, excluding
# protection/category tags that aren't real named plays. NOTE: this is NOT
# filtered to rows where Procedure=='WARP' -- 'Procedure' only tracks how the
# call was communicated that rep (HUDDLE/WARP one-word/ALASKA no-huddle), not
# whether the play itself belongs in this table. The same named play (e.g.
# TIFFANY) can show up huddled one rep and warp-called the next; both count.
# Requiring Procedure=='WARP' here previously dropped the vast majority of
# real reps (a named play called via HUDDLE is still that named play).
# ALSO NOT filtered to pass reps only (Run Family blank) -- a named WARP
# play-call can be a designed run (e.g. HEDGEHOG, BLOODHOUND), and Matt
# wants those included in the WARP Plays section too, with a RUN/PASS
# sub-breakdown per play mirroring the Run Family section's pattern (see
# is_run_sub/is_pass_sub + the run_sub/pass_sub gate in _warp_list below).
# NOTE: WZ/TZ/GAP/MZ are NOT real WARP play names -- they're generic
# Wide Zone/Tite Zone/Gap/Mid Zone run-FAMILY shorthand (same as the
# Run Family tag itself), used when no distinct coded play name was
# called. A genuine named/coded run call (HEDGEHOG, BLOODHOUND, etc.)
# belongs in WARP Plays; a bare family abbreviation does not. Confirmed
# by Matt after Practice #2 (WZ had shown up as a WARP entry -- wrong).
WARP_EXCLUDE={'RAP','MVMT','SCREEN','6MAN','5MAN','QG','WZ','TZ','GAP','MZ'}
warp_map={}
for r in rows:
    nm=r['Play'].strip() or '(unknown)'
    if nm in WARP_EXCLUDE: continue
    warp_map.setdefault(nm, []).append(r)
warp_plays=[]
for nm, items in sorted(warp_map.items(), key=lambda kv:-len(kv[1])):
    isp=[r for r in items if is_pass(r)]
    b=stat_block(items); b['comp']=comp_pct(isp) if isp else 0.0; b.update(route_thrown_block(isp) if isp else {}); b['name']=nm
    warp_plays.append(b)

# ── Sectioned Pass Concepts (CONCEPTS / MVMT-RAP / SCREEN / RZ PASS) ────
# Same divider grouping as Spring's self-scout Pass tab: concepts_rows is
# everything except MVMT/RAP/SCREEN tags (those get their own sections),
# and RZ PASS is a separate overlapping view (any pass rep with field
# position <=12, regardless of which of the other 3 buckets it's also in).
def _concept_list(items_all):
    gm={}
    for r in items_all: gm.setdefault(concept_name(r), []).append(r)
    out=[]
    for nm, items in sorted(gm.items(), key=lambda kv:-len(kv[1])):
        c=pass_block(items); c['name']=nm; out.append(c)
    return out

_concepts_rows=[r for r in pc_pass_rows if r['Play'].strip() not in ('MVMT','RAP','SCREEN')]
_mvmt_rap_rows=[r for r in pc_pass_rows if r['Play'].strip() in ('MVMT','RAP')]
_screen_rows=[r for r in pc_pass_rows if r['Play'].strip()=='SCREEN']
_rz_pass_rows=[r for r in pc_pass_rows if is_rz(r)]
pass_groups={
    'concepts':_concept_list(_concepts_rows), 'concepts_total':pass_block(_concepts_rows),
    'mvmt_rap':_concept_list(_mvmt_rap_rows), 'mvmt_rap_total':pass_block(_mvmt_rap_rows),
    'screen':_concept_list(_screen_rows), 'screen_total':pass_block(_screen_rows),
    'rz':_concept_list(_rz_pass_rows), 'rz_total':pass_block(_rz_pass_rows),
    'overall_total':pass_block(pc_pass_rows),
}

# ── Sectioned WARP Plays (TOTAL, then per-procedure HUDDLE/WARP/ALASKA/WAIT) ──
def _warp_play_row(items):
    b=stat_block(items); b['comp']=comp_pct(items) if items else 0.0
    return b
def _warp_list(items_by_name):
    out=[]
    for nm, items in sorted(items_by_name.items(), key=lambda kv:-len(kv[1])):
        p=_warp_play_row(items); p['name']=nm
        wr=[r for r in items if is_run_sub(r)]; wpv=[r for r in items if is_pass_sub(r)]
        if wr and wpv:
            p['run_sub']=_warp_play_row(wr); p['run_sub']['name']='RUN'
            p['pass_sub']=_warp_play_row(wpv); p['pass_sub']['name']='PASS'
        out.append(p)
    return out

_warp_all_items=[r for items in warp_map.values() for r in items]
warp_groups={
    'total_section':_warp_list(warp_map),
    'total':_warp_play_row(_warp_all_items),
    'procedures':{},
}
for _proc in ['HUDDLE','WARP','ALASKA','WAIT']:
    _pm={}
    for r in rows:
        if r['Procedure'].strip().upper() != _proc: continue
        _nm=r['Play'].strip() or '(unknown)'
        if _nm in WARP_EXCLUDE: continue
        _pm.setdefault(_nm, []).append(r)
    _proc_items=[r for items in _pm.values() for r in items]
    warp_groups['procedures'][_proc]={'plays':_warp_list(_pm), 'total':_warp_play_row(_proc_items)}

POS_KEYS=['H','F','Q','Y','Z','X']
positions=[]
for pos in POS_KEYS:
    p_rows=[r for r in rows if r['TRACKING'].strip()==pos]
    if not p_rows: continue
    b=stat_block(p_rows); b['pos']=pos; b['pct']=pct(len(p_rows), n)
    b['carry_n']= n_run if pos=='H' else 0
    b['target_n']=len(p_rows)
    positions.append(b)

sacks=sum(1 for r in pass_rows if is_sack(r))
sack_pct=pct(sacks, n_pass)
overall=stat_block(rows); run_overall=stat_block(run_rows); pass_overall=pass_block(pass_rows)

# ── Individual player breakdowns (name-level, from jersey-tagged columns) ──
qb_map={}
for r in pass_rows:
    j=jint(r['pff_QB'])
    if j is None: continue
    qb_map.setdefault(j, []).append(r)
qbs=[]
for j, items in sorted(qb_map.items(), key=lambda kv:-len(kv[1])):
    name=ROSTER.get(j, ('#'+str(j),'QB'))[0]
    b=pass_block(items); b['name']=name; b['jersey']=j
    b['sacks']=sum(1 for r in items if is_sack(r)); b['sack_pct']=pct(b['sacks'], len(items))
    qbs.append(b)

rb_rush_map={}
for r in run_rows:
    j=jint(r['pff_RBS'])
    if j is None: continue
    rb_rush_map.setdefault(j, []).append(r)
rb_recv_map={}
for r in pass_rows:
    if r['TRACKING'].strip() != 'H': continue
    j=jint(r['Target'])
    if j is None: continue
    rb_recv_map.setdefault(j, []).append(r)
all_rb_j=sorted(set(list(rb_rush_map.keys())+list(rb_recv_map.keys())), key=lambda j:-len(rb_rush_map.get(j,[])))
rbs=[]
for j in all_rb_j:
    name=ROSTER.get(j, ('#'+str(j),'RB'))[0]
    rush_items=rb_rush_map.get(j, []); recv_items=rb_recv_map.get(j, [])
    if not rush_items and not recv_items: continue
    rush_b=stat_block(rush_items) if rush_items else {'n':0,'avg':0,'eff':0,'expl':0,'neg':0}
    recv_b=pass_block(recv_items) if recv_items else {'n':0,'avg':0,'eff':0,'comp':0}
    rbs.append({'name':name,'jersey':j,'rush':rush_b,
                'recv':{'n':recv_b['n'],'avg':recv_b['avg'],'eff':recv_b['eff'],'comp':recv_b['comp']}})
rbs.sort(key=lambda r:-r['rush']['n'])

recv_map={}
for r in pass_rows:
    if r['TRACKING'].strip()=='H': continue
    j=jint(r['Target'])
    if j is None: continue
    recv_map.setdefault(j, []).append(r)
receivers=[]
for j, items in sorted(recv_map.items(), key=lambda kv:-len(kv[1])):
    ros=ROSTER.get(j); name=ros[0] if ros else ('#'+str(j)); pos=ros[1] if ros else 'WR'
    if pos not in ('TE','WR'): continue
    b=pass_block(items); b['name']=name; b['jersey']=j; b['pos']=pos
    b['drops']=sum(1 for r in items if is_drop(r))
    receivers.append(b)

qb_group=dict(pass_overall); qb_group['name']='QB Group'; qb_group['sacks']=sacks; qb_group['sack_pct']=sack_pct; qb_group['concepts']=[]
rb_recv_rows=[r for r in pass_rows if r['TRACKING'].strip()=='H']
rb_group={'name':'RB Group','rush':run_overall,
          'recv': {k:pass_block(rb_recv_rows)[k] for k in ('n','avg','comp','eff')} if rb_recv_rows else {'n':0,'avg':0,'eff':0,'comp':0}}

te_rows=[r for r in pass_rows if r['TRACKING'].strip()=='Y']
wr_rows=[r for r in pass_rows if r['TRACKING'].strip() in ('X','Z','F')]
recv_groups=[]
if te_rows:
    b=pass_block(te_rows); b.update({'pos':'Y','label':'TE','name':'TE (Y)'})
    b['drops']=sum(1 for r in te_rows if is_drop(r))
    recv_groups.append(b)
if wr_rows:
    b=pass_block(wr_rows); b.update({'pos':'Z','label':'WR','name':'WR (Z)'})
    b['drops']=sum(1 for r in wr_rows if is_drop(r))
    recv_groups.append(b)

down_data=[]
for d in ['1','2','3','4']:
    dr=[r for r in rows if r['pff_DOWN'].strip()==d]
    if not dr: continue
    b=stat_block(dr); b['down']=int(d)
    b['run_n']=sum(1 for r in dr if is_run(r)); b['pass_n']=sum(1 for r in dr if is_pass(r))
    down_data.append(b)
third_rows_all=[r for r in rows if r['pff_DOWN'].strip()=='3']
buckets3=[('Short (1-3)', lambda x:1<=x<=3), ('Medium (4-6)', lambda x:4<=x<=6), ('Long (7+)', lambda x:x>=7)]
third_data=[]
for label, cond in buckets3:
    br=[r for r in third_rows_all if r['pff_DISTANCE'].strip() and cond(float(r['pff_DISTANCE']))]
    if not br: continue
    b=stat_block(br); b['label']=label
    b['run_n']=sum(1 for r in br if is_run(r)); b['pass_n']=sum(1 for r in br if is_pass(r))
    third_data.append(b)
pers_vals={}
for r in rows:
    pv=r['pff_OFFPERSONNELBASIC'].strip()
    if pv: pers_vals.setdefault(pv, []).append(r)
pers_data=[]
for pv, pr in sorted(pers_vals.items(), key=lambda kv:-len(kv[1])):
    b=stat_block(pr); b['pers']=pv
    b['run_n']=sum(1 for r in pr if is_run(r)); b['pass_n']=sum(1 for r in pr if is_pass(r))
    pers_data.append(b)
group_data=[]
for g in ['1','2','3']:
    gr=[r for r in rows if r['Group'].strip()==g]
    if not gr: continue
    b=stat_block(gr); b['group']='Group '+g
    group_data.append(b)
procedure_data=[]
for proc in ['HUDDLE','WARP','ALASKA']:
    pr=[r for r in rows if r['Procedure'].strip()==proc]
    if not pr: continue
    b={'procedure':proc,'n':len(pr),'run_n':sum(1 for r in pr if is_run(r)),'pass_n':sum(1 for r in pr if is_pass(r)),
       'avg':avgy(pr),'eff':pct(sum(1 for r in pr if is_eff(r)),len(pr)),'expl':pct(sum(1 for r in pr if is_expl(r)),len(pr))}
    procedure_data.append(b)

skill_map={}
for r in rows:
    qb=jint(r['pff_QB']); rb=jint(r['pff_RBS'])
    pers=r['pff_OFFPERSONNELBASIC'].strip()
    slots=[jint(r['POSITION_Y']),jint(r['POSITION_F']),jint(r['POSITION_Z']),jint(r['POSITION_X'])]
    tes=sorted(set(j for j in slots if j is not None and ROSTER.get(j,(None,None))[1]=='TE'))
    wrs=sorted(set(j for j in slots if j is not None and ROSTER.get(j,(None,'WR'))[1]!='TE'))
    key='|'.join(str(x) for x in ([qb,rb]+tes+wrs+[pers]))
    skill_map.setdefault(key, {'qb':qb,'rb':rb,'tes':tes,'wrs':wrs,'pers':pers,'rows':[]})
    skill_map[key]['rows'].append(r)
skill_lineups=[]
for key, info in sorted(skill_map.items(), key=lambda kv:-len(kv[1]['rows'])):
    items=info['rows']
    b=stat_block(items)
    b['pers']=info['pers']; b['qb']=info['qb']; b['rb']=info['rb']; b['tes']=info['tes']; b['wrs']=info['wrs']
    b['run_n']=sum(1 for r in items if is_run(r))
    play_map={}
    for r in items:
        call=(r['Play Call'].strip() or r['Play'].strip() or '(unknown)')
        play_map.setdefault(call, []).append(r)
    plays=[]
    for call, pitems in sorted(play_map.items(), key=lambda kv:-len(kv[1])):
        typ='RUN' if is_run(pitems[0]) else 'PASS'
        plays.append({'call':call,'type':typ,'n':len(pitems),'avg':avgy(pitems),'eff':round(pct(sum(1 for r in pitems if is_eff(r)),len(pitems)))})
    b['plays']=plays
    skill_lineups.append(b)

ol_map={}
for r in rows:
    lt=jint(r['Jersey #2']); lg=jint(r['Jersey #3']); c=jint(r['Jersey #4']); rg=jint(r['Jersey #5']); rt=jint(r['Jersey #6'])
    if None in (lt,lg,c,rg,rt): continue
    key=(lt,lg,c,rg,rt)
    ol_map.setdefault(key, []).append(r)
ol_lineups=[]
for key, items in sorted(ol_map.items(), key=lambda kv:-len(kv[1])):
    run_items=[r for r in items if is_run(r)]
    if not run_items: continue
    b=stat_block(run_items)
    b['lt'],b['lg'],b['c'],b['rg'],b['rt']=key
    play_map={}
    for r in run_items:
        call=(r['Play Call'].strip() or r['Play'].strip() or '(unknown)')
        play_map.setdefault(call, []).append(r)
    plays=[]
    for call, pitems in sorted(play_map.items(), key=lambda kv:-len(kv[1])):
        plays.append({'call':call,'type':'RUN','n':len(pitems),'avg':avgy(pitems),'eff':round(pct(sum(1 for r in pitems if is_eff(r)),len(pitems)))})
    b['plays']=plays
    ol_lineups.append(b)

data = {
    'n':n, 'n_run':n_run, 'n_pass':n_pass, 'avg':overall['avg'], 'eff':overall['eff'],
    'expl':overall['expl'], 'neg':overall['neg'], 'comp':pass_overall['comp'], 'sack_pct':sack_pct,
    'run_families':run_families, 'run_overall':run_overall,
    'rz':{'n':len(rz_rows),'avg':avgy(rz_rows),'eff':pct(sum(1 for r in rz_rows if is_eff(r)),len(rz_rows)) if rz_rows else 0,'comp':comp_pct(rz_rows) if rz_rows else 0},
    'of':{'n':pass_overall['n'],'avg':pass_overall['avg'],'eff':pass_overall['eff'],'comp':pass_overall['comp']},
    'qb_group':qb_group, 'rb_group':rb_group, 'recv_groups':recv_groups,
    'pass_concepts':pass_concepts, 'warp_plays':warp_plays, 'positions':positions,
    'down_data':down_data, 'third_data':third_data, 'pers_data':pers_data, 'group_data':group_data,
    'procedure_data':procedure_data, 'skill_lineups':skill_lineups, 'ol_lineups':ol_lineups,
    'qbs':qbs, 'rbs':rbs, 'receivers':receivers,
    'pass_groups':pass_groups, 'warp_groups':warp_groups,
}
with open(os.path.join(out_dir, f'{day_key}_{variant}.json'),'w') as f:
    json.dump(data, f)
print(f"[{variant}] n={n} n_run={n_run} n_pass={n_pass} skill_lineups={len(skill_lineups)} ol_lineups={len(ol_lineups)} "
      f"qbs={len(qbs)} rbs={len(rbs)} receivers={len(receivers)}")

_needs_concept=[r for r in pc_pass_rows if concept_name(r).startswith('NEEDS CONCEPT')]
if _needs_concept:
    print(f"[{variant}] WARNING: {len(_needs_concept)} pass rep(s) tagged with a protection/tempo-only "
          f"Play value ({', '.join(sorted(set(concept_name(r) for r in _needs_concept)))}) and no "
          f"Primary/Reset or Full Concept charted -- these will show as a flagged 'NEEDS CONCEPT' row "
          f"instead of a real concept until the CSV (or Matt) supplies the actual concept. Affected reps:")
    for r in _needs_concept:
        print(f"    # {r.get('#','?')}  QB {r.get('pff_QB','?')}  Play='{r['Play'].strip()}'  "
              f"Play Call='{r.get('Play Call','').strip()}'")
