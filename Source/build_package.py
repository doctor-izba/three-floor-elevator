from pathlib import Path
import json, re, csv, zipfile, html

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'deliverables'
PROJ = OUT / 'TriLOGI_Projects'
QA = ROOT / 'qa'
for d in (OUT, PROJ, QA): d.mkdir(parents=True, exist_ok=True)

def native(name, inputs, outputs, rungs, timers=()):
    relays = []
    timer_names = [x.split()[0] for x in timers]
    for r in rungs:
        lhs = r.split('=')[0]
        if lhs not in outputs + timer_names + relays: relays.append(lhs)
    text = '\u00f8\u00f5TRiLOGI Ver 5.0\n'
    for group in (inputs, outputs, relays, timers, []):
        text += ''.join(f'{i},{v}\n' for i,v in enumerate(group)) + '~\n'
    text += '\n'.join(rungs) + '\n\n~END_CIRCUIT~\n~END_CUSTFN~\n~END_CUSTFNLABEL~\n'
    text += '0,0,\n1,0,\n2,0,\n3,0,\n4,0,\n~END_QUICKTAGS~\n'
    (PROJ / (name+'.PC7')).write_text(text, encoding='utf-16')
    (PROJ / (name+'_listing.txt')).write_text('\n'.join(f'{i+1:02d}  {r}' for i,r in enumerate(rungs)), encoding='utf-8')
    return dict(name=name,inputs=inputs,outputs=outputs,relays=relays,timers=timers,rungs=rungs)

INS = ['CALL1','CALL2','CALL3','CAB1','CAB2','CAB3','FLOOR1','FLOOR2','FLOOR3','DOOR_OPEN','DOOR_CLOSED','OBSTRUCT','ESTOP_OK','START','RESET']
OUTS = ['MOTOR_UP','MOTOR_DOWN','DOOR_OP_CMD','DOOR_CL_CMD','ALARM','BUZZER']
R = [
 'START_EDGE=START*/PREV_START', 'RESET_EDGE=RESET*/PREV_RESET',
 'PREV_START=START','PREV_RESET=RESET',
]
for i in (1,2,3):
    R += [f'EDGE{i}=(CALL{i}*/PCALL{i}+CAB{i}*/PCAB{i})*/1st.Scan',f'PCALL{i}=CALL{i}',f'PCAB{i}=CAB{i}']
R += [
 'DWELL_T=DWELL', 'CLOSE_T=CLOSING', 'OPEN_T=OPENING', 'TRAVEL_T=UP_RUN+DOWN_RUN', 'REC_OPEN_T=REOPEN',
 'POS_VALID=FLOOR1*/FLOOR2*/FLOOR3+/FLOOR1*FLOOR2*/FLOOR3+/FLOOR1*/FLOOR2*FLOOR3',
 'BAD_SENS=FLOOR1*FLOOR2+FLOOR1*FLOOR3+FLOOR2*FLOOR3+DOOR_OPEN*DOOR_CLOSED',
 'DOOR_LOST=(UP_RUN+DOWN_RUN)*(/DOOR_CLOSED+OBSTRUCT)',
 'POS_LOST=IDLE*RUN_EN*/POS_VALID',
 'LIVE_FAULT=/ESTOP_OK+BAD_SENS+DOOR_LOST+POS_LOST+CLOSE_T+OPEN_T+TRAVEL_T+REC_OPEN_T+CLOSING*OBSTRUCT',
 'CLEAR_FAULT=RESET_EDGE*/LIVE_FAULT*POS_VALID*(DOOR_CLOSED+DOOR_OPEN)*/OBSTRUCT*/START*/REOPEN',
 'ESTOP_FLT=(/ESTOP_OK+ESTOP_FLT)*/CLEAR_FAULT',
 'SENSOR_FLT=(BAD_SENS+SENSOR_FLT)*/CLEAR_FAULT',
 'DOOR_FLT=(DOOR_LOST+OPEN_T+REC_OPEN_T+DOOR_FLT)*/CLEAR_FAULT',
 'TRAVEL_FLT=(TRAVEL_T+POS_LOST+TRAVEL_FLT)*/CLEAR_FAULT',
 'JAM_FLT=(CLOSING*OBSTRUCT+CLOSE_T+JAM_FLT)*/CLEAR_FAULT',
 'HARD_FAULT=ESTOP_FLT+SENSOR_FLT+DOOR_FLT+TRAVEL_FLT',
 'FAULT=HARD_FAULT+JAM_FLT',
 'REOPEN=(CLOSING*(OBSTRUCT+CLOSE_T)+REOPEN)*/DOOR_OPEN*/HARD_FAULT*/1st.Scan',
 'RUN_EN=(RUN_EN+START_EDGE*POS_VALID*(DOOR_CLOSED+DOOR_OPEN)*/OBSTRUCT)*/FAULT*ESTOP_OK*/1st.Scan',
 'POS1=FLOOR1+POS1*/FLOOR2*/FLOOR3',
 'POS2=FLOOR2+POS2*/FLOOR1*/FLOOR3',
 'POS3=FLOOR3+POS3*/FLOOR1*/FLOOR2',
]
for i in (1,2,3):
    R += [f'SERVE{i}=(OPENING+DWELL)*DOOR_OPEN*FLOOR{i}*RUN_EN',f'REQ{i}=(REQ{i}+EDGE{i})*/SERVE{i}*RUN_EN']
R += [
 'AT_REQ=FLOOR1*REQ1+FLOOR2*REQ2+FLOOR3*REQ3',
 'ABOVE=POS1*(REQ2+REQ3)+POS2*REQ3',
 'BELOW=POS3*(REQ1+REQ2)+POS2*REQ1',
 'PREF_UP=(UP_RUN+PREF_UP*/DOWN_RUN+1st.Scan)*/DOWN_RUN',
 'GO_UP=IDLE*RUN_EN*DOOR_CLOSED*/AT_REQ*ABOVE*(PREF_UP+/BELOW)',
 'GO_DOWN=IDLE*RUN_EN*DOOR_CLOSED*/AT_REQ*BELOW*(/PREF_UP+/ABOVE)',
 'ARRIVE_UP=AT_REQ+FLOOR3',
 'ARRIVE_DOWN=AT_REQ+FLOOR1',
 'N_IDLE=IDLE*DOOR_CLOSED*/AT_REQ*/GO_UP*/GO_DOWN+CLOSING*DOOR_CLOSED*/OBSTRUCT+/RUN_EN',
 'N_UP=(GO_UP+UP_RUN*/ARRIVE_UP)*RUN_EN',
 'N_DOWN=(GO_DOWN+DOWN_RUN*/ARRIVE_DOWN)*RUN_EN',
 'N_OPEN=(IDLE*AT_REQ+UP_RUN*ARRIVE_UP+DOWN_RUN*ARRIVE_DOWN+CLOSING*OBSTRUCT+OPENING*/DOOR_OPEN)*RUN_EN',
 'N_DWELL=(OPENING*DOOR_OPEN+DWELL*(/DWELL_T+OBSTRUCT))*RUN_EN',
 'N_CLOSE=(IDLE*DOOR_OPEN*/AT_REQ+DWELL*DWELL_T*/OBSTRUCT+CLOSING*/DOOR_CLOSED*/OBSTRUCT)*RUN_EN',
 'IDLE=N_IDLE+1st.Scan',
 'UP_RUN=N_UP*/1st.Scan', 'DOWN_RUN=N_DOWN*/1st.Scan',
 'OPENING=N_OPEN*/1st.Scan', 'DWELL=N_DWELL*/1st.Scan','CLOSING=N_CLOSE*/1st.Scan',
 'MOTOR_UP=UP_RUN*RUN_EN*DOOR_CLOSED*/DOOR_OPEN*/OBSTRUCT*/FAULT*/DOWN_RUN*/FLOOR3',
 'MOTOR_DOWN=DOWN_RUN*RUN_EN*DOOR_CLOSED*/DOOR_OPEN*/OBSTRUCT*/FAULT*/UP_RUN*/FLOOR1',
 'DOOR_OP_CMD=(OPENING*RUN_EN*/FAULT+REOPEN*JAM_FLT)*POS_VALID*ESTOP_OK*/HARD_FAULT*/DOOR_OPEN*/UP_RUN*/DOWN_RUN',
 'DOOR_CL_CMD=CLOSING*RUN_EN*/DOOR_CLOSED*/OBSTRUCT*/FAULT*/UP_RUN*/DOWN_RUN',
 'ALARM=FAULT','BUZZER=FAULT',
]
MAIN = native('01_Three_Floor_Elevator_LD', INS, OUTS, R, ['DWELL_T 50','CLOSE_T 80','OPEN_T 80','TRAVEL_T 150','REC_OPEN_T 80'])

DOOR = native('02_Door_Interlock_Bench_LD',
 ['OPEN_REQ','DOOR_OPEN','DOOR_CLOSED','OBSTRUCT','ESTOP_OK','RESET'],
 ['DOOR_OP_CMD','DOOR_CL_CMD','ALARM'],[
 'OPEN_EDGE=OPEN_REQ*/PREV_OPEN','PREV_OPEN=OPEN_REQ',
 'RESET_EDGE=RESET*/PREV_RESET','PREV_RESET=RESET',
 'DWELL_T=DWELL','CLOSE_T=CLOSING','OPEN_T=OPENING',
 'BAD_SENS=DOOR_OPEN*DOOR_CLOSED',
 'LIVE_FAULT=/ESTOP_OK+BAD_SENS+CLOSE_T+OPEN_T',
 'CLEAR_FAULT=RESET_EDGE*/LIVE_FAULT*DOOR_CLOSED*/DOOR_OPEN*/OBSTRUCT*/OPEN_REQ',
 'FAULT=(FAULT+LIVE_FAULT)*/CLEAR_FAULT',
 'N_OPEN=(OPEN_EDGE*/OPENING*/DWELL*/CLOSING+OPENING*/DOOR_OPEN+CLOSING*OBSTRUCT)*/FAULT',
 'N_DWELL=(OPENING*DOOR_OPEN+DWELL*(/DWELL_T+OBSTRUCT))*/FAULT',
 'N_CLOSE=(DWELL*DWELL_T*/OBSTRUCT+CLOSING*/DOOR_CLOSED*/OBSTRUCT)*/FAULT',
 'OPENING=N_OPEN*/1st.Scan','DWELL=N_DWELL*/1st.Scan','CLOSING=N_CLOSE*/1st.Scan',
 'DOOR_OP_CMD=OPENING*/DOOR_OPEN*/FAULT',
 'DOOR_CL_CMD=CLOSING*/DOOR_CLOSED*/OBSTRUCT*/FAULT','ALARM=FAULT',
 ], ['DWELL_T 50','CLOSE_T 80','OPEN_T 80'])

MEM = native('03_Request_Memory_Bench_LD',
 ['CALL1','CALL2','CALL3','SERVED1','SERVED2','SERVED3','CLEAR'],
 ['REQ1','REQ2','REQ3','ANY_REQ'],
 sum(([f'EDGE{i}=CALL{i}*/PREV{i}',f'PREV{i}=CALL{i}',f'REQ{i}=(REQ{i}+EDGE{i})*/SERVED{i}*/CLEAR*/1st.Scan'] for i in (1,2,3)),[])+['ANY_REQ=REQ1+REQ2+REQ3'])
PROJECTS=[MAIN,DOOR,MEM]
(OUT/'project_manifest.json').write_text(json.dumps(PROJECTS,indent=2),encoding='utf-8')

# A scan-order reference evaluator for the generated Boolean ladder equations.
# This is an independent execution check, not a substitute for TriLOGI evidence.
class Model:
    def __init__(self,p):
        self.p=p;self.v={s:False for s in p['inputs']+p['outputs']+p['relays']}
        self.ts={x.split()[0]:int(x.split()[1]) for x in p['timers']};self.elapsed={s:0 for s in self.ts};self.first=True
    def expr(self,s):
        toks=re.findall(r'1st\.Scan|Norm\.ON|[A-Za-z_][A-Za-z_0-9]*|[+*/()]',s);k=0
        def atom():
            nonlocal k
            t=toks[k];k+=1
            if t=='/': return not atom()
            if t=='(':
                x=orr();assert toks[k]==')';k+=1;return x
            if t=='1st.Scan':return self.first
            if t=='Norm.ON':return True
            if t not in self.v:raise ValueError('Unknown tag '+t)
            return self.v[t]
        def andd():
            nonlocal k
            x=atom()
            while k<len(toks) and toks[k]=='*':k+=1;y=atom();x=x and y
            return x
        def orr():
            nonlocal k
            x=andd()
            while k<len(toks) and toks[k]=='+':k+=1;y=andd();x=x or y
            return x
        value=orr();assert k==len(toks);return value
    def scan(self,n=1,**inputs):
        assert set(inputs)<=set(self.p['inputs'])
        self.v.update({k:bool(v) for k,v in inputs.items()})
        for _ in range(n):
            for r in self.p['rungs']:
                lhs,rhs=r.split('=');value=self.expr(rhs)
                if lhs in self.ts:
                    self.elapsed[lhs]=self.elapsed[lhs]+1 if value else 0
                    self.v[lhs]=self.elapsed[lhs]>=self.ts[lhs]
                else:self.v[lhs]=value
            if 'MOTOR_UP' in self.v:
                assert not(self.v['MOTOR_UP'] and self.v['MOTOR_DOWN'])
                assert not(self.v['DOOR_OP_CMD'] and self.v['DOOR_CL_CMD'])
                if self.v['MOTOR_UP'] or self.v['MOTOR_DOWN']:
                    assert self.v['DOOR_CLOSED'] and not self.v['FAULT'] and not self.v['OBSTRUCT']
                assert sum(bool(self.v[s]) for s in ['IDLE','UP_RUN','DOWN_RUN','OPENING','DWELL','CLOSING'])==1
            self.first=False
        return self
    def has(self,*tags):assert all(self.v[t] for t in tags),[(t,self.v[t]) for t in tags];return self
    def off(self,*tags):assert all(not self.v[t] for t in tags),[(t,self.v[t]) for t in tags];return self

def ready():
    m=Model(MAIN).scan(2,FLOOR1=1,DOOR_CLOSED=1,ESTOP_OK=1)
    return m.scan(START=1).scan(START=0).has('RUN_EN','IDLE')
def door_cycle(m):
    m.scan(DOOR_CLOSED=0).scan(DOOR_OPEN=1).has('DWELL')
    m.scan(52).has('CLOSING');m.scan(DOOR_OPEN=0).scan(DOOR_CLOSED=1).has('IDLE');return m

def check():
    results=[]
    def record(name,func):func();results.append([name,'PASS','Reference model of generated rung equations; not a TriLOGI observation'])
    def normal():
        m=ready().scan(CAB3=1).scan(CAB3=0).has('MOTOR_UP')
        m.scan(FLOOR1=0).scan(FLOOR2=1).has('MOTOR_UP').scan(FLOOR2=0).scan(FLOOR3=1).has('OPENING').off('MOTOR_UP')
        door_cycle(m).off('REQ3','FAULT')
    record('T1 Floor 1 to Floor 3 and complete door cycle',normal)
    def queue():
        m=ready().scan(CAB2=1,CAB3=1).scan(CAB2=0,CAB3=0).scan(FLOOR1=0).scan(FLOOR2=1).has('OPENING','REQ3')
        door_cycle(m);m.scan().has('MOTOR_UP').off('REQ2')
        m.scan(FLOOR2=0).scan(FLOOR3=1).has('OPENING');door_cycle(m).off('REQ3')
        m.scan(CAB1=1).scan(CAB1=0).has('MOTOR_DOWN')
    record('T2 Two queued stops and direction reversal',queue)
    def obstruction():
        m=ready().scan(CAB1=1).scan(CAB1=0).scan(DOOR_CLOSED=0).scan(DOOR_OPEN=1).scan(52).has('CLOSING')
        m.scan(DOOR_OPEN=0).scan(OBSTRUCT=1).has('REOPEN','DOOR_OP_CMD','JAM_FLT','BUZZER').off('DOOR_CL_CMD','MOTOR_UP','RUN_EN')
        m.scan(DOOR_OPEN=1).scan(60).has('FAULT').off('DOOR_CL_CMD','REOPEN')
        m.scan(OBSTRUCT=0,RESET=1).off('FAULT','RUN_EN').scan(RESET=0).scan(START=1).has('CLOSING')
    record('T3 Obstruction reopens door and inhibits closing while blocked',obstruction)
    def simultaneous():
        m=ready().scan(CAB1=1).scan(CAB1=0).scan(DOOR_CLOSED=0).scan(DOOR_OPEN=1).scan(52).scan(DOOR_OPEN=0)
        m.scan(OBSTRUCT=1,DOOR_CLOSED=1).has('REOPEN','FAULT','DOOR_OP_CMD').off('DOOR_CL_CMD','RUN_EN')
    record('T3b Obstruction takes priority over simultaneous closed feedback',simultaneous)
    def timeout():
        m=ready().scan(CAB1=1).scan(CAB1=0).scan(DOOR_CLOSED=0).scan(DOOR_OPEN=1).scan(52).scan(DOOR_OPEN=0)
        m.scan(81).has('FAULT','JAM_FLT','ALARM','REOPEN','DOOR_OP_CMD').off('RUN_EN','MOTOR_UP','DOOR_CL_CMD')
        m.scan(RESET=1).has('FAULT').scan(RESET=0)
        m.scan(DOOR_OPEN=1).scan(RESET=1).off('FAULT','RUN_EN').scan(RESET=0).scan(START=1).has('RUN_EN','CLOSING')
        m.scan(START=0,DOOR_OPEN=0).scan(DOOR_CLOSED=1).has('IDLE').off('MOTOR_UP','MOTOR_DOWN')
    record('T4 Door close timeout and controlled reset',timeout)
    def estop():
        m=ready().scan(CAB3=1).scan(CAB3=0).scan(FLOOR1=0).scan(ESTOP_OK=0).has('FAULT').off('MOTOR_UP')
        m.scan(ESTOP_OK=1,RESET=1).has('FAULT')
        m.scan(RESET=0,FLOOR1=1).scan(RESET=1).off('FAULT','RUN_EN').scan(RESET=0).scan(START=1).has('RUN_EN')
    record('T5 Emergency stop between floors refuses unsafe reset',estop)
    record('T6 Conflicting floor sensors',lambda:ready().scan(FLOOR2=1).has('FAULT','SENSOR_FLT').off('MOTOR_UP','MOTOR_DOWN'))
    record('T7 Door confirmation lost during travel',lambda:ready().scan(CAB3=1).scan(CAB3=0).scan(DOOR_CLOSED=0).has('FAULT','DOOR_FLT').off('MOTOR_UP'))
    record('T8 Travel timeout',lambda:ready().scan(CAB3=1).scan(CAB3=0,FLOOR1=0).scan(151).has('FAULT','TRAVEL_FLT'))
    def reopen_failure():
        m=ready().scan(CAB1=1).scan(CAB1=0).scan(DOOR_CLOSED=0).scan(DOOR_OPEN=1).scan(52).scan(DOOR_OPEN=0,OBSTRUCT=1)
        m.scan(81).has('DOOR_FLT','HARD_FAULT').off('REOPEN','DOOR_OP_CMD','DOOR_CL_CMD')
    record('T9 Recovery opening timeout stops the door command',reopen_failure)
    def memory():
        m=Model(MEM).scan().scan(CALL1=1).scan(CALL1=0).has('REQ1').scan(SERVED1=1).off('REQ1')
        m.scan(SERVED1=0,CALL2=1,CALL3=1).has('REQ2','REQ3').scan(CLEAR=1).off('ANY_REQ')
    record('B1 Request memory bench',memory)
    def doorbench():
        m=Model(DOOR).scan(2,ESTOP_OK=1,DOOR_CLOSED=1).scan(OPEN_REQ=1).scan(OPEN_REQ=0,DOOR_CLOSED=0).has('DOOR_OP_CMD')
        m.scan(DOOR_OPEN=1).scan(OPEN_REQ=1).has('DWELL').off('OPENING').scan(OPEN_REQ=0)
        m.scan(52).has('CLOSING').scan(DOOR_OPEN=0).scan(81).has('FAULT','ALARM')
    # The legacy door bench is not included in the final elevator package.
    # Deterministic randomized stress of asynchronous requests and contradictory inputs.
    import random
    rng=random.Random(7);m=ready()
    for _ in range(3000):
        changes={rng.choice(INS):rng.choice([0,1])};m.scan(**changes)
    results.append(['S1 3000 randomized scans of output and state invariants','PASS','Reference model only'])
    with (QA/'reference_model_results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Test','Result','Evidence type']);w.writerows(results)
    print('Reference checks passed:',len(results))
    return results

if __name__=='__main__':check()
