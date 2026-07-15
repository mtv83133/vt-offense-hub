import csv, json, sys, os

if len(sys.argv) < 4:
    print("Usage: python3 build_fall_variant.py <team|skelly|combined> <path_to_csv> <day_key> [output_dir]")
    print("  day_key becomes the output filename prefix, e.g. 'fall_2' -> fall_2_team.json")
    print("  output_dir defaults to './output' (created if missing)")
    sys.exit(1)

variant = sys.argv[1]  # team, skelly, combined
csv_path = sys.argv[2]
day_key = sys.argv[3]
out_dir = sys.argv[4] if len(sys.argv) > 4 else './output'
os.makedirs(out_dir, exist_ok=True)

with open(csv_path, encoding='utf-8-sig') as f:
    rd = csv.DictReader(f)
    rows = list(rd)
rows = [r for r in rows if r['pff_RUNPASS'].strip() not in ('PEN','NP','')]
if variant == 'team':
    rows = [r for r in rows if r['COMPETITIVE'].strip() != 'SKELLY']
elif variant == 'skelly':
    rows = [r for r in rows if r['COMPETITIVE'].strip() == 'SKELLY']
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
def is_run(r): return r['Run Family'].strip()!=''
def is_pass(r): return r['Run Family'].strip()==''
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
def pass_block(items):
    b=stat_block(items); b['comp']=comp_pct(items); return b
def concept_name(r):
    primary=r['Primary'].strip(); reset=r['Reset'].strip()
    if primary: return primary+(' / '+reset if reset else '')
    full=r['Full Concept'].strip()
    if full: return full
    return r['Play'].strip() or '(unknown)'

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

run_rows=[r for r in rows if is_run(r)]
pass_rows=[r for r in rows if is_pass(r)]
fam_rows=[r for r in rows if r['Run Family'].strip()!='']
n=len(rows); n_run=len(run_rows); n_pass=len(pass_rows)

FAM_ORDER=['WIDE ZONE','TITE ZONE','MID ZONE','GAP','DRAW']
fam_map={}
for r in fam_rows:
    fam=r['Run Family'].strip(); sch=r['RunScheme'].strip() or '(unnamed)'
    fam_map.setdefault(fam, {}).setdefault(sch, []).append(r)
run_families=[]
for fam, schemes in sorted(fam_map.items(), key=lambda kv: -sum(len(v) for v in kv[1].values())):
    all_fam_rows=[r for sr in schemes.values() for r in sr]
    fobj=stat_block(all_fam_rows); fobj['name']=fam
    fr=[r for r in all_fam_rows if is_run_sub(r)]; fp=[r for r in all_fam_rows if is_pass_sub(r)]
    if fr and fp:
        fobj['run_sub']=stat_block(fr)
        fobj['pass_sub']=stat_block(fp)
    scheme_list=[]
    for sch, sr in sorted(schemes.items(), key=lambda kv:-len(kv[1])):
        sobj=stat_block(sr); sobj['name']=sch
        sr_run=[r for r in sr if is_run_sub(r)]; sr_pass=[r for r in sr if is_pass_sub(r)]
        if sr_run and sr_pass:
            sobj['run_sub']=stat_block(sr_run)
            sobj['pass_sub']=stat_block(sr_pass)
        scheme_list.append(sobj)
    fobj['schemes']=scheme_list
    run_families.append(fobj)

rz_rows=[r for r in pass_rows if is_rz(r)]
gm_all={}
for r in pass_rows: gm_all.setdefault(concept_name(r), []).append(r)
pass_concepts=[]
for nm, items in sorted(gm_all.items(), key=lambda kv:-len(kv[1])):
    c=pass_block(items); c['name']=nm; pass_concepts.append(c)

WARP_EXCLUDE={'RAP','MVMT','SCREEN','6MAN','5MAN','QG'}
warp_map={}
for r in rows:
    if r['Procedure'].strip()=='WARP' and r['Run Family'].strip()=='':
        nm=r['Play'].strip() or '(unknown)'
        if nm in WARP_EXCLUDE: continue
        warp_map.setdefault(nm, []).append(r)
warp_plays=[]
for nm, items in sorted(warp_map.items(), key=lambda kv:-len(kv[1])):
    isp=[r for r in items if is_pass(r)]
    b=stat_block(items); b['comp']=comp_pct(isp) if isp else 0.0; b['name']=nm
    warp_plays.append(b)

POS_KEYS=['H','F','Q','Y','Z','X']
positions=[]
for pos in POS_KEYS:
    p_rows=[r for r in rows if r['TRACKING'].strip()==pos]
    if not p_rows: continue
    b=stat_block(p_rows); b['pos']=pos; b['pct']=pct(len(p_rows), n)
    b['carry_n']= n_run if pos=='H' else 0
    b['target_n']=len(p_rows)
    positions.append(b)

sacks=sum(1 for r in pass_rows if is_sack(r))
sack_pct=pct(sacks, n_pass)
overall=stat_block(rows); run_overall=stat_block(run_rows); pass_overall=pass_block(pass_rows)

qb_group=dict(pass_overall); qb_group['name']='QB Group'; qb_group['sacks']=sacks; qb_group['sack_pct']=sack_pct; qb_group['concepts']=[]
rb_recv_rows=[r for r in pass_rows if r['TRACKING'].strip()=='H']
rb_group={'name':'RB Group','rush':run_overall,
          'recv': {k:pass_block(rb_recv_rows)[k] for k in ('n','avg','comp','eff')} if rb_recv_rows else {'n':0,'avg':0,'eff':0,'comp':0}}

te_rows=[r for r in pass_rows if r['TRACKING'].strip()=='Y']
wr_rows=[r for r in pass_rows if r['TRACKING'].strip() in ('X','Z','F')]
recv_groups=[]
if te_rows:
    b=pass_block(te_rows); b.update({'pos':'Y','label':'TE','name':'TE (Y)'}); recv_groups.append(b)
if wr_rows:
    b=pass_block(wr_rows); b.update({'pos':'Z','label':'WR','name':'WR (Z)'}); recv_groups.append(b)

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
procedure_data=[]
for proc in ['HUDDLE','WARP','ALASKA']:
    pr=[r for r in rows if r['Procedure'].strip()==proc]
    if not pr: continue
    b={'procedure':proc,'n':len(pr),'run_n':sum(1 for r in pr if is_run(r)),'pass_n':sum(1 for r in pr if is_pass(r)),
       'avg':avgy(pr),'eff':pct(sum(1 for r in pr if is_eff(r)),len(pr)),'expl':pct(sum(1 for r in pr if is_expl(r)),len(pr))}
    procedure_data.append(b)

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
    b=stat_block(items)
    b['pers']=info['pers']; b['qb']=info['qb']; b['rb']=info['rb']; b['tes']=info['tes']; b['wrs']=info['wrs']
    b['run_n']=sum(1 for r in items if is_run(r))
    play_map={}
    for r in items:
        call=(r['Play Call'].strip() or r['Play'].strip() or '(unknown)')
        play_map.setdefault(call, []).append(r)
    plays=[]
    for call, pitems in sorted(play_map.items(), key=lambda kv:-len(kv[1])):
        typ='RUN' if is_run(pitems[0]) else 'PASS'
        plays.append({'call':call,'type':typ,'n':len(pitems),'avg':avgy(pitems),'eff':round(pct(sum(1 for r in pitems if is_eff(r)),len(pitems)))})
    b['plays']=plays
    skill_lineups.append(b)

ol_map={}
for r in rows:
    lt=jint(r['Jersey #2']); lg=jint(r['Jersey #3']); c=jint(r['Jersey #4']); rg=jint(r['Jersey #5']); rt=jint(r['Jersey #6'])
    if None in (lt,lg,c,rg,rt): continue
    key=(lt,lg,c,rg,rt)
    ol_map.setdefault(key, []).append(r)
ol_lineups=[]
for key, items in sorted(ol_map.items(), key=lambda kv:-len(kv[1])):
    b=stat_block(items)
    b['lt'],b['lg'],b['c'],b['rg'],b['rt']=key
    ol_lineups.append(b)

data = {
    'n':n, 'n_run':n_run, 'n_pass':n_pass, 'avg':overall['avg'], 'eff':overall['eff'],
    'expl':overall['expl'], 'neg':overall['neg'], 'comp':pass_overall['comp'], 'sack_pct':sack_pct,
    'run_families':run_families, 'run_overall':run_overall,
    'rz':{'n':len(rz_rows),'avg':avgy(rz_rows),'eff':pct(sum(1 for r in rz_rows if is_eff(r)),len(rz_rows)) if rz_rows else 0,'comp':comp_pct(rz_rows) if rz_rows else 0},
    'of':{'n':pass_overall['n'],'avg':pass_overall['avg'],'eff':pass_overall['eff'],'comp':pass_overall['comp']},
    'qb_group':qb_group, 'rb_group':rb_group, 'recv_groups':recv_groups,
    'pass_concepts':pass_concepts, 'warp_plays':warp_plays, 'positions':positions,
    'down_data':down_data, 'third_data':third_data, 'pers_data':pers_data, 'group_data':group_data,
    'procedure_data':procedure_data, 'skill_lineups':skill_lineups, 'ol_lineups':ol_lineups,
}
with open(os.path.join(out_dir, f'{day_key}_{variant}.json'),'w') as f:
    json.dump(data, f)
print(f"[{variant}] n={n} n_run={n_run} n_pass={n_pass} skill_lineups={len(skill_lineups)} ol_lineups={len(ol_lineups)}")
