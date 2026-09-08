#!/usr/bin/env python3
"""
Refreshes the 9 TM/FM chart-data JS fields (tmEogFormationChart/FrontsDonut/
CovDonut, tmEohFormationChart/FrontsDonut/CovDonut, fmFormationChart/
FrontsDonut/CovDonut) inside each team's TEAMS_DATA blob in advance-scout.html,
to match the freshly-rebuilt TM/FM sections (see fix_tm_fm_rz_gl_full.py).
Brace-aware remove-all-then-insert-one, scoped per-team object, mirroring the
established fix_teams_data_v2.py convention from earlier this session.
"""
import re, json, sys
sys.path.insert(0, '/tmp/vt-offense-hub-scratch/data-pipeline')
from gen_html import chart_objects

SRC = '/tmp/vt-offense-hub-scratch/_source/advance-scout.html'

def load_bucket(team):
    with open(f'/tmp/{team.lower()}_check.json') as f:
        return json.load(f)

def find_object_span(html, var_decl):
    """var_decl e.g. 'const MARYLAND_DATA = '. Returns (obj_start, obj_end)
    bounding the {...} object literal (obj_end is index AFTER the closing
    brace), via simple brace counting (safe here: no braces inside JS string
    literals in this file's data, confirmed by prior session's use of the
    same technique)."""
    decl_idx = html.index(var_decl)
    obj_start = html.index('{', decl_idx)
    depth = 0
    i = obj_start
    while True:
        c = html[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return obj_start, i + 1
        i += 1

def find_key_value_span(scope, key, search_from=0):
    """Finds '"key":{...}' (brace-counting the value) within scope starting
    at search_from. Returns (span_start, span_end) INCLUDING a leading or
    trailing comma (whichever is adjacent) for clean removal, or None."""
    pat = f'"{key}":'
    idx = scope.find(pat, search_from)
    if idx == -1:
        return None
    val_start = idx + len(pat)
    if scope[val_start] != '{':
        raise ValueError(f"expected object value for {key}")
    depth = 0
    i = val_start
    while True:
        c = scope[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                val_end = i + 1
                break
        i += 1
    span_start, span_end = idx, val_end
    if span_end < len(scope) and scope[span_end] == ',':
        span_end += 1
    elif span_start > 0 and scope[span_start - 1] == ',':
        span_start -= 1
    return span_start, span_end

def remove_all_occurrences(scope, key):
    removed = 0
    while True:
        span = find_key_value_span(scope, key)
        if span is None:
            break
        scope = scope[:span[0]] + scope[span[1]:]
        removed += 1
    return scope, removed

def main():
    html = open(SRC, encoding='utf-8').read()
    teams = ['MARYLAND', 'VMI', 'ODU']

    for team in teams:
        bucket = load_bucket(team)
        var_decl = f'const {team}_DATA = '
        obj_start, obj_end = find_object_span(html, var_decl)
        scope = html[obj_start:obj_end]

        new_fields = {}
        for key, bkey in [('tmEog', 'tmEog'), ('tmEoh', 'tmEoh'), ('fm', 'fm')]:
            fc, fd, cd = chart_objects(bucket[bkey])
            new_fields[f'{key}FormationChart'] = fc
            new_fields[f'{key}FrontsDonut'] = fd
            new_fields[f'{key}CovDonut'] = cd

        total_removed = 0
        for k in new_fields:
            scope, n_removed = remove_all_occurrences(scope, k)
            total_removed += n_removed

        anchor_span = find_key_value_span(scope, 'cdCovDonut')
        if anchor_span is None:
            raise ValueError(f"{team}: cdCovDonut anchor not found")
        insert_at = anchor_span[1]
        insertion = ''.join(f',"{k}":{json.dumps(v, separators=(",", ":"))}' for k, v in new_fields.items())
        scope = scope[:insert_at] + insertion + scope[insert_at:]

        html = html[:obj_start] + scope + html[obj_end:]
        print(f"{team}: removed {total_removed} old field copies, inserted {len(new_fields)} fresh ones")

    with open(SRC, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done.")

if __name__ == '__main__':
    main()
