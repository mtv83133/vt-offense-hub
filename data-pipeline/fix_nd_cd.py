#!/usr/bin/env python3
import re, sys, json
sys.path.insert(0, '/tmp/vt-offense-hub/data-pipeline')
from gen_html import formation_table_rows, family_table_rows, rb_table_rows, chart_objects

def load(team):
    with open(f'/tmp/{team.lower()}_situational.json') as f:
        return json.load(f)

def fix_block(block, bucket, label_full, label_short):
    """label_full = 'Normal Downs' / 'Conversion Downs'; label_short = 'ND' / 'CD'"""
    orig = block
    n_report = []

    # (a) Total Plays callout
    def callout_repl(m):
        cls = m.group(1)
        top_front = bucket["frontFamily"][0] if bucket["frontFamily"] else None
        front_txt = f'{top_front["label"]} front dominant ({top_front["pct"]}%)' if top_front else 'no front data'
        return f'<div class="callout {cls}"><strong>Total {label_short} Plays: {bucket["n"]}</strong> · {front_txt} · {bucket["blitzPct"]}% blitz rate overall</div>'
    pat = re.compile(r'<div class="callout (info|warn)"><strong>Total \w+ Plays:.*?</div>')
    block, cnt = pat.subn(callout_repl, block, count=1)
    n_report.append(('total_callout', cnt))

    # (b) Formation Tendencies table
    pat = re.compile(
        r'(<div class="card-hd">Formation Tendencies — ' + re.escape(label_full) + r'</div>\s*<table class="tbl">\s*<thead>.*?</thead>\s*<tbody>)(.*?)(</tbody>)',
        re.DOTALL)
    new_rows = formation_table_rows(bucket["formations"])
    block, cnt = pat.subn(lambda m: m.group(1) + new_rows + m.group(3), block, count=1)
    n_report.append(('formation_table', cnt))

    # (c) Front Family table -- ND variant (separate card) or CD variant (combined card)
    pat_nd = re.compile(
        r'(<div class="card-hd">Front Family Distribution</div>\s*<table class="tbl">\s*<thead>.*?</thead>\s*<tbody>)(.*?)(</tbody>)',
        re.DOTALL)
    new_ff_rows = family_table_rows(bucket["frontFamily"])
    block, cnt = pat_nd.subn(lambda m: m.group(1) + new_ff_rows + m.group(3), block, count=1)
    if cnt == 0:
        pat_cd = re.compile(
            r'(<div class="card-hd">Front Family — Conversion Downs Overall</div>\s*<table class="tbl">\s*<thead>.*?</thead>\s*<tbody>)(.*?)(</tbody>)',
            re.DOTALL)
        block, cnt = pat_cd.subn(lambda m: m.group(1) + new_ff_rows + m.group(3), block, count=1)
    n_report.append(('front_family_table', cnt))

    # (d) Coverage Distribution table
    pat = re.compile(
        r'(<div class="card-hd">Coverage Distribution</div>\s*<table class="tbl">\s*<thead>.*?</thead>\s*<tbody>)(.*?)(</tbody>)',
        re.DOTALL)
    new_cov_rows = family_table_rows(bucket["covFamily"])
    block, cnt = pat.subn(lambda m: m.group(1) + new_cov_rows + m.group(3), block, count=1)
    n_report.append(('coverage_table', cnt))

    # (e) Blitz callout (simplified -- drop stale 5-man+/pressure-direction sub-claims)
    pat = re.compile(
        r'<div class="callout danger"><strong>\d+% Blitz Rate</strong> on ' + re.escape(label_full) + r' \(\d+/\d+ plays\).*?</div>',
        re.DOTALL)
    new_blitz_callout = f'<div class="callout danger"><strong>{bucket["blitzPct"]}% Blitz Rate</strong> on {label_full} ({bucket["blitzCount"]}/{bucket["n"]} plays)</div>'
    block, cnt = pat.subn(new_blitz_callout, block, count=1)
    n_report.append(('blitz_callout', cnt))

    # (f) RB Blitz Tendency table
    rb_label = label_full if label_short == 'ND' else 'Conversion'
    pat = re.compile(
        r'(<div class="card-hd">RB Blitz Tendency \(' + re.escape(rb_label) + r'\)</div>\s*<table class="tbl">\s*<thead>.*?</thead>\s*<tbody>)(.*?)(</tbody>)',
        re.DOTALL)
    new_rb_rows = rb_table_rows(bucket["rbBlitzTendency"])
    block, cnt = pat.subn(lambda m: m.group(1) + new_rb_rows + m.group(3), block, count=1)
    n_report.append(('rb_blitz_table', cnt))

    return block, n_report

def main():
    html = open('/tmp/vt-offense-hub/_source/advance-scout.html', encoding='utf-8').read()

    targets = [
        ('MARYLAND', 'nd', 'Normal Downs', 'ND', '<div class="sec-body" id="sec-nd-body">', '</div><!-- /sec-nd-body -->'),
        ('MARYLAND', 'cd', 'Conversion Downs', 'CD', '<div class="sec-body" id="sec-cd-body">', '</div><!-- /sec-cd-body -->'),
        ('VMI', 'nd', 'Normal Downs', 'ND', '<script type="text/html" id="tmpl-nd-VMI">', '</script>'),
        ('VMI', 'cd', 'Conversion Downs', 'CD', '<script type="text/html" id="tmpl-cd-VMI">', '</script>'),
        ('ODU', 'nd', 'Normal Downs', 'ND', '<script type="text/html" id="tmpl-nd-ODU">', '</script>'),
        ('ODU', 'cd', 'Conversion Downs', 'CD', '<script type="text/html" id="tmpl-cd-ODU">', '</script>'),
    ]

    for team, sec, label_full, label_short, start_marker, end_marker in targets:
        data = load(team)
        bucket = data[sec]
        start_idx = html.index(start_marker)
        content_start = start_idx + len(start_marker)
        end_idx = html.index(end_marker, content_start)
        block = html[content_start:end_idx]

        new_block, report = fix_block(block, bucket, label_full, label_short)
        print(f"{team} {sec}: {report}")
        if any(c == 0 for _, c in report):
            print(f"  !!! WARNING: some replacements found 0 matches for {team} {sec}")

        html = html[:content_start] + new_block + html[end_idx:]

    with open('/tmp/vt-offense-hub/_source/advance-scout.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done -- ND/CD blocks corrected for MARYLAND, VMI, ODU.")

if __name__ == '__main__':
    main()
