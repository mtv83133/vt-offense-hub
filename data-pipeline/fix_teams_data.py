#!/usr/bin/env python3
import re, sys, json
sys.path.insert(0, '/tmp/vt-offense-hub/data-pipeline')
from gen_html import chart_objects

def load(team):
    with open(f'/tmp/{team.lower()}_situational.json') as f:
        return json.load(f)

def js_obj(d):
    """Compact JS object literal matching the site's existing minified style."""
    return json.dumps(d, separators=(',', ':'))

def find_object_span(html, team, quoted):
    """Find the [start,end) span of the `{ ... }` object literal assigned to
    `const <TEAM>_DATA =`.

    VMI_DATA / ODU_DATA (quoted=True) sit back-to-back with no other statements
    between them (`...VMI_DATA = {...};\nconst ODU_DATA = {...};\nconst TEAMS_DATA
    = {...};`), so the reliable boundary is simply "up to the next `\nconst `
    statement" -- far more robust than a hand-rolled brace/string scanner against
    unescaped quotes in free-text notes.

    MARYLAND_DATA (quoted=False) is followed by OTHER code (TEAM_LABELS,
    TEAMS_WITH_DEEP_DATA, etc.) before VMI_DATA, so the next-`const` trick would
    overshoot -- it still uses a manual single-quote-aware brace scanner."""
    marker = f'const {team}_DATA = '
    start_idx = html.index(marker)
    brace_start = html.index('{', start_idx)

    if quoted:
        next_stmt = html.index('\nconst ', brace_start)
        tail = html[brace_start:next_stmt].rstrip()
        if not tail.endswith('};'):
            raise RuntimeError(f"{team}_DATA statement doesn't end with '}};' as expected: ...{tail[-30:]!r}")
        end_idx = brace_start + len(tail) - 1  # exclude trailing ';', keep the '}'
        return brace_start, end_idx

    delim = "'"
    i = brace_start
    depth = 0
    in_str = False
    n = len(html)
    while i < n:
        c = html[i]
        if in_str:
            if c == '\\':
                i += 2
                continue
            elif c == delim:
                in_str = False
        else:
            if c == delim:
                in_str = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return brace_start, i + 1
        i += 1
    raise RuntimeError(f"unbalanced braces for {team}_DATA")

def replace_key(scope, key, new_val_json, quoted):
    """Replace a single top-level 'key: {...}' (Maryland style, unquoted) or
    '"key":{...}' (VMI/ODU JSON style) with the new value, within a team-scoped
    substring. Must match exactly once."""
    # `scope` is the object's INNER text (outer { and } already stripped by the
    # caller), so the "last field in the object" case is anchored on end-of-string
    # directly -- not another trailing '}'.
    if quoted:
        pat = re.compile(r'"' + re.escape(key) + r'":\s*\{.*?\}(?=,\s*"|\s*$)', re.DOTALL)
        new_text = f'"{key}":{new_val_json}'
    else:
        pat = re.compile(re.escape(key) + r':\s*\{.*?\}(?=,\s*\w+:|\s*$)', re.DOTALL)
        new_text = f'{key}: {new_val_json}'
    matches = pat.findall(scope)
    if len(matches) != 1:
        raise RuntimeError(f"key {key} matched {len(matches)} times (expected 1)")
    return pat.sub(lambda m: new_text, scope, count=1)

def main():
    p = '/tmp/vt-offense-hub/_source/advance-scout.html'
    html = open(p, encoding='utf-8').read()

    teams = [
        ('MARYLAND', False),  # Maryland uses unquoted JS-literal keys
        ('VMI', True),
        ('ODU', True),
    ]

    for team, quoted in teams:
        start, end = find_object_span(html, team, quoted)
        scope = html[start:end]
        assert scope[0] == '{' and scope[-1] == '}'
        inner = scope[1:-1]

        data = load(team)
        nd_form, nd_fronts, nd_cov = chart_objects(data['nd'])
        cd_form, cd_fronts, cd_cov = chart_objects(data['cd'])
        tmeog_form, tmeog_fronts, tmeog_cov = chart_objects(data['tmEog'])
        tmeoh_form, tmeoh_fronts, tmeoh_cov = chart_objects(data['tmEoh'])
        fm_form, fm_fronts, fm_cov = chart_objects(data['fm'])

        inner = replace_key(inner, 'ndFormationChart', js_obj(nd_form), quoted)
        inner = replace_key(inner, 'ndFrontsDonut', js_obj(nd_fronts), quoted)
        inner = replace_key(inner, 'ndCovDonut', js_obj(nd_cov), quoted)
        inner = replace_key(inner, 'cdFormationChart', js_obj(cd_form), quoted)
        inner = replace_key(inner, 'cdFrontsDonut', js_obj(cd_fronts), quoted)
        # cdCovDonut is NOT always the last field in the object (VMI has dc/stats/
        # runFamilies/etc. after it; Maryland and ODU do have it last) -- so replace
        # it with the same mid-object-safe helper as the others, rather than
        # assuming an end-of-scope anchor.
        inner = replace_key(inner, 'cdCovDonut', js_obj(cd_cov), quoted)

        new_fields = {
            "tmEogFormationChart": tmeog_form, "tmEogFrontsDonut": tmeog_fronts, "tmEogCovDonut": tmeog_cov,
            "tmEohFormationChart": tmeoh_form, "tmEohFrontsDonut": tmeoh_fronts, "tmEohCovDonut": tmeoh_cov,
            "fmFormationChart": fm_form, "fmFrontsDonut": fm_fronts, "fmCovDonut": fm_cov,
        }
        # Insert the 9 new fields immediately after the (just-replaced) cdCovDonut
        # value, regardless of where in the object that field lives.
        cdcov_text = f'"cdCovDonut":{js_obj(cd_cov)}' if quoted else f'cdCovDonut: {js_obj(cd_cov)}'
        anchor_count = inner.count(cdcov_text)
        if anchor_count != 1:
            raise RuntimeError(f"cdCovDonut anchor matched {anchor_count} times for {team}")
        if quoted:
            insert_text = ',' + ",".join(f'"{k}":{js_obj(v)}' for k, v in new_fields.items())
        else:
            insert_text = ', ' + ", ".join(f'{k}: {js_obj(v)}' for k, v in new_fields.items())
        inner = inner.replace(cdcov_text, cdcov_text + insert_text, 1)

        new_scope = '{' + inner + '}'
        html = html[:start] + new_scope + html[end:]
        print(f"{team}: OK -- nd/cd charts corrected, 9 new tm/fm chart fields added")

    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done.")

if __name__ == '__main__':
    main()
