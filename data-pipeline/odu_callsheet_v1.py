"""
ODU game-week CALLSHEET_STRUCTURE -- transcribed 2026-09-09 from Matt's "ODU CALL SHEET V1"
PDFs (5 files: OPENERS, RUN GAME - COMING OUT TRICKS ZEROS, PASS GAME, 3RD & 4TH DOWN, RZ),
mirroring vmi_callsheet_v2.py's schema and matching conventions exactly.

Transcription rules applied (same as vmi_callsheet_v2.py -- do not deviate without
re-deriving against compute_callsheet.py):

1. Every hash-paired (non-warp) play's "lt" field is the play exactly as printed in the
   document's LEFT-HAND (LH) column; "rt" is the RIGHT-HAND (RH) column, verbatim (minus
   the W-number and any trailing "(LH)"/"(RH)" print annotation). Column position = hash
   side, NOT any embedded "LT"/"RT" word in the play text itself (same caveat as VMI).
2. Leading W-numbers (W7, W115, etc.) are DROPPED from every lt/rt/call field --
   compute_callsheet.py's strip_dressing() strips them from the charted row before
   comparing, so the module text must not include them either.
3. [BRACKET] situational tags ([ON QK], [ON ORG], [ON 2], [ALERT APOLLO], [AMBUSH], etc.)
   are KEPT verbatim in lt/rt fields for non-warp plays (strip_dressing strips them
   automatically at match time). For warp plays (single "call" field, matched via
   match_warp(), which does NOT run strip_dressing) they are DROPPED from "call" but kept
   in "label" for readability.
4. A play whose LH/RH columns collapse to the identical string once the W-number and any
   "(LH)"/"(RH)" suffix are stripped (e.g. "PASADENA (LH)" / "PASADENA (RH)", or a play
   dressed identically both hashes) is encoded as warp:True with a single "call" field --
   never as warp:False with lt==rt, which would double-count every rep (see vmi_callsheet_v2
   rule 6 for why).
5. ODU's call sheet lays out some rows as two INDEPENDENT single-hash plays side-by-side in
   the same table row (not a true LT/RT pair of the same play) -- confirmed by cross-
   referencing the same codes/plays elsewhere in the document set where they appear again
   with a genuine matching partner, or don't reappear at all. Treated as two separate
   standalone entries in those cases (mirrors VMI's Tricks/2PT-Plays "(LH only)"/"(RH only)"
   convention), not force-paired into one lt/rt entry.
6. Genuine duplicate play listings across multiple categories are intentional (same
   convention/precedent as vmi_callsheet_v2.py rule 8) -- ODU's plays repeat heavily across
   down/distance and field-zone categories (e.g. KOBE, SUBMARINE, TORNADO, CHICAGO appear
   in 5+ categories each). Not de-duplicated.
7. No "note" fields -- every real play is kept, no "(?)" icon convention used here.

OPEN ITEMS -- RESOLVED 2026-09-09 against real ODU Tuesday/Wednesday practice data (Matt's
rule: "IF THEY APPEAR IN THE PRACTICE DATA THEN INCLUDE THEM ... IF THEY DO NOT APPEAR THEN
EXCLUDE"). Original transcription flagged 5 ambiguous items rather than guess; each was
checked against the real charted Play Call text and resolved as follows:
  a) "3RD 6-9 WAIT APOLLO // PASADENA, OREGON, TIRE SAN DIEGO" -- CONFIRMED real, charted
     verbatim (Wed rows 20/21/24/25, exact string match including the "3RD 6-9" prefix even
     on the RZ page copy). Added as a warp entry to BOTH 3RD & 4TH DOWN > 3rd & 6-9 (4.1/gm)
     and SITUATIONAL > Redzone 3rd & 3-6 (3.4/gm) (it appeared on both source pages). No
     "3RD 3-5 WAIT APOLLO // CHICAGO, COLORADO, COLUMBUS, OREGON" variant ever appears in
     either CSV -- not added, per the exclude-if-absent rule.
  b) "SAN DIEGO - BIRMINGHAM - BUCCANEERS" (hyphen-chain) -- "birmingham" and "buccaneer"
     confirmed ABSENT from both CSVs (grep, case-insensitive, both files). Stays excluded.
     However "SANDIEGO" (one word, no space) DOES appear standalone (Tue row 59, hash L) --
     added as its own warp entry, PASS GAME > Dropback, spelled exactly as charted.
  c) "VANILLA" (RZ > Hi Red coaching note) -- CONFIRMED real by both the practice data AND
     Matt directly ("WE DID RUN VANILLA"), charted as its own standalone Play Call (Wed rows
     57/62/67), each paired on the opposite hash with "W53 OVER TRIPS RT 38 [ON ORG] --
     VANILLA" (rows 56/61/66) -- Matt confirmed both the standalone calls AND the annotated
     OVER TRIPS-setup reps count as real VANILLA reps (n=6 total, not just the 3 standalone
     ones). Added as a warp entry in TWO categories per his 2026-09-10 follow-up: SITUATIONAL
     > Hi Red (25-13) Alert For Zero (original placement) AND RUN GAME > Tricks (added).
  d) "AKE TANGO OFF W115 TANGO SLING RT/LT..." (PASS GAME > 4 Minute) -- no "tango off",
     "take tango", or "ake tango" text anywhere in either CSV. REMOVED from the structure
     (was an OCR misread / unconfirmed prefix, not a real charted call).
  e) Minor cross-page wording drift (e.g. "HASH 4" vs "OVER 4" on F-SHORT OVER DAWN) -- left
     as originally transcribed per-page; compute_callsheet.py's exact-then-substring matching
     tolerates this (confirmed, not blocking).

STILL-OPEN DATA-QUALITY FLAGS (informational only, do not change this module -- these are
raw-CSV charting artifacts, not callsheet transcription issues):
  - Tue row 26: "W64 BOX LT NASY Z-GAS NAKED 9 Y-SLIP PAIL" -- "NASY" looks like a typo for
    "NASTY" and is also missing the "[ON QK]" bracket present on this callsheet's matching
    entry. Left as-is; matches fine via strip_dressing's leading-token strip either way, but
    worth a heads-up for the charter.
  - Wed rows 18/22: "W111 JERSEY MURDER W141 Y-BAT SQUARE CHICAGO (LH)" -- two W-numbers
    appear merged into one cell, which breaks strip_dressing's single-leading-token strip for
    just these 2 reps (the embedded "W141" survives into the compared text). Low-impact (2
    reps out of the week), flagged rather than silently patched.
"""
CALLSHEET_STRUCTURE = [
    {"group": 'OPENERS', "name": 'Opening Script', "plays": [
        {"label": "F-SHORT OVER DAWN 5/4 ENTER CRUNCH Y-GLAZE", "warp": False, "lt": "F-SHORT OVER DAWN RT HASH 5 ENTER CRUNCH Y-GLAZE", "rt": "F-SHORT OVER DAWN LT OVER 4 ENTER CRUNCH Y-GLAZE"},
        {"label": "8/9 DUO Z-SHORT 53/52 Z-JAIL/Z-PRISON", "warp": False, "lt": "8 DUO LT Z-SHORT 53 Z-JAIL", "rt": "9 DUO RT Z-SHORT 52 Z-PRISON"},
        {"label": "CHICAGO", "warp": True, "call": "CHICAGO"},
        {"label": "PS TRIPS NASTY HASH 28/29 F-STAR", "warp": False, "lt": "PS TRIPS RT NASTY HASH 28 F-STAR", "rt": "PS TRIPS LT NASTY HASH 29 F-STAR"},
        {"label": "TORNADO", "warp": True, "call": "TORNADO"},
        {"label": "HUG BOX NASTY 50/51 FLOCK H-REEF", "warp": False, "lt": "HUG BOX RT NASTY 50 FLOCK H-REEF", "rt": "HUG BOX LT NASTY 51 FLOCK H-REEF"},
        {"label": "BOX NASTY Z-GAS 8/9 ENTER CRUNCH [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS 8 ENTER CRUNCH [ON QK]", "rt": "BOX LT NASTY Z-GAS 9 ENTER CRUNCH [ON QK]"},
        {"label": "STILLETTO", "warp": True, "call": "STILLETTO"},
        {"label": "SUBMARINE", "warp": True, "call": "SUBMARINE"},
        {"label": "UNDER SLING Z-GONE FIRM 69 SMOKESHOW (LH only)", "warp": True, "call": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW"},
        {"label": "USHER JAM F-HABIT 5/4 CRUNCH", "warp": False, "lt": "USHER LT JAM F-HABIT 5 CRUNCH", "rt": "USHER RT JAM F-HABIT 4 CRUNCH"},
        {"label": "DENSE F-STOVE PASS 6/7 ENGINE Z-STEEPLE", "warp": False, "lt": "DENSE RT F-STOVE PASS 6 ENGINE Z-STEEPLE", "rt": "DENSE LT F-STOVE PASS 7 ENGINE Z-STEEPLE"},
        {"label": "UNDER TROOP TRIM 48/49 FORCE Z-STAR", "warp": False, "lt": "UNDER TROOP RT TRIM 48 FORCE Z-STAR", "rt": "UNDER TROOP LT TRIM 49 FORCE Z-STAR"},
        {"label": "TRIPS Z-IN SQUARE 38/39 TOSS Z-STAR", "warp": False, "lt": "TRIPS RT Z-IN SQUARE 38 TOSS Z-STAR", "rt": "TRIPS LT Z-IN SQUARE 39 TOSS Z-STAR"},
        {"label": "BRAZIL", "warp": True, "call": "BRAZIL"},
    ]},
    {"group": 'RUN GAME', "name": 'Wide Zone', "plays": [
        {"label": "TRIPS Z-IN SQUARE 38/39 TOSS Z-STAR", "warp": False, "lt": "TRIPS RT Z-IN SQUARE 38 TOSS Z-STAR", "rt": "TRIPS LT Z-IN SQUARE 39 TOSS Z-STAR"},
        {"label": "PS TRIPS NASTY HASH 28/29 F-STAR", "warp": False, "lt": "PS TRIPS RT NASTY HASH 28 F-STAR", "rt": "PS TRIPS LT NASTY HASH 29 F-STAR"},
        {"label": "BRAZIL", "warp": True, "call": "BRAZIL"},
        {"label": "BOX NASTY Z-GAS 8/9 ENTER CRUNCH [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS 8 ENTER CRUNCH [ON QK]", "rt": "BOX LT NASTY Z-GAS 9 ENTER CRUNCH [ON QK]"},
        {"label": "KOBE", "warp": True, "call": "KOBE"},
        {"label": "UNDER TROOP TRIM 48/49 FORCE Z-STAR", "warp": False, "lt": "UNDER TROOP RT TRIM 48 FORCE Z-STAR", "rt": "UNDER TROOP LT TRIM 49 FORCE Z-STAR"},
        {"label": "OVER TRIPS 38/39 [ON ORG]", "warp": False, "lt": "OVER TRIPS RT 38 [ON ORG]", "rt": "OVER TRIPS LT 39 [ON ORG]"},
    ]},
    {"group": 'RUN GAME', "name": 'Tite Zone', "plays": [
        {"label": "DENSE 1/0 CRAPPY Z-STAR [ON QK]", "warp": False, "lt": "DENSE RT 1 CRAPPY Z-STAR [ON QK]", "rt": "DENSE LT 0 CRAPPY Z-STAR [ON QK]"},
        {"label": "TANGO TROOP X-TRIM 1/0 PUSH COUNTER", "warp": False, "lt": "TANGO TROOP LT X-TRIM 1 PUSH COUNTER", "rt": "TANGO TROOP RT X-TRIM 0 PUSH COUNTER"},
    ]},
    {"group": 'RUN GAME', "name": 'Midzone', "plays": [
        {"label": "F-SHORT OVER DAWN HASH 5/4 ENTER CRUNCH Y-GLAZE", "warp": False, "lt": "F-SHORT OVER DAWN RT HASH 5 ENTER CRUNCH Y-GLAZE", "rt": "F-SHORT OVER DAWN LT HASH 4 ENTER CRUNCH Y-GLAZE"},
        {"label": "SUBMARINE - STRAY BASH 35/34 X-ASH", "warp": True, "call": "SUBMARINE"},
        {"label": "USHER JAM F-HABIT 5/4 CRUNCH", "warp": False, "lt": "USHER LT JAM F-HABIT 5 CRUNCH", "rt": "USHER RT JAM F-HABIT 4 CRUNCH"},
    ]},
    {"group": 'RUN GAME', "name": 'Gap Scheme', "plays": [
        {"label": "TORNADO - TRIPS NASTY HASH 6/7 TANK F-STAR", "warp": True, "call": "TORNADO"},
        {"label": "BOX NASTY 6/7 TANK F-STAR", "warp": False, "lt": "BOX RT NASTY 6 TANK F-STAR", "rt": "BOX LT NASTY 7 TANK F-STAR"},
    ]},
    {"group": 'RUN GAME', "name": 'Tricks', "plays": [
        {"label": "UNDER SLING Z-GONE FIRM 69 SMOKESHOW (LH only)", "warp": True, "call": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW"},
        {"label": "PS DIP HASH PASS 1 CRAPPY FIREBALL (LH only)", "warp": True, "call": "PS DIP LT HASH PASS 1 CRAPPY FIREBALL"},
        {"label": "VANILLA", "warp": True, "call": "VANILLA"},
    ]},
    {"group": 'RUN GAME', "name": 'Coming Out (1.4 per game)', "plays": [
        {"label": "DENSE 1/0 CRAPPY Z-STAR [ON 2]", "warp": False, "lt": "DENSE RT 1 CRAPPY Z-STAR [ON 2]", "rt": "DENSE LT 0 CRAPPY Z-STAR [ON 2]"},
        {"label": "OVER THING 1/0 COWBOY PIN [ON 2]", "warp": False, "lt": "OVER THING RT 1 COWBOY PIN [ON 2]", "rt": "OVER THING LT 0 COWBOY PIN [ON 2]"},
        {"label": "TANGO SLING Z-SLAB 1/0 FILTHY Z-CRAPPY", "warp": False, "lt": "TANGO SLING RT Z-SLAB 1 FILTHY Z-CRAPPY", "rt": "TANGO SLING LT Z-SLAB 0 FILTHY Z-CRAPPY"},
        {"label": "OVER TRIPS 38/39 [ON ORG]", "warp": False, "lt": "OVER TRIPS RT 38 [ON ORG]", "rt": "OVER TRIPS LT 39 [ON ORG]"},
        {"label": "ROYCE", "warp": True, "call": "ROYCE"},
        {"label": "SLING Z-SLAB NAKED 1/0 Z-SLIPPER Y-FLAG", "warp": False, "lt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG"},
        {"label": "THING ROLL Z-STUTTER COMEBACK [ON 2]", "warp": False, "lt": "THING RT ROLL RT Z-STUTTER COMEBACK [ON 2]", "rt": "THING LT ROLL LT Z-STUTTER COMEBACK [ON 2]"},
        {"label": "BENCH FALCONS", "warp": True, "call": "BENCH FALCONS"},
    ]},
    {"group": 'RUN GAME', "name": '2PT Plays [Think Players Not Plays]', "plays": [
        {"label": "TRIO SAME PAINT 60 MONEY X-HITCH (LH only)", "warp": True, "call": "TRIO RT SAME PAINT 60 MONEY X-HITCH"},
        {"label": "TRIO P-62 Y-CORN NOD X-VERT MURDER CORN (LH only)", "warp": True, "call": "TRIO RT P-62 Y-CORN NOD X-VERT MURDER CORN"},
        {"label": "BOX P-62 SALT X-VERT (LH only)", "warp": True, "call": "BOX RT P-62 SALT X-VERT"},
        {"label": "F-GOT STRAY BOX SAME U-52 RIB F-SCORPION KILL 30 COWBOY (RH only)", "warp": True, "call": "F-GOT STRAY RT BOX SAME U-52 RIB F-SCORPION KILL 30 COWBOY"},
        {"label": "BOX NASTY SAME 62 CRUSH Z-STATION H-BEND (LH only)", "warp": True, "call": "BOX RT NASTY SAME 62 CRUSH Z-STATION H-BEND"},
    ]},
    {"group": 'RUN GAME', "name": 'Zero', "plays": [
        {"label": "SUBMARINE - STRAY BASH 35/34 X-ASH", "warp": True, "call": "SUBMARINE"},
        {"label": "USHER JAM F-HABIT 5/4 CRUNCH", "warp": False, "lt": "USHER LT JAM F-HABIT 5 CRUNCH", "rt": "USHER RT JAM F-HABIT 4 CRUNCH"},
        {"label": "BRAZIL", "warp": True, "call": "BRAZIL"},
        {"label": "8/9 DUO Z-SHORT 53/52 Z-JAIL/Z-PRISON", "warp": False, "lt": "8 DUO LT Z-SHORT 53 Z-JAIL", "rt": "9 DUO RT Z-SHORT 52 Z-PRISON"},
        {"label": "APOLLO KILL CHICAGO // KOBE", "warp": True, "call": "APOLLO KILL CHICAGO // KOBE"},
    ]},
    {"group": 'PASS GAME', "name": 'PAP', "plays": [
        {"label": "TRIPS Z-IN SQUARE FAKE 6/7 TOSS Z-WIN Y-ESCORT X-POST", "warp": False, "lt": "TRIPS RT Z-IN SQUARE FAKE 6 TOSS Z-WIN Y-ESCORT X-POST", "rt": "TRIPS LT Z-IN SQUARE FAKE 7 TOSS Z-WIN Y-ESCORT X-POST"},
        {"label": "DENSE F-STOVE PASS 6/7 ENGINE Z-STEEPLE", "warp": False, "lt": "DENSE RT F-STOVE PASS 6 ENGINE Z-STEEPLE", "rt": "DENSE LT F-STOVE PASS 7 ENGINE Z-STEEPLE"},
        {"label": "SLING HASH F-GAS FAKE 6/7 MACHO TOSS SPOT TOPPER F-FIT", "warp": False, "lt": "SLING LT HASH F-GAS FAKE 6 MACHO TOSS SPOT TOPPER F-FIT", "rt": "SLING RT HASH F-GAS FAKE 7 MACHO TOSS SPOT TOPPER F-FIT"},
    ]},
    {"group": 'PASS GAME', "name": 'Shots', "plays": [
        {"label": "Z-SHORT BOX 5-62/4-63 X-FENCE F-DRAG KILL BRAZIL", "warp": False, "lt": "Z-SHORT BOX RT 5-62 RIB X-FENCE F-DRAG KILL BRAZIL", "rt": "Z-SHORT BOX LT 4-63 LICK X-FENCE F-DRAG KILL BRAZIL"},
        {"label": "UNDER TROOP TRIM FAKE 9/8 PUSH COWBOY PUP Z-VAPOR", "warp": False, "lt": "UNDER TROOP RT TRIM FAKE 9 PUSH COWBOY PUP Z-VAPOR", "rt": "UNDER TROOP LT TRIM FAKE 8 PUSH COWBOY PUP Z-VAPOR"},
    ]},
    {"group": 'PASS GAME', "name": 'Nakeds', "plays": [
        {"label": "TIFFANY", "warp": True, "call": "TIFFANY"},
        {"label": "BOX NASTY Z-GAS NAKED 8/9 Y-SLIP PAIL [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS NAKED 8 Y-SLIP PAIL [ON QK]", "rt": "BOX LT NASTY Z-GAS NAKED 9 Y-SLIP PAIL [ON QK]"},
        {"label": "TANGO UNDER TROOP NAKED 8/9 OREGON X-OVER", "warp": False, "lt": "TANGO UNDER TROOP RT NAKED 8 OREGON X-OVER", "rt": "TANGO UNDER TROOP LT NAKED 9 OREGON X-OVER"},
        {"label": "DAWN Z-SHAM NAKED 8/9 Y-FLAG H-SLIP", "warp": False, "lt": "DAWN LT Z-SHAM NAKED 8 Y-FLAG H-SLIP", "rt": "DAWN RT Z-SHAM NAKED 9 Y-FLAG H-SLIP"},
    ]},
    {"group": 'PASS GAME', "name": 'Movements', "plays": [
        {"label": "PS TRIPS Z-IN SQUARE DASH FLOAT", "warp": False, "lt": "PS TRIPS RT Z-IN SQUARE DASH RT FLOAT", "rt": "PS TRIPS LT Z-IN SQUARE DASH LT FLOAT"},
        {"label": "ROYCE", "warp": True, "call": "ROYCE"},
        {"label": "HUG DODGE [ON ORG]", "warp": True, "call": "HUG DODGE"},
    ]},
    {"group": 'PASS GAME', "name": 'Quicks', "plays": [
        {"label": "STILLETTO", "warp": True, "call": "STILLETTO"},
        {"label": "PS TRIPS HASH NASTY 50/51 ESKIMO X-QUICKY", "warp": False, "lt": "PS TRIPS RT HASH NASTY 50 ESKIMO X-QUICKY", "rt": "PS TRIPS LT HASH NASTY 51 ESKIMO X-QUICKY"},
        {"label": "HUG BOX NASTY 50/51 FLOCK H-REEF", "warp": False, "lt": "HUG BOX RT NASTY 50 FLOCK H-REEF", "rt": "HUG BOX LT NASTY 51 FLOCK H-REEF"},
    ]},
    {"group": 'PASS GAME', "name": 'Dropback', "plays": [
        {"label": "HUG CHIEFS", "warp": True, "call": "HUG CHIEFS"},
        {"label": "Y-IN SQUARE CHICAGO", "warp": True, "call": "CHICAGO"},
        {"label": "COLUMBUS", "warp": True, "call": "COLUMBUS"},
        {"label": "COLORADO", "warp": True, "call": "COLORADO"},
        {"label": "CAMBRIDGE MURDER CHICAGO", "warp": True, "call": "CAMBRIDGE MURDER CHICAGO"},
        {"label": "JERSEY MURDER Y-BAT SQUARE CHICAGO", "warp": True, "call": "JERSEY MURDER Y-BAT SQUARE CHICAGO"},
        {"label": "PASADENA -- DICE ATTACK Z-PIVOT", "warp": True, "call": "PASADENA"},
        {"label": "DUO Z-SHORT B-62/63 SMOKE PUMP DAGGER", "warp": False, "lt": "DUO LT Z-SHORT B-62 SMOKE PUMP DAGGER", "rt": "DUO RT Z-SHORT B-63 SMOKE PUMP DAGGER"},
        {"label": "SANDIEGO", "warp": True, "call": "SANDIEGO"},
    ]},
    {"group": 'PASS GAME', "name": 'Screens', "plays": [
        {"label": "8/9 DUO Z-SHORT 53/52 Z-JAIL/Z-PRISON", "warp": False, "lt": "8 DUO LT Z-SHORT 53 Z-JAIL", "rt": "9 DUO RT Z-SHORT 52 Z-PRISON"},
        {"label": "PS TRIPS NASTY HASH W-50/51 F-INMATE Y-ESCORT", "warp": False, "lt": "PS TRIPS RT NASTY HASH W-50 F-INMATE Y-ESCORT", "rt": "PS TRIPS LT NASTY HASH W-51 F-INMATE Y-ESCORT"},
    ]},
    {"group": 'PASS GAME', "name": '2nd & Long (7+)', "plays": [
        {"label": "BOX NASTY Z-GAS 8/9 ENTER CRUNCH [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS 8 ENTER CRUNCH [ON QK]", "rt": "BOX LT NASTY Z-GAS 9 ENTER CRUNCH [ON QK]"},
        {"label": "KOBE", "warp": True, "call": "KOBE"},
        {"label": "SUBMARINE - STRAY BASH 35/34 X-ASH", "warp": True, "call": "SUBMARINE"},
        {"label": "TORNADO - TRIPS NASTY HASH 6/7 TANK F-STAR", "warp": True, "call": "TORNADO"},
        {"label": "PS TRIPS HASH NASTY 50/51 ESKIMO X-QUICKY", "warp": False, "lt": "PS TRIPS RT HASH NASTY 50 ESKIMO X-QUICKY", "rt": "PS TRIPS LT HASH NASTY 51 ESKIMO X-QUICKY"},
        {"label": "HUG BOX NASTY 50/51 FLOCK H-REEF", "warp": False, "lt": "HUG BOX RT NASTY 50 FLOCK H-REEF", "rt": "HUG BOX LT NASTY 51 FLOCK H-REEF"},
        {"label": "Y-IN SQUARE CHICAGO", "warp": True, "call": "CHICAGO"},
        {"label": "COLORADO", "warp": True, "call": "COLORADO"},
        {"label": "PS TRIPS Z-IN SQUARE DASH FLOAT", "warp": False, "lt": "PS TRIPS RT Z-IN SQUARE DASH RT FLOAT", "rt": "PS TRIPS LT Z-IN SQUARE DASH LT FLOAT"},
        {"label": "TIFFANY", "warp": True, "call": "TIFFANY"},
        {"label": "TANGO UNDER TROOP NAKED 8/9 OREGON X-OVER", "warp": False, "lt": "TANGO UNDER TROOP RT NAKED 8 OREGON X-OVER", "rt": "TANGO UNDER TROOP LT NAKED 9 OREGON X-OVER"},
    ]},
    {"group": 'PASS GAME', "name": '4 Minute', "plays": [
        {"label": "BOX NASTY Z-GAS 8/9 ENTER CRUNCH [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS 8 ENTER CRUNCH [ON QK]", "rt": "BOX LT NASTY Z-GAS 9 ENTER CRUNCH [ON QK]"},
        {"label": "F-SHORT OVER DAWN 5/4 ENTER CRUNCH Y-GLAZE", "warp": False, "lt": "F-SHORT OVER DAWN RT HASH 5 ENTER CRUNCH Y-GLAZE", "rt": "F-SHORT OVER DAWN LT OVER 4 ENTER CRUNCH Y-GLAZE"},
        {"label": "DENSE 1/0 CRAPPY Z-STAR [ON QK]", "warp": False, "lt": "DENSE RT 1 CRAPPY Z-STAR [ON QK]", "rt": "DENSE LT 0 CRAPPY Z-STAR [ON QK]"},
        {"label": "[TURBO] STARBURST [JT MOVE]", "warp": True, "call": "STARBURST"},
        {"label": "ZULU SLING F-GOT 11/10 PUSH H-COUNTER [ON QK]", "warp": False, "lt": "ZULU SLING RT F-GOT 11 PUSH H-COUNTER [ON QK]", "rt": "ZULU SLING LT F-GOT 10 PUSH H-COUNTER [ON QK]"},
        {"label": "SLEAK HASH F-BAT SQUARE 35/34 F-BOW RITZ", "warp": False, "lt": "SLEAK LT HASH F-BAT SQUARE 35 F-BOW RITZ", "rt": "SLEAK RT HASH F-BAT SQUARE 34 F-BOW RITZ"},
        {"label": "SLING Z-SLAB NAKED 1/0 Z-SLIPPER Y-FLAG", "warp": False, "lt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG"},
        {"label": "[TURBO] OVER TRAIN ROLL RUB PACER (LH only)", "warp": True, "call": "OVER TRAIN RT ROLL RT RUB PACER"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '3rd & 1 (1.2/gm) [Submarine]', "plays": [
        {"label": "UNDER SLEAK F-BAT Q SNEAK PUSH [ON QK]", "warp": False, "lt": "UNDER SLEAK LT F-BAT Q SNEAK PUSH [ON QK]", "rt": "UNDER SLEAK RT F-BAT Q SNEAK PUSH [ON QK]"},
        {"label": "TANGO SLING Z-SLAB 1/0 FILTHY Z-CRAPPY", "warp": False, "lt": "TANGO SLING RT Z-SLAB 1 FILTHY Z-CRAPPY", "rt": "TANGO SLING LT Z-SLAB 0 FILTHY Z-CRAPPY"},
        {"label": "FOXTROT TRIPS 11/10 PUSH H-COUNTER [ON QK]", "warp": False, "lt": "FOXTROT TRIPS LT 11 PUSH H-COUNTER [ON QK]", "rt": "FOXTROT TRIPS RT 10 PUSH H-COUNTER [ON QK]"},
        {"label": "[AMBUSH] ULTRA 1/0 FILTHY (LAYTH MOVE)", "warp": False, "lt": "[AMBUSH] ULTRA RT 1 FILTHY (LAYTH MOVE)", "rt": "[AMBUSH] ULTRA LT 0 FILTHY (LAYTH MOVE)"},
        {"label": "UNDER DIP TRIM F-SLAB 1-69/0-68 FEATHER", "warp": False, "lt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER", "rt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER"},
        {"label": "SLING Z-SLAB NAKED 1/0 Z-SLIPPER Y-FLAG", "warp": False, "lt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG"},
        {"label": "SLING Z-SLAB POUND 1/0 ENTER F-POP Z-CRAPPY X-FADE", "warp": False, "lt": "SLING RT Z-SLAB POUND 1 ENTER F-POP Z-CRAPPY X-FADE", "rt": "SLING LT Z-SLAB POUND 0 ENTER F-POP Z-CRAPPY X-FADE"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '3rd & 2 (1.8/gm) [Submarine]', "plays": [
        {"label": "TANGO SLING Z-SLAB 1/0 FILTHY Z-CRAPPY", "warp": False, "lt": "TANGO SLING RT Z-SLAB 1 FILTHY Z-CRAPPY", "rt": "TANGO SLING LT Z-SLAB 0 FILTHY Z-CRAPPY"},
        {"label": "FOXTROT TRIPS 11/10 PUSH H-COUNTER [ON QK]", "warp": False, "lt": "FOXTROT TRIPS LT 11 PUSH H-COUNTER [ON QK]", "rt": "FOXTROT TRIPS RT 10 PUSH H-COUNTER [ON QK]"},
        {"label": "[AMBUSH] ULTRA 1/0 FILTHY (LAYTH MOVE)", "warp": False, "lt": "[AMBUSH] ULTRA RT 1 FILTHY (LAYTH MOVE)", "rt": "[AMBUSH] ULTRA LT 0 FILTHY (LAYTH MOVE)"},
        {"label": "UNDER DIP TRIM F-SLAB 1-69/0-68 FEATHER", "warp": False, "lt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER", "rt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER"},
        {"label": "SLING Z-SLAB NAKED 1/0 Z-SLIPPER Y-FLAG", "warp": False, "lt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG"},
        {"label": "SLING Z-SLAB POUND 1/0 ENTER F-POP Z-CRAPPY X-FADE", "warp": False, "lt": "SLING RT Z-SLAB POUND 1 ENTER F-POP Z-CRAPPY X-FADE", "rt": "SLING LT Z-SLAB POUND 0 ENTER F-POP Z-CRAPPY X-FADE"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '3rd & 3-5 (3.4/gm) [Columbus, Cambridge]', "plays": [
        {"label": "LOOSE BOX Z-BAT SQUARE B-62/63 Z-DRIVE Y-THRU X-VERT", "warp": False, "lt": "LOOSE BOX RT Z-BAT SQUARE B-62 Z-DRIVE Y-THRU X-VERT", "rt": "LOOSE BOX LT Z-BAT SQUARE B-63 Z-DRIVE Y-THRU X-VERT"},
        {"label": "Z-GONE DICE CLOSE SAME W-62/63 Z-DRIVE WHIP STUCKO", "warp": False, "lt": "Z-GONE DICE LT CLOSE SAME W-62 Z-DRIVE WHIP STUCKO", "rt": "Z-GONE DICE RT CLOSE SAME W-63 Z-DRIVE WHIP STUCKO"},
        {"label": "JERSEY MURDER Y-BAT SQUARE CHICAGO", "warp": True, "call": "JERSEY MURDER Y-BAT SQUARE CHICAGO"},
        {"label": "BOX NASTY SAME 62/63 CRUSH Z-STATION H-BEND", "warp": False, "lt": "BOX RT NASTY SAME 62 CRUSH Z-STATION H-BEND", "rt": "BOX LT NASTY SAME 63 CRUSH Z-STATION H-BEND"},
        {"label": "DENSE F-BAT SQUARE W-62/63 F-CHUB Y-BAR", "warp": False, "lt": "DENSE RT F-BAT SQUARE W-62 F-CHUB Y-BAR", "rt": "DENSE LT F-BAT SQUARE W-63 F-CHUB Y-BAR"},
        {"label": "BOX NASTY Z-GAS 8/9 ENTER CRUNCH", "warp": False, "lt": "BOX RT NASTY Z-GAS 8 ENTER CRUNCH", "rt": "BOX LT NASTY Z-GAS 9 ENTER CRUNCH"},
        {"label": "KOBE", "warp": True, "call": "KOBE"},
        {"label": "DENSE 1/0 CRAPPY Z-STAR [ON QK]", "warp": False, "lt": "DENSE RT 1 CRAPPY Z-STAR [ON QK]", "rt": "DENSE LT 0 CRAPPY Z-STAR [ON QK]"},
        {"label": "PS TRIPS Z-IN SQUARE DASH FLOAT", "warp": False, "lt": "PS TRIPS RT Z-IN SQUARE DASH RT FLOAT", "rt": "PS TRIPS LT Z-IN SQUARE DASH LT FLOAT"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '3rd & 6-9 (4.1/gm)', "plays": [
        {"label": "PASADENA [ON QK] [ALERT APOLLO]", "warp": True, "call": "PASADENA"},
        {"label": "PATRIOTS [ON QK] [ALERT SHANK]", "warp": True, "call": "PATRIOTS"},
        {"label": "Z-GONE OREGON", "warp": True, "call": "Z-GONE OREGON"},
        {"label": "LOOSE BOX Z-BAT SQUARE B-62/63 Z-DRIVE Y-THRU X-VERT", "warp": False, "lt": "LOOSE BOX RT Z-BAT SQUARE B-62 Z-DRIVE Y-THRU X-VERT", "rt": "LOOSE BOX LT Z-BAT SQUARE B-63 Z-DRIVE Y-THRU X-VERT"},
        {"label": "TIRE SANDIEGO [ALERT APOLLO]", "warp": True, "call": "TIRE SANDIEGO"},
        {"label": "DOCK F-STING 5/4 CRUNCH F-SMOKE [ON ORG]", "warp": False, "lt": "DOCK LT F-STING 5 CRUNCH F-SMOKE [ON ORG]", "rt": "DOCK RT F-STING 4 CRUNCH F-SMOKE [ON ORG]"},
        {"label": "KOBE", "warp": True, "call": "KOBE"},
        {"label": "SUBMARINE - STRAY BASH 35/34 X-ASH", "warp": True, "call": "SUBMARINE"},
        {"label": "PS TRIPS Z-IN SQUARE DASH FLOAT", "warp": False, "lt": "PS TRIPS RT Z-IN SQUARE DASH RT FLOAT", "rt": "PS TRIPS LT Z-IN SQUARE DASH LT FLOAT"},
        {"label": "3RD 6-9 WAIT APOLLO // PASADENA, OREGON, TIRE SAN DIEGO", "warp": True, "call": "3RD 6-9 WAIT APOLLO // PASADENA, OREGON, TIRE SAN DIEGO"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '3rd & 10 Plus (2.1/gm)', "plays": [
        {"label": "PASADENA [ON QK] [ALERT APOLLO]", "warp": True, "call": "PASADENA"},
        {"label": "PATRIOTS [ON QK] [ALERT SHANK]", "warp": True, "call": "PATRIOTS"},
        {"label": "DOLPHINS [ALERT SHANK]", "warp": True, "call": "DOLPHINS"},
        {"label": "DOCK F-STING 5/4 CRUNCH F-SMOKE [ON ORG]", "warp": False, "lt": "DOCK LT F-STING 5 CRUNCH F-SMOKE [ON ORG]", "rt": "DOCK RT F-STING 4 CRUNCH F-SMOKE [ON ORG]"},
        {"label": "PS TRIPS Z-IN SQUARE DASH FLOAT", "warp": False, "lt": "PS TRIPS RT Z-IN SQUARE DASH RT FLOAT", "rt": "PS TRIPS LT Z-IN SQUARE DASH LT FLOAT"},
        {"label": "PS TRIPS NASTY HASH W-50/51 F-INMATE Y-ESCORT", "warp": False, "lt": "PS TRIPS RT NASTY HASH W-50 F-INMATE Y-ESCORT", "rt": "PS TRIPS LT NASTY HASH W-51 F-INMATE Y-ESCORT"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '4th & 1 [Think Players, Not Plays]', "plays": [
        {"label": "TANGO SLING Z-SLAB 1/0 FILTHY Z-CRAPPY", "warp": False, "lt": "TANGO SLING RT Z-SLAB 1 FILTHY Z-CRAPPY", "rt": "TANGO SLING LT Z-SLAB 0 FILTHY Z-CRAPPY"},
        {"label": "T-SHIFT TO FEATHER", "warp": True, "call": "T-SHIFT TO FEATHER"},
        {"label": "SLING Z-SLAB NAKED 1/0 Z-SLIPPER Y-FLAG", "warp": False, "lt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '4th & 2-3 [Think Players, Not Plays]', "plays": [
        {"label": "TANGO SLING Z-SLAB 1/0 FILTHY Z-CRAPPY", "warp": False, "lt": "TANGO SLING RT Z-SLAB 1 FILTHY Z-CRAPPY", "rt": "TANGO SLING LT Z-SLAB 0 FILTHY Z-CRAPPY"},
        {"label": "T-SHIFT TO FEATHER", "warp": True, "call": "T-SHIFT TO FEATHER"},
    ]},
    {"group": '3RD & 4TH DOWN', "name": '4th & 4-6 [Think Players, Not Plays]', "plays": [
        {"label": "LOOSE BOX Z-BAT SQUARE B-62/63 Z-DRIVE Y-THRU X-VERT", "warp": False, "lt": "LOOSE BOX RT Z-BAT SQUARE B-62 Z-DRIVE Y-THRU X-VERT", "rt": "LOOSE BOX LT Z-BAT SQUARE B-63 Z-DRIVE Y-THRU X-VERT"},
        {"label": "Y-BAT SQUARE CHICAGO", "warp": True, "call": "Y-BAT SQUARE CHICAGO"},
    ]},
    {"group": 'SITUATIONAL', "name": 'Fringe (40-26) Alert For Zero (3rd Downs)', "plays": [
        {"label": "UNDER SLING Z-GONE FIRM 69 SMOKESHOW (LH only)", "warp": True, "call": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW"},
        {"label": "DUO Z-SHORT B-62/63 SMOKE PUMP DAGGER", "warp": False, "lt": "DUO LT Z-SHORT B-62 SMOKE PUMP DAGGER", "rt": "DUO RT Z-SHORT B-63 SMOKE PUMP DAGGER"},
        {"label": "SUBMARINE - STRAY BASH 35/34 X-ASH", "warp": True, "call": "SUBMARINE"},
        {"label": "STILLETTO", "warp": True, "call": "STILLETTO"},
        {"label": "PS TRIPS NASTY HASH W-50/51 F-INMATE Y-ESCORT", "warp": False, "lt": "PS TRIPS RT NASTY HASH W-50 F-INMATE Y-ESCORT", "rt": "PS TRIPS LT NASTY HASH W-51 F-INMATE Y-ESCORT"},
        {"label": "TIFFANY", "warp": True, "call": "TIFFANY"},
        {"label": "BOX NASTY Z-GAS NAKED 8/9 Y-SLIP PAIL [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS NAKED 8 Y-SLIP PAIL [ON QK]", "rt": "BOX LT NASTY Z-GAS NAKED 9 Y-SLIP PAIL [ON QK]"},
        {"label": "APOLLO KILL CHICAGO", "warp": True, "call": "APOLLO KILL CHICAGO"},
    ]},
    {"group": 'SITUATIONAL', "name": 'Hi Red (25-13) Alert For Zero (3rd Downs)', "plays": [
        {"label": "Y-IN SQUARE CHICAGO", "warp": True, "call": "CHICAGO"},
        {"label": "DAWN Z-SHAM NAKED 8/9 Y-FLAG H-SLIP", "warp": False, "lt": "DAWN LT Z-SHAM NAKED 8 Y-FLAG H-SLIP", "rt": "DAWN RT Z-SHAM NAKED 9 Y-FLAG H-SLIP"},
        {"label": "COLORADO", "warp": True, "call": "COLORADO"},
        {"label": "PS TRIPS Z-IN SQUARE DASH FLOAT", "warp": False, "lt": "PS TRIPS RT Z-IN SQUARE DASH RT FLOAT", "rt": "PS TRIPS LT Z-IN SQUARE DASH LT FLOAT"},
        {"label": "PS TRIPS NASTY HASH W-50/51 F-INMATE Y-ESCORT", "warp": False, "lt": "PS TRIPS RT NASTY HASH W-50 F-INMATE Y-ESCORT", "rt": "PS TRIPS LT NASTY HASH W-51 F-INMATE Y-ESCORT"},
        {"label": "HUG BOX NASTY 50/51 FLOCK H-REEF", "warp": False, "lt": "HUG BOX RT NASTY 50 FLOCK H-REEF", "rt": "HUG BOX LT NASTY 51 FLOCK H-REEF"},
        {"label": "FOXTROT TRIPS 11/10 PUSH H-COUNTER [ON QK]", "warp": False, "lt": "FOXTROT TRIPS LT 11 PUSH H-COUNTER [ON QK]", "rt": "FOXTROT TRIPS RT 10 PUSH H-COUNTER [ON QK]"},
        {"label": "USHER JAM F-HABIT 5/4 CRUNCH", "warp": False, "lt": "USHER LT JAM F-HABIT 5 CRUNCH", "rt": "USHER RT JAM F-HABIT 4 CRUNCH"},
        {"label": "[TURBO] STARBURST [JT MOVE / LYNCH MOVE]", "warp": True, "call": "STARBURST"},
        {"label": "VANILLA", "warp": True, "call": "VANILLA"},
    ]},
    {"group": 'SITUATIONAL', "name": 'Redzone 3rd & 3-6 (3.4/gm)', "plays": [
        {"label": "BUFF F-BAT SQUARE W-62/63 F-CHUB Y-STATION", "warp": False, "lt": "BUFF RT F-BAT SQUARE W-62 F-CHUB Y-STATION", "rt": "BUFF LT F-BAT SQUARE W-63 F-CHUB Y-STATION"},
        {"label": "DOCK W-62/63 LICK/RIB Y-PABLO REEF MURDER RADAR", "warp": False, "lt": "DOCK LT W-62 LICK Y-PABLO REEF MURDER RADAR", "rt": "DOCK RT W-63 RIB Y-PABLO REEF MURDER RADAR"},
        {"label": "3RD 6-9 WAIT APOLLO // PASADENA, OREGON, TIRE SAN DIEGO", "warp": True, "call": "3RD 6-9 WAIT APOLLO // PASADENA, OREGON, TIRE SAN DIEGO"},
    ]},
    {"group": 'SITUATIONAL', "name": 'Low Red (12-4)', "plays": [
        {"label": "TRIO P-62/63 Y-CORN NOD X-VERT MURDER CORN", "warp": False, "lt": "TRIO RT P-62 Y-CORN NOD X-VERT MURDER CORN", "rt": "TRIO LT P-63 Y-CORN NOD X-VERT MURDER CORN"},
        {"label": "BASH NASTY Y-INFO V-62/63 Z-SLINGSHOT", "warp": False, "lt": "BASH RT NASTY Y-INFO V-62 Z-SLINGSHOT", "rt": "BASH LT NASTY Y-INFO V-63 Z-SLINGSHOT"},
        {"label": "BOX NASTY SAME 62/63 CRUSH Z-STATION H-BEND", "warp": False, "lt": "BOX RT NASTY SAME 62 CRUSH Z-STATION H-BEND", "rt": "BOX LT NASTY SAME 63 CRUSH Z-STATION H-BEND"},
        {"label": "Z-SHORT LOOSE BOX P-62/63 PEPPER SWITCH X-VERT", "warp": False, "lt": "Z-SHORT LOOSE BOX RT P-62 PEPPER SWITCH X-VERT", "rt": "Z-SHORT LOOSE BOX LT P-63 PEPPER SWITCH X-VERT"},
        {"label": "UNDER THING Z-SHORT PLAYBOY 9 Z-FLAG (LH only)", "warp": True, "call": "UNDER THING RT Z-SHORT PLAYBOY 9 Z-FLAG"},
        {"label": "SLING Z-SLAB NAKED 1/0 Z-SLIPPER Y-FLAG", "warp": False, "lt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG"},
        {"label": "STEELERS", "warp": True, "call": "STEELERS"},
        {"label": "OVER THING 1/0 COWBOY PIN", "warp": False, "lt": "OVER THING RT 1 COWBOY PIN", "rt": "OVER THING LT 0 COWBOY PIN"},
    ]},
    {"group": 'SITUATIONAL', "name": 'Red Runs', "plays": [
        {"label": "FOXTROT TRIPS 11/10 PUSH H-COUNTER [ON QK]", "warp": False, "lt": "FOXTROT TRIPS LT 11 PUSH H-COUNTER [ON QK]", "rt": "FOXTROT TRIPS RT 10 PUSH H-COUNTER [ON QK]"},
        {"label": "SLEAK HASH F-BAT SQUARE 35/34 F-BOW RITZ", "warp": False, "lt": "SLEAK LT HASH F-BAT SQUARE 35 F-BOW RITZ", "rt": "SLEAK RT HASH F-BAT SQUARE 34 F-BOW RITZ"},
        {"label": "OVER THING 1/0 COWBOY PIN", "warp": False, "lt": "OVER THING RT 1 COWBOY PIN", "rt": "OVER THING LT 0 COWBOY PIN"},
        {"label": "[TURBO] STARBURST [JT MOVE / LYNCH MOVE]", "warp": True, "call": "STARBURST"},
        {"label": "BOX NASTY Z-GAS 8/9 ENTER CRUNCH [ON QK]", "warp": False, "lt": "BOX RT NASTY Z-GAS 8 ENTER CRUNCH [ON QK]", "rt": "BOX LT NASTY Z-GAS 9 ENTER CRUNCH [ON QK]"},
        {"label": "KOBE", "warp": True, "call": "KOBE"},
        {"label": "F-SHORT OVER DAWN HASH 5/4 ENTER CRUNCH Y-GLAZE", "warp": False, "lt": "F-SHORT OVER DAWN RT HASH 5 ENTER CRUNCH Y-GLAZE", "rt": "F-SHORT OVER DAWN LT HASH 4 ENTER CRUNCH Y-GLAZE"},
        {"label": "SUBMARINE - STRAY BASH 35/34 X-ASH", "warp": True, "call": "SUBMARINE"},
    ]},
    {"group": 'SITUATIONAL', "name": 'GL +3 Run [Think Players, Not Plays] [Tempo: Bobcat]', "plays": [
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "T-EARLS", "warp": True, "call": "T-EARLS"},
        {"label": "[TURBO] STARBURST [JT MOVE / LYNCH MOVE]", "warp": True, "call": "STARBURST"},
        {"label": "ZULU SLING F-GOT 11/10 PUSH H-COUNTER [ON QK]", "warp": False, "lt": "ZULU SLING RT F-GOT 11 PUSH H-COUNTER [ON QK]", "rt": "ZULU SLING LT F-GOT 10 PUSH H-COUNTER [ON QK]"},
    ]},
    {"group": 'SITUATIONAL', "name": 'GL +3 Pass [Think Players, Not Plays]', "plays": [
        {"label": "UNDER DIP TRIM F-SLAB 1-69/0-68 FEATHER", "warp": False, "lt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER", "rt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER"},
        {"label": "SLING Z-SLAB POUND 1/0 ENTER F-POP Z-CRAPPY X-FADE", "warp": False, "lt": "SLING RT Z-SLAB POUND 1 ENTER F-POP Z-CRAPPY X-FADE", "rt": "SLING LT Z-SLAB POUND 0 ENTER F-POP Z-CRAPPY X-FADE"},
        {"label": "T-SHIFT TO FEATHER", "warp": True, "call": "T-SHIFT TO FEATHER"},
        {"label": "F-GAS STRAY SPRINT RUB PACER (LH only)", "warp": True, "call": "F-GAS STRAY LT SPRINT RT RUB PACER"},
        {"label": "F-GOT STRAY BOX SAME U-53/52 F-SCORPION KILL 31/30 COWBOY", "warp": False, "lt": "F-GOT STRAY LT BOX SAME U-53 F-SCORPION KILL 31 COWBOY", "rt": "F-GOT STRAY RT BOX SAME U-52 RIB F-SCORPION KILL 30 COWBOY"},
    ]},
]
