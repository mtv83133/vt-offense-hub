#!/usr/bin/env python3
"""
Best-effort transcription of VMI CALLSHEET V1.pdf (uploaded 2026-08-27) into
structured categories for the Install Tracker's new "Callsheet" pill.

IMPORTANT -- read before trusting this blindly:
This callsheet is a dense, image-only (no text layer) Google Sheets export
that had to be read off a rendered PNG rather than extracted as text. Most
entries are high-confidence (clean, unambiguous print), but a handful are
flagged with a "note" field where the source image was genuinely hard to
read (cut-off bracketed text, a category boundary that wasn't 100% clear,
or a call that only showed one hash direction in the crop). Matt should
glance over the live Callsheet tab and flag anything wrong -- it'll be an
easy fix, and he said he's updating this callsheet frequently anyway, so
this whole file gets regenerated each time he sends a new version.

Per Matt's 2026-08-27 direction:
  - Left/right hash versions of a dressed call (e.g. STRAY LT F-SLAB 49
    KNOCK Z-SMOKE vs STRAY RT F-SLAB 48 KNOCK Z-SMOKE) are kept as two
    separate rows, each with its own rep count/%.
  - One-word WARP/tempo calls (BISON, BOBCAT, BREEZE, KENYA, MARLINS,
    MISSOURI, SHANK, COLUMBUS, TENNESSEE, VIKINGS, BUCANEERS, ECLIPSE,
    (TIRE) PHILLY, STEEPLE) are NOT hash-paired -- one line each, matched
    by exact call name regardless of hash.

Each category entry:
  {"label": <display name>, "warp": bool,
   "call": <exact Play Call string>}                      -- warp/single, OR
  {"label": <display name>, "warp": False,
   "lt": <exact LT Play Call string>, "rt": <exact RT Play Call string>}
An optional "note" flags anything transcribed with lower confidence.
"""

CALLSHEET_STRUCTURE = [
    {"group": "RUN GAME", "name": "Openers", "plays": []},
    {"group": "RUN GAME", "name": "Wide Zone", "plays": [
        {"label": "KENYA", "warp": True, "call": "KENYA"},
        {"label": "STRAY F-SLAB 49/48 KNOCK Z-SMOKE", "warp": False,
         "lt": "STRAY LT F-SLAB 49 KNOCK Z-SMOKE", "rt": "STRAY RT F-SLAB 48 KNOCK Z-SMOKE"},
        {"label": "Z-SHORT BRAZIL", "warp": True, "call": "Z-SHORT BRAZIL",
         "note": "Only one version visible on the sheet -- verify if this needs an LT/RT pair."},
        {"label": "PS TROOP NASTY 49/48 FORCE", "warp": False,
         "lt": "PS TROOP LT NASTY 49 FORCE", "rt": "PS TROOP RT NASTY 48 FORCE"},
    ]},
    {"group": "RUN GAME", "name": "Tite Zone", "plays": [
        {"label": "BISON", "warp": True, "call": "BISON"},
        {"label": "[CATFISH] BISON", "warp": True, "call": "[CATFISH] BISON",
         "note": "Bracketed variant tag on the sheet -- confirm exact charted spelling matches."},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "PS TROOP NASTY 1/0 COWBOY", "warp": False,
         "lt": "PS TROOP LT NASTY 1 COWBOY", "rt": "PS TROOP RT NASTY 0 COWBOY"},
    ]},
    {"group": "RUN GAME", "name": "Midzone", "plays": [
        {"label": "DOCK F-STING 5/4 CRUNCH F-SMOKE", "warp": False,
         "lt": "DOCK LT F-STING 5 CRUNCH F-SMOKE", "rt": "DOCK RT F-STING 4 CRUNCH F-SMOKE"},
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "warp": False,
         "lt": "STRAY LT F-SLAB 4 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY"},
        {"label": "WAIT TUCSON // SANDIEGO", "warp": True, "call": "WAIT TUCSON // SANDIEGO",
         "note": "Also appears under Quicks (Pass Game) on the sheet -- confirm this isn't a mis-read duplicate."},
        {"label": "TRIPS NASTY 52/53 ATTACK H-REEF", "warp": False,
         "lt": "TRIPS LT NASTY 52 ATTACK H-REEF", "rt": "TRIPS RT NASTY 53 ATTACK H-REEF"},
    ]},
    {"group": "RUN GAME", "name": "Gap Scheme", "plays": [
        {"label": "TRAIN RT SAME 1 TANK", "warp": True, "call": "TRAIN RT SAME 1 TANK",
         "note": "Only an RT version was visible in this crop -- confirm whether there's an LT pair."},
        {"label": "BREEZE", "warp": True, "call": "BREEZE"},
        {"label": "SLEAK Z-STING 36/37 TROPIC Z-SMOKE", "warp": False,
         "lt": "SLEAK LT Z-STING 36 TROPIC Z-SMOKE", "rt": "SLEAK RT Z-STING 37 TROPIC Z-SMOKE"},
        {"label": "DICE CLOSE 52/53 H-REEF ATTACK", "warp": False,
         "lt": "DICE LT CLOSE 52 H-REEF ATTACK", "rt": "DICE RT CLOSE 53 H-REEF ATTACK"},
        {"label": "STRAY W-62/63 F-STATION Z-CHEVY", "warp": False,
         "lt": "STRAY LT W-62 F-STATION Z-CHEVY", "rt": "STRAY RT W-63 F-STATION Z-CHEVY"},
    ]},
    {"group": "RUN GAME", "name": "Trips", "plays": [
        {"label": "MARLINS", "warp": True, "call": "MARLINS"},
        {"label": "MISSOURI", "warp": True, "call": "MISSOURI"},
    ]},
    {"group": "RUN GAME", "name": "Tricks", "plays": [
        {"label": "Q FLY (NORTH THING)", "warp": True, "call": "Q FLY (NORTH THING)",
         "note": "Personnel tag on the sheet was hard to read -- not blocking, just flagging."},
        {"label": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW", "warp": True,
         "call": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW",
         "note": "Only an LT version was visible -- confirm whether there's an RT pair."},
    ]},
    {"group": "PASS GAME", "name": "PAP / Shots", "plays": [
        {"label": "STRAY FAKE 6/7 MACHO TOSS SPOT TOPPER F-FIT", "warp": False,
         "lt": "STRAY LT FAKE 6 MACHO TOSS SPOT TOPPER F-FIT", "rt": "STRAY RT FAKE 7 MACHO TOSS SPOT TOPPER F-FIT"},
        {"label": "BOX Z-GAS FAKE 8/9 CRUNCH F-STEEPLE", "warp": False,
         "lt": "BOX LT Z-GAS FAKE 8 CRUNCH F-STEEPLE", "rt": "BOX RT Z-GAS FAKE 9 CRUNCH F-STEEPLE"},
        {"label": "STEEPLE WARP", "warp": True, "call": "STEEPLE WARP"},
        {"label": "DICE FAKE 6/7 Y-WIN VETO", "warp": False,
         "lt": "DICE LT FAKE 7 Y-WIN VETO", "rt": "DICE RT FAKE 6 Y-WIN VETO"},
        {"label": "NASTY FAKE 8/9 CRUNCH X-STEEPLE Z-COMEBACK", "warp": False,
         "lt": "NASTY FAKE 8 CRUNCH X-STEEPLE Z-COMEBACK", "rt": "NASTY FAKE 9 CRUNCH X-STEEPLE Z-COMEBACK",
         "note": "Sheet had a cut-off bracketed note ([POSSIBLE M...]) after this -- may need updating once the callsheet is finished."},
    ]},
    {"group": "PASS GAME", "name": "Nakeds", "plays": [
        {"label": "TRIPS NASTY LICK/RIB 4-63/5-62 TOPHAT X-CLIMB", "warp": False,
         "lt": "TRIPS LT NASTY LICK 4-63 TOPHAT X-CLIMB", "rt": "TRIPS RT NASTY RIB 5-62 TOPHAT X-CLIMB"},
        {"label": "STRAY F-SLAB NAKED 8/9 Y-FLAG F-SLIP", "warp": False,
         "lt": "STRAY LT F-SLAB NAKED 8 Y-FLAG F-SLIP", "rt": "STRAY RT F-SLAB NAKED 9 Y-FLAG F-SLIP"},
        {"label": "PS TROOP NASTY NAKED 8/9 OREGON", "warp": False,
         "lt": "PS TROOP LT NASTY NAKED 8 OREGON", "rt": "PS TROOP RT NASTY NAKED 9 OREGON"},
    ]},
    {"group": "PASS GAME", "name": "Movements", "plays": [
        {"label": "Z-SHORT SQUARE BEAMER", "warp": True, "call": "Z-SHORT SQUARE BEAMER",
         "note": "Only one version visible -- confirm whether there's an LT/RT pair."},
    ]},
    {"group": "PASS GAME", "name": "Quicks", "plays": [
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "ECLIPSE", "warp": True, "call": "ECLIPSE"},
        {"label": "BUCANEERS", "warp": True, "call": "BUCANEERS"},
        {"label": "VIKINGS", "warp": True, "call": "VIKINGS"},
        {"label": "COLUMBUS", "warp": True, "call": "COLUMBUS"},
        {"label": "TENNESSEE", "warp": True, "call": "TENNESSEE"},
    ]},
    {"group": "PASS GAME", "name": "Dropback", "plays": []},
    {"group": "PASS GAME", "name": "Screens", "plays": [
        {"label": "TRIO FAKE 6/7 F-JAIL/F-PRISON X-SMOKE", "warp": False,
         "lt": "TRIO LT FAKE 6 F-JAIL X-SMOKE", "rt": "TRIO RT FAKE 7 F-PRISON X-SMOKE"},
        {"label": "SHANK", "warp": True, "call": "SHANK"},
        {"label": "PS TRIPS HASH W-51/50 Y-SELL INMATE X-HITCH", "warp": False,
         "lt": "PS TRIPS LT HASH W-51 Y-SELL INMATE X-HITCH", "rt": "PS TRIPS RT HASH W-50 Y-SELL INMATE X-HITCH"},
    ]},
]
