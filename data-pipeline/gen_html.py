#!/usr/bin/env python3
"""
Generates HTML fragments (Formation Tendencies table, Front Family
donut+table, Coverage Family donut+table, Blitz callout + RB Blitz
Tendency table) from compute_situational.py's JSON output, for both the
corrected ND/CD sections and the brand-new 2MIN/4MIN sections.
"""
import json, html

def esc(s):
    return html.escape(str(s), quote=False)

def blitz_class(pct):
    if pct >= 40: return "hlb b"
    if pct >= 25: return "hl b"
    return "b"

def pct_class(pct, idx):
    return "b hl" if idx == 0 else ""

def formation_table_rows(formations):
    rows = []
    for f in formations:
        rows.append(
            f'<tr><td class="b">{esc(f["formation"])}</td><td>{esc(f["pers"])}</td>'
            f'<td>{f["plays"]} ({f["pct"]}%)</td>'
            f'<td class="{blitz_class(f["blitzPct"])}">{f["blitzPct"]}%</td>'
            f'<td>{esc(f["topFront"])}</td><td>{esc(f["topCoverage"])}</td></tr>'
        )
    return "\n                ".join(rows) if rows else '<tr><td colspan="6" style="text-align:center;color:var(--muted)">No data yet</td></tr>'

def family_table_rows(items, label_header="Family"):
    rows = []
    for i, it in enumerate(items):
        cls = ' class="b hl"' if i == 0 else ""
        rows.append(f'<tr><td{cls}>{esc(it["label"])}</td><td>{it["count"]}</td><td{cls}>{it["pct"]}%</td></tr>')
    return "\n                ".join(rows) if rows else '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data yet</td></tr>'

def rb_table_rows(items):
    rows = []
    for i, it in enumerate(items):
        cls = ' class="b hlb"' if i == 0 else ""
        rows.append(f'<tr><td{cls if i==0 else ""}>{esc(it["label"])}</td><td>{it["count"]}</td><td{cls}>{it["pct"]}%</td></tr>')
    return "\n                  ".join(rows) if rows else '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data yet</td></tr>'

def donut_labels_data(items):
    labels = [f'{it["label"]} {it["pct"]}%' for it in items]
    data = [it["pct"] for it in items]
    return labels, data

def chart_objects(bucket):
    """Returns (formationChart, frontsDonut, covDonut) dicts for the JS data object."""
    forms = bucket["formations"][:8]
    formation_chart = {
        "labels": [f["formation"].split(" ")[0] if f["formation"] != "EMPTY" else "EMPTY" for f in forms],
        "freq": [f["pct"] for f in forms],
        "blitz": [f["blitzPct"] for f in forms],
    }
    fl, fd = donut_labels_data(bucket["frontFamily"])
    fronts_donut = {"labels": fl, "data": fd}
    cl, cd = donut_labels_data(bucket["covFamily"])
    cov_donut = {"labels": cl, "data": cd}
    return formation_chart, fronts_donut, cov_donut

def nd_cd_callout(bucket, label):
    n = bucket["n"]
    top_front = bucket["frontFamily"][0] if bucket["frontFamily"] else None
    front_txt = f'{top_front["label"]} front dominant ({top_front["pct"]}%)' if top_front else "no front data"
    return f'<div class="callout info"><strong>Total {label} Plays: {n}</strong> · {front_txt} · {bucket["blitzPct"]}% blitz rate overall</div>'

def blitz_callout(bucket, label, danger=True):
    cls = "danger" if danger else "info"
    return (f'<div class="callout {cls}"><strong>{bucket["blitzPct"]}% Blitz Rate</strong> on {label} '
            f'({bucket["blitzCount"]}/{bucket["n"]} plays)</div>')

def formation_bar_canvas(canvas_id):
    return f'<div class="ch-lg"><canvas id="{canvas_id}"></canvas></div>'

def small_donut_canvas(canvas_id):
    return f'<div class="ch-sm"><canvas id="{canvas_id}"></canvas></div>'

def build_simple_fronts_panel(bucket, label, id_prefix, canvas_prefix):
    """Fronts sub-tab for buckets with no down-distance splits (2MIN/4MIN)."""
    pers_card = fronts_by_personnel_card(bucket.get("frontsByPersonnel", []))
    pers_row = (
        '<div class="g2 mb14">\n          ' + pers_card + '\n        </div>'
        if pers_card else ""
    )
    return (
        '\n      <div class="stcon" id="' + id_prefix + '-fronts">\n'
        '        <div class="print-label">' + label + ' — Fronts</div>\n'
        '        <div class="g2 mb14">\n'
        '          <div class="card">\n'
        '            <div class="card-hd">Front Family — ' + label + '</div>\n'
        "            " + small_donut_canvas(canvas_prefix + "-fronts-donut") + "\n"
        '          </div>\n'
        '          <div class="card">\n'
        '            <div class="card-hd">Front Family Distribution</div>\n'
        '            <table class="tbl">\n'
        '              <thead><tr><th>Family</th><th># Plays</th><th>% Snaps</th></tr></thead>\n'
        '              <tbody>\n'
        "                " + family_table_rows(bucket["frontFamily"]) + "\n"
        '              </tbody>\n'
        '            </table>\n'
        '          </div>\n'
        '        </div>\n'
        "        " + pers_row + "\n"
        '      </div>'
    )

def build_simple_coverage_panel(bucket, label, id_prefix, canvas_prefix):
    """Coverage sub-tab for buckets with no down-distance splits (2MIN/4MIN)."""
    pers_card = coverage_by_personnel_card(bucket.get("coverageByPersonnel", []))
    pers_row = (
        '<div class="g2 mb14">\n          ' + pers_card + '\n        </div>'
        if pers_card else ""
    )
    return (
        '\n      <div class="stcon" id="' + id_prefix + '-coverage">\n'
        '        <div class="print-label">' + label + ' — Coverage</div>\n'
        '        <div class="g2 mb14">\n'
        '          <div class="card">\n'
        '            <div class="card-hd">Coverage Family — ' + label + '</div>\n'
        "            " + small_donut_canvas(canvas_prefix + "-cov-donut") + "\n"
        '          </div>\n'
        '          <div class="card">\n'
        '            <div class="card-hd">Coverage Distribution</div>\n'
        '            <table class="tbl">\n'
        '              <thead><tr><th>Family (Shell)</th><th># Plays</th><th>% Snaps</th></tr></thead>\n'
        '              <tbody>\n'
        "                " + family_table_rows(bucket["covFamily"]) + "\n"
        '              </tbody>\n'
        '            </table>\n'
        '          </div>\n'
        '        </div>\n'
        "        " + pers_row + "\n"
        '      </div>'
    )

def field_breakpoint_narrative(bp):
    """Turns a compute_situational.find_secondary_breakpoint() result into an
    Overview callout string, matching the style of the existing RZ 'line of
    demarcation' callouts. Returns None if bp is None/falsy -- callers must
    skip rendering the Overview card entirely in that case rather than
    showing an empty placeholder (this analysis is intentionally conservative
    and often legitimately finds nothing to report)."""
    if not bp:
        return None
    thresh = bp["thresh"]
    rz_line = bp["rzLine"]
    blitz_in, blitz_out = bp["blitzIn"], bp["blitzOut"]
    blitz_txt = (
        f"Blitz rate also shifts, {blitz_out}% outside vs {blitz_in}% inside the +{thresh}. "
        if abs(blitz_in - blitz_out) >= 8 else ""
    )
    return (
        f'<span class="hlb">SECOND BREAKING POINT: THE +{thresh}</span> \u2014 Beyond their red-zone '
        f'adjustment at the +{rz_line}, coverage tendencies shift again once the ball crosses the +{thresh} '
        f'(a {bp["covScorePct"]}-point swing in coverage-family mix, {bp["nInside"]} snaps inside vs '
        f'{bp["nOutside"]} outside). {blitz_txt}'
        f'Treat the +{thresh} as a second scheme-change checkpoint, not just the red zone.'
    )

def build_breakdown_section(bucket, label, id_prefix, canvas_prefix, onclick_fn):
    """
    Builds the full 4-stab (Formations/Fronts/Coverage/Blitz) breakdown HTML
    for a bucket, e.g. id_prefix='tm-eog', canvas_prefix='ch-tm-eog'.
    Mirrors ND/CD's structure but without the down-distance sub-splits.
    """
    if bucket["n"] == 0:
        return f'''<div class="callout info">No {label} data charted yet for this opponent.</div>'''

    formations_panel = f'''
      <div class="stcon on" id="{id_prefix}-formations">
        <div class="print-label">{label} — Formation Tendencies</div>
        {nd_cd_callout(bucket, label)}
        <div class="g2">
          <div class="card">
            <div class="card-hd">Formation Tendencies — {label}</div>
            <table class="tbl">
              <thead><tr><th>Formation</th><th>Pers</th><th>Plays</th><th>Blitz%</th><th>Top Front</th><th>Top Coverage</th></tr></thead>
              <tbody>
                {formation_table_rows(bucket["formations"])}
              </tbody>
            </table>
          </div>
          <div class="card">
            <div class="card-hd">Formation Frequency vs Blitz Rate</div>
            {formation_bar_canvas(canvas_prefix + "-form")}
          </div>
        </div>
      </div>'''

    fronts_panel = build_simple_fronts_panel(bucket, label, id_prefix, canvas_prefix)

    coverage_panel = build_simple_coverage_panel(bucket, label, id_prefix, canvas_prefix)

    blitz_panel = build_blitz_panel(bucket, label, id_prefix, down_label=label, plays_header="Plays", splits=None)

    return f'''<div class="stabs" id="{id_prefix}-tabs">
        <div class="stab on" onclick="{onclick_fn('formations')}">Formations</div>
        <div class="stab" onclick="{onclick_fn('fronts')}">Fronts</div>
        <div class="stab" onclick="{onclick_fn('coverage')}">Coverage</div>
        <div class="stab" onclick="{onclick_fn('blitz')}">Blitz</div>
      </div>
      {formations_panel}
      {fronts_panel}
      {coverage_panel}
      {blitz_panel}'''

# ============================================================================
# Down-distance splits (Fronts/Coverage/Stunts) + expanded Blitz sub-tab
# (pressure direction cards, 5/6/7-man schemes, Blitz by Personnel,
# Coverage on Blitz, Front on Blitz) -- added for the ND/CD table-parity
# rebuild + 2MIN/4MIN blitz scheme tables (July 2026).
# ============================================================================

def split_front_cards(splits):
    """Fronts sub-tab: one card per down-distance split, 'Front' table."""
    cards = []
    for s in splits:
        rows = family_table_rows(s["fronts"]) if s["fronts"] else \
            '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data yet</td></tr>'
        # family_table_rows expects {label,count,pct} with hl on first row -- reuse via generic table
        row_html = []
        for i, f in enumerate(s["fronts"]):
            cls = ' class="b hl"' if i == 0 else ''
            bcls = ' class="b"' if i == 0 else ''
            row_html.append(f'<tr><td{bcls}>{esc(f["label"])}</td><td>{f["count"]}</td><td{cls}>{f["pct"]}%</td></tr>')
        body = "\n                ".join(row_html) if row_html else '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data yet</td></tr>'
        cards.append(f'''<div class="card">
            <div class="card-hd">Fronts — {esc(s["label"])}</div>
            <table class="tbl">
              <thead><tr><th>Front</th><th>#</th><th>%</th></tr></thead>
              <tbody>
                {body}
              </tbody>
            </table>
          </div>''')
    return cards

def split_coverage_cards(splits):
    cards = []
    for s in splits:
        row_html = []
        for i, c in enumerate(s["coverage"]):
            cls = ' class="b hl"' if i == 0 else ''
            bcls = ' class="b"' if i == 0 else ''
            row_html.append(f'<tr><td{bcls}>{esc(c["label"])}</td><td>{c["count"]}</td><td{cls}>{c["pct"]}%</td></tr>')
        body = "\n                ".join(row_html) if row_html else '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data yet</td></tr>'
        cards.append(f'''<div class="card">
            <div class="card-hd">Coverage — {esc(s["label"])}</div>
            <table class="tbl">
              <thead><tr><th>Coverage</th><th>#</th><th>%</th></tr></thead>
              <tbody>
                {body}
              </tbody>
            </table>
          </div>''')
    return cards

def stunts_table_card(splits):
    rows = []
    for s in splits:
        rows.append(f'<tr><td>{esc(s["label"])}</td><td>{s["stuntCount"]}</td><td>{s["n"]}</td><td>{s["stuntPct"]}%</td></tr>')
    body = "\n                ".join(rows)
    return f'''<div class="card"><div class="card-hd">Stunts by Down &amp; Distance</div>
            <table class="tbl">
              <thead><tr><th>Down &amp; Distance</th><th>Stunts</th><th>Plays</th><th>Stunt %</th></tr></thead>
              <tbody>
                {body}
              </tbody>
            </table>
          </div>'''

def pcards_html(pcards, blitz_total):
    if not pcards:
        return '<div class="callout info">No blitz-direction data charted yet.</div>'
    out = []
    for c in pcards:
        out.append(f'<div class="pcard {c["cls"]}"><div class="ppct">{c["pct"]}%</div><div class="plbl">{esc(c["label"])}</div><div class="pcnt">{c["count"]}/{blitz_total} plays</div></div>')
    return "\n          ".join(out)

def scheme_table(items, total_n, header_suffix=""):
    rows = []
    for i, it in enumerate(items):
        cls = ' class="b hlb"' if i == 0 else ''
        bcls = ' class="b"' if i == 0 else ''
        rows.append(f'<tr><td{bcls}>{esc(it["label"])}</td><td>{it["count"]}</td><td{cls}>{it["pct"]}%</td></tr>')
    body = "\n                  ".join(rows) if rows else '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data yet</td></tr>'
    return body

def personnel_table_rows(items, plays_header):
    rows = []
    for i, it in enumerate(items):
        cls = ' class="hlb b"' if it["blitzPct"] >= 40 else (' class="hl b"' if it["blitzPct"] >= 25 else '')
        rows.append(f'<tr><td class="b">{esc(it["pers"])}</td><td>{it["plays"]}</td><td>{it["blitz"]}</td><td{cls}>{it["blitzPct"]}%</td></tr>')
    return "\n                  ".join(rows) if rows else '<tr><td colspan="4" style="text-align:center;color:var(--muted)">No data yet</td></tr>'

def fronts_by_personnel_card(items):
    if not items:
        return ""
    rows = []
    for i, it in enumerate(items):
        cls = ' class="hlb b"' if it["topFrontPct"] >= 40 else (' class="hl b"' if it["topFrontPct"] >= 25 else '')
        rows.append(f'<tr><td class="b">{esc(it["pers"])}</td><td>{it["plays"]}</td><td>{esc(it["topFront"])}</td><td{cls}>{it["topFrontPct"]}%</td></tr>')
    body = "\n                ".join(rows)
    return f'''<div class="card mb14">
            <div class="card-hd">Fronts by Personnel</div>
            <table class="tbl">
              <thead><tr><th>Off Pers</th><th>Plays</th><th>Top Front</th><th>Top Front %</th></tr></thead>
              <tbody>
                {body}
              </tbody>
            </table>
          </div>'''

def coverage_by_personnel_card(items):
    if not items:
        return ""
    rows = []
    for i, it in enumerate(items):
        cls = ' class="hlb b"' if it["topCoveragePct"] >= 25 else (' class="hl b"' if it["topCoveragePct"] >= 15 else '')
        rows.append(f'<tr><td class="b">{esc(it["pers"])}</td><td>{it["plays"]}</td><td>{esc(it["topCoverage"])}</td><td{cls}>{it["topCoveragePct"]}%</td></tr>')
    body = "\n                ".join(rows)
    return f'''<div class="card mb14">
            <div class="card-hd">Coverage by Personnel</div>
            <table class="tbl">
              <thead><tr><th>Off Pers</th><th>Plays</th><th>Top Coverage</th><th>Top Coverage %</th></tr></thead>
              <tbody>
                {body}
              </tbody>
            </table>
          </div>'''

def build_blitz_panel(bucket, label, id_prefix, down_label="", plays_header="Plays", splits=None):
    """Full standardized Blitz sub-tab: callout, direction cards, 5/6/7-man
    scheme tables, RB tendency, Blitz by Personnel, Coverage on Blitz,
    Front on Blitz, and (ND/CD only, when `splits` is given) Stunts by
    Down & Distance. Any individual table/card with NO underlying data is
    omitted entirely -- no blank tables or "No data yet" placeholders."""
    rb_card = ""
    if bucket["rbBlitzTendency"]:
        rb_card = f'''<div class="card mb14">
              <div class="card-hd">RB Blitz Tendency ({down_label or label})</div>
              <table class="tbl">
                <thead><tr><th>RB Alignment</th><th># Plays</th><th>% of Blitz</th></tr></thead>
                <tbody>
                  {rb_table_rows(bucket["rbBlitzTendency"])}
                </tbody>
              </table>
            </div>'''

    personnel_card = ""
    if bucket["blitzByPersonnel"]:
        personnel_card = f'''<div class="card mb14">
              <div class="card-hd">Blitz by Personnel</div>
              <table class="tbl">
                <thead><tr><th>Off Pers</th><th>{plays_header}</th><th>Blitz</th><th>Blitz%</th></tr></thead>
                <tbody>
                  {personnel_table_rows(bucket["blitzByPersonnel"], plays_header)}
                </tbody>
              </table>
            </div>'''

    cov_blitz_card = ""
    if bucket["coverageOnBlitz"]:
        cov_blitz_card = f'''<div class="card">
              <div class="card-hd">Coverage on Blitz</div>
              <table class="tbl">
                <thead><tr><th>Coverage</th><th># Plays</th><th>% of Blitz</th></tr></thead>
                <tbody>
                  {scheme_table(bucket["coverageOnBlitz"], bucket["blitzCount"])}
                </tbody>
              </table>
            </div>'''

    front_blitz_card = ""
    if bucket["frontOnBlitz"]:
        front_blitz_card = f'''<div class="card">
              <div class="card-hd">Front on Blitz</div>
              <table class="tbl">
                <thead><tr><th>Front</th><th># Plays</th><th>% of Blitz</th></tr></thead>
                <tbody>
                  {scheme_table(bucket["frontOnBlitz"], bucket["blitzCount"])}
                </tbody>
              </table>
            </div>'''

    five_card = ""
    if bucket["pressureFive"]:
        five_card = f'''<div class="card mb14">
              <div class="card-hd">5-Man Pressure Schemes ({bucket["blitzCount"]} blitzes)</div>
              <table class="tbl">
                <thead><tr><th>Scheme</th><th>#</th><th>% of Blitz</th></tr></thead>
                <tbody>
                  {scheme_table(bucket["pressureFive"], bucket["blitzCount"])}
                </tbody>
              </table>
            </div>'''

    six_card = ""
    if bucket["pressureSix"]:
        six_card = f'''<div class="card mb14">
              <div class="card-hd">6-Man Pressure Schemes ({bucket["blitzCount"]} blitzes)</div>
              <table class="tbl">
                <thead><tr><th>Scheme</th><th>#</th><th>% of Blitz</th></tr></thead>
                <tbody>
                  {scheme_table(bucket["pressureSix"], bucket["blitzCount"])}
                </tbody>
              </table>
            </div>'''

    seven_card = ""
    if bucket["pressureSeven"]:
        seven_card = f'''<div class="card">
              <div class="card-hd">7-Man Pressures ({bucket["blitzCount"]} blitzes)</div>
              <table class="tbl">
                <thead><tr><th>Scheme</th><th>#</th><th>% of Blitz</th></tr></thead>
                <tbody>
                  {scheme_table(bucket["pressureSeven"], bucket["blitzCount"])}
                </tbody>
              </table>
            </div>'''

    pcards_block = ""
    if bucket["pcards"]:
        pcards_block = f'''<div class="g4 mb14">
          {pcards_html(bucket["pcards"], bucket["blitzCount"])}
        </div>'''

    left_col = "\n            ".join(c for c in [five_card, six_card, seven_card] if c)
    right_col = "\n            ".join(c for c in [rb_card, personnel_card, cov_blitz_card] if c)
    two_col_row = ""
    if left_col or right_col:
        two_col_row = f'''<div class="g2">
          <div>
            {left_col}
          </div>
          <div>
            {right_col}
          </div>
        </div>'''

    bottom_row_items = [c for c in [front_blitz_card, stunts_table_card(splits) if splits else ""] if c]
    bottom_row = ""
    if bottom_row_items:
        bottom_row = f'''<div class="g2 mt14">
          {"".join(bottom_row_items)}
        </div>'''

    return f'''
      <div class="stcon" id="{id_prefix}-blitz">
        <div class="print-label">{label} — Blitz</div>
        {blitz_callout(bucket, label)}
        {pcards_block}
        {two_col_row}
        {bottom_row}
      </div>'''

def build_fronts_panel_with_splits(bucket, label, id_prefix, canvas_prefix, splits):
    cards = split_front_cards(splits)
    grid_class = "g2" if len(cards) <= 4 else "g3"
    pers_card = fronts_by_personnel_card(bucket.get("frontsByPersonnel", []))
    pers_row = f'''<div class="g2 mb14">
          {pers_card}
        </div>''' if pers_card else ""
    return f'''
      <div class="stcon" id="{id_prefix}-fronts">
        <div class="print-label">{label} — Fronts</div>
        <div class="g2 mb14">
          <div class="card">
            <div class="card-hd">Front Family — {label}</div>
            {small_donut_canvas(canvas_prefix + "-fronts-donut")}
          </div>
          <div class="card">
            <div class="card-hd">Front Family Distribution</div>
            <table class="tbl">
              <thead><tr><th>Family</th><th># Plays</th><th>% Snaps</th></tr></thead>
              <tbody>
                {family_table_rows(bucket["frontFamily"])}
              </tbody>
            </table>
          </div>
        </div>
        {pers_row}
        <div class="{grid_class}">
          {"".join(cards)}
        </div>
      </div>'''

def build_coverage_panel_with_splits(bucket, label, id_prefix, canvas_prefix, splits):
    cards = split_coverage_cards(splits)
    grid_class = "g2" if len(cards) <= 4 else "g3"
    pers_card = coverage_by_personnel_card(bucket.get("coverageByPersonnel", []))
    pers_row = f'''<div class="g2 mb14">
          {pers_card}
        </div>''' if pers_card else ""
    return f'''
      <div class="stcon" id="{id_prefix}-coverage">
        <div class="print-label">{label} — Coverage</div>
        <div class="g2 mb14">
          <div class="card">
            <div class="card-hd">Coverage Family — {label}</div>
            {small_donut_canvas(canvas_prefix + "-cov-donut")}
          </div>
          <div class="card">
            <div class="card-hd">Coverage Distribution</div>
            <table class="tbl">
              <thead><tr><th>Family (Shell)</th><th># Plays</th><th>% Snaps</th></tr></thead>
              <tbody>
                {family_table_rows(bucket["covFamily"])}
              </tbody>
            </table>
          </div>
        </div>
        {pers_row}
        <div class="{grid_class}">
          {"".join(cards)}
        </div>
      </div>'''

def bib_pct_class(pct):
    """Conditional-formatting heat band for a Bible-tab percentage: mirrors the
    color-scale highlighting on the staff's original spreadsheet -- the higher the
    concentration, the hotter the color, so tendencies jump out at a glance."""
    if pct >= 40:
        return 'p-hot'
    if pct >= 25:
        return 'p-warm'
    if pct >= 15:
        return 'p-mild'
    return 'p-cool'

def bible_leaf_html(entries):
    """Innermost Cov-Fam/Front-Fam leaf rows: [{label,count,pct}] -> compact list."""
    if not entries:
        return '<div class="bib-empty">No data</div>'
    return "".join(
        f'<div class="bib-row bib-leaf"><span class="bib-lbl">{esc(e["label"])}</span>'
        f'<span class="bib-n">{e["count"]}x</span>'
        f'<span class="bib-pct {bib_pct_class(e["pct"])}">{e["pct"]}%</span></div>'
        for e in entries
    )

def bible_group_html(groups, label_key, inner_key):
    """One level of nesting: each group has [label_key], 'n', optional 'pct', and a leaf
    list at [inner_key]. Renders a bold header row per group + its indented leaf rows."""
    if not groups:
        return '<div class="bib-empty">No data</div>'
    out = []
    for g in groups:
        pct_val = g.get("pct")
        pct_str = f'{pct_val}%' if pct_val is not None else ""
        pct_cls = bib_pct_class(pct_val) if pct_val is not None else ""
        out.append(
            f'<div class="bib-grp"><div class="bib-row bib-hdr">'
            f'<span class="bib-lbl">{esc(str(g[label_key]))}</span>'
            f'<span class="bib-n">{g["n"]}x</span><span class="bib-pct {pct_cls}">{pct_str}</span></div>'
        )
        out.append(bible_leaf_html(g[inner_key]))
        out.append('</div>')
    return "".join(out)

def bible_pers_by_front_html(groups):
    """Triple nest: PERS(O) -> Front Family -> Cov Fam."""
    if not groups:
        return '<div class="bib-empty">No data</div>'
    out = []
    for g in groups:
        out.append(
            f'<div class="bib-grp"><div class="bib-row bib-hdr">'
            f'<span class="bib-lbl">{esc(g["pers"])}</span><span class="bib-n">{g["n"]}x</span></div>'
        )
        for f in g["fronts"]:
            out.append(
                f'<div class="bib-row bib-sub"><span class="bib-lbl">{esc(f["front"])}</span>'
                f'<span class="bib-n">{f["n"]}x</span>'
                f'<span class="bib-pct {bib_pct_class(f["pct"])}">{f["pct"]}%</span></div>'
            )
            out.append(bible_leaf_html(f["coverage"]))
        out.append('</div>')
    return "".join(out)

def bible_card(title, body_html, span=False):
    span_attr = ' style="grid-column:1/-1"' if span else ""
    return f'<div class="card bib-card"{span_attr}><div class="card-hd">{esc(title)}</div><div class="bib-body">{body_html}</div></div>'

def build_bible_section(bible):
    """'Bible' tab: Normal-Downs coverage cross-tab reference (matches the staff's own
    NDD Bible cheat sheet). bible = compute_situational.py's compute_bible() output,
    or None if there are no Normal Downs rows for this opponent."""
    if not bible:
        return '''<div class="callout info"><strong>No Normal Downs data available for this opponent yet.</strong> This section will populate automatically once a CSV is charted.</div>'''

    n = bible["n"]
    cards = []
    cards.append(bible_card("Overall Coverage", bible_leaf_html(bible["overallCoverage"])))
    cards.append(bible_card("Coverage by Off Personnel", bible_group_html(bible["coverageByOffPers"], "pers", "coverage")))
    cards.append(bible_card("Fronts by Off Personnel", bible_group_html(bible["frontByOffPers"], "pers", "fronts")))

    if bible["fibN"]:
        cards.append(bible_card(f'Coverage to FIB ({bible["fibN"]}x)', bible_leaf_html(bible["coverageToFib"])))
    if bible["warpN"]:
        cards.append(bible_card(f'Coverage to Tempo — WARP ({bible["warpN"]}x)', bible_group_html(bible["coverageToTempo"], "pers", "coverage")))

    if bible["coverageByBucket"]:
        cb = bible["coverageByBucket"]
        bucket_groups = [
            {"label": f'NICKEL ({cb["nickel"]["n"]} of {cb["total"]})', "n": cb["nickel"]["n"], "pct": cb["nickel"]["pct"], "coverage": cb["nickel"]["coverage"]},
            {"label": f'BASE ({cb["base"]["n"]} of {cb["total"]})', "n": cb["base"]["n"], "pct": cb["base"]["pct"], "coverage": cb["base"]["coverage"]},
        ]
        cards.append(bible_card("Coverage by Big Bucket Defensive Personnel", bible_group_html(bucket_groups, "label", "coverage")))

    if bible["oVsD"]:
        cards.append(bible_card("O Personnel vs D Personnel", bible_group_html(bible["oVsD"], "pers", "defpers")))
    if bible["coverageByDefPers"]:
        cards.append(bible_card("Coverage by Def Personnel", bible_group_html(bible["coverageByDefPers"], "defpers", "coverage")))

    cards.append(bible_card("Coverage by Pers by Front", bible_pers_by_front_html(bible["coverageByPersByFront"]), span=True))
    cards.append(bible_card("Coverage to Formation Group", bible_group_html(bible["coverageToFormFamily"], "form", "coverage"), span=True))

    notes_card = '''<div class="card bib-card" style="grid-column:1/-1">
        <div class="card-hd">Notes</div>
        <textarea class="bib-notes" rows="4" placeholder="Add scouting notes for this opponent here (personnel tendencies, coverage tells, situational reads)..."></textarea>
      </div>'''

    return f'''<div class="print-label">Normal Downs Bible — {n} plays</div>
      <div class="g2 bib-grid">
        {"".join(cards)}
      </div>
      {notes_card}'''
