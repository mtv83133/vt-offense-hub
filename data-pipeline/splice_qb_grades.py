#!/usr/bin/env python3
"""
splice_qb_grades.py -- adds or updates one day's worth of QB grading records
(from build_qb_grades.py's output) into self-scout.html's QB_GRADES_DATA
JS blob, between the @@QB_GRADES_DATA_START@@ / @@QB_GRADES_DATA_END@@
markers. Mirrors the add-or-update-existing-day behavior of splice_data.py.

Usage:
  python3 splice_qb_grades.py <path-to-self-scout.html> <day_key> <date YYYY-MM-DD> <label> <path-to-day_qb_grades.json>
Example:
  python3 splice_qb_grades.py DO-NOT-SHARE-plaintext-source/self-scout.html fall_1 2026-08-05 "Day 1" /tmp/fall_1_qb_grades.json
"""
import json, sys

if len(sys.argv) < 6:
    print("Usage: python3 splice_qb_grades.py <self-scout.html> <day_key> <date> <label> <day_qb_grades.json>")
    sys.exit(1)

html_path, day_key, date, label, grades_json_path = sys.argv[1:6]

with open(grades_json_path) as f:
    day_data = json.load(f)  # {'day_key':..., 'records':[...]}

full = open(html_path, encoding='utf-8').read()
marker = 'var QB_GRADES_DATA = '
start = full.find(marker)
if start == -1:
    print("ERROR: QB_GRADES_DATA marker not found in self-scout.html -- add the block first.")
    sys.exit(1)
i = start + len(marker)
if full[i] != '{':
    print("ERROR: expected '{' after QB_GRADES_DATA marker")
    sys.exit(1)
depth = 0
in_str = False
str_ch = None
esc = False
obj_start = i
j = i
while j < len(full):
    c = full[j]
    if in_str:
        if esc:
            esc = False
        elif c == '\\':
            esc = True
        elif c == str_ch:
            in_str = False
    else:
        if c == '"' or c == "'":
            in_str = True
            str_ch = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                j += 1
                break
    j += 1
obj_end = j
obj_text = full[obj_start:obj_end]
current = json.loads(obj_text)

new_day = {'key': day_key, 'date': date, 'label': label, 'records': day_data['records']}
days = current.get('days', [])
existing_idx = next((idx for idx, d in enumerate(days) if d.get('key') == day_key), None)
if existing_idx is not None:
    days[existing_idx] = new_day
    action = 'Updated existing'
else:
    days.append(new_day)
    action = 'Added new'
current['days'] = days
current['loaded'] = True

new_blob = json.dumps(current)
end_pos = obj_end
if full[end_pos] == ';':
    end_pos += 1
new_full = full[:start] + marker + new_blob + ';' + full[end_pos:]
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_full)
print(f"{action} day '{day_key}' in QB_GRADES_DATA ({len(day_data['records'])} records). "
      f"Total days now: {len(days)}. Wrote {html_path} ({len(new_full)} bytes)")
