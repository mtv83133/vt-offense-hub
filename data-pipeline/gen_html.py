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

def total_pressure_callout(bucket, label):
    """Companion stat to blitz_callout, added 2026-08-30 per Matt's blitz vs
    sim-pressure redefinition -- Blitz Rate now only counts 5+ rushers, so
    this shows the combined (blitz + sim/show pressure) rate alongside it."""
    return (f'<div class="callout info"><strong>{bucket["totalPressurePct"]}% Total Pressure</strong> on {label} '
            f'({bucket["totalPressureCount"]}/{bucket["n"]} plays -- blitz + sim/show pressure)</div>')

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

    sim_card = ""
    if bucket.get("simPressurePackages"):
        sim_card = f'''<div class="card mb14">
              <div class="card-hd">Simulated Pressures Used ({bucket["simPressureCount"]} sim/show looks, &le;4 rushers)</div>
              <table class="tbl">
                <thead><tr><th>Package</th><th>#</th><th>% of Sim Pressure</th></tr></thead>
                <tbody>
                  {scheme_table(bucket["simPressurePackages"], bucket["simPressureCount"])}
                </tbody>
              </table>
            </div>'''

    pcards_block = ""
    if bucket["pcards"]:
        pcards_block = f'''<div class="g4 mb14">
          {pcards_html(bucket["pcards"], bucket["blitzCount"])}
        </div>'''

    left_col = "\n            ".join(c for c in [five_card, six_card, seven_card, sim_card] if c)
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
        {total_pressure_callout(bucket, label)}
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

_BIB_BAD = (229, 72, 77)
_BIB_WARN = (232, 163, 61)
_BIB_GOOD = (46, 158, 79)

def bib_heat_style(pct, group_vals):
    """Relative (Excel-style 3-color-scale) heat fill for a Bible-tab leaf percentage,
    scoped to the local group it's part of -- matches the staff's original spreadsheet
    cheat sheet, where the highest share in a given breakdown reads green and the
    lowest reads red, rather than a fixed absolute threshold."""
    vals = [v for v in group_vals if v is not None]
    if pct is None or not vals:
        return ''
    lo, hi = min(vals), max(vals)
    t = 0.5 if hi <= lo else (pct - lo) / (hi - lo)
    if t < 0.5:
        a, b, f = _BIB_BAD, _BIB_WARN, t * 2
    else:
        a, b, f = _BIB_WARN, _BIB_GOOD, (t - 0.5) * 2
    r = round(a[0] + (b[0] - a[0]) * f)
    g = round(a[1] + (b[1] - a[1]) * f)
    bl = round(a[2] + (b[2] - a[2]) * f)
    return f'background:rgba({r},{g},{bl},.6);color:#fff'

def bible_leaf_rows(entries, indent):
    """Innermost Cov-Fam/Front-Fam leaf rows: [{label,count,pct}] -> <tr> rows, heat-scaled
    relative to this list only (Overall Coverage flat list, or one group's own leaves)."""
    if not entries:
        return '<tr><td colspan="3" class="bib-empty2">No data</td></tr>'
    vals = [e["pct"] for e in entries]
    cls = f'bib-l{indent}'
    return "".join(
        f'<tr class="{cls}"><td>{esc(e["label"])}</td><td class="bib-c">{e["count"]}x</td>'
        f'<td class="bib-c" style="{bib_heat_style(e["pct"], vals)}">{e["pct"]}%</td></tr>'
        for e in entries
    )

def bible_group_rows(groups, label_key, inner_key):
    """One level of nesting: each group has [label_key], 'n', optional 'pct', and a leaf
    list at [inner_key]. Header row is plain/bold (not heat-colored); its leaves are
    heat-scaled among themselves."""
    if not groups:
        return '<tr><td colspan="3" class="bib-empty2">No data</td></tr>'
    out = []
    for g in groups:
        pct_val = g.get("pct")
        pct_str = f'{pct_val}%' if pct_val is not None else ""
        out.append(
            f'<tr class="bib-g"><td>{esc(str(g[label_key]))}</td>'
            f'<td class="bib-c">{g["n"]}x</td><td class="bib-c">{pct_str}</td></tr>'
        )
        out.append(bible_leaf_rows(g[inner_key], 1))
    return "".join(out)

def bible_pers_by_front_rows(groups):
    """Triple nest: PERS(O) -> Front Family -> Cov Fam. Both header levels stay plain;
    only the innermost Cov Fam leaves get heat-scaled, scoped to their own front."""
    if not groups:
        return '<tr><td colspan="3" class="bib-empty2">No data</td></tr>'
    out = []
    for g in groups:
        out.append(f'<tr class="bib-g"><td>{esc(g["pers"])}</td><td class="bib-c">{g["n"]}x</td><td class="bib-c"></td></tr>')
        for f in g["fronts"]:
            out.append(
                f'<tr class="bib-g2"><td>{esc(f["front"])}</td>'
                f'<td class="bib-c">{f["n"]}x</td><td class="bib-c">{f["pct"]}%</td></tr>'
            )
            out.append(bible_leaf_rows(f["coverage"], 2))
    return "".join(out)

def bible_card(title, rows_html):
    return (
        f'<div class="card bib-card2"><div class="card-hd">{esc(title)}</div>'
        f'<table class="bib-tbl"><thead><tr><th>Label</th><th class="bib-c">Cnt</th>'
        f'<th class="bib-c">%</th></tr></thead><tbody>{rows_html}</tbody></table></div>'
    )

def rz_family_str(items, bold_first=True):
    if not items:
        return '<span style="color:var(--muted)">No data</span>'
    parts = []
    for i, it in enumerate(items):
        label = f'{esc(it["label"])} {it["pct"]}%'
        parts.append(f'<strong>{label}</strong>' if bold_first and i == 0 else label)
    return ' · '.join(parts)

def rz_situational_rows(situational):
    if not situational:
        return '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data</td></tr>'
    return "".join(
        f'<tr><td>{esc(s["label"])}</td><td>{s["n"]}</td><td>{s["blitzPct"]}%</td></tr>'
        for s in situational
    )

def prm_pressure_class(pct):
    if pct >= 40: return "prm-p-hi"
    if pct >= 20: return "prm-p-mid"
    return "prm-p-lo"

def prm_entry_str(entry):
    if not entry:
        return '<span class="prm-none">—</span>'
    return f'{esc(entry["label"])} <span class="prm-pct">{entry["pct"]}%</span>'

def prm_mixers_str(mixers, blitz_looks):
    parts = [f'{esc(m["label"])} ({m["pct"]}%)' for m in (mixers or [])]
    parts += [f'{esc(b["label"])} ({b["count"]}x)' for b in (blitz_looks or [])]
    return ' · '.join(parts) if parts else '<span class="prm-none">—</span>'

def prm_rows(group):
    """PREPARE FOR / REACT TO / MIXERS / PRESSURE, shared by the ND Formation
    Breakdown (Bible tab) and RZ zone cards -- both compute_bible()'s
    ndFormationBreakdown entries and compute_rz()'s zone dicts carry
    prepareFor/reactTo/mixers/blitzLooks, differing only in the pressure-rate
    key name (pressurePct vs blitzPct)."""
    pressure_pct = group.get("pressurePct", group.get("blitzPct", 0))
    pressure_n = group.get("pressureN", group.get("blitzCount", 0))
    return f'''<div class="prm-mini">
        <div class="prm-row"><span class="prm-lbl">Prepare For</span><span class="prm-val">{prm_entry_str(group.get("prepareFor"))}</span></div>
        <div class="prm-row"><span class="prm-lbl">React To</span><span class="prm-val">{prm_entry_str(group.get("reactTo"))}</span></div>
        <div class="prm-row"><span class="prm-lbl">Mixers</span><span class="prm-val prm-mixers">{prm_mixers_str(group.get("mixers"), group.get("blitzLooks"))}</span></div>
        <div class="prm-row"><span class="prm-lbl">Pressure</span><span class="prm-val prm-pressure {prm_pressure_class(pressure_pct)}">{pressure_pct}% <span class="prm-pn">({pressure_n}/{group["n"]})</span></span></div>
      </div>'''

def prm_card(title, group):
    return f'''<div class="prm-card">
        <div class="prm-hd"><span class="prm-title">{esc(title)}</span><span class="prm-n">{group["n"]} snaps</span></div>
        {prm_rows(group)}
      </div>'''

def build_nd_formation_breakdown(items, small_sample=None):
    """Normal Downs Breakdown by Formation -- the staff's 'Michigan Breakdown'-
    style PREPARE FOR/REACT TO/MIXERS/PRESSURE cards, one per FinalForm formation
    group. Sits inside the Bible tab's .bib-cols grid, spanning the full width.
    Formations below MIN_FORM_N (compute_bible()) are rolled into a single
    small-sample note rather than cluttering the grid with 1-2-snap cards."""
    if not items:
        return ''
    cards = "".join(prm_card(it["form"], it) for it in items)
    small_html = ""
    if small_sample and small_sample.get("count"):
        forms_str = ", ".join(esc(f) for f in small_sample["forms"])
        small_html = (
            f'<div class="prm-small-note">+ {small_sample["count"]} more formation'
            f'{"s" if small_sample["count"] != 1 else ""} with fewer than 3 charted snaps '
            f'({small_sample["n"]} plays total): {forms_str}</div>'
        )
    return f'''<div class="card bib-card2" style="grid-column:1/-1">
        <div class="card-hd">Normal Downs Breakdown by Formation</div>
        <div class="prm-grid">{cards}</div>
        {small_html}
      </div>'''

def build_rz_zcard(z):
    front_str = rz_family_str(z["front"])
    sit_table = (
        '<table class="tbl mt8"><thead><tr><th>Down</th><th>Plays</th><th>Blitz%</th></tr></thead>'
        f'<tbody>{rz_situational_rows(z["situational"])}</tbody></table>'
    )
    return f'''<div class="zcard {z["cls"]}">
          <div class="zhd">{esc(z["label"])} — {z["n"]} plays</div>
          <div class="txt-sm mb8"><strong>Front:</strong> {front_str}</div>
          {prm_rows(z)}
          {sit_table}
        </div>'''

def build_rz_section(rz):
    """Red Zone tab, rebuilt 2026-08-24 from compute_situational.py's compute_rz()
    output. Unlike the Bible tab there's no earlier generator for this section to
    reuse (the previous RZ tab content was hand-authored against stale/older data
    and its exact source script no longer exists) -- this is a fresh, fully
    data-driven build using only what's actually in the current raw CSV. Returns
    a placeholder callout if there's no RZ data charted yet for this opponent."""
    if not rz:
        return '''<div class="callout info"><strong>No Red Zone data available for this opponent yet.</strong> This section will populate automatically once RZ snaps are charted.</div>'''

    cards = [
        f'<div class="pcard int"><div class="ppct">{rz["blitzPct"]}%</div><div class="plbl">RZ Blitz Rate</div><div class="pcnt">{rz["blitzCount"]}/{rz["n"]} plays</div></div>',
    ]
    if "totalPressurePct" in rz:
        # Companion stat added 2026-08-30 per Matt's blitz vs. sim-pressure
        # redefinition -- RZ Blitz Rate above is now 5+ rushers only, this
        # shows the combined (blitz + sim/show pressure) rate beside it.
        cards.append(
            f'<div class="pcard int"><div class="ppct">{rz["totalPressurePct"]}%</div>'
            f'<div class="plbl">RZ Total Pressure %</div><div class="pcnt">{rz["totalPressureCount"]}/{rz["n"]} plays</div></div>'
        )
    if rz["topCoverageGL"]:
        cards.append(
            f'<div class="pcard fld"><div class="ppct">{rz["topCoverageGL"]["pct"]}%</div>'
            f'<div class="plbl">Top Coverage at Goal Line</div><div class="pcnt">{esc(rz["topCoverageGL"]["label"])}</div></div>'
        )
    if rz["topFrontGL"]:
        cards.append(
            f'<div class="pcard dbl"><div class="ppct">{rz["topFrontGL"]["pct"]}%</div>'
            f'<div class="plbl">Top Front at Goal Line</div><div class="pcnt">{esc(rz["topFrontGL"]["label"])}</div></div>'
        )
    if rz["glSixManUniversal"]:
        cards.append('<div class="pcard bnd"><div class="ppct">100%</div><div class="pcnt">6-man on every GL blitz</div><div class="plbl">&nbsp;</div></div>')

    callout_html = ""
    if rz["callout"]:
        callout_html = f'<div class="callout danger mb14"><strong>OUTER RZ → GOAL LINE SHIFTS</strong> — {esc(rz["callout"])}</div>'
    else:
        callout_html = '<div class="callout info mb14">Not enough Red Zone plays charted yet to identify a reliable front/coverage shift between zones.</div>'

    lod_html = ""
    lod = rz.get("lineOfDemarcation")
    if lod:
        lod_html = (
            f'<div class="callout warn mb14"><strong>LINE OF DEMARCATION: THE +{lod["yardLine"]}</strong> — '
            f'{esc(lod["text"])} ({lod["nInside"]} snaps inside vs {lod["nOutside"]} outside).</div>'
        )

    zcards = "".join(build_rz_zcard(z) for z in rz["zones"])

    return f'''<div class="g4 mb14">
        {"".join(cards)}
      </div>
      {lod_html}
      {callout_html}
      <div class="g3 mb14">
        {zcards}
      </div>'''

def build_gl_section(gl):
    """Standalone Goal Line tab (#sec-gl / tmpl-gl-<TEAM>), from
    compute_situational.py's compute_gl_detail() output. Added 2026-08-27 to
    replace a one-off hand-authored block that had drifted out of sync with
    the RZ tab's own (correct, data-driven) Goal Line zone card for the
    identical situation -- this generator guarantees the two can't disagree
    again, since both now read the same underlying rows/filters."""
    if not gl:
        return '''<div class="callout info"><strong>No Goal Line data available for this opponent yet.</strong> This section will populate automatically once Goal Line snaps are charted.</div>'''

    # Combined into a single callout bubble (not two stacked ones) per Matt's
    # 2026-08-30 request -- the narrative summary sentence and the KEY
    # package-dominance line both belong together, just as two sentences in
    # one box rather than two separate colored callouts.
    narrative_bits = []
    if gl.get("narrative"):
        narrative_bits.append(f'<strong>KEY:</strong> {esc(gl["narrative"])}')
    if gl["pkgCallout"]:
        narrative_bits.append(esc(gl["pkgCallout"]))

    narrative_html = ""
    if narrative_bits:
        narrative_html = f'<div class="callout danger mb14">{"<br>".join(narrative_bits)}</div>'

    front_rows = "".join(
        f'<tr><td>{esc(f["label"])}</td><td>{f["count"]}</td><td>{f["pct"]}%</td></tr>'
        for f in gl["frontFamily"]
    ) or '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data</td></tr>'

    by_down_rows = "".join(
        f'<tr><td>{esc(d["label"])}</td><td>{esc(d["topFront"])}</td><td>{d["blitzPct"]}%</td></tr>'
        for d in gl["byDown"]
    ) or '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data</td></tr>'

    cov_rows = "".join(
        f'<tr><td>{esc(c["label"])}</td><td>{c["count"]}</td><td>{c["pct"]}%</td></tr>'
        for c in gl["coverage"]
    ) or '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No data</td></tr>'

    def pkg_rows(pkgs):
        return "".join(
            f'<tr><td>{esc(p["label"])}</td><td>{p["count"]}</td><td>{p["pct"]}%</td></tr>'
            for p in pkgs
        )
    blitz_pkg_rows = pkg_rows(gl["fivePkgs"]) + pkg_rows(gl["sixPkgs"]) + pkg_rows(gl["sevenPkgs"])
    if not blitz_pkg_rows:
        blitz_pkg_rows = '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No blitz plays charted yet</td></tr>'

    # Simulated/show pressure packages (<=4 rushers, Blitz field charted) --
    # separate table from true blitz packages, added 2026-08-30 per Matt's
    # blitz vs. sim-pressure redefinition.
    sim_pkg_rows = pkg_rows(gl.get("simPressurePkgs", []))
    if not sim_pkg_rows:
        sim_pkg_rows = '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No simulated pressure looks charted yet</td></tr>'
    sim_n = gl.get("simPressureN", 0)
    sim_pct = round(sim_n/gl["n"]*100) if gl["n"] else 0

    return f'''{narrative_html}
      <div class="g3">
        <div class="card">
          <div class="card-hd">Front Families</div>
          <table class="tbl"><thead><tr><th>Family</th><th>#</th><th>%</th></tr></thead><tbody>{front_rows}</tbody></table>
          <div class="mt8 card-hd">Front &amp; Blitz by Down</div>
          <table class="tbl"><thead><tr><th>Down</th><th>Top Front</th><th>Blitz Rate</th></tr></thead><tbody>{by_down_rows}</tbody></table>
        </div>
        <div class="card">
          <div class="card-hd">Coverage</div>
          <table class="tbl"><thead><tr><th>Coverage</th><th>#</th><th>%</th></tr></thead><tbody>{cov_rows}</tbody></table>
        </div>
        <div class="card">
          <div class="card-hd">Pressure Summary</div>
          <table class="tbl"><thead><tr><th>Package</th><th>Plays</th><th>%</th></tr></thead><tbody>
            <tr><td><strong>Total Pressure</strong></td><td>{gl.get("totalPressureN", gl["blitzCount"])} of {gl["n"]}</td><td>{gl.get("totalPressurePct", gl["blitzPct"])}%</td></tr>
            <tr><td>Blitz (5+ Rushers)</td><td>{gl["blitzCount"]} of {gl["n"]}</td><td>{gl["blitzPct"]}%</td></tr>
            <tr><td style="padding-left:16px">— 5-Man</td><td>{gl["fiveManN"]}</td><td>{round(gl["fiveManN"]/gl["blitzCount"]*100) if gl["blitzCount"] else 0}%</td></tr>
            <tr><td style="padding-left:16px">— 6-Man</td><td>{gl["sixManN"]}</td><td>{round(gl["sixManN"]/gl["blitzCount"]*100) if gl["blitzCount"] else 0}%</td></tr>
            <tr><td style="padding-left:16px">— 7-Man</td><td>{gl["sevenManN"]}</td><td>{round(gl["sevenManN"]/gl["blitzCount"]*100) if gl["blitzCount"] else 0}%</td></tr>
            <tr><td>Sim/Show Pressure (&le;4 Rushers)</td><td>{sim_n} of {gl["n"]}</td><td>{sim_pct}%</td></tr>
          </tbody></table>
          <div class="mt8 card-hd">Blitz Packages Used</div>
          <table class="tbl"><thead><tr><th>Package</th><th>#</th><th>%</th></tr></thead><tbody>{blitz_pkg_rows}</tbody></table>
          <div class="mt8 card-hd">Simulated Pressures Used</div>
          <table class="tbl"><thead><tr><th>Package</th><th>#</th><th>%</th></tr></thead><tbody>{sim_pkg_rows}</tbody></table>
        </div>
      </div>'''

def build_bible_section(bible):
    """'Bible' tab: Normal-Downs coverage cross-tab reference (matches the staff's own
    NDD Bible cheat sheet, dense-spreadsheet style). bible = compute_situational.py's
    compute_bible() output, or None if there are no Normal Downs rows for this opponent."""
    if not bible:
        return '''<div class="callout info"><strong>No Normal Downs data available for this opponent yet.</strong> This section will populate automatically once a CSV is charted.</div>'''

    n = bible["n"]
    cards = []
    cards.append(bible_card("Overall Coverage", bible_leaf_rows(bible["overallCoverage"], 0)))
    cards.append(bible_card("Coverage by Off Personnel", bible_group_rows(bible["coverageByOffPers"], "pers", "coverage")))
    cards.append(bible_card("Fronts by Off Personnel", bible_group_rows(bible["frontByOffPers"], "pers", "fronts")))

    if bible["fibN"]:
        cards.append(bible_card(f'Coverage to FIB ({bible["fibN"]}x)', bible_leaf_rows(bible["coverageToFib"], 0)))
    if bible["warpN"]:
        cards.append(bible_card(f'Coverage to Tempo — WARP ({bible["warpN"]}x)', bible_group_rows(bible["coverageToTempo"], "pers", "coverage")))

    if bible["coverageByBucket"]:
        cb = bible["coverageByBucket"]
        bucket_groups = [
            {"label": f'NICKEL ({cb["nickel"]["n"]} of {cb["total"]})', "n": cb["nickel"]["n"], "pct": cb["nickel"]["pct"], "coverage": cb["nickel"]["coverage"]},
            {"label": f'BASE ({cb["base"]["n"]} of {cb["total"]})', "n": cb["base"]["n"], "pct": cb["base"]["pct"], "coverage": cb["base"]["coverage"]},
        ]
        cards.append(bible_card("Coverage by Big Bucket Defensive Personnel", bible_group_rows(bucket_groups, "label", "coverage")))

    if bible["oVsD"]:
        cards.append(bible_card("O Personnel vs D Personnel", bible_group_rows(bible["oVsD"], "pers", "defpers")))
    if bible["coverageByDefPers"]:
        cards.append(bible_card("Coverage by Def Personnel", bible_group_rows(bible["coverageByDefPers"], "defpers", "coverage")))

    cards.append(bible_card("Coverage by Pers by Front", bible_pers_by_front_rows(bible["coverageByPersByFront"])))

    notes_card = '''<div class="card bib-card" style="grid-column:1/-1">
        <div class="card-hd">Notes</div>
        <textarea class="bib-notes" rows="4" placeholder="Add scouting notes for this opponent here (personnel tendencies, coverage tells, situational reads)..."></textarea>
      </div>'''

    # Normal Downs Breakdown by Formation replaces the old flat "Coverage to
    # Formation Group" table with the PREPARE FOR/REACT TO/MIXERS/PRESSURE card
    # format (same underlying FinalForm cross-tab, richer presentation).
    formation_breakdown = build_nd_formation_breakdown(bible.get("ndFormationBreakdown"), bible.get("ndFormationSmallSample"))

    return f'''<div class="print-label">Normal Downs Bible — {n} plays</div>
      <div class="bib-cols">
        {"".join(cards)}
      </div>
      {formation_breakdown}
      {notes_card}'''

def _tag_table_rows(items, colspan=2):
    if not items:
        return f'<tr><td colspan="{colspan}" style="text-align:center;color:var(--muted)">No data yet</td></tr>'
    rows = []
    for i, it in enumerate(items):
        cls = ' class="b hl"' if i == 0 else ""
        rows.append(f'<tr><td{cls}>{esc(it["label"])}</td><td{cls}>{it["n"]}</td></tr>')
    return "\n".join(rows)

def build_p10_summary(bucket):
    """Quick-summary pcard bar for the top of the P&10 (1st Play of Every
    Drive) tab -- shown above the Formations/Fronts/Coverage/Blitz stabs,
    outside any single sub-tab, so it's visible no matter which one is
    active. Per Matt's 2026-08-31 request for "a quick summary at top".
    Four headline numbers: dominant Front Family, Zone/Man coverage split
    (via manZoneP10, same classification as the site-wide Man/Zone feature),
    true Blitz Rate (5+ rushers, same definition every other tab uses), and
    Nickel-vs-Base personnel usage. Total Pressure (blitz + sim/show) is
    intentionally left out of this headline bar -- it's one click away on
    the Blitz sub-tab (build_blitz_panel already shows it there for every
    bucket) and four stats keeps this bar genuinely "quick". Caller
    (build_p10_section) only invokes this when bucket["n"] > 0."""
    n = bucket["n"]
    top_front = bucket["frontFamily"][0] if bucket["frontFamily"] else None
    front_label = top_front["label"] if top_front else "—"
    front_pct = top_front["pct"] if top_front else 0
    mz = bucket.get("manZoneP10") or {"zonePct": 0, "manPct": 0}
    dp = bucket.get("defPersonnel") or {"nickelPct": 0, "nickel": 0, "n": 0}
    return f'''<div class="g4 mb14">
        <div class="pcard int"><div class="ppct">{front_pct}%</div><div class="plbl">{esc(front_label)} Front</div><div class="pcnt">{n} plays</div></div>
        <div class="pcard fld"><div class="ppct">{mz["zonePct"]}%</div><div class="plbl">Zone Coverage</div><div class="pcnt">{mz["manPct"]}% Man</div></div>
        <div class="pcard dbl"><div class="ppct">{bucket["blitzPct"]}%</div><div class="plbl">Blitz Rate</div><div class="pcnt">{bucket["blitzCount"]}/{n} plays</div></div>
        <div class="pcard bnd"><div class="ppct">{dp["nickelPct"]}%</div><div class="plbl">Nickel Personnel</div><div class="pcnt">{dp["nickel"]}/{dp["n"]} plays</div></div>
      </div>'''

def build_p10_section(data):
    """Full P&10 (1st Play of Every Drive) tab: Quick Summary pcard bar +
    the standard 4-stab breakdown (Formations/Fronts/Coverage/Blitz), same
    shape as 2MIN/4MIN (build_breakdown_section) -- P&10 has no down-distance
    splits table since it's always 1st & 10 by definition. data = compute_p10.
    py's JSON output (the {"team","totalRowsLoaded","p10RowsUsed","p10":{...}}
    dict); pass {} / {"p10": None} for an opponent with no P&10 file charted
    yet to get the single empty-state message instead of a real breakdown."""
    bucket = data.get("p10") if data else None
    if not bucket or not bucket.get("n"):
        return '<div class="callout info">No P&10 (1st Play of Every Drive) data charted yet for this opponent.</div>'
    summary = build_p10_summary(bucket)
    breakdown = build_breakdown_section(
        bucket, "1st Play of Drive (P&10)", "p10", "ch-p10",
        onclick_fn=lambda t: f"switchStab('p10','{t}')"
    )
    return summary + "\n      " + breakdown

def build_run_section(run_tab):
    """Run Defense tab: run-family efficiency callout/chart hooks (the actual
    bars/canvas are drawn client-side from TEAMS_DATA.runFamilies -- this just
    needs the narrative callout) + DL 3-Tech (RB Side) alignment and DE
    Reaction (P.O.A. / Read) breakdown tables. run_tab = compute_situational.
    py's compute_run_tab() output. Matches the existing tmpl-run-<TEAM> /
    sec-run-body structure and CSS classes used by ODU/MARYLAND/VMI."""
    if not run_tab or not run_tab.get("n"):
        return '''<div class="callout success"><strong>Run Efficiency Allowed: —</strong> — awaiting PFF/XOS breakdown for this opponent.</div>
<div class="g2 mb14">
<div class="card"><div class="card-hd">Run Family Efficiencies (Higher % = Better for Offense)</div><div id="run-eff-bars"></div><div class="txt-xs txt-muted mt8">No run-family data loaded yet for this opponent.</div></div>
<div class="card"><div class="card-hd">Run Family Efficiency Chart</div><div class="ch-lg"><canvas id="ch-run-eff"></canvas></div></div>
</div>
<div class="g2">
<div class="card"><div class="card-hd">DL Techniques — 3 Tech (RB Side)</div><table class="tbl"><thead><tr><th>Alignment</th><th># Plays</th></tr></thead><tbody><tr><td colspan="2" style="text-align:center;color:var(--muted)">No data yet</td></tr></tbody></table></div>
<div class="card"><div class="card-hd">Run Game Reactions</div><div class="g2">
<div><div class="card-hd" style="margin-bottom:6px">DE Reaction (P.O.A.)</div><table class="tbl"><thead><tr><th>Reaction</th><th>#</th></tr></thead><tbody><tr><td colspan="2" style="text-align:center;color:var(--muted)">No data yet</td></tr></tbody></table></div>
<div><div class="card-hd" style="margin-bottom:6px">DE Reaction (Read)</div><table class="tbl"><thead><tr><th>Reaction</th><th>#</th></tr></thead><tbody><tr><td colspan="2" style="text-align:center;color:var(--muted)">No data yet</td></tr></tbody></table></div>
</div></div>
</div>'''

    narrative = esc(run_tab["narrative"]) if run_tab.get("narrative") else f'Overall Run Efficiency Allowed: {run_tab["effPct"]}% ({run_tab["effN"]}/{run_tab["n"]} qualifying snaps).'
    # narrative already has "Overall Run Efficiency Allowed: X%" as plain text --
    # bold just that lead-in span to match the site's existing callout style.
    narrative = narrative.replace(
        f'Overall Run Efficiency Allowed: {run_tab["effPct"]}%',
        f'<strong>Overall Run Efficiency Allowed: {run_tab["effPct"]}%</strong>', 1)

    return f'''<div class="callout success">{narrative}</div>
<div class="g2 mb14">
<div class="card"><div class="card-hd">Run Family Efficiencies (Higher % = Better for Offense)</div><div id="run-eff-bars"></div><div class="txt-xs txt-muted mt8">🟢 &lt;50% = Good D · 🟡 50-59% = Moderate · 🔴 60%+ = Offense Wins</div></div>
<div class="card"><div class="card-hd">Run Family Efficiency Chart</div><div class="ch-lg"><canvas id="ch-run-eff"></canvas></div></div>
</div>
<div class="g2">
<div class="card"><div class="card-hd">DL Techniques — 3 Tech (RB Side)</div><table class="tbl"><thead><tr><th>Alignment</th><th># Plays</th></tr></thead><tbody>{_tag_table_rows(run_tab["threeTech"])}</tbody></table></div>
<div class="card"><div class="card-hd">Run Game Reactions</div><div class="g2">
<div><div class="card-hd" style="margin-bottom:6px">DE Reaction (P.O.A.)</div><table class="tbl"><thead><tr><th>Reaction</th><th>#</th></tr></thead><tbody>{_tag_table_rows(run_tab["dePoa"])}</tbody></table></div>
<div><div class="card-hd" style="margin-bottom:6px">DE Reaction (Read)</div><table class="tbl"><thead><tr><th>Reaction</th><th>#</th></tr></thead><tbody>{_tag_table_rows(run_tab["deRead"])}</tbody></table></div>
</div></div>
</div>'''
