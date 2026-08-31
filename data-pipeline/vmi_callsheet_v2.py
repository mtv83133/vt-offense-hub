#!/usr/bin/env python3
"""
Best-effort transcription of VMI CALLSHEET V2.pdf (uploaded 2026-08-31),
superseding vmi_callsheet_v1.py.

IMPORTANT -- read before trusting this blindly:
Same caveat as V1: this is a dense, image-only (no text layer) Google
Sheets export read off a rendered PNG, not extracted as text. V2 is MUCH
bigger than V1 -- it grew from a simple RUN GAME/PASS GAME list into two
distinct parts:

  1. CALLSHEET_STRUCTURE -- the RUN GAME / PASS GAME play list, same shape
     as V1 (same feature: joins against Install Tracker rep data via
     compute_callsheet.py to show install %). More plays than V1 (V1's
     list was clearly a work-in-progress -- V2 fleshes out Wide Zone, Tite
     Zone, Midzone, Gap Scheme, Tricks, PAP/Shots, Nakeds, Movements,
     Quicks, Dropback, Screens, and adds a new Empty category and a
     SEQUENCES category).

  2. SITUATIONAL_STRUCTURE -- brand new in V2: a down-and-distance /
     field-zone game-day call sheet (Plus Territory, Fringe, Hi Red,
     Redzone 3rd&3-6, Low Red, GL+3 Run, GL+3 Pass, 2PT Plays, Coming Out,
     2nd & Long, 3rd&1, 3rd&2, 3rd&3-5, 3rd&6-9, 3rd&10+, 4th&1, 4th&2-3,
     4th&4-6). This has NO install-tracker join -- practice reps aren't
     tagged with opponent field position, so there's no real data to
     match rep counts against. It renders as a pure reference/browse call
     sheet (what a coach would look up mid-game), not a tracked metric.
     Each entry keeps both the RH and LH version as separate list items
     (rather than V1's paired lt/rt dict) since there's no matching logic
     that needs a single clean key -- just show both hash options.

Given the density of this transcription (~150+ individual entries), some
entries are near-certain misreads on exact jersey/hole numbers (which
don't affect the RUN/PASS GAME install-tracker matching -- that logic
strips leading number tags anyway -- but do matter for the situational
list's own internal record-keeping). Matt should glance over both new
Callsheet views and flag anything wrong -- per his own 2026-08-27 note,
he's updating this callsheet frequently, so this file is expected to get
regenerated again soon.
"""

# ── PART 1: RUN GAME / PASS GAME (same shape/purpose as V1) ───────────────
CALLSHEET_STRUCTURE = [
    {"group": "RUN GAME", "name": "Openers", "plays": []},
    {"group": "RUN GAME", "name": "Wide Zone", "plays": [
        {"label": "KENYA", "warp": True, "call": "KENYA"},
        {"label": "STRAY F-SLAB 49/48 KNOCK Z-SMOKE", "warp": False,
         "lt": "STRAY LT F-SLAB 49 KNOCK Z-SMOKE", "rt": "STRAY RT F-SLAB 48 KNOCK Z-SMOKE"},
        {"label": "Z-SHORT BRAZIL", "warp": True, "call": "Z-SHORT BRAZIL",
         "note": "Listed with both a 39 (LH) and 40 (RH) number tag on the sheet, but the "
                 "dressed text itself has no LT/RT marker -- treated as one warp entry so "
                 "install-tracker matching (which strips the leading number) doesn't double-count."},
        {"label": "PS TROOP NASTY 49/48 FORCE", "warp": False,
         "lt": "PS TROOP LT NASTY 49 FORCE", "rt": "PS TROOP RT NASTY 48 FORCE"},
        {"label": "UNDER DIP HASH F-SLAB 49/48 KNOCK", "warp": False,
         "lt": "UNDER DIP LT HASH F-SLAB 49 KNOCK", "rt": "UNDER DIP RT HASH F-SLAB 48 KNOCK",
         "note": "Hash direction / number pairing on this row was hard to read precisely -- verify."},
        {"label": "FREIBURG KILL FOGBOW", "warp": True, "call": "FREIBURG KILL FOGBOW",
         "note": "Only one hash version visible (RH) in this crop -- confirm if there's an LH pair."},
        {"label": "PS HOUSE FAR F-HABIT 28/29 KEY", "warp": False,
         "lt": "PS HOUSE LT FAR F-HABIT 29 KEY", "rt": "PS HOUSE RT FAR F-HABIT 28 KEY",
         "note": "Number pairing (28/29) approximate -- verify against sheet."},
    ]},
    {"group": "RUN GAME", "name": "Tite Zone", "plays": [
        {"label": "BISON", "warp": True, "call": "BISON"},
        {"label": "[CATFISH] BISON", "warp": True, "call": "[CATFISH] BISON"},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "PS TROOP NASTY 1/0 COWBOY Z-HITCH", "warp": False,
         "lt": "PS TROOP LT NASTY 1 COWBOY Z-HITCH", "rt": "PS TROOP RT NASTY 0 COWBOY Z-HITCH",
         "note": "Sheet flags this row itself as [POSSIBLE RED] -- confirm with Matt."},
    ]},
    {"group": "RUN GAME", "name": "Midzone", "plays": [
        {"label": "DOCK F-STING 4/5 CRUNCH F-SMOKE", "warp": False,
         "lt": "DOCK LT F-STING 5 CRUNCH F-SMOKE", "rt": "DOCK RT F-STING 4 CRUNCH F-SMOKE"},
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "warp": False,
         "lt": "STRAY LT F-SLAB 5 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY",
         "note": "Only one number (5) was legible on both hash versions in this crop -- verify LT should be a different number."},
        {"label": "BREEZE", "warp": True, "call": "BREEZE"},
        {"label": "SLEAK Z-STING 36/37 TROPIC", "warp": False,
         "lt": "SLEAK LT Z-STING 37 TROPIC", "rt": "SLEAK RT Z-STING 36 TROPIC"},
        {"label": "OVER DAWN 36/37 TROPIC", "warp": False,
         "lt": "OVER DAWN LT 37 TROPIC", "rt": "OVER DAWN RT 36 TROPIC"},
    ]},
    {"group": "RUN GAME", "name": "Gap Scheme", "plays": [
        {"label": "PS HOUSE FAR F-HABIT 6/7 PUNCH", "warp": False,
         "lt": "PS HOUSE LT FAR F-HABIT 6 PUNCH", "rt": "PS HOUSE RT FAR F-HABIT 7 PUNCH",
         "note": "Hash/number pairing approximate -- verify."},
        {"label": "STRAY F-SHORT SQUARE Q-26/27 F-PUNCH H-W", "warp": False,
         "lt": "STRAY LT F-SHORT SQUARE Q-27 F-PUNCH H-W", "rt": "STRAY RT F-SHORT SQUARE Q-26 F-PUNCH H-W",
         "note": "Low-confidence read on this whole row -- dense/cut-off text."},
        {"label": "SLING Z-SWIM 36/37 OPTION F-LEVER H-SAFETY", "warp": False,
         "lt": "SLING LT Z-SWIM 37 OPTION F-LEVER H-SAFETY", "rt": "SLING RT Z-SWIM 36 OPTION F-LEVER H-SAFETY"},
        {"label": "DIP HASH FK 8/9 CRIP", "warp": False,
         "lt": "DIP LT HASH FK 9 CRIP Y-CHECK FIREBALL", "rt": "DIP RT HASH FK 8 CRIP X-TEEPEE",
         "note": "LOW CONFIDENCE -- the LH and RH versions of this row appear to have different "
                 "endings (Y-CHECK FIREBALL vs X-TEEPEE), which is unusual. May actually be two "
                 "separate plays, not one LT/RT pair. Flag to Matt."},
    ]},
    {"group": "RUN GAME", "name": "Tricks", "plays": [
        {"label": "SLEAK FAKE 7 MACHO RUM", "warp": True, "call": "SLEAK RT FAKE 7 MACHO RUM",
         "note": "Only an RT version visible in this crop -- confirm whether there's an LT pair."},
        {"label": "UNDER SLING Z-GONE FIRM 69 SMOKESHOW", "warp": True,
         "call": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW",
         "note": "Marked 'LH ONLY' on the sheet -- confirmed no RT pair exists."},
    ]},
    {"group": "PASS GAME", "name": "PAP / Shots", "plays": [
        {"label": "STRAY FAKE 6/7 MACHO TOSS SPOT TOPPER F-FIT", "warp": False,
         "lt": "STRAY LT FAKE 6 MACHO TOSS SPOT TOPPER F-FIT", "rt": "STRAY RT FAKE 7 MACHO TOSS SPOT TOPPER F-FIT"},
        {"label": "BOX Z-GAS FAKE 8/9 CRUNCH F-STEEPLE", "warp": False,
         "lt": "BOX LT Z-GAS FAKE 8 CRUNCH F-STEEPLE", "rt": "BOX RT Z-GAS FAKE 9 CRUNCH F-STEEPLE"},
        {"label": "STRAY FLEX BOX X-GAS FAKE 8/9 CRUNCH Z-STEEPLE", "warp": False,
         "lt": "STRAY LT FLEX BOX X-GAS FAKE 8 CRUNCH Z-STEEPLE", "rt": "STRAY RT FLEX BOX X-GAS FAKE 9 CRUNCH Z-STEEPLE",
         "note": "New vs V1 -- verify hash/number pairing."},
        {"label": "DICE FAKE 6/7 Y-WIN VETO", "warp": False,
         "lt": "DICE LT FAKE 7 Y-WIN VETO", "rt": "DICE RT FAKE 6 Y-WIN VETO"},
        {"label": "FLASH", "warp": True, "call": "FLASH"},
        {"label": "TWINKY - UNDER DAWN HASH FK 8/9 CRIP X-TEEPEE", "warp": True, "call": "TWINKY",
         "note": "TWINKY is the WARP/tempo codename; the dressed call is UNDER DAWN HASH FK CRIP X-TEEPEE."},
        {"label": "TENNESSEE", "warp": True, "call": "TENNESSEE"},
    ]},
    {"group": "PASS GAME", "name": "Nakeds", "plays": [
        {"label": "SLING Z-GAS VERTICALS?", "warp": True, "call": "SLING RT Z-GAS VERTICALS",
         "note": "Sheet has a literal '?' after this call -- Matt flagged this as unconfirmed himself, kept as-is."},
        {"label": "STRAY F-SLAB NAKED 8/9 Y-FLAG F-SLIP", "warp": False,
         "lt": "STRAY LT F-SLAB NAKED 8 Y-FLAG F-SLIP", "rt": "STRAY RT F-SLAB NAKED 9 Y-FLAG F-SLIP"},
        {"label": "PS TROOP NASTY NAKED 8/9 Y-LEVELS", "warp": False,
         "lt": "PS TROOP RT NASTY NAKED 8 Y-LEVELS", "rt": "PS TROOP LT NASTY NAKED 9 Y-LEVELS"},
        {"label": "UNDER DIP HASH NAKED 8/9 F-SLIPPER", "warp": False,
         "lt": "UNDER DIP RT HASH NAKED 9 F-SLIPPER", "rt": "UNDER DIP LT HASH NAKED 8 F-SLIPPER"},
    ]},
    {"group": "PASS GAME", "name": "Movements", "plays": [
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "warp": False,
         "lt": "Y-GOT TRIPS RT F-STING DASH RT FLOAT", "rt": "Y-GOT TRIPS LT F-STING DASH LT FLOAT",
         "note": "New vs V1 -- verify hash pairing direction."},
        {"label": "Y-GOT DODGE", "warp": True, "call": "Y-GOT DODGE"},
        {"label": "ROYCE - TRIPS ROLL SWITCH COMEBACK", "warp": True, "call": "ROYCE",
         "note": "ROYCE is the WARP codename; dressed call is TRIPS ROLL SWITCH COMEBACK."},
    ]},
    {"group": "PASS GAME", "name": "Quicks", "plays": [
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "MARLINS", "warp": True, "call": "MARLINS"},
        {"label": "ECLIPSE", "warp": True, "call": "ECLIPSE"},
        {"label": "EMPTY 52/53 MONEY H-PABLO", "warp": False,
         "lt": "EMPTY RT 53 MONEY H-PABLO", "rt": "EMPTY LT 52 MONEY H-PABLO"},
        {"label": "STILETTO", "warp": True, "call": "STILETTO"},
    ]},
    {"group": "PASS GAME", "name": "Dropback", "plays": [
        {"label": "VIKINGS", "warp": True, "call": "VIKINGS"},
        {"label": "COLUMBUS", "warp": True, "call": "COLUMBUS"},
        {"label": "TRIPS NASTY S2/S3 ATTACK H-REEF", "warp": False,
         "lt": "TRIPS RT NASTY S2 ATTACK H-REEF", "rt": "TRIPS RT NASTY S3 ATTACK H-REEF",
         "note": "New vs V1 -- verify hash pairing (both read as RT in this crop, may be a transcription error)."},
        {"label": "DICE CLOSE S2/S3 H-REEF ATTACK", "warp": False,
         "lt": "DICE LT CLOSE S2 H-REEF ATTACK", "rt": "DICE RT CLOSE S3 H-REEF ATTACK"},
        {"label": "STRAY W-62/63 F-STATION Z-CHEVY", "warp": False,
         "lt": "STRAY LT W-62 F-STATION Z-CHEVY", "rt": "STRAY RT W-63 F-STATION Z-CHEVY"},
        {"label": "MARLINS (2)", "warp": True, "call": "MARLINS",
         "note": "Appears a second time in the Dropback category on the sheet -- kept as a separate entry rather than merged, since it may be a distinct personnel/formation tag not captured in this transcription."},
        {"label": "CAMBRIDGE MURDER CHICAGO", "warp": True, "call": "CAMBRIDGE MURDER CHICAGO"},
        {"label": "MISSOURI", "warp": True, "call": "MISSOURI"},
        {"label": "PATRIOTS MURDER SEAHAWKS", "warp": True, "call": "PATRIOTS MURDER SEAHAWKS",
         "note": "Marked (POSSE THOUGHT) on the sheet -- a reminder/consideration, not a dressed call to install."},
        {"label": "JERSEY", "warp": True, "call": "JERSEY",
         "note": "Only appears on the LH pass; may be missing an RH pair or may be single-hash only."},
    ]},
    {"group": "PASS GAME", "name": "Screens", "plays": [
        {"label": "TRIO FAKE 6/7 F-JAIL/F-PRISON X-SMOKE", "warp": False,
         "lt": "TRIO LT FAKE 6 F-JAIL X-SMOKE", "rt": "TRIO RT FAKE 7 F-PRISON X-SMOKE"},
        {"label": "SHANK", "warp": True, "call": "SHANK"},
        {"label": "PS TRIPS HASH W-50/51 Y-SELL INMATE X-HITCH", "warp": False,
         "lt": "PS TRIPS RT HASH W-50 Y-SELL INMATE X-HITCH", "rt": "PS TRIPS LT HASH W-51 Y-SELL INMATE X-HITCH"},
    ]},
    {"group": "PASS GAME", "name": "Empty", "plays": [
        {"label": "EMPTY 52/53 MONEY H-PABLO", "warp": False,
         "lt": "EMPTY RT 53 MONEY H-PABLO", "rt": "EMPTY LT 52 MONEY H-PABLO",
         "note": "New category vs V1 -- same call also appears under Quicks; kept as its own entry per its own column on the sheet."},
        {"label": "STILETTO", "warp": True, "call": "STILETTO"},
        {"label": "HAY DICE 52/53 VERTS H-NOW", "warp": False,
         "lt": "HAY 9 DICE LT 52 VERTS H-NOW", "rt": "HAY 8 DICE RT 53 VERTS H-NOW"},
    ]},
    {"group": "SEQUENCES", "name": "Sequences", "plays": [
        {"label": "BREEZE", "warp": True, "call": "BREEZE",
         "note": "New category vs V1 -- only one entry visible in this crop; sheet may have more that weren't captured."},
    ]},
]

# ── PART 2: Opponent situational / game-day call sheet (NEW in V2) ────────
# No install-tracker join -- rendered as a pure reference list. Each entry
# is {"label": <dressed call or WARP name>, "note": <optional context>}.
# "hash" is "RH"/"LH"/None (warp calls / one-word codenames aren't hash-
# specific the way dressed run/pass calls are).
SITUATIONAL_STRUCTURE = [
    {"category": "Plus Territory", "context": "Fringe (40-26), alert for zero on 3rd downs", "plays": [
        {"label": "MICHIGAN", "hash": "RH"}, {"label": "MICHIGAN", "hash": "LH"},
        {"label": "PATRIOTS", "hash": "RH"}, {"label": "PATRIOTS", "hash": "LH"},
        {"label": "MARLINS / PHILLY", "hash": "RH"}, {"label": "MARLINS / PHILLY", "hash": "LH"},
        {"label": "TRIPS NASTY S2/S3 ATTACK H-REEF", "hash": "RH", "note": "W75/W76 -- exact number pairing approximate"},
        {"label": "SEAHAWKS [CLAMP] MURDER PATRIOTS", "hash": "RH"}, {"label": "SEAHAWKS [CLAMP] MURDER PATRIOTS", "hash": "LH"},
        {"label": "DICE FAKE 6/7 Y-WIN VETO", "hash": "RH"}, {"label": "DICE FAKE 6/7 Y-WIN VETO", "hash": "LH"},
        {"label": "SLING Z-SWIM 36/37 OPTION F-LEVER H-SAFETY", "hash": "RH"}, {"label": "SLING Z-SWIM 36/37 OPTION F-LEVER H-SAFETY", "hash": "LH"},
        {"label": "TRIPS FAKE 6/7 TOP CHIP TOPPER X-SLANT KILL FLASH", "hash": "RH"}, {"label": "TRIPS FAKE 6/7 TOP CHIP TOPPER X-SLANT KILL FLASH", "hash": "LH"},
    ]},
    {"category": "Fringe", "context": "40-26 yard line, alert for zero on 3rd downs", "plays": [
        {"label": "TRIPS NASTY S2/S3 ATTACK H-REEF", "hash": "RH/LH"},
        {"label": "TRIO FAKE 6/7 F-PRISON X-SMOKE", "hash": "RH/LH"},
        {"label": "TIRE PHILLY", "hash": "RH/LH"},
        {"label": "DICE CLOSE S2/S3 H-REEF ATTACK", "hash": "RH/LH"},
        {"label": "CHIEFS MURDER MARLINS", "hash": None},
        {"label": "MARLINS / PHILLY", "hash": "RH/LH"},
    ]},
    {"category": "Hi Red", "context": "25-13 yard line, alert for zero on 3rd downs", "plays": [
        {"label": "BUFF F-BAT SQUARE W-62/63 F-CHUB Y-STATION", "hash": "RH/LH"},
        {"label": "DOCK W-62/63 LICK/RIB Y-PABLO REEF MURDER RADAR", "hash": "RH/LH"},
        {"label": "F-GOT COLUMBUS", "hash": "RH/LH"},
    ]},
    {"category": "Redzone 3rd & 3-6", "context": "3.4 per game", "plays": [
        {"label": "TRIO P-62/63 Y-CORN NOD X-VERT MURDER CORN", "hash": "RH/LH"},
        {"label": "HUG BOX NASTY S2/S3 PEPPER H-REEF", "hash": "RH/LH"},
        {"label": "Y-GOT LOOSE BOX P-62/63 PEPPER SWITCH X-VERT", "hash": "RH/LH"},
        {"label": "SLING Z-SLAB NAKED 0/1 Z-SLIPPER Y-FLAG", "hash": "RH/LH"},
        {"label": "BOBCAT", "hash": "RH/LH"},
    ]},
    {"category": "Low Red", "context": "12-4 yard line", "plays": [
        {"label": "FOXTROT TRIPS SAME 10/11 PUSH H-CRAPPY", "hash": "RH/LH", "note": "[ON QK]"},
        {"label": "PS TROOP NASTY 48/49 FORCE", "hash": "RH/LH"},
        {"label": "STRAY F-SLAB 48/49 KNOCK Z-SMOKE", "hash": "RH/LH"},
        {"label": "BISON", "hash": "RH/LH"},
        {"label": "BOBCAT", "hash": "RH/LH"},
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "hash": "RH/LH"},
    ]},
    {"category": "GL +3 Run", "context": "Think players, not plays", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "hash": None, "note": "Personnel/matchup reminder, not a dressed call."},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "hash": "RH/LH"},
        {"label": "Z-SHORT BOBCAT Z-FIND", "hash": "RH/LH"},
        {"label": "UNDER THING NASTY Z-SHORT 1 CAPTAIN", "hash": "RH/LH", "note": "Highlighted yellow on the sheet."},
    ]},
    {"category": "GL +3 Pass", "context": "Think players, not plays", "plays": [
        {"label": "UNDER DAWN TRIM Z-SLAB 0-68 FEATHER", "hash": "RH/LH"},
        {"label": "SLING Z-SLAB PASS 0 ENTER F-POP Z-CRAPPY X-FADE", "hash": "RH", "note": "[ON 2]"},
        {"label": "TRIPS NASTY Z-SHORT V-63 Z-SLINGSHOT", "hash": "RH", "note": "[ON QK]"},
    ]},
    {"category": "2PT Plays", "plays": [
        {"label": "F-GAS STRAY SPRINT RUB PACER", "hash": "LH"},
        {"label": "[AMBUSH] SPRINT GOBBLE", "hash": "LH", "note": "[ON QK]"},
    ]},
    {"category": "Coming Out", "context": "1.4 per game", "plays": [
        {"label": "PS TROOP NASTY 0/1 COWBOY Z-HITCH", "hash": "RH/LH", "note": "[ON 2]"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "hash": "RH/LH"},
        {"label": "BOX SAME W-52/53 F-ESKIMO X-ISO", "hash": "RH/LH", "note": "[WHO AT X] flagged on sheet"},
        {"label": "TIRE PHILLY", "hash": "RH/LH"},
        {"label": "THING ROLL Z-STUTTER COMEBACK", "hash": "RH/LH", "note": "[ON 2]"},
        {"label": "TIRE FALCONS", "hash": "RH/LH", "note": "-- 3rd & 7+"},
    ]},
    {"category": "2nd & Long", "context": "7+ yards", "plays": []},
    {"category": "3rd & 1", "context": "1.2 per game", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "hash": None},
        {"label": "PS NORTH THING F-SHORT F-SNEAK", "hash": "RH/LH", "note": "Highlighted yellow on the sheet."},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "hash": "RH/LH"},
        {"label": "UNDER THING NASTY Z-SHORT 0/1 CAPTAIN", "hash": "RH/LH"},
        {"label": "BOBCAT", "hash": "RH/LH"},
    ]},
    {"category": "3rd & 2", "context": "1.8 per game", "plays": [
        {"label": "SLING Z-SLAB NAKED 1/2 Z-SLIPPER Y-FLAG", "hash": "RH/LH"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "hash": "RH/LH"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "hash": "RH/LH"},
        {"label": "BOBCAT", "hash": "RH/LH"},
        {"label": "UNDER THING NASTY Z-SHORT 0/1 CAPTAIN", "hash": "RH/LH"},
    ]},
    {"category": "3rd & 3-5", "context": "3.4 per game", "plays": [
        {"label": "F-IN SQUARE COLUMBUS", "hash": "RH/LH"},
        {"label": "CAMBRIDGE MURDER CHICAGO", "hash": "RH/LH"},
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "hash": "RH/LH"},
        {"label": "CHIEFS", "hash": None, "note": "(POSSE THOUGHT)"},
        {"label": "BUFF NASTY F-60 SAME W-62 Y-BAR F-CHUB", "hash": None, "note": "(POSSE THOUGHT)"},
        {"label": "BUFF NASTY F-G0 P-62 CRUSH X-DRIVE", "hash": None, "note": "(POSSE THOUGHT)"},
    ]},
    {"category": "3rd & 6-9", "context": "4.1 per game", "plays": [
        {"label": "Y-GOT PATRIOTS", "hash": "RH/LH"},
        {"label": "DOLPHINS", "hash": "RH/LH"},
        {"label": "BUCANEERS", "hash": "RH/LH"},
        {"label": "MISSOURI", "hash": "RH/LH"},
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "hash": "RH/LH"},
        {"label": "TRIPS F-STING S0 PUT F-BAR H-COOP", "hash": None, "note": "(POSSE THOUGHT)"},
    ]},
    {"category": "3rd & 10 Plus", "context": "2.1 per game", "plays": [
        {"label": "Y-GOT PATRIOTS", "hash": "RH/LH"},
        {"label": "DOLPHINS", "hash": "RH/LH"},
        {"label": "MISSOURI / BUCANEERS", "hash": None, "note": "(POSSE THOUGHTS)"},
    ]},
    {"category": "4th & 1", "context": "Think players, not plays", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "hash": None},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "hash": "RH/LH"},
    ]},
    {"category": "4th & 2-3", "context": "Think players, not plays", "plays": [
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "hash": "RH/LH"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "hash": "RH/LH"},
    ]},
    {"category": "4th & 4-6", "context": "Think players, not plays", "plays": [
        {"label": "F-IN SQUARE COLUMBUS", "hash": "RH/LH"},
        {"label": "Y-IN SQUARE CHICAGO", "hash": "RH/LH"},
    ]},
]
