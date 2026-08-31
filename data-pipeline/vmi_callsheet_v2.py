#!/usr/bin/env python3
"""
Best-effort transcription of VMI CALLSHEET V2.pdf (uploaded 2026-08-31),
superseding vmi_callsheet_v1.py.

REVISED 2026-08-31 (same day, 2nd pass) per Matt's direct follow-up:
"I NEED THE SITUATIONAL TAB TO LOOK EXACTLY LIKE THE REGULAR CALL SHEET TAB
& ALSO JUST COMBINE THE TWO TOGETHER TO MAKE ONE CALLSHEET TAB ... ALSO
EXCLUDE SEQUENCES CATEGORY." Three changes from the first pass:

  1. SEQUENCES category (BREEZE) removed entirely -- Matt doesn't want it
     on the callsheet at all (BREEZE still appears once, correctly, under
     RUN GAME > Gap Scheme, so it isn't lost, just not double-listed as its
     own category).
  2. The old standalone SITUATIONAL_STRUCTURE (rendered as a separate
     reference-only card grid, no install-tracker join) is GONE. Every
     situational category is now folded directly into CALLSHEET_STRUCTURE
     as its own group ("SITUATIONAL"), in the exact same
     {"group","name","plays":[{"label","warp"/"lt"+"rt","note"?}]} shape as
     RUN GAME/PASS GAME -- so it goes through the same compute_callsheet.py
     join against week.all_install and renders in the one unified
     _rCallsheet() table (Reps / % of Week columns, same as everything
     else). This means situational calls that ARE also gameplan run/pass
     calls now show real install-tracker rep counts; ones that are pure
     game-day-only references (personnel reminders, "(POSSE THOUGHT)"
     notes, etc.) will legitimately show 0 reps -- that's expected, not a
     bug, since practice doesn't chart opponent field position.
  3. Two label/boundary corrections found while re-verifying the
     situational grid image more carefully for this merge (see notes
     inline below): "Plus Territory" and "Fringe" turned out to be ONE
     category (same 8 plays, two stacked header lines on the sheet), and
     the plays originally mis-filed under "Fringe" actually belong to
     "Hi Red (25-13)". The previous "Hi Red" content's exact category
     boundary is still unconfirmed -- kept as its own flagged group below
     rather than guessed into the wrong bucket.

IMPORTANT -- read before trusting this blindly:
Same caveat as before: this is a dense, image-only (no text layer) Google
Sheets export read off a rendered PNG, not extracted as text, with tiny
90-degree-rotated print. Where a situational play is a duplicate of an
already-confirmed RUN GAME/PASS GAME call, this file reuses that call's
exact LT/RT dressed text (higher confidence, and avoids the install-tracker
double-counting risk described in compute_callsheet.py's docstring for
plays whose LT/RT text only differs by a leading number tag). Where a
situational play has no RUN/PASS GAME match and its LT/RT number pairing
wasn't independently re-verified this pass, it's kept as a single "warp"
entry (not a guessed lt/rt pair) specifically to avoid that double-count
risk -- Matt, if you send cleaner section-crop PDFs of the situational
grid (per your own question -- yes, smaller crops would meaningfully
improve read accuracy on this dense a page), the flagged ones below are
the ones worth re-checking first.
"""

CALLSHEET_STRUCTURE = [
    # ── RUN GAME / PASS GAME (unchanged from first V2 pass, one fix) ───────
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
         "lt": "STRAY LT F-SLAB 4 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY",
         "note": "Corrected 2026-08-31 -- confirmed LT=4/RT=5 via a duplicate of this same play "
                 "found in the situational grid's Red Runs/Tempo category (previously both hash "
                 "versions had been misread as '5')."},
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
    # NOTE: SEQUENCES category (BREEZE) intentionally removed 2026-08-31 per
    # Matt's direct request. BREEZE itself is not lost -- it's still listed
    # once, correctly, under RUN GAME > Gap Scheme above.

    # ── SITUATIONAL (folded in from the old standalone tab, 2026-08-31) ────
    # Same shape as RUN GAME/PASS GAME now -- joins against week.all_install
    # like everything else. Plays that duplicate a RUN/PASS GAME call reuse
    # that call's exact lt/rt text. Plays unique to the situational grid
    # whose LT/RT number pairing wasn't independently re-verified this pass
    # are kept as a single "warp" entry (not a guessed pair) to avoid
    # double-counting reps -- see file docstring.
    {"group": "SITUATIONAL", "name": "Plus Territory / Fringe (40-26)", "plays": [
        {"label": "MICHIGAN", "warp": True, "call": "MICHIGAN"},
        {"label": "PATRIOTS", "warp": True, "call": "PATRIOTS"},
        {"label": "MARLINS", "warp": True, "call": "MARLINS"},
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "TRIPS NASTY S2/S3 ATTACK H-REEF", "warp": False,
         "lt": "TRIPS RT NASTY S2 ATTACK H-REEF", "rt": "TRIPS RT NASTY S3 ATTACK H-REEF"},
        {"label": "SEAHAWKS [CLAMP] MURDER PATRIOTS", "warp": True, "call": "SEAHAWKS [CLAMP] MURDER PATRIOTS"},
        {"label": "DICE FAKE 6/7 Y-WIN VETO", "warp": False,
         "lt": "DICE LT FAKE 7 Y-WIN VETO", "rt": "DICE RT FAKE 6 Y-WIN VETO"},
        {"label": "SLING Z-SWIM 36/37 OPTION F-LEVER H-SAFETY", "warp": False,
         "lt": "SLING LT Z-SWIM 37 OPTION F-LEVER H-SAFETY", "rt": "SLING RT Z-SWIM 36 OPTION F-LEVER H-SAFETY"},
        {"label": "TRIPS FAKE 6/7 TOP CHIP TOPPER X-SLANT KILL FLASH", "warp": True,
         "call": "TRIPS FAKE TOP CHIP TOPPER X-SLANT KILL FLASH",
         "note": "Number/hash pairing not independently verified -- treated as single entry."},
    ]},
    {"group": "SITUATIONAL", "name": "Hi Red (25-13)", "plays": [
        {"label": "TRIO FAKE 6/7 F-JAIL/F-PRISON X-SMOKE", "warp": False,
         "lt": "TRIO LT FAKE 6 F-JAIL X-SMOKE", "rt": "TRIO RT FAKE 7 F-PRISON X-SMOKE"},
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY",
         "note": "Also listed under Plus Territory/Fringe and Coming Out -- same call, shown once per category on the printed sheet."},
        {"label": "DICE CLOSE S2/S3 H-REEF ATTACK", "warp": False,
         "lt": "DICE LT CLOSE S2 H-REEF ATTACK", "rt": "DICE RT CLOSE S3 H-REEF ATTACK"},
        {"label": "CHIEFS MURDER MARLINS", "warp": True, "call": "CHIEFS MURDER MARLINS"},
    ]},
    {"group": "SITUATIONAL", "name": "Redzone (Other)", "plays": [
        {"label": "BUFF F-BAT SQUARE W-62/63 F-CHUB Y-STATION", "warp": True,
         "call": "BUFF F-BAT SQUARE F-CHUB Y-STATION",
         "note": "Category boundary for this row unconfirmed as of the 2026-08-31 merge (was mislabeled "
                 "'Hi Red' in the first pass, which turned out to be wrong once Plus Territory/Fringe/Hi "
                 "Red got re-verified) -- kept under its own group pending a cleaner section crop."},
        {"label": "DOCK W-62/63 LICK/RIB Y-PABLO REEF MURDER RADAR", "warp": True,
         "call": "DOCK LICK RIB Y-PABLO REEF MURDER RADAR"},
        {"label": "F-GOT COLUMBUS", "warp": True, "call": "F-GOT COLUMBUS"},
    ]},
    {"group": "SITUATIONAL", "name": "Redzone 3rd & 3-6 (3.4/gm)", "plays": [
        {"label": "TRIO P-62/63 Y-CORN NOD X-VERT MURDER CORN", "warp": True, "call": "TRIO Y-CORN NOD X-VERT MURDER CORN"},
        {"label": "HUG BOX NASTY S2/S3 PEPPER H-REEF", "warp": True, "call": "HUG BOX NASTY PEPPER H-REEF"},
        {"label": "Y-GOT LOOSE BOX P-62/63 PEPPER SWITCH X-VERT", "warp": True, "call": "Y-GOT LOOSE BOX PEPPER SWITCH X-VERT"},
        {"label": "SLING Z-SLAB NAKED 0/1 Z-SLIPPER Y-FLAG", "warp": False,
         "lt": "SLING LT Z-SLAB NAKED 0 Z-SLIPPER Y-FLAG", "rt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG",
         "note": "Number pairing follows the confirmed SLING Z-SLAB 0(LT)/1(RT) convention seen elsewhere on this sheet -- not independently re-checked for this specific play."},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
    ]},
    {"group": "SITUATIONAL", "name": "Low Red (12-4)", "plays": [
        {"label": "FOXTROT TRIPS SAME 10/11 PUSH H-CRAPPY", "warp": True, "call": "FOXTROT TRIPS SAME PUSH H-CRAPPY",
         "note": "[ON QK]"},
        {"label": "PS TROOP NASTY 48/49 FORCE", "warp": True, "call": "PS TROOP NASTY FORCE",
         "note": "Distinct from the confirmed PS TROOP NASTY 49/48 FORCE (Wide Zone) -- different number tag on the sheet."},
        {"label": "STRAY F-SLAB 48/49 KNOCK Z-SMOKE", "warp": True, "call": "STRAY F-SLAB KNOCK Z-SMOKE (48/49)",
         "note": "Distinct from the confirmed STRAY F-SLAB 49/48 KNOCK Z-SMOKE (Wide Zone) -- different number tag on the sheet."},
        {"label": "BISON", "warp": True, "call": "BISON"},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "warp": False,
         "lt": "STRAY LT F-SLAB 4 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY"},
    ]},
    {"group": "SITUATIONAL", "name": "Red Runs / Tempo", "plays": [
        {"label": "STRAY F-SLAB 4/5 ENTER CRAPPY", "warp": False,
         "lt": "STRAY LT F-SLAB 4 ENTER CRAPPY", "rt": "STRAY RT F-SLAB 5 ENTER CRAPPY",
         "note": "The duplicate of this play in this category is what confirmed the LT=4/RT=5 Midzone fix."},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
    ]},
    {"group": "SITUATIONAL", "name": "GL +3 Run", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "warp": True, "call": "T-EARLS // LOSEY // FERG",
         "note": "Personnel/matchup reminder, not a dressed call to install."},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "Z-SHORT BOBCAT Z-FIND", "warp": True, "call": "Z-SHORT BOBCAT Z-FIND"},
        {"label": "UNDER THING NASTY Z-SHORT 0/1 CAPTAIN", "warp": False,
         "lt": "UNDER THING LT NASTY Z-SHORT 0 CAPTAIN", "rt": "UNDER THING RT NASTY Z-SHORT 1 CAPTAIN",
         "note": "Highlighted yellow on the sheet."},
    ]},
    {"group": "SITUATIONAL", "name": "GL +3 Pass", "plays": [
        {"label": "UNDER DAWN TRIM Z-SLAB 0-68 FEATHER", "warp": True, "call": "UNDER DAWN TRIM Z-SLAB 0-68 FEATHER"},
        {"label": "SLING Z-SLAB PASS 0 ENTER F-POP Z-CRAPPY X-FADE", "warp": True,
         "call": "SLING Z-SLAB PASS ENTER F-POP Z-CRAPPY X-FADE", "note": "[ON 2] -- both RH and LH versions appear on the sheet."},
        {"label": "TRIPS NASTY Z-SHORT V-63 Z-SLINGSHOT", "warp": True, "call": "TRIPS NASTY Z-SHORT V-63 Z-SLINGSHOT",
         "note": "[ON QK]"},
    ]},
    {"group": "SITUATIONAL", "name": "2PT Plays", "plays": [
        {"label": "F-GAS STRAY SPRINT RUB PACER", "warp": True, "call": "F-GAS STRAY SPRINT RUB PACER"},
        {"label": "[AMBUSH] SPRINT GOBBLE", "warp": True, "call": "[AMBUSH] SPRINT GOBBLE", "note": "[ON QK]"},
    ]},
    {"group": "SITUATIONAL", "name": "Coming Out (1.4/gm)", "plays": [
        {"label": "PS TROOP NASTY 0/1 COWBOY Z-HITCH", "warp": False,
         "lt": "PS TROOP LT NASTY 0 COWBOY Z-HITCH", "rt": "PS TROOP RT NASTY 1 COWBOY Z-HITCH",
         "note": "Distinct number tag (0/1) from the confirmed PS TROOP NASTY 1/0 COWBOY Z-HITCH (Tite Zone). [ON 2]"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "BOX SAME W-52/53 F-ESKIMO X-ISO", "warp": True, "call": "BOX SAME F-ESKIMO X-ISO",
         "note": "[WHO AT X] flagged on sheet."},
        {"label": "(TIRE) PHILLY", "warp": True, "call": "(TIRE) PHILLY"},
        {"label": "THING ROLL Z-STUTTER COMEBACK", "warp": True, "call": "THING ROLL Z-STUTTER COMEBACK", "note": "[ON 2]"},
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
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 2 (1.8/gm)", "plays": [
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "BOBCAT", "warp": True, "call": "BOBCAT"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
        {"label": "SLING Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "warp": False,
         "lt": "SLING LT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG", "rt": "SLING RT Z-SLAB NAKED 1 Z-SLIPPER Y-FLAG",
         "note": "Both hash versions read as number 1 in this crop -- flagged, may need re-verification."},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 3-5 (3.4/gm)", "plays": [
        {"label": "F-IN SQUARE COLUMBUS", "warp": False,
         "lt": "F-IN SQUARE COLUMBUS (LH)", "rt": "F-IN SQUARE COLUMBUS (RH)",
         "note": "Both hash versions confirmed present (W89 LH / W90 RH) -- exact jersey/hole tag not carried into the dressed text since RUN/PASS GAME matching strips leading number tags anyway."},
        {"label": "CAMBRIDGE MURDER CHICAGO", "warp": True, "call": "CAMBRIDGE MURDER CHICAGO"},
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "warp": False,
         "lt": "Y-GOT TRIPS RT F-STING DASH RT FLOAT", "rt": "Y-GOT TRIPS LT F-STING DASH LT FLOAT"},
        {"label": "CHIEFS", "warp": True, "call": "CHIEFS", "note": "(POSSE THOUGHT)"},
        {"label": "BUFF RT NASTY F-60 SAME W-62 Y-BAR F-CHUB", "warp": True,
         "call": "BUFF RT NASTY F-60 SAME W-62 Y-BAR F-CHUB", "note": "(POSSE THOUGHT)"},
        {"label": "BUFF RT NASTY F-GO P-62 CRUSH X-DRIVE", "warp": True,
         "call": "BUFF RT NASTY F-GO P-62 CRUSH X-DRIVE", "note": "(POSSE THOUGHT)"},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 6-9 (4.1/gm)", "plays": [
        {"label": "Y-GOT PATRIOTS", "warp": True, "call": "Y-GOT PATRIOTS"},
        {"label": "DOLPHINS", "warp": True, "call": "DOLPHINS"},
        {"label": "BUCANEERS", "warp": True, "call": "BUCANEERS"},
        {"label": "MISSOURI", "warp": True, "call": "MISSOURI"},
        {"label": "Y-GOT TRIPS F-STING DASH FLOAT", "warp": False,
         "lt": "Y-GOT TRIPS RT F-STING DASH RT FLOAT", "rt": "Y-GOT TRIPS LT F-STING DASH LT FLOAT"},
        {"label": "TRIPS F-STING S0 PUT F-BAR H-COOP", "warp": True, "call": "TRIPS F-STING S0 PUT F-BAR H-COOP",
         "note": "(POSSE THOUGHT)"},
    ]},
    {"group": "SITUATIONAL", "name": "3rd & 10 Plus (2.1/gm)", "plays": [
        {"label": "MISSOURI", "warp": True, "call": "MISSOURI"},
        {"label": "Y-GOT TRIPS RT F-STING DASH RT FLOAT", "warp": True, "call": "Y-GOT TRIPS RT F-STING DASH RT FLOAT"},
        {"label": "Y-GOT PATRIOTS", "warp": True, "call": "Y-GOT PATRIOTS"},
        {"label": "DOLPHINS", "warp": True, "call": "DOLPHINS"},
        {"label": "MISSOURI / BUCANEERS", "warp": True, "call": "MISSOURI / BUCANEERS", "note": "(POSSE THOUGHTS)"},
    ]},
    {"group": "SITUATIONAL", "name": "4th & 1", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "warp": True, "call": "T-EARLS // LOSEY // FERG"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
    ]},
    {"group": "SITUATIONAL", "name": "4th & 2-3", "plays": [
        {"label": "T-EARLS // LOSEY // FERG", "warp": True, "call": "T-EARLS // LOSEY // FERG"},
        {"label": "SLING Z-SLAB 0/1 ENTER Z-CRAPPY", "warp": False,
         "lt": "SLING LT Z-SLAB 0 ENTER Z-CRAPPY", "rt": "SLING RT Z-SLAB 1 ENTER Z-CRAPPY"},
        {"label": "UNDER DIP TRIM F-SLAB 0-68/1-69 FEATHER", "warp": False,
         "lt": "UNDER DIP LT TRIM F-SLAB 0-68 FEATHER", "rt": "UNDER DIP RT TRIM F-SLAB 1-69 FEATHER"},
    ]},
    {"group": "SITUATIONAL", "name": "4th & 4-6", "plays": [
        {"label": "F-IN SQUARE COLUMBUS", "warp": False,
         "lt": "F-IN SQUARE COLUMBUS (LH)", "rt": "F-IN SQUARE COLUMBUS (RH)",
         "note": "Not independently re-verified for this specific category this pass -- carried over from the first-pass read."},
        {"label": "Y-IN SQUARE CHICAGO", "warp": True, "call": "Y-IN SQUARE CHICAGO",
         "note": "Not independently re-verified for this specific category this pass -- carried over from the first-pass read."},
    ]},
]
