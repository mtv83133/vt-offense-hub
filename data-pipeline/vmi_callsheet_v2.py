#!/usr/bin/env python3
"""
VMI Callsheet -- transcribed from 4 clean, section-scoped PDF crops Matt sent
2026-08-31 (RUN GAME/TRICKS, PASS GAME, 3RD-4TH DOWN, RZ-SITUATIONS), fully
superseding the earlier vmi_callsheet_v2.py pass, which was read off one
dense, tiny, 90-degree-rotated full-page export and had a real error rate as
a result. Per Matt's direct request ("I think we need to clean up the
callsheet... can we start over with uploading it and rebuild it?"), this is
a ground-up rebuild against clean, legible, per-section source images --
NOT a patch of the old file.

Confidence is much higher this pass: every section PDF rendered at 4x zoom
(2448x3168) came out fully legible with a clear grid, explicit "LT"/"RT"
text embedded directly in most dressed calls, and explicit "(LH)"/"(RH)"
tags on single/warp calls. Where the old file had a "(?)" uncertainty note
from guessing at number pairing, this pass either confirms the guess was
right, corrects it with a real read, or (for a handful of genuinely new
plays not in the old file at all) adds it fresh. Notable corrections vs.
the previous pass, so nothing looks like it silently changed:

  - Plus Territory and Fringe are confirmed to be ONE category (the sheet's
    own header is literally "Plus Territory" stacked over "FRINGE (40-26)
    ALERT FOR ZERO (3RD DOWNS)" as one red block).
  - The "Hi Red (25-13)" content from the previous pass was right, but the
    "Redzone (Other)" plays I'd flagged as unconfirmed (BUFF F-BAT SQUARE,
    DOCK LICK/RIB, F-GOT COLUMBUS) are now confirmed to belong under
    "Redzone 3rd & 3-6", not their own group.
  - What I'd filed under "Low Red" in the first pass (FOXTROT TRIPS, PS
    TROOP NASTY 48/49 FORCE, STRAY F-SLAB 48/49 KNOCK, BISON, BOBCAT, STRAY
    F-SLAB 4/5 ENTER CRAPPY) actually belongs to "Red Runs [TEMPO BISON,
    BOBCAT, KENYA]" -- Low Red's real plays are TRIO P-62/63 Y-CORN NOD,
    HUG BOX NASTY 52/53 PEPPER, Y-GOT LOOSE BOX P-62/63, SLING Z-SLAB NAKED,
    and STEELERS (a warp call that didn't appear anywhere in the old file).
  - Several LT/RT number pairings that were guessed backwards last pass are
    now corrected (BOX NASTY Z-GAS FAKE 8/9, PS TROOP NASTY NAKED 8/9,
    UNDER DIP HASH NAKED 8/9, Y-GOT TRIPS F-STING DASH, EMPTY 52/53 MONEY,
    SLEAK Z-STING 36/37, PS TROOP NASTY 1/0 COWBOY Z-HITCH). "TRIPS NASTY
    S2/S3 ATTACK H-REEF" and "DICE CLOSE S2/S3" were OCR misreads of "52/53"
    in the dense version -- confirmed as plain numbers here.
  - A few plays present in the old file (VIKINGS, COLUMBUS as standalone
    Dropback calls, MARLINS (2), PS TRIPS HASH W-50/51 Y-SELL INMATE
    X-HITCH under Screens, STILETTO, HAY DICE 52/53 VERTS H-NOW) do not
    appear anywhere in these clean crops and have been dropped rather than
    carried forward on guesswork.
  - New plays/categories confirmed for the first time: BUCANEERS and
    WAGON JERSEY (Dropback), STEELERS (Low Red), TRIPS FAKE 6/7 TOP CHIP
    TOPPER X-SLANT KILL FLASH with real LT=6/RT=7 pairing, BUFF F-BAT
    SQUARE and DOCK LICK/RIB with real number pairing, UNDER DAWN TRIM
    Z-SLAB (GL+3 Pass -- distinct from UNDER DIP TRIM F-SLAB, not a
    duplicate), 2PT Plays' TRIPS NASTY Z-SHORT V-63 Z-SLINGSHOT.
  - SEQUENCES category remains removed per Matt's earlier direction (still
    not present in any of these crops either).

A handful of entries are genuinely single-hash-only or use non-hash
personnel/direction tags baked into the call itself (e.g. "F-GAS STRAY LT
SPRINT RT RUB PACER") -- these stay as one "warp" line with the literal
sheet text rather than a forced lt/rt split. "MARLINS / PHILLY" appears as
a combined reference on the sheet in a few situational categories; rather
than create an unmatchable literal "MARLINS / PHILLY" call (which would
always show 0 reps even though MARLINS and PHILLY are each separately
tracked and DO have reps under PASS GAME > Quicks), it's split into its two
real components here so the rep/% numbers stay meaningful.
"""

CALLSHEET_STRUCTURE = [
    # ── RUN GAME ─────────────────────────────────────────────────────────
    {"group": "RUN GAME", "name": "Openers", "plays": []},
    {"group": "RUN GAME", "name": "Wide Zone", "plays": [
        {"label": "KENYA", "warp": True, "call": "KENYA"},
        {"label": "STRAY F-SLAB 49/48 KNOCK Z-SMOKE", "warp": False,
         "lt": "STRAY LT F-SLAB 49 KNOCK Z-SMOKE", "rt": "STRAY RT F-SLAB 48 KNOCK Z-SMOKE"},
        {"label": "Z-SHORT BRAZIL", "warp": True, "call": "Z-SHORT BRAZIL",
         "note": "Same dressed text on both hashes (W39 LH / W40 RH) -- one warp entry so matching doesn't double-count."},
        {"label": "PS TROOP NASTY 49/48 FORCE", "warp": False,
         "lt": "PS TROOP LT NASTY 49 FORCE", "rt": "PS TROOP RT NASTY 48 FORCE"},
        {"label": "UNDER DIP HASH F-SLAB 49/48 KNOCK", "warp": False,
         "lt": "UNDER DIP LT HASH F-SLAB 49 KNOCK", "rt": "UNDER DIP RT HASH F-SLAB 48 KNOCK"},
        {"label": "FREIBURG KILL FOGBOW", "warp": True, "call": "FREIBURG KILL FOGBOW",
         "note": "Same dressed text on both hashes (W53 LH / W54 RH) -- one warp entry."},
        {"label": "PS HOUSE FAR F-HABIT 28/29 KEY", "warp": False,
         "lt": "PS HOUSE LT FAR F-HABIT 29 KEY", "rt": "PS HOUSE RT FAR F-HABIT 28 KEY"},
    ]},
    {"group": "RUN GAME", "name": "Tite Zone", "plays": [
        {"label": "BISON", "warp": True, "call": "BISON"},
        {"label": "[CATFISH] BISON", "warp": True, "call": "[CATFISH] BISON",
         "note": "Same dressed text on both hashes (W45 LH / W46 RH) -- one warp entry."},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "PS TROOP NASTY 1/0 COWBOY Z-HITCH", "warp": False,
         "lt": "PS TROOP LT NASTY 0 COWBOY Z-HITCH", "rt": "PS TROOP RT NASTY 1 COWBOY Z-HITCH",
         "note": "[POSSIBLE RED] flagged on the sheet. Same play (W47/W48) also appears under the situational Coming Out category tagged [ON 2]."},
    ]},
    {"group": "RUN GAME", "name": "Midzone", "plays": [
        {"label": "DOCK F-STING 4/5 CRUNCH F-SMOKE", "warp": False,
         "lt": "DOCK LT F-STING 5 CRUNCH F-SMOKE", "rt": "DOCK RT F-STING 4 CRUNCH F-SMOKE"},
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "warp": False,
         "lt": "STRAY LT F-SLAB 4 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY"},
        {"label": "BREEZE", "warp": True, "call": "BREEZE"},
    ]},
    {"group": "RUN GAME", "name": "Gap Scheme", "plays": [
        {"label": "SLEAK Z-STING 36/37 TROPIC", "warp": False,
         "lt": "SLEAK LT Z-STING 36 TROPIC", "rt": "SLEAK RT Z-STING 37 TROPIC"},
        {"label": "OVER DAWN 36/37 TROPIC", "warp": False,
         "lt": "OVER DAWN LT 37 TROPIC", "rt": "OVER DAWN RT 36 TROPIC"},
        {"label": "PS HOUSE FAR F-HABIT 6/7 PUNCH", "warp": False,
         "lt": "PS HOUSE LT FAR F-HABIT 6 PUNCH", "rt": "PS HOUSE RT FAR F-HABIT 7 PUNCH"},
        {"label": "STRAY F-SHORT SQUARE Q-26/27 F-PUNCH H-W", "warp": False,
         "lt": "STRAY LT F-SHORT SQUARE Q-27 F-PUNCH H-W", "rt": "STRAY RT F-SHORT SQUARE Q-26 F-PUNCH H-W"},
        {"label": "SLING Z-SWIM 36/37 OPTION F-LEVER H-SAFETY", "warp": False,
         "lt": "SLING LT Z-SWIM 37 OPTION F-LEVER H-SAFETY", "rt": "SLING RT Z-SWIM 36 OPTION F-LEVER H-SAFETY"},
    ]},
    {"group": "RUN GAME", "name": "Tricks", "plays": [
        {"label": "UNDER SLING Z-GONE FIRM 69 SMOKESHOW", "warp": True,
         "call": "UNDER SLING LT Z-GONE FIRM 69 SMOKESHOW", "note": "LH ONLY per the sheet -- no RT pair."},
        {"label": "PS DIP HASH PASS 1 CRAPPY Y-CHECK FIREBALL", "warp": True,
         "call": "PS DIP RT HASH PASS 1 CRAPPY Y-CHECK FIREBALL",
         "note": "Only an RT version shown on the sheet, standalone (not paired with the LH-only Under Sling entry next to it)."},
        {"label": "SLEAK FAKE 7 MACHO RUM", "warp": True, "call": "SLEAK RT FAKE 7 MACHO RUM",
         "note": "Only an RT version shown on the sheet."},
    ]},

    # ── PASS GAME ────────────────────────────────────────────────────────
    {"group": "PASS GAME", "name": "PAP", "plays": [
        {"label": "STRAY FAKE 6/7 MACHO TOSS SPOT TOPPER F-FIT", "warp": False,
         "lt": "STRAY LT FAKE 6 MACHO TOSS SPOT TOPPER F-FIT", "rt": "STRAY RT FAKE 7 MACHO TOSS SPOT TOPPER F-FIT"},
        {"label": "BOX NASTY Z-GAS FAKE 8/9 CRUNCH F-STEEPLE", "warp": False,
         "lt": "BOX LT NASTY Z-GAS FAKE 9 CRUNCH F-STEEPLE", "rt": "BOX RT NASTY Z-GAS FAKE 8 CRUNCH F-STEEPLE"},
        {"label": "STRAY FLEX BOX X-GAS FAKE 8/9 CRUNCH Z-STEEPLE", "warp": False,
         "lt": "STRAY LT FLEX BOX X-GAS FAKE 8 CRUNCH Z-STEEPLE", "rt": "STRAY RT FLEX BOX X-GAS FAKE 9 CRUNCH Z-STEEPLE"},
        {"label": "DICE FAKE 6/7 Y-WIN VETO", "warp": False,
         "lt": "DICE LT FAKE 7 Y-WIN VETO", "rt": "DICE RT FAKE 6 Y-WIN VETO"},
        {"label": "FLASH", "warp": True, "call": "FLASH"},
    ]},
    {"group": "PASS GAME", "name": "Shots", "plays": [
        {"label": "TWINKY", "warp": True, "call": "TWINKY",
         "note": "TWINKY is the WARP/tempo codename; dressed call is UNDER DAWN HASH FK 8/9 CRIP X-TEEPEE."},
        {"label": "TENNESSEE", "warp": True, "call": "TENNESSEE"},
        {"label": "SLING Z-GAS VERTICALS?", "warp": True, "call": "SLING RT Z-GAS VERTICALS",
         "note": "Sheet has a literal '?' after this call -- Matt flagged it as unconfirmed himself, kept as-is."},
    ]},
    {"group": "PASS GAME", "name": "Nakeds", "plays": [
        {"label": "STRAY F-SLAB NAKED 8/9 Y-FLAG F-SLIP", "warp": False,
         "lt": "STRAY LT F-SLAB NAKED 8 Y-FLAG F-SLIP", "rt": "STRAY RT F-SLAB NAKED 9 Y-FLAG F-SLIP"},
        {"label": "PS TROOP NASTY NAKED 8/9 Y-LEVELS", "warp": False,
         "lt": "PS TROOP LT NASTY NAKED 9 Y-LEVELS", "rt": "PS TROOP RT NASTY NAKED 8 Y-LEVELS"},
        {"label": "UNDER DIP HASH NAKED 8/9 F-SLIPPER", "warp": False,
         "lt": "UNDER DIP LT HASH NAKED 8 F-SLIPPER", "rt": "UNDER DIP RT HASH NAKED 9 F-SLIPPER"},
    ]},
    {"group": "PASS GAME", "name": "Movements", "plays": [
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "warp": False,
         "lt": "Y-GOT TRIPS LT F-STING DASH LT FLOAT", "rt": "Y-GOT TRIPS RT F-STING DASH RT FLOAT"},
        {"label": "Y-GOT DODGE", "warp": True, "call": "Y-GOT DODGE"},
        {"label": "ROYCE", "warp": True, "call": "ROYCE",
         "note": "ROYCE is the WARP codename; dressed call is TRIPS ROLL SWITCH COMEBACK."},
    ]},
    {"group": "PASS GAME", "name": "Quicks", "plays": [
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "MARLINS", "warp": True, "call": "MARLINS"},
        {"label": "ECLIPSE", "warp": True, "call": "ECLIPSE"},
        {"label": "EMPTY 52/53 MONEY H-PABLO", "warp": False,
         "lt": "EMPTY LT 52 MONEY H-PABLO", "rt": "EMPTY RT 53 MONEY H-PABLO"},
    ]},
    {"group": "PASS GAME", "name": "Dropback", "plays": [
        {"label": "TRIPS NASTY 52/53 ATTACK H-REEF", "warp": False,
         "lt": "TRIPS LT NASTY 53 ATTACK H-REEF", "rt": "TRIPS RT NASTY 52 ATTACK H-REEF"},
        {"label": "DICE CLOSE 52/53 H-REEF ATTACK", "warp": False,
         "lt": "DICE LT CLOSE 52 H-REEF ATTACK", "rt": "DICE RT CLOSE 53 H-REEF ATTACK"},
        {"label": "PATRIOTS MURDER SEAHAWKS", "warp": True, "call": "PATRIOTS MURDER SEAHAWKS"},
        {"label": "CAMBRIDGE MURDER CHICAGO", "warp": True, "call": "CAMBRIDGE MURDER CHICAGO"},
        {"label": "STRAY W-62/63 F-STATION Z-CHEVY", "warp": False,
         "lt": "STRAY LT W-62 F-STATION Z-CHEVY", "rt": "STRAY RT W-63 F-STATION Z-CHEVY"},
        {"label": "BUCANEERS", "warp": True, "call": "BUCANEERS"},
        {"label": "MISSOURI", "warp": True, "call": "MISSOURI"},
        {"label": "WAGON JERSEY", "warp": True, "call": "WAGON JERSEY"},
    ]},
    {"group": "PASS GAME", "name": "Screens", "plays": [
        {"label": "TRIO FAKE 6/7 F-JAIL/F-PRISON X-SMOKE", "warp": False,
         "lt": "TRIO LT FAKE 6 F-JAIL X-SMOKE", "rt": "TRIO RT FAKE 7 F-PRISON X-SMOKE"},
        {"label": "SHANK", "warp": True, "call": "SHANK"},
    ]},
    {"group": "PASS GAME", "name": "Empty", "plays": [
        {"label": "EMPTY 52/53 MONEY H-PABLO", "warp": False,
         "lt": "EMPTY LT 52 MONEY H-PABLO", "rt": "EMPTY RT 53 MONEY H-PABLO",
         "note": "Same call also listed under Quicks -- its own line on the sheet's Empty category too."},
    ]},

    # ── SITUATIONAL ──────────────────────────────────────────────────────
    {"group": "SITUATIONAL", "name": "Plus Territory / Fringe (40-26)", "plays": [
        {"label": "MICHIGAN", "warp": True, "call": "MICHIGAN"},
        {"label": "PATRIOTS", "warp": True, "call": "PATRIOTS"},
        {"label": "MARLINS", "warp": True, "call": "MARLINS",
         "note": "Sheet lists 'MARLINS / PHILLY' as a combined reference -- split so real install reps show for each (see (TIRE) PHILLY below)."},
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "TRIPS NASTY 52/53 ATTACK H-REEF", "warp": False,
         "lt": "TRIPS LT NASTY 53 ATTACK H-REEF", "rt": "TRIPS RT NASTY 52 ATTACK H-REEF"},
        {"label": "SEAHAWKS [CLAMP] MURDER PATRIOTS", "warp": True, "call": "SEAHAWKS [CLAMP] MURDER PATRIOTS"},
        {"label": "DICE FAKE 6/7 Y-WIN VETO", "warp": False,
         "lt": "DICE LT FAKE 7 Y-WIN VETO", "rt": "DICE RT FAKE 6 Y-WIN VETO"},
        {"label": "SLING Z-SWIM 36/37 OPTION F-LEVER H-SAFETY", "warp": False,
         "lt": "SLING LT Z-SWIM 37 OPTION F-LEVER H-SAFETY", "rt": "SLING RT Z-SWIM 36 OPTION F-LEVER H-SAFETY"},
        {"label": "TRIPS FAKE 6/7 TOP CHIP TOPPER X-SLANT KILL FLASH", "warp": False,
         "lt": "TRIPS LT FAKE 6 TOP CHIP TOPPER X-SLANT KILL FLASH", "rt": "TRIPS RT FAKE 7 TOP CHIP TOPPER X-SLANT KILL FLASH"},
    ]},
    {"group": "SITUATIONAL", "name": "Hi Red (25-13)", "plays": [
        {"label": "TRIPS NASTY 52/53 ATTACK H-REEF", "warp": False,
         "lt": "TRIPS LT NASTY 53 ATTACK H-REEF", "rt": "TRIPS RT NASTY 52 ATTACK H-REEF"},
        {"label": "TRIO FAKE 6/7 F-JAIL/F-PRISON X-SMOKE", "warp": False,
         "lt": "TRIO LT FAKE 6 F-JAIL X-SMOKE", "rt": "TRIO RT FAKE 7 F-PRISON X-SMOKE"},
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "DICE CLOSE 52/53 H-REEF ATTACK", "warp": False,
         "lt": "DICE LT CLOSE 52 H-REEF ATTACK", "rt": "DICE RT CLOSE 53 H-REEF ATTACK"},
        {"label": "CHIEFS MURDER MARLINS", "warp": True, "call": "CHIEFS MURDER MARLINS"},
        {"label": "MARLINS", "warp": True, "call": "MARLINS",
         "note": "Sheet lists 'MARLINS / PHILLY' as a combined reference -- split so real install reps show for each."},
    ]},
    {"group": "SITUATIONAL", "name": "Redzone 3rd & 3-6 (3.4/gm)", "plays": [
        {"label": "BUFF F-BAT SQUARE W-62/63 F-CHUB Y-STATION", "warp": False,
         "lt": "BUFF LT F-BAT SQUARE W-62 F-CHUB Y-STATION", "rt": "BUFF RT F-BAT SQUARE W-63 F-CHUB Y-STATION"},
        {"label": "DOCK W-62/63 LICK/RIB Y-PABLO REEF MURDER RADAR", "warp": False,
         "lt": "DOCK LT W-62 LICK Y-PABLO REEF MURDER RADAR", "rt": "DOCK RT W-63 RIB Y-PABLO REEF MURDER RADAR"},
        {"label": "F-GOT COLUMBUS", "warp": True, "call": "F-GOT COLUMBUS"},
    ]},
    {"group": "SITUATIONAL", "name": "Low Red (12-4)", "plays": [
        {"label": "TRIO P-62/63 Y-CORN NOD X-VERT MURDER CORN", "warp": False,
         "lt": "TRIO LT P-62 Y-CORN NOD X-VERT MURDER CORN", "rt": "TRIO RT P-63 Y-CORN NOD X-VERT MURDER CORN"},
        {"label": "HUG BOX NASTY 52/53 PEPPER H-REEF", "warp": False,
         "lt": "HUG BOX LT NASTY 53 PEPPER H-REEF", "rt": "HUG BOX RT NASTY 52 PEPPER H-REEF"},
        {"label": "Y-GOT LOOSE BOX P-62/63 PEPPER SWITCH X-VERT", "warp": False,
         "lt": "Y-GOT LOOSE BOX LT P-63 PEPPER SWITCH X-VERT", "rt": "Y-GOT LOOSE BOX RT P-62 PEPPER SWITCH X-VERT"},
        {"label": "SLING Z-SLAB NAKED 0/1 Z-SLIPPER Y-FLAG", "warp": False,
         "lt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG", "rt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG"},
        {"label": "STEELERS", "warp": True, "call": "STEELERS"},
    ]},
    {"group": "SITUATIONAL", "name": "Red Runs (Tempo: Bison, Bobcat, Kenya)", "plays": [
        {"label": "FOXTROT TRIPS SAME 10/11 PUSH H-CRAPPY", "warp": False,
         "lt": "FOXTROT TRIPS LT SAME 10 PUSH H-CRAPPY", "rt": "FOXTROT TRIPS RT SAME 11 PUSH H-CRAPPY",
         "note": "[ON QK]"},
        {"label": "PS TROOP NASTY 48/49 FORCE", "warp": False,
         "lt": "PS TROOP LT NASTY 49 FORCE", "rt": "PS TROOP RT NASTY 48 FORCE"},
        {"label": "STRAY F-SLAB 49/48 KNOCK Z-SMOKE", "warp": False,
         "lt": "STRAY LT F-SLAB 49 KNOCK Z-SMOKE", "rt": "STRAY RT F-SLAB 48 KNOCK Z-SMOKE"},
        {"label": "BISON", "warp": True, "call": "BISON"},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "warp": False,
         "lt": "STRAY LT F-SLAB 4 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY"},
    ]},
    {"group": "SITUATIONAL", "name": "GL +3 Run (Tempo: Bobcat)", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "warp": True, "call": "T-EARLS // LOSEY // FERG",
         "note": "Personnel/matchup reminder, not a dressed call to install."},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "Z-SHORT BOBCAT Z-FIND", "warp": True, "call": "Z-SHORT BOBCAT Z-FIND"},
        {"label": "UNDER THING NASTY Z-SHORT 1 CAPTAIN", "warp": True,
         "call": "UNDER THING RT NASTY Z-SHORT 1 CAPTAIN",
         "note": "Highlighted yellow -- sheet shows the RT version (W87) printed in both hash columns here, so kept as a single entry rather than a guessed LT pair."},
    ]},
    {"group": "SITUATIONAL", "name": "GL +3 Pass", "plays": [
        {"label": "UNDER DAWN TRIM Z-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DAWN LT TRIM Z-SLAB 1-69 FEATHER", "rt": "UNDER DAWN RT TRIM Z-SLAB 0-68 FEATHER",
         "note": "Distinct from UNDER DIP TRIM F-SLAB below -- different personnel tag (DAWN vs DIP, Z-SLAB vs F-SLAB), not a duplicate."},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
        {"label": "SLING Z-SLAB PASS 0/1 ENTER F-POP Z-CRAPPY X-FADE", "warp": False,
         "lt": "SLING LT Z-SLAB PASS 0 ENTER F-POP Z-CRAPPY X-FADE", "rt": "SLING RT Z-SLAB PASS 1 ENTER F-POP Z-CRAPPY X-FADE"},
        {"label": "F-GAS STRAY SPRINT RUB PACER", "warp": True, "call": "F-GAS STRAY LT SPRINT RT RUB PACER",
         "note": "Only one version shown (Tiger tag) -- also referenced again under 2PT Plays."},
    ]},
    {"group": "SITUATIONAL", "name": "2PT Plays", "plays": [
        {"label": "TRIPS NASTY Z-SHORT V-63 Z-SLINGSHOT", "warp": True,
         "call": "TRIPS NASTY Z-SHORT V-63 Z-SLINGSHOT", "note": "[RH] on the sheet."},
        {"label": "F-GAS STRAY SPRINT RUB PACER", "warp": True, "call": "F-GAS STRAY LT SPRINT RT RUB PACER",
         "note": "[LH] -- same play as the GL+3 Pass entry above."},
        {"label": "[AMBUSH] SPRINT GOBBLE", "warp": True, "call": "[AMBUSH] SPRINT RT GOBBLE",
         "note": "[LH] / [ON QK] on the sheet."},
    ]},
    {"group": "SITUATIONAL", "name": "Coming Out (1.4/gm)", "plays": [
        {"label": "PS TROOP NASTY 0/1 COWBOY Z-HITCH", "warp": False,
         "lt": "PS TROOP LT NASTY 0 COWBOY Z-HITCH", "rt": "PS TROOP RT NASTY 1 COWBOY Z-HITCH",
         "note": "[ON 2] -- same play (W47/W48) as Tite Zone's PS TROOP NASTY 1/0 COWBOY Z-HITCH."},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "BOX SAME W-52/53 F-ESKIMO X-ISO", "warp": False,
         "lt": "BOX LT SAME W-53 F-ESKIMO X-ISO", "rt": "BOX RT SAME W-52 F-ESKIMO X-ISO",
         "note": "[WHO AT X?] flagged on sheet."},
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "THING ROLL Z-STUTTER COMEBACK", "warp": False,
         "lt": "THING LT ROLL LT Z-STUTTER COMEBACK", "rt": "THING RT ROLL RT Z-STUTTER COMEBACK",
         "note": "[ON 2]"},
        {"label": "TIRE FALCONS", "warp": True, "call": "TIRE FALCONS", "note": "3rd & 7+"},
    ]},
    {"group": "SITUATIONAL", "name": "2nd & Long (7+)", "plays": []},
    {"group": "SITUATIONAL", "name": "3rd & 1 (1.2/gm)", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "warp": True, "call": "T-EARLS // LOSEY // FERG"},
        {"label": "PS NORTH THING F-SHORT F-SNEAK", "warp": False,
         "lt": "PS NORTH THING LT F-SHORT F-SNEAK", "rt": "PS NORTH THING RT F-SHORT F-SNEAK",
         "note": "Highlighted yellow on the sheet."},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "UNDER THING NASTY Z-SHORT 0/1 CAPTAIN", "warp": False,
         "lt": "UNDER THING LT NASTY Z-SHORT 0 CAPTAIN", "rt": "UNDER THING RT NASTY Z-SHORT 1 CAPTAIN"},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "SLING Z-SLAB NAKED 0/1 Z-SLIPPER Y-FLAG", "warp": False,
         "lt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG", "rt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 2 (1.8/gm)", "plays": [
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "UNDER THING NASTY Z-SHORT 0/1 CAPTAIN", "warp": False,
         "lt": "UNDER THING LT NASTY Z-SHORT 0 CAPTAIN", "rt": "UNDER THING RT NASTY Z-SHORT 1 CAPTAIN"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
        {"label": "SLING Z-SLAB NAKED 0/1 Z-SLIPPER Y-FLAG", "warp": False,
         "lt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG", "rt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG"},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 3-5 (3.4/gm)", "plays": [
        {"label": "F-IN SQUARE COLUMBUS", "warp": True, "call": "F-IN SQUARE COLUMBUS"},
        {"label": "CAMBRIDGE MURDER CHICAGO", "warp": True, "call": "CAMBRIDGE MURDER CHICAGO"},
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "warp": False,
         "lt": "Y-GOT TRIPS LT F-STING DASH LT FLOAT", "rt": "Y-GOT TRIPS RT F-STING DASH RT FLOAT"},
        {"label": "CHIEFS", "warp": True, "call": "CHIEFS", "note": "(POSSE THOUGHT)"},
        {"label": "BUFF NASTY F-60 SAME W-62 Y-BAR F-CHUB", "warp": True,
         "call": "BUFF RT NASTY F-60 SAME W-62 Y-BAR F-CHUB", "note": "(POSSE THOUGHT)"},
        {"label": "BUFF NASTY F-GO P-62 CRUSH X-DRIVE", "warp": True,
         "call": "BUFF RT NASTY F-GO P-62 CRUSH X-DRIVE", "note": "(POSSE THOUGHT). Sheet renders this as 'F-G0' -- read as F-GO."},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 6-9 (4.1/gm)", "plays": [
        {"label": "Y-GOT PATRIOTS", "warp": True, "call": "Y-GOT PATRIOTS"},
        {"label": "DOLPHINS", "warp": True, "call": "DOLPHINS"},
        {"label": "BUCANEERS", "warp": True, "call": "BUCANEERS"},
        {"label": "MISSOURI", "warp": True, "call": "MISSOURI"},
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "warp": False,
         "lt": "Y-GOT TRIPS LT F-STING DASH LT FLOAT", "rt": "Y-GOT TRIPS RT F-STING DASH RT FLOAT"},
        {"label": "TRIPS F-STING 50 PUT F-BAR H-COOP", "warp": True, "call": "TRIPS RT F-STING 50 PUT F-BAR H-COOP",
         "note": "(POSSE THOUGHT)"},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 10 Plus (2.1/gm)", "plays": [
        {"label": "Y-GOT PATRIOTS", "warp": True, "call": "Y-GOT PATRIOTS"},
        {"label": "DOLPHINS", "warp": True, "call": "DOLPHINS"},
        {"label": "MISSOURI / BUCANEERS", "warp": True, "call": "MISSOURI / BUCANEERS", "note": "(POSSE THOUGHTS)"},
    ]},
    {"group": "SITUATIONAL", "name": "4th & 1 (Think Players, Not Plays)", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "warp": True, "call": "T-EARLS // LOSEY // FERG"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
    ]},
    {"group": "SITUATIONAL", "name": "4th & 2-3 (Think Players, Not Plays)", "plays": [
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
    ]},
    {"group": "SITUATIONAL", "name": "4th & 4-6 (Think Players, Not Plays)", "plays": [
        {"label": "F-IN SQUARE COLUMBUS", "warp": True, "call": "F-IN SQUARE COLUMBUS"},
        {"label": "Y-IN SQUARE CHICAGO", "warp": True, "call": "Y-IN SQUARE CHICAGO"},
    ]},
]
