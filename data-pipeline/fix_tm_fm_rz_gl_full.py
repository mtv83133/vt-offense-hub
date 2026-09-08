#!/usr/bin/env python3
"""
Full-fidelity rebuild of the TM-EOG / TM-EOH / FM sections (all 3 teams) plus
MARYLAND's RZ and GL sections, from a completely fresh compute_situational.py
run against each team's canonical raw CSV.

Why: Matt asked (2026-09-07) for a full sweep confirming every "total plays"
bubble reconciles with the real data. Investigation found ND/CD/Bible/RunTab/
P&10 already fully in sync (their own dedicated fix_*.py scripts get rerun on
every CSV update), but TM-EOG/TM-EOH/FM sections have NO equivalent full
rebuild script -- they only ever got their Formation Tendencies TABLE patched
(fix_tm_fm_p10_formations.py, 2026-09-07 morning) while the surrounding
Fronts/Coverage/Blitz panels and "Total X Plays: N" bubble text were never
regenerated after later CSV corrections (dedup fix, blitz redefinition,
coverage typo fixes, etc.), so they silently drifted out of sync -- most
severely VMI's FM section, showing "51" plays live vs. 22 real ones.

Separately, MARYLAND's RZ/GL sections predate the 2026-08-30 Total-Pressure-%
feature (never rebuilt since), so they're missing that whole card/row on top
of a small blitzCount drift.

This script replaces the ENTIRE TM-EOG/TM-EOH/FM HTML block (stabs + all 4
sub-panels) via gen_html.build_breakdown_section(), which guarantees full
internal consistency (formations table, fronts/coverage/blitz tables, and the
"Total X Plays: N" callout all come from the exact same bucket). MARYLAND's
RZ/GL sections are rebuilt wholesale via build_rz_section()/build_gl_section().
"""
import re, json, sys
sys.path.insert(0, '/tmp/vt-offense-hub-scratch/data-pipeline')
from gen_html import build_breakdown_section, build_rz_section, build_gl_section

SRC = '/tmp/vt-offense-hub-scratch/_source/advance-scout.html'

def load_bucket(team):
    with open(f'/tmp/{team.lower()}_check.json') as f:
        return json.load(f)

def find_div_content_span(html, open_tag_regex, search_from):
    m = re.search(open_tag_regex, html[search_from:])
    if not m:
        raise ValueError(f"open tag not found: {open_tag_regex}")
    content_start = search_from + m.end()
    depth = 1
    i = content_start
    content_end = None
    while depth > 0:
        next_open = html.find('<div', i)
        next_close = html.find('</div>', i)
        if next_close == -1:
            raise ValueError("no matching </div> found")
        if next_open != -1 and next_open < next_close:
            depth += 1
            i = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                content_end = next_close
            i = next_close + 6
    return content_start, content_end

def replace_wrap_content(html, wrap_id, new_inner, search_from, search_to):
    window_end = search_to
    pat = r'<div[^>]*\bid="' + re.escape(wrap_id) + r'"[^>]*>'
    m = re.search(pat, html[search_from:window_end])
    if not m:
        raise ValueError(f"{wrap_id} not found in window")
    content_start, content_end = find_div_content_span(html, pat, search_from)
    return html[:content_start] + new_inner + html[content_end:]

def replace_span(html, start_marker, end_marker, new_content, search_from=0):
    start_idx = html.index(start_marker, search_from)
    content_start = start_idx + len(start_marker)
    end_idx = html.index(end_marker, content_start)
    return html[:content_start] + new_content + html[end_idx:]

def team_bounds(html, team, section):
    if team == 'MARYLAND':
        start_marker = f'<div class="sec-body" id="sec-{section}-body">'
        end_marker = f'</div><!-- /sec-{section}-body -->'
    else:
        start_marker = f'<script type="text/html" id="tmpl-{section}-{team}">'
        end_marker = '</script>'
    start = html.index(start_marker)
    end = html.index(end_marker, start)
    return start, end


def main():
    html = open(SRC, encoding='utf-8').read()
    teams = ['MARYLAND', 'VMI', 'ODU']
    buckets = {t: load_bucket(t) for t in teams}

    for team in teams:
        b = buckets[team]
        eog_html = build_breakdown_section(
            b['tmEog'], '2-Minute — End of Game', 'tm-eog', 'ch-tm-eog',
            lambda t: f"switchTmSub('eog','{t}')")
        eoh_html = build_breakdown_section(
            b['tmEoh'], '2-Minute — End of Half', 'tm-eoh', 'ch-tm-eoh',
            lambda t: f"switchTmSub('eoh','{t}')")

        start, end = team_bounds(html, team, 'tm')
        html = replace_wrap_content(html, 'tm-eog-wrap', eog_html, start, end)
        start, end = team_bounds(html, team, 'tm')
        html = replace_wrap_content(html, 'tm-eoh-wrap', eoh_html, start, end)
        print(f"{team}: TM-EOG/TM-EOH rebuilt (n={b['tmEog']['n']}/{b['tmEoh']['n']})")

    for team in teams:
        b = buckets[team]
        fm_html = build_breakdown_section(
            b['fm'], '4-Minute Offense', 'fm', 'ch-fm',
            lambda t: f"switchStab('fm','{t}')")
        if team == 'MARYLAND':
            html = replace_span(html, '<div class="sec-body" id="sec-fm-body">',
                                 '</div><!-- /sec-fm-body -->', fm_html)
        else:
            html = replace_span(html, f'<script type="text/html" id="tmpl-fm-{team}">',
                                 '</script>', fm_html)
        print(f"{team}: FM rebuilt (n={b['fm']['n']})")

    rz_html = build_rz_section(buckets['MARYLAND']['rz'])
    html = replace_span(html, '<div class="sec-body" id="sec-rz-body">',
                         '</div><!-- /sec-rz-body -->', rz_html)
    print(f"MARYLAND: RZ rebuilt (n={buckets['MARYLAND']['rz']['n']})")

    gl_html = build_gl_section(buckets['MARYLAND']['gl'])
    html = replace_span(html, '<div class="sec-body" id="sec-gl-body">',
                         '</div><!-- /sec-gl-body -->', gl_html)
    print(f"MARYLAND: GL rebuilt (n={buckets['MARYLAND']['gl']['n']})")

    with open(SRC, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done.")

if __name__ == '__main__':
    main()
