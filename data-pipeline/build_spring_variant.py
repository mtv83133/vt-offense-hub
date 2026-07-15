import csv, json, sys, os

if len(sys.argv) < 3:
    print("Usage: python3 build_variant.py <team|skelly|combined> <path_to_csv> [output_dir]")
    print("  output_dir defaults to './output' (created if missing)")
    sys.exit(1)

variant = sys.argv[1]  # 'team', 'skelly', 'combined'
csv_path = sys.argv[2]
out_dir = sys.argv[3] if len(sys.argv) > 3 else './output'
os.makedirs(out_dir, exist_ok=True)

with open(csv_path, encoding='utf-8-sig') as f:
    rd = csv.DictReader(f)
    rows = list(rd)
rows = [r for r in rows if r['pff_RUNPASS'].strip() not in ('PEN','NP','')]

if variant == 'team':
    rows = [r for r in rows if r['COMPETITIVE'].strip() != 'SKELLY']
elif variant == 'skelly':
    rows = [r for r in rows if r['COMPETITIVE'].strip() == 'SKELLY']
elif variant == 'combined':
    pass  # all rows
print(f"[{variant}] usable rows:", len(rows))

def gain(r):
    s = r['pff_GAINLOSS'].strip()
    if s in ('', 'NP'): return 0.0
    try: return float(s)
    except: return 0.0
def is_sack(r): return r['pff_PASSRESULT'].strip()=='S'
def is_comp(r): return r['pff_PASSRESULT'].strip()=='C'
def is_eff(r): return r['Efficient'].strip()=='Y'
def is_expl(r): return r['EXPLOSIVE'].strip()=='Y'
# Overall "called run-scheme vs called pass-play" split
def is_run(r): return r['Run Family'].strip()!=''
def is_pass(r): return r['Run Family'].strip()==''
# Within a run-scheme: did it actually end in a run (handoff) or get thrown (RPO/broken play)?
def is_run_sub(r):
    pr = r['pff_PASSRESULT'].strip()
    if pr == 'R': return True
    if pr == '': return r['pff_RUNPASS'].strip() == 'R'  # blank result: fall back to the called tag, don't assume
    return False
def is_pass_sub(r):
    pr = r['pff_PASSRESULT'].strip()
    return pr in ('C','I','S','D','X','Q')
def is_neg(r): return gain(r) < 0 or is_sack(r)
def is_rz(r):
    fp = r['pff_FIELDPOSITION'].strip()
    if fp.startswith('+'):
        try: return int(fp[1:]) <= 12
        except: return False
    return False

def pct(cnt,total): return round(cnt/total*1000)/10 if total else 0.0
def avgy(items): return round(sum(gain(r) for r in items)/len(items)*10)/10 if items else 0.0

def targeted(items): return [r for r in items if r['pff_PASSRESULT'].strip() in ('C','I','D')]
def comp_pct(items):
    ta = targeted(items)
    return pct(sum(1 for r in ta if is_comp(r)), len(ta))

def stat_block(items):
    n=len(items)
    return {'n':n,'avg':avgy(items),'eff':pct(sum(1 for r in items if is_eff(r)),n),
            'expl':pct(sum(1 for r in items if is_expl(r)),n),'neg':pct(sum(1 for r in items if is_neg(r)),n)}
def stat_block_full(items):
    b = stat_block(items); b['comp']=comp_pct(items)
    b['sacks']=sum(1 for r in items if is_sack(r)); b['ints']=0
    return b
def pass_block(items):
    b = stat_block(items); b['comp']=comp_pct(items); return b
def route_block(items):
    b = pass_block(items); n=len(items)
    b['rt1']=pct(sum(1 for r in items if r['Route Thrown'].strip()=='1'),n)
    b['rt2']=pct(sum(1 for r in items if r['Route Thrown'].strip()=='2'),n)
    b['rt3']=pct(sum(1 for r in items if r['Route Thrown'].strip()=='3'),n)
    b['rto']=pct(sum(1 for r in items if r['Route Thrown'].strip()=='O'),n)
    b['rta']=pct(sum(1 for r in items if r['Route Thrown'].strip()=='A'),n)
    b['rts']=pct(sum(1 for r in items if r['Route Thrown'].strip()=='S'),n)
    return b
def concept_name(r):
    primary=r['Primary'].strip(); reset=r['Reset'].strip()
    if primary: return primary + (' / '+reset if reset else '')
    full=r['Full Concept'].strip()
    if full: return full
    return r['Play'].strip() or '(unknown)'

run_rows=[r for r in rows if is_run(r)]
pass_rows=[r for r in rows if is_pass(r)]
fam_rows=[r for r in rows if r['Run Family'].strip()!='']
n=len(rows); n_run=len(run_rows); n_pass=len(pass_rows)

ROSTER = {
 12:('K. Ryan','QB'),17:('Grunkemeyer','QB'),14:('T. Huhn','QB'),22:('B. Baker','QB'),
 16:('J. Overton Jr.','RB'),23:('T. Mason','RB'),35:('J. Buetow','RB'),
 46:('D. Taylor','RB'),27:('M. Hawkins','RB'),32:('B. Davis','RB'),
 26:('M. Mickens','RB'),49:('G. Peterson','RB'),50:('D. Taylor','RB'),
 36:('B. Jones','TE'),82:('B. Gosnell','TE'),13:('Ja. Hairston','TE'),
 87:('H. St. Germain','TE'),99:('C. Reemsnyder','TE'),
 44:('M. Henderson','TE'),85:('L. Reynolds','TE'),
 2:('T. Heath','WR'),6:('B. Adams','WR'),7:('C. Wiggins','WR'),
 0:('A. Greene','WR'),81:('I. Hairston','WR'),80:('L.J. Booker','WR'),
 18:('A.J. Brand','WR'),86:('J. Hobbs','WR'),15:('S. Peterkin','WR'),
 83:('L. Stuewe','WR'),28:('D. Hube','WR'),3:('Q. Brown','WR'),
 19:('T. Denmark','WR'),20:('J. Exinor Jr.','WR'),5:('M. Jackson','WR'),
 51:('Haughawout','OL'),56:('Ghannam','OL'),66:('Cunningham','OL'),
 77:('B. Meadows','OL'),79:('J. Garrett','OL'),76:('A. Lynch','OL'),
 53:('T. Ricard','OL'),57:('L. Austin','OL'),62:('K. Altuner','OL'),
 71:('G. Crawford','OL'),61:('J. Bell','OL'),74:('M. Bright','OL'),
 75:('B. Eziuka','OL'),70:('L. Howland','OL'),65:('T. Simpson','OL'),
 72:('J. Terry','OL'),54:('M. Troutman III','OL')
}
def jint(val):
    if val is None: return None
    s=str(val).strip()
    if s in ('','-','N/A','n/a'): return None
    if s[:1] in ('O','o'): s=s[1:]
    try: return int(s)
    except: return None

FAM_ORDER=['WIDE ZONE','TITE ZONE','MID ZONE','GAP','DRAW']
fam_map={}
for r in fam_rows:
    fam=r['Run Family'].strip(); sch=r['RunScheme'].strip() or '(unnamed)'
    fam_map.setdefault(fam, {}).setdefault(sch, []).append(r)

RUN_families=[]
for fam in FAM_ORDER:
    if fam not in fam_map: continue
    schemes=fam_map[fam]
    all_fam_rows=[r for sr in schemes.values() for r in sr]
    fobj={'name':fam,'total':stat_block(all_fam_rows)}
    fr=[r for r in all_fam_rows if is_run_sub(r)]; fp=[r for r in all_fam_rows if is_pass_sub(r)]
    if fr and fp:
        fobj['run_sub']=stat_block(fr)
        fobj['pass_sub']=stat_block(fp)
    scheme_list=[]
    for sch, sr in sorted(schemes.items(), key=lambda kv:-len(kv[1])):
        sobj={'name':sch,'total':stat_block(sr)}
        sr_run=[r for r in sr if is_run_sub(r)]; sr_pass=[r for r in sr if is_pass_sub(r)]
        if sr_run and sr_pass:
            sobj['run_sub']=stat_block(sr_run)
            sobj['pass_sub']=stat_block(sr_pass)
        scheme_list.append(sobj)
    fobj['schemes']=scheme_list
    RUN_families.append(fobj)
RUN_DATA={'families':RUN_families,'overall':stat_block(run_rows)}

D={}
D['overall']=stat_block_full(rows)
D['pass_ov']=stat_block_full(pass_rows)
D['run_ov']=stat_block_full(run_rows)
D['sacks']=sum(1 for r in pass_rows if is_sack(r)); D['ints']=0
D['sack_pct']=pct(D['sacks'], n_pass); D['int_pct']=0.0

D_run_families={}
for fam in FAM_ORDER:
    if fam not in fam_map: continue
    all_fam_rows=[r for sr in fam_map[fam].values() for r in sr]
    fobj=stat_block_full(all_fam_rows); fobj['name']=fam
    play_map={}
    for r in all_fam_rows: play_map.setdefault(r['Play'].strip() or '(unknown)', []).append(r)
    concepts=[]
    for pname, pitems in sorted(play_map.items(), key=lambda kv:-len(kv[1])):
        c=stat_block_full(pitems); c['name']=pname; concepts.append(c)
    fobj['concepts']=concepts
    D_run_families[fam]=fobj
D['run_families']=D_run_families

gm_all={}
for r in pass_rows: gm_all.setdefault(concept_name(r), []).append(r)
pass_concepts=[]
for nm, items in sorted(gm_all.items(), key=lambda kv:-len(kv[1])):
    c=stat_block_full(items); c['name']=nm; pass_concepts.append(c)
D['pass_concepts']=pass_concepts

rz_rows_all=[r for r in pass_rows if is_rz(r)]
gm_rz={}
for r in rz_rows_all: gm_rz.setdefault(concept_name(r), []).append(r)
rz_concepts=[]
for nm, items in sorted(gm_rz.items(), key=lambda kv:-len(kv[1])):
    c=stat_block_full(items); c['name']=nm; rz_concepts.append(c)
D['rz_concepts']=rz_concepts

WARP_EXCLUDE={'RAP','MVMT','SCREEN','6MAN','5MAN','QG'}
warp_map={}
for r in rows:
    if r['Run Family'].strip()!='': continue
    nm=r['Play'].strip() or '(unknown)'
    if nm in WARP_EXCLUDE: continue
    warp_map.setdefault(nm, []).append(r)
D_warp=[]
for nm, items in sorted(warp_map.items(), key=lambda kv:-len(kv[1])):
    w=stat_block_full(items); w['name']=nm
    wr=[r for r in items if is_run_sub(r)]; wp=[r for r in items if is_pass_sub(r)]
    if wr and wp:
        w['run_sub']=stat_block(wr)
        w['pass_sub']=stat_block(wp)
    D_warp.append(w)
D['warp']=D_warp

POS_KEYS=['H','F','Q','Y','Z','X']
D_positions=[]
for pos in POS_KEYS:
    p_rows=[r for r in rows if r['TRACKING'].strip()==pos]
    if not p_rows: continue
    b=stat_block_full(p_rows); b['pos']=pos; b['pct']=pct(len(p_rows), n)
    D_positions.append(b)
D['positions']=D_positions
D['family_order']=FAM_ORDER

# PW_DATA
concepts_rows=[r for r in pass_rows if r['Play'].strip() not in ('MVMT','RAP','SCREEN')]
mvmt_rap_rows=[r for r in pass_rows if r['Play'].strip() in ('MVMT','RAP')]
screen_rows=[r for r in pass_rows if r['Play'].strip()=='SCREEN']
rz_rows=[r for r in pass_rows if is_rz(r)]

def build_concept_list(items_all):
    gm={}
    for r in items_all: gm.setdefault(concept_name(r), []).append(r)
    out=[]
    for nm, items in sorted(gm.items(), key=lambda kv:-len(kv[1])):
        c=route_block(items); c['name']=nm; out.append(c)
    return out

PW_pass={}
PW_pass['concepts']=build_concept_list(concepts_rows); PW_pass['concepts_total']=route_block(concepts_rows)
PW_pass['mvmt_rap']=build_concept_list(mvmt_rap_rows); PW_pass['mvmt_rap_total']=route_block(mvmt_rap_rows)
PW_pass['screen']=build_concept_list(screen_rows); PW_pass['screen_total']=route_block(screen_rows)
PW_pass['rz']=build_concept_list(rz_rows); PW_pass['rz_total']=route_block(rz_rows)
PW_pass['overall_total']=route_block(pass_rows)

def warp_play_row(items):
    b=stat_block(items); b['comp']=comp_pct(items); return b

warp_map2={}
for r in rows:
    if r['Run Family'].strip()!='': continue
    nm=r['Play'].strip() or '(unknown)'
    if nm in WARP_EXCLUDE: continue
    warp_map2.setdefault(nm, []).append(r)
PW_total_section=[]
for nm, items in sorted(warp_map2.items(), key=lambda kv:-len(kv[1])):
    p=warp_play_row(items); p['name']=nm
    wr=[r for r in items if is_run_sub(r)]; wp=[r for r in items if is_pass_sub(r)]
    if wr and wp:
        p['run_sub']=warp_play_row(wr); p['run_sub']['name']='RUN'
        p['pass_sub']=warp_play_row(wp); p['pass_sub']['name']='PASS'
    PW_total_section.append(p)
warp_all_items=[r for items in warp_map2.values() for r in items]
PW_warp={'total_section':PW_total_section,'total':warp_play_row(warp_all_items),'procedures':{}}
for proc in ['HUDDLE','WARP','ALASKA']:
    proc_rows=[r for r in rows if r['Procedure'].strip()==proc]
    pm={}
    for r in proc_rows:
        if r['Run Family'].strip()!='': continue
        nm=r['Play'].strip() or '(unknown)'
        if nm in WARP_EXCLUDE: continue
        pm.setdefault(nm, []).append(r)
    plays=[]
    for nm, items in sorted(pm.items(), key=lambda kv:-len(kv[1])):
        p=warp_play_row(items); p['name']=nm
        pr=[r for r in items if is_run_sub(r)]; pp=[r for r in items if is_pass_sub(r)]
        if pr and pp:
            p['run_sub']=warp_play_row(pr); p['run_sub']['name']='RUN'
            p['pass_sub']=warp_play_row(pp); p['pass_sub']['name']='PASS'
        plays.append(p)
    proc_warp_items=[r for items in pm.values() for r in items]
    PW_warp['procedures'][proc]={'plays':plays,'total':warp_play_row(proc_warp_items)}
PW_DATA={'pass':PW_pass,'warp':PW_warp}

# PLAYER_DATA
qb_map={}
for r in pass_rows:
    j=jint(r['pff_QB'])
    if j is None: continue
    qb_map.setdefault(j, []).append(r)
qbs=[]
for j, items in sorted(qb_map.items(), key=lambda kv:-len(kv[1])):
    name=ROSTER.get(j, ('#'+str(j),'QB'))[0]
    b=pass_block(items); b['name']=name; b['jersey']=j
    b['sacks']=sum(1 for r in items if is_sack(r)); b['sack_pct']=pct(b['sacks'], len(items))
    cm={}
    for r in items: cm.setdefault(concept_name(r), []).append(r)
    concepts=[]
    for nm, citems in sorted(cm.items(), key=lambda kv:-len(kv[1])):
        if len(citems) < 3: continue
        c=stat_block(citems); c['name']=nm; concepts.append(c)
    b['concepts']=concepts
    qbs.append(b)

rb_rush_map={}
for r in run_rows:
    j=jint(r['pff_RBS'])
    if j is None: continue
    rb_rush_map.setdefault(j, []).append(r)
rb_recv_map={}
for r in pass_rows:
    if r['TRACKING'].strip() != 'H': continue
    j=jint(r['Target'])
    if j is None: continue
    rb_recv_map.setdefault(j, []).append(r)
all_rb_j=sorted(set(list(rb_rush_map.keys())+list(rb_recv_map.keys())), key=lambda j:-len(rb_rush_map.get(j,[])))
rbs=[]
for j in all_rb_j:
    name=ROSTER.get(j, ('#'+str(j),'RB'))[0]
    rush_items=rb_rush_map.get(j, []); recv_items=rb_recv_map.get(j, [])
    if not rush_items and not recv_items: continue
    rush_b=stat_block(rush_items) if rush_items else {'n':0,'avg':0,'eff':0,'expl':0,'neg':0}
    recv_b=pass_block(recv_items) if recv_items else {'n':0,'avg':0,'eff':0,'comp':0}
    recv_b={'n':recv_b['n'],'avg':recv_b['avg'],'eff':recv_b['eff'],'expl':recv_b.get('expl',0),'neg':recv_b.get('neg',0),'comp':recv_b['comp']}
    rbs.append({'name':name,'jersey':j,'rush':rush_b,'recv':recv_b})
rbs.sort(key=lambda r:-r['rush']['n'])

recv_map={}
for r in pass_rows:
    if r['TRACKING'].strip()=='H': continue
    j=jint(r['Target'])
    if j is None: continue
    recv_map.setdefault(j, []).append(r)
receivers=[]
for j, items in sorted(recv_map.items(), key=lambda kv:-len(kv[1])):
    ros=ROSTER.get(j); name=ros[0] if ros else ('#'+str(j)); pos=ros[1] if ros else 'WR'
    if pos not in ('TE','WR'): continue
    b=pass_block(items); b['name']=name; b['jersey']=j; b['pos']=pos
    receivers.append(b)

down_data=[]
for d in ['1','2','3','4']:
    dr=[r for r in rows if r['pff_DOWN'].strip()==d]
    if not dr: continue
    b=stat_block(dr); b['down']=int(d)
    b['run_n']=sum(1 for r in dr if is_run(r)); b['pass_n']=sum(1 for r in dr if is_pass(r))
    down_data.append(b)

third_rows_all=[r for r in rows if r['pff_DOWN'].strip()=='3']
buckets3=[('Short (1-3)', lambda x:1<=x<=3), ('Medium (4-6)', lambda x:4<=x<=6), ('Long (7+)', lambda x:x>=7)]
third_data=[]
for label, cond in buckets3:
    br=[r for r in third_rows_all if r['pff_DISTANCE'].strip() and cond(float(r['pff_DISTANCE']))]
    if not br: continue
    b=stat_block(br); b['label']=label
    b['run_n']=sum(1 for r in br if is_run(r)); b['pass_n']=sum(1 for r in br if is_pass(r))
    third_data.append(b)

pers_vals={}
for r in rows:
    pv=r['pff_OFFPERSONNELBASIC'].strip()
    if pv: pers_vals.setdefault(pv, []).append(r)
pers_data=[]
for pv, pr in sorted(pers_vals.items(), key=lambda kv:-len(kv[1])):
    b=stat_block(pr); b['pers']=pv
    b['run_n']=sum(1 for r in pr if is_run(r)); b['pass_n']=sum(1 for r in pr if is_pass(r))
    pers_data.append(b)

group_data=[]
for g in ['1','2','3']:
    gr=[r for r in rows if r['Group'].strip()==g]
    if not gr: continue
    b=stat_block(gr); b['group']='Group '+g
    group_data.append(b)

skill_map={}
for r in rows:
    qb=jint(r['pff_QB']); rb=jint(r['pff_RBS'])
    pers=r['pff_OFFPERSONNELBASIC'].strip()
    slots=[jint(r['POSITION_Y']),jint(r['POSITION_F']),jint(r['POSITION_Z']),jint(r['POSITION_X'])]
    tes=sorted(set(j for j in slots if j is not None and ROSTER.get(j,(None,None))[1]=='TE'))
    wrs=sorted(set(j for j in slots if j is not None and ROSTER.get(j,(None,'WR'))[1]!='TE'))
    key='|'.join(str(x) for x in ([qb,rb]+tes+wrs+[pers]))
    skill_map.setdefault(key, {'qb':qb,'rb':rb,'tes':tes,'wrs':wrs,'pers':pers,'rows':[]})
    skill_map[key]['rows'].append(r)
skill_lineups=[]
for key, info in sorted(skill_map.items(), key=lambda kv:-len(kv[1]['rows'])):
    items=info['rows']
    if len(items) < 2: continue
    b=stat_block(items)
    b['key']=key; b['pers']=info['pers']; b['qb']=info['qb']; b['rb']=info['rb']
    b['tes']=info['tes']; b['wrs']=info['wrs']
    b['run_n']=sum(1 for r in items if is_run(r)); b['pass_n']=sum(1 for r in items if is_pass(r))
    play_map={}
    for r in items:
        call=(r['Play Call'].strip() or r['Play'].strip() or '(unknown)')
        play_map.setdefault(call, []).append(r)
    plays=[]
    for call, pitems in sorted(play_map.items(), key=lambda kv:-len(kv[1])):
        typ='RUN' if is_run(pitems[0]) else 'PASS'
        plays.append({'call':call,'n':len(pitems),'avg':avgy(pitems),'eff':round(pct(sum(1 for r in pitems if is_eff(r)),len(pitems))),'type':typ})
    b['plays']=plays
    skill_lineups.append(b)
skill_lineups=skill_lineups[:40]

ol_map={}
for r in rows:
    lt=jint(r['Jersey #2']); lg=jint(r['Jersey #3']); c=jint(r['Jersey #4']); rg=jint(r['Jersey #5']); rt=jint(r['Jersey #6'])
    if None in (lt,lg,c,rg,rt): continue
    key=(lt,lg,c,rg,rt)
    ol_map.setdefault(key, []).append(r)
ol_lineups=[]
for key, items in sorted(ol_map.items(), key=lambda kv:-len(kv[1])):
    run_items=[r for r in items if is_run(r)]
    if len(run_items) < 2: continue
    b=stat_block(run_items)
    b['lt'],b['lg'],b['c'],b['rg'],b['rt']=key
    b['eff']=round(b['eff']); b['expl']=round(b['expl']); b['neg']=round(b['neg'])
    ol_lineups.append(b)
ol_lineups=ol_lineups[:20]

procedure_data=[]
for proc in ['HUDDLE','WARP','ALASKA']:
    pr=[r for r in rows if r['Procedure'].strip()==proc]
    if not pr: continue
    b=stat_block(pr); b['procedure']=proc
    b['run_n']=sum(1 for r in pr if is_run(r)); b['pass_n']=sum(1 for r in pr if is_pass(r))
    procedure_data.append(b)

PLAYER_DATA={'qbs':qbs,'rbs':rbs,'receivers':receivers,'down_data':down_data,'third_data':third_data,
             'pers_data':pers_data,'group_data':group_data,'skill_lineups':skill_lineups,'ol_lineups':ol_lineups,
             'procedure_data':procedure_data}

with open(os.path.join(out_dir, f'D_{variant}.json'),'w') as f: json.dump(D,f)
with open(os.path.join(out_dir, f'RUN_DATA_{variant}.json'),'w') as f: json.dump(RUN_DATA,f)
with open(os.path.join(out_dir, f'PW_DATA_{variant}.json'),'w') as f: json.dump(PW_DATA,f)
with open(os.path.join(out_dir, f'PLAYER_DATA_{variant}.json'),'w') as f: json.dump(PLAYER_DATA,f)
print(f"[{variant}] built: n={n} n_run={n_run} n_pass={n_pass}")
