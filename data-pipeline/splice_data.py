#!/usr/bin/env python3
"""
splice_data.py -- inject freshly-built variant JSON into self-scout.html

Usage:
  # Spring 2026 (or any single-period-with-3-variants dataset stored as
  # `const SPRING_VARIANTS = {...}` in the page):
  python3 splice_data.py spring self-scout.html \
      --team-dir output/ --skelly-dir output/ --combined-dir output/ \
      [--js-var SPRING_VARIANTS]

  Each --*-dir must contain D_<variant>.json, RUN_DATA_<variant>.json,
  PW_DATA_<variant>.json, PLAYER_DATA_<variant>.json (the exact filenames
  build_spring_variant.py writes). Only the variants you pass a --*-dir for
  get replaced; anything you omit is left untouched.

  # Fall Camp / Season Practices (data stored as
  # `var FALL_DATA = {...}` or `var INSEASON_DATA = {...}`):
  python3 splice_data.py period self-scout.html \
      --js-var FALL_DATA --day-key fall_2 \
      --team-json output/fall_2_team.json \
      --skelly-json output/fall_2_skelly.json \
      --combined-json output/fall_2_combined.json \
      [--label "Day 2"] [--date 2026-08-05] [--new-day]

  --new-day appends a new entry to `days[]` (use for a brand-new practice
  day). Omit it to overwrite an existing day that matches --day-key.
  After every day is spliced, `all_variants` is automatically recomputed
  as a simple merge equal to the most recent day's variants (single-day
  camps) -- for multi-day camps you'll want to extend this script's
  `merge_all_variants()` to properly combine multiple days before it's
  trustworthy; it is NOT done automatically for >1 day.

Both subcommands:
  1. Parse the exact JS object literal out of the page (brace-depth scan,
     not regex -- these blobs are minified onto one line).
  2. json.loads it, mutate only the requested keys, json.dumps it back
     with compact separators, and splice the replacement back into the
     original HTML text (everything outside the object is byte-identical).
  3. Leave validation to validate_self_scout.py -- ALWAYS run that next.
"""
import argparse, json, os, sys


def extract_js_object(html, prefix):
    start = html.find(prefix)
    if start == -1:
        raise SystemExit(f"Could not find '{prefix}' in the page.")
    start += len(prefix)
    depth = 0
    started = False
    end = None
    for j in range(start, len(html)):
        c = html[j]
        if c == '{':
            depth += 1
            started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                end = j + 1
                break
    if end is None:
        raise SystemExit(f"Could not find matching closing brace for '{prefix}'.")
    return start, end, json.loads(html[start:end])


def splice_js_object(html, prefix, new_obj):
    start, end, _old = extract_js_object(html, prefix)
    new_blob = json.dumps(new_obj, separators=(',', ':'))
    return html[:start] + new_blob + html[end:]


def cmd_spring(args):
    html = open(args.html, encoding='utf-8').read()
    prefix = f'const {args.js_var} = '
    start, end, sv = extract_js_object(html, prefix)

    dirs = {'team': args.team_dir, 'skelly': args.skelly_dir, 'combined': args.combined_dir}
    for variant, d in dirs.items():
        if not d:
            continue
        if variant not in sv:
            print(f"WARNING: '{variant}' not present in {args.js_var}, skipping.")
            continue
        for key, fname in [('D', 'D'), ('RUN_DATA', 'RUN_DATA'), ('PW_DATA', 'PW_DATA'), ('PLAYER_DATA', 'PLAYER_DATA')]:
            path = os.path.join(d, f'{fname}_{variant}.json')
            if not os.path.exists(path):
                print(f"WARNING: {path} not found, leaving existing '{variant}'.{key} untouched.")
                continue
            sv[variant][key] = json.load(open(path))
        print(f"Spliced '{variant}' from {d}")

    new_html = html[:start] + json.dumps(sv, separators=(',', ':')) + html[end:]
    open(args.html, 'w', encoding='utf-8').write(new_html)
    print(f"Wrote {args.html} ({len(new_html)} bytes)")


def cmd_period(args):
    html = open(args.html, encoding='utf-8').read()
    prefix = f'var {args.js_var} = '
    start, end, fd = extract_js_object(html, prefix)

    variants = {}
    for variant, path in [('team', args.team_json), ('skelly', args.skelly_json), ('combined', args.combined_json)]:
        if path:
            variants[variant] = json.load(open(path))

    if not variants:
        raise SystemExit("Pass at least one of --team-json/--skelly-json/--combined-json.")

    days = fd.setdefault('days', [])
    existing = next((d for d in days if d.get('key') == args.day_key), None)

    if args.new_day:
        if existing is not None:
            raise SystemExit(f"--new-day given but day_key '{args.day_key}' already exists. Drop --new-day to overwrite it.")
        entry = {
            'key': args.day_key,
            'label': args.label or args.day_key,
            'date': args.date or '',
            'variants': variants,
        }
        days.append(entry)
        print(f"Added new day '{args.day_key}'")
    else:
        if existing is None:
            raise SystemExit(f"day_key '{args.day_key}' not found in days[]. Pass --new-day to add it.")
        existing['variants'].update(variants)
        if args.label:
            existing['label'] = args.label
        if args.date:
            existing['date'] = args.date
        print(f"Updated existing day '{args.day_key}'")

    fd['loaded'] = True

    if len(days) == 1:
        # Single-day camp: all_variants is just that day's variants.
        fd['all_variants'] = days[0]['variants']
    else:
        print("NOTE: multiple days now present. all_variants was NOT recomputed --")
        print("      this script only auto-merges for the single-day case.")
        print("      Combine days[*].variants[v] into all_variants[v] by hand")
        print("      (weighted merge across days) before shipping, or extend")
        print("      this script with a merge_all_variants() implementation.")

    new_html = html[:start] + json.dumps(fd, separators=(',', ':')) + html[end:]
    open(args.html, 'w', encoding='utf-8').write(new_html)
    print(f"Wrote {args.html} ({len(new_html)} bytes)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('spring')
    sp.add_argument('html')
    sp.add_argument('--js-var', default='SPRING_VARIANTS')
    sp.add_argument('--team-dir')
    sp.add_argument('--skelly-dir')
    sp.add_argument('--combined-dir')
    sp.set_defaults(func=cmd_spring)

    pp = sub.add_parser('period')
    pp.add_argument('html')
    pp.add_argument('--js-var', required=True, help='FALL_DATA or INSEASON_DATA')
    pp.add_argument('--day-key', required=True)
    pp.add_argument('--label')
    pp.add_argument('--date')
    pp.add_argument('--new-day', action='store_true')
    pp.add_argument('--team-json')
    pp.add_argument('--skelly-json')
    pp.add_argument('--combined-json')
    pp.set_defaults(func=cmd_period)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
