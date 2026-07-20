# Self-Scout Data Pipeline

Scripts for turning a 61-column XOS/PFF practice CSV export into the baked
JSON data that powers `self-scout.html`'s Spring 2026 / Fall Camp / Season
Practices sections, including the Team / Skelly / Combined rep-filter.

Everything here was hardened after a round of bugs found in the Skelly and
Combined filter views (wrong WARP play names, phantom run/pass
sub-breakdowns, an inflated WARP total). The rules below are the direct
result of that debugging -- **follow them exactly** when processing new
practice data, don't re-derive them from scratch.

## Files

- `build_spring_variant.py` -- builds `D` / `RUN_DATA` / `PW_DATA` /
  `PLAYER_DATA` for one rep-filter variant (`team`, `skelly`, or
  `combined`) from a practice CSV. Used for Spring 2026's schema (the one
  with separate `D.warp` / `RUN_DATA.families` / `PW_DATA.pass` / `PW_DATA.warp`
  objects).
- `build_period_variant.py` -- builds the flatter single-object schema used
  by Fall Camp / Season Practices (`n`, `n_run`, `n_pass`, `run_families`,
  `warp_plays`, etc. all in one dict). Reusable for every future practice
  day -- pass a `day_key` (e.g. `fall_2`, `season_wk3`) and it writes
  `<day_key>_<variant>.json`.
- `splice_data.py` -- injects the JSON those two scripts produce back into
  `self-scout.html`, replacing only the `const SPRING_VARIANTS = {...}` or
  `var FALL_DATA = {...}` / `var INSEASON_DATA = {...}` blob. Never
  hand-edit that JSON in the HTML file directly -- always regenerate with
  the build script and splice it in, so the two stay in sync.
- `validate_self_scout.py` -- run this on `self-scout.html` after every
  splice, before committing. It fails loudly on any of the bug classes
  below. **Never ship without a clean run of this.**

## IMPORTANT -- the site is now password-locked (read this first)

As of the encryption pass, `self-scout.html`, `advance-scout.html`, and
`index.html` in the repo root are the **locked/deployed** versions -- their
`<body>` is AES-256-GCM ciphertext, not readable/editable HTML. **This
whole pipeline (build → splice → validate) only works against the
plaintext master, never against a locked file.**

The plaintext masters live in `_source/` (gitignored -- never committed,
never pushed to the public repo):

- `_source/self-scout.html`
- `_source/advance-scout.html`
- `_source/index.html`

Workflow for ANY future edit (data pipeline or hand edit alike):

```bash
# 1. Do all your normal work (pipeline steps below, or hand edits) against
#    the PLAINTEXT master in _source/, e.g.:
python3 splice_data.py spring _source/self-scout.html ...
python3 validate_self_scout.py _source/self-scout.html

# 2. Re-lock it to produce the deployable file (same password each time --
#    ask Matt if it's not already in hand):
node security-tools/lock_page.js _source/self-scout.html self-scout.html HOKIESOFF2026

# 3. Commit/push self-scout.html (the locked one). Never commit anything
#    from _source/.
```

If a locked file is ever committed without a matching update to its
`_source/` master, or the master is lost, the deployed file cannot be
edited or re-locked -- there is no way to recover the plaintext body from
ciphertext without the password. Keep `_source/` backed up (it's synced to
Matt's local Projects folder alongside the deployed files, in a clearly
separate location).

## Workflow for a new practice CSV

```bash
# 1. Build all three rep-filter variants
python3 build_spring_variant.py team     /path/to/practice.csv output/
python3 build_spring_variant.py skelly   /path/to/practice.csv output/
python3 build_spring_variant.py combined /path/to/practice.csv output/
# (or build_period_variant.py <variant> <csv> <day_key> output/ for Fall/Season)

# 2. Splice into the PLAINTEXT MASTER (not the locked repo-root file!)
python3 splice_data.py spring _source/self-scout.html \
  --team-dir output/ --skelly-dir output/ --combined-dir output/
# (or: splice_data.py period _source/self-scout.html --js-var FALL_DATA
#      --day-key fall_2 --new-day --label "Day 2" --date 2026-08-05
#      --team-json output/fall_2_team.json ...)

# 3. Validate before locking/committing
python3 validate_self_scout.py _source/self-scout.html

# 4. Re-lock to produce the deployable file, then commit/push THAT
node security-tools/lock_page.js _source/self-scout.html self-scout.html HOKIESOFF2026
```

If validation fails, fix the build script (not the HTML by hand) and
re-run the whole loop.

## Corrected business rules (the "why")

### Row filtering
- Drop `pff_RUNPASS` in `('PEN','NP','')` -- penalties and no-plays aren't
  real reps.
- `COMPETITIVE` column has three values: `TEAM`, `LIVE`, `SKELLY`.
  - **`team` variant** = everything except `SKELLY` (i.e. `TEAM` + `LIVE`).
  - **`skelly` variant** = `COMPETITIVE == 'SKELLY'` only.
  - **`combined` variant** = no filter, every row.

### Run vs. pass (the *called* play)
```python
def is_run(r):  return r['Run Family'].strip() != ''
def is_pass(r): return r['Run Family'].strip() == ''
```
This is about the **called** play type. Do NOT use `pff_RUNPASS` for this
split -- it produces a ~20-play gap vs. the validated numbers. `Run Family`
is the correct column.

### Negative play
```python
def is_neg(r): return gain(r) < 0 or is_sack(r)
```
A 0-yard gain is NOT a negative play. Only actual yardage loss or a sack
counts.

### Completion %
Denominator is targeted attempts only (`pff_PASSRESULT in ('C','I','D')`),
excluding sacks/scrambles/spikes:
```python
def comp_pct(items):
    targeted = [r for r in items if r['pff_PASSRESULT'].strip() in ('C','I','D')]
    return pct(sum(1 for r in targeted if is_comp(r)), len(targeted))
```

### Drops
`pff_PASSRESULT == 'D'` marks a drop -- charged to the intended receiver,
not the QB. Counted (not just included in the targeted-attempts
denominator) via `pass_block()`, which every per-player receiving stat
block (QB `concepts`/pass totals, RB `recv`, WR/TE `receivers`) is built
from -- so `drops` is always present alongside `comp` with zero extra
wiring needed for future practice data:
```python
def is_drop(r): return r['pff_PASSRESULT'].strip()=='D'
def pass_block(items):
    b = stat_block(items); b['comp']=comp_pct(items)
    b['drops']=sum(1 for r in items if is_drop(r))
    return b
```
Rendered as a **DROPS** column in `self-scout.html`'s RB Receiving and
WR/TE pass-target tables (`rbRecvTbody` / `recvTbody`). Not currently
surfaced for QBs (they don't drop their own passes) even though the field
exists on their stat block too -- harmless, just unused there.

### Run/pass sub-breakdown WITHIN a called run-scheme or WARP play
This is about the **outcome**, not the call -- "did this called run actually
end in a handoff, or did it get thrown (RPO/broken play)?"
```python
def is_run_sub(r):
    pr = r['pff_PASSRESULT'].strip()
    if pr == 'R': return True
    if pr == '':  return r['pff_RUNPASS'].strip() == 'R'  # blank result: fall back to the called tag
    return False
def is_pass_sub(r):
    return r['pff_PASSRESULT'].strip() in ('C','I','S','D','X','Q')
```
**Do not** treat a blank `pff_PASSRESULT` as an automatic run (`in ('R','')`
was the original bug) -- it silently turned every play with missing PFF
data into a false run, even on called-pass rows.

### "Both-or-neither" display rule
A `run_sub` / `pass_sub` pair should **only** be added to an entry if BOTH
exist:
```python
fr = [r for r in items if is_run_sub(r)]
fp = [r for r in items if is_pass_sub(r)]
if fr and fp:
    entry['run_sub'] = stat_block(fr)
    entry['pass_sub'] = stat_block(fp)
# else: add neither key. A 100%-run or 100%-pass entry doesn't need a
# redundant sub-breakdown that just repeats its own totals.
```
If you see an entry with only `run_sub` OR only `pass_sub` but not both,
that's a bug -- `validate_self_scout.py` will catch it.

### WARP naming and scope
WARP entries are **real named play-calls** (city names, animal names,
misc nouns -- e.g. `MISSOURI`, `COLORADO`, `SAN DIEGO`, `BLOODHOUND`),
**not** protection calls or run-scheme/category abbreviations. Scope:
```python
WARP_EXCLUDE = {'RAP','MVMT','SCREEN','6MAN','5MAN','QG'}
warp_map = {}
for r in rows:
    if r['Run Family'].strip() != '': continue          # run plays excluded entirely
    nm = r['Play'].strip() or '(unknown)'
    if nm in WARP_EXCLUDE: continue                       # protection/category tags excluded
    warp_map.setdefault(nm, []).append(r)
```
Use the **raw `Play` column value** as the name here -- NOT the
`concept_name()` fallback logic used for `pass_concepts`/`rz_concepts`.
(We tried `concept_name()` for WARP once; it renamed real WARP plays like
`MISSOURI` to their underlying route concept, e.g. `SWERVE`, which is
wrong -- WARP is about the play-CALL name, not the route concept thrown.)

**If a new literal `Play` value shows up in future data that you can't
confidently classify as a real play-call name vs. a protection/category
tag, don't guess -- add it to neither list and ask Matt.** Wrong guesses
here are exactly what caused this whole debugging cycle.

### WARP total