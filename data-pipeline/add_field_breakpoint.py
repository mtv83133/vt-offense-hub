#!/usr/bin/env python3
"""Adds the (currently-null-for-all-3-teams) fieldBreakpoint field to each
team's TEAMS_DATA object, computed via find_secondary_breakpoint() +
field_breakpoint_narrative(). Appended as the new last field in each object."""
import json, sys
sys.path.insert(0, '/tmp/vt-offense-hub/data-pipeline')
from fix_teams_data import find_object_span, js_obj
from gen_html import field_breakpoint_narrative

def load(team):
    with open(f'/tmp/{team.lower()}_situational.json') as f:
        return json.load(f)

def main():
    p = '/tmp/vt-offense-hub/_source/advance-scout.html'
    html = open(p, encoding='utf-8').read()

    teams = [('MARYLAND', False), ('VMI', True), ('ODU', True)]
    for team, quoted in teams:
        start, end = find_object_span(html, team, quoted)
        scope = html[start:end]
        assert scope[0] == '{' and scope[-1] == '}'
        inner = scope[1:-1]

        data = load(team)
        narrative = field_breakpoint_narrative(data.get("secondaryBreakpoint"))
        value = json.dumps(narrative)  # null or a JSON string

        if quoted:
            addition = f',"fieldBreakpoint":{value}'
        else:
            addition = f', fieldBreakpoint: {value}'

        inner = inner.rstrip()
        if inner.endswith(','):
            inner = inner[:-1]
        inner = inner + addition

        new_scope = '{' + inner + '}'
        html = html[:start] + new_scope + html[end:]
        print(f"{team}: fieldBreakpoint = {narrative!r}")

    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Done.")

if __name__ == '__main__':
    main()
