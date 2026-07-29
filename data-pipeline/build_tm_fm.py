#!/usr/bin/env python3
import sys, json
sys.path.insert(0, '/tmp/vt-offense-hub/data-pipeline')
from gen_html import build_breakdown_section

def load(team):
    with open(f'/tmp/{team.lower()}_situational.json') as f:
        return json.load(f)

def tm_section_html(data):
    eog_html = build_breakdown_section(
        data["tmEog"], "2-Minute — End of Game", "tm-eog", "ch-tm-eog",
        onclick_fn=lambda t: f"switchTmSub('eog','{t}')"
    )
    eoh_html = build_breakdown_section(
        data["tmEoh"], "2-Minute — End of Half", "tm-eoh", "ch-tm-eoh",
        onclick_fn=lambda t: f"switchTmSub('eoh','{t}')"
    )
    return f'''<div class="tm-mode-toggle">
        <div class="tm-mode-btn on" id="tm-mode-eog-btn" onclick="switchTmMode('eog')">End of Game</div>
        <div class="tm-mode-btn" id="tm-mode-eoh-btn" onclick="switchTmMode('eoh')">End of Half</div>
      </div>
      <div class="tm-mode-wrap on" id="tm-eog-wrap">
      {eog_html}
      </div>
      <div class="tm-mode-wrap" id="tm-eoh-wrap">
      {eoh_html}
      </div>'''

def fm_section_html(data):
    return build_breakdown_section(
        data["fm"], "4-Minute Offense", "fm", "ch-fm",
        onclick_fn=lambda t: f"switchStab('fm','{t}')"
    )

def main():
    out = {}
    for team in ["MARYLAND", "VMI", "ODU"]:
        data = load(team)
        out[team] = {
            "tm": tm_section_html(data),
            "fm": fm_section_html(data),
        }
    with open('/tmp/tm_fm_sections.json', 'w') as f:
        json.dump(out, f)
    for team in out:
        print(f"{team}: tm len={len(out[team]['tm'])} fm len={len(out[team]['fm'])}")

if __name__ == '__main__':
    main()
