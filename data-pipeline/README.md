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

## Workflow for a new practice CSV

```bash
# 1. Build all three rep-filter variants
python3 build_spring_variant.py team     /path/to/practice.csv output/
python3 build_spring_variant.py skelly   /path/to/practice.csv output/
python3 build_spring_variant.py combined /path/to/practice.csv output/
# (or build_period_variant.py <variant> <csv> <day_key> output/ for Fall/Season)

# 2. Splice into the page
python3 splice_data.py spring self-scout.html \
  --team-dir output/ --skelly-dir output/ --combined-dir output/
# (or: splice_data.py period self-scout.html --js-var FALL_DATA
#      --day-key fall_2 --new-day --label "Day 2" --date 2026-08-05
#      --team-json output/fall_2_team.json ...)

# 3. Validate before committing
python3 validate_self_scout.py self-scout.html
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

### WARP total consistency
`PW_DATA.warp.total` (and every `PW_DATA.warp.procedures.<TEMPO>.total`)
must be computed from the **same filtered row set** as the entries next to
it, never from the full unfiltered row list:
```python
warp_all_items = [r for items in warp_map.values() for r in items]
PW_warp = {'total_section': ..., 'total': warp_play_row(warp_all_items), ...}
```
`validate_self_scout.py` checks `total.n == sum(entry.n for entry in
total_section)` and that it's `<= pass_ov.n <= overall.n`. If that check
fails, `total` is being computed over the wrong rows again.

### Concept naming (Pass Concepts / Red Zone tabs -- NOT WARP)
```python
def concept_name(r):
    primary = r['Primary'].strip(); reset = r['Reset'].strip()
    if primary: return primary + (' / ' + reset if reset else '')
    full = r['Full Concept'].strip()
    if full: return full
    return r['Play'].strip() or '(unknown)'
```

### Jersey parsing
Strip a leading `O`/`o`, then `int()`. Empty string / `-` / `N/A` -> `None`
(missing). `0` is a valid jersey number.

### Roster
`ROSTER` (jersey -> `(name, position)`) is hardcoded at the top of both
build scripts. **Update it there** whenever the roster changes (transfers,
new signees) -- it is not read from the CSV.

## Known pre-existing limitation

The Team variant's `pass_ov.n`/`run_ov.n` (553/363) are the original,
already-shipped baseline and were **not** regenerated from this pipeline --
only its WARP section was rebuilt (surgically) to fix the total-inflation
bug. If you ever fully rebuild Team from a CSV with this pipeline you'll
get 548/368 instead (a ~5-play difference, previously investigated and
accepted as noise in the source data). Don't be alarmed by that gap; don't
"fix" it without checking with Matt first, since 553/363 is the number
that's been validated and shipped.
