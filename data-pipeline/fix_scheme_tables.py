#!/usr/bin/env python3
"""
Rebuilds, for all 3 loaded opponents (Maryland, VMI, ODU):
  - ND/CD Fronts sub-tab (down-distance split cards)
  - ND/CD Coverage sub-tab (down-distance split cards)
  - ND/CD Blitz sub-tab (direction cards, 5/6/7-man schemes, RB tendency,
    Blitz by Personnel, Coverage on Blitz, Front on Blitz, Stunts by Down
    & Distance) -- standardized to the SAME table set for every team.
  - 2 Min (EOG/EOH) and 4 Min Blitz sub-tabs (direction cards, 5/6/7-man
    schemes, RB tendency, Blitz by Personnel, Coverage on Blitz, Front on
    Blitz -- no down splits, situational buckets aren't down-driven).

All numbers come from compute_situational.py's exclusion-corrected output
(/tmp/<team>_situational.json), consistent with the ND/CD headline stats and
Formation/Fronts/Coverage tabs already corrected earlier this session.
"""
import re, json, sys
sys.path.insert(0, '/tmp/vt-offense-hub/data-pipeline')
from gen_html import (
    build_fronts_panel_with_splits, build_coverage_panel_with_splits, build_blitz_panel,
    build_simple_fronts_panel, build_simple_coverage_panel,
)

def load(team):
    with open(f'/tmp/{team.lower()}_situational.json') as f:
        return json.load(f)

def find_div_span(html, id_value, search_start=0):
    pat = re.compile(r'<div[^>]*\bid="' + re.escape(id_value) + r'"[^>]*>')
    m = pat.search(html, search_start)
    if not m:
        raise RuntimeError(f"div id={id_value} not found from offset {search_start}")
    start = m.start()
    i = m.end()
    depth = 1
    tagpat = re.compile(r'<div\b|</div>')
    while depth > 0:
        m2 = tagpat.search(html, i)
        if not m2:
            raise RuntimeError(f"unbalanced div for id={id_value}")
        if m2.group() == '</div>':
            depth -= 1
        else:
            depth += 1
        i = m2.end()
    return start, i

def replace_div(html, id_value, new_inner_html_full_div):
    """new_inner_html_full_div must be the COMPLETE replacement including the
    outer <div id="..."> ... </div> wrapper (our gen_html builders already
    produce this)."""
    start, end = find_div_span(html, id_value)
    return html[:start] + new_inner_html_full_div + html[end:]

def rebuild_nd_cd_block(scope, data, prefix, label, down_label, plays_header, splits_key):
    bucket = data[prefix]  # 'nd' or 'cd'
    splits = data[splits_key]
    scope = replace_div(scope, f'{prefix}-fronts',
        build_fronts_panel_with_splits(bucket, label, prefix, f'ch-{prefix}', splits))
    scope = replace_div(scope, f'{prefix}-coverage',
        build_coverage_panel_with_splits(bucket, label, prefix, f'ch-{prefix}', splits))
    scope = replace_div(scope, f'{prefix}-blitz',
        build_blitz_panel(bucket, label, prefix, down_label=down_label, plays_header=plays_header, splits=splits))
    return scope

def rebuild_tm_fm_section(scope, bucket, label, id_prefix):
    if bucket["n"] == 0:
        return scope  # empty bucket -> whole section is just a placeholder callout, nothing to replace
    scope = replace_div(scope, f'{id_prefix}-fronts',
        build_simple_fronts_panel(bucket, label, id_prefix, f'ch-{id_prefix}'))
    scope = replace_div(scope, f'{id_prefix}-coverage',
        build_simple_coverage_panel(bucket, label, id_prefix, f'ch-{id_prefix}'))
    scope = replace_div(scope, f'{id_prefix}-blitz',
        build_blitz_panel(bucket, label, id_prefix, down_label=label, plays_header="Plays", splits=None))
    return scope

def main():
    p = '/tmp/vt-offense-hub/_source/advance-scout.html'
    html = open(p, encoding='utf-8').read()

    data = {t: load(t) for t in ['MARYLAND', 'VMI', 'ODU']}

    # Locate every block's start marker, sort by position, end = next marker's start.
    markers = {}
    markers[('MARYLAND', 'ND')] = html.index('id="sec-nd-body"')
    markers[('MARYLAND', 'CD')] = html.index('id="sec-cd-body"')
    markers[('MARYLAND', 'TM')] = html.index('id="sec-tm-body"')
    markers[('MARYLAND', 'FM')] = html.index('id="sec-fm-body"')
    for m in re.finditer(r'<script type="text/html" id="tmpl-(nd|cd|tm|fm)-(VMI|ODU)">', html):
        markers[(m.group(2), m.group(1).upper())] = m.end()

    ordered = sorted(markers.items(), key=lambda kv: kv[1])
    spans = {}
    for i, (key, start) in enumerate(ordered):
        end = ordered[i+1][1] if i+1 < len(ordered) else len(html)
        spans[key] = (start, end)

    # Process in REVERSE position order so earlier (lower-offset) blocks'
    # indices stay valid while we splice later ones.
    for key, (start, end) in sorted(spans.items(), key=lambda kv: -kv[1][0]):
        team, section = key
        scope = html[start:end]
        d = data[team]

        if section == 'ND':
            scope = rebuild_nd_cd_block(scope, d, 'nd', 'Normal Downs', 'Normal Downs', 'ND Plays', 'ndSplits')
        elif section == 'CD':
            scope = rebuild_nd_cd_block(scope, d, 'cd', 'Conversion Downs', 'Conversion', 'CD Plays', 'cdSplits')
        elif section == 'TM':
            scope = rebuild_tm_fm_section(scope, d['tmEog'], '2-Minute — End of Game', 'tm-eog')
            scope = rebuild_tm_fm_section(scope, d['tmEoh'], '2-Minute — End of Half', 'tm-eoh')
        elif section == 'FM':
            scope = rebuild_tm_fm_section(scope, d['fm'], '4-Minute Offense', 'fm')

        html = html[:start] + scope + html[end:]
        print(f"{team}-{section}: OK")

    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done.")

if __name__ == '__main__':
    main()
