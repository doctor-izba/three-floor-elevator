"""Create a native TriLOGI fixture executing the unchanged controller rung set.

Field channels become internal relays driven by TBASIC test stimulus. Outputs,
native timers, rung order and controller equations are unchanged. Evidence must
be read from the actual TriLOGI simulator, not inferred from this generator.
"""
import json
from build_package import MAIN, INS, OUTS, OUT, PROJ, QA, Model

SCENARIOS=[]
def scenario(name,end,events,checks):
    SCENARIOS.append(dict(name=name,end=end,events={int(k):v for k,v in events.items()},checks=checks))
base={2:{'START':1},3:{'START':0}}
scenario('T1 Normal trip and door cycle',78,base|{
 5:{'CAB3':1},6:{'CAB3':0,'FLOOR1':0},8:{'FLOOR2':1},9:{'FLOOR2':0},11:{'FLOOR3':1},13:{'DOOR_CLOSED':0},15:{'DOOR_OPEN':1},72:{'DOOR_OPEN':0},74:{'DOOR_CLOSED':1}},[
 (7,['MOTOR_UP','REQ3'],['MOTOR_DOWN']), (12,['OPENING'],['MOTOR_UP']), (16,['DWELL'],['REQ3']), (71,['CLOSING'],[]),(76,['IDLE','RUN_EN'],['FAULT','REQ3'])])
scenario('T2 Queued stops and direction reversal',220,base|{
 5:{'CAB2':1,'CAB3':1},6:{'CAB2':0,'CAB3':0,'FLOOR1':0},11:{'FLOOR2':1},13:{'DOOR_CLOSED':0},15:{'DOOR_OPEN':1},70:{'DOOR_OPEN':0},72:{'DOOR_CLOSED':1},76:{'FLOOR2':0},80:{'FLOOR3':1},82:{'DOOR_CLOSED':0},84:{'DOOR_OPEN':1},140:{'DOOR_OPEN':0},142:{'DOOR_CLOSED':1},144:{'CAB1':1},145:{'CAB1':0},146:{'FLOOR3':0},148:{'FLOOR2':1},149:{'FLOOR2':0},152:{'FLOOR1':1},156:{'DOOR_CLOSED':0},158:{'DOOR_OPEN':1},214:{'DOOR_OPEN':0},216:{'DOOR_CLOSED':1}},[
 (12,['OPENING','REQ3'],['MOTOR_UP']), (75,['MOTOR_UP','REQ3'],['REQ2']), (85,['DWELL'],['REQ3']), (147,['MOTOR_DOWN'],['MOTOR_UP']), (154,['OPENING'],['MOTOR_DOWN']), (218,['IDLE'],['FAULT','REQ1'])])
doorbase=base|{5:{'CAB1':1},6:{'CAB1':0,'DOOR_CLOSED':0},8:{'DOOR_OPEN':1},64:{'DOOR_OPEN':0}}
scenario('T3 Obstruction reopening and deliberate recovery',90,doorbase|{
 66:{'OBSTRUCT':1},70:{'DOOR_OPEN':1},72:{'RESET':1},74:{'RESET':0},75:{'OBSTRUCT':0},76:{'RESET':1},77:{'RESET':0},80:{'START':1},81:{'START':0},84:{'DOOR_OPEN':0},86:{'DOOR_CLOSED':1}},[
 (68,['JAM_FLT','REOPEN','DOOR_OP_CMD','BUZZER'],['MOTOR_UP','MOTOR_DOWN','DOOR_CL_CMD','RUN_EN']), (73,['FAULT'],['REOPEN','DOOR_CL_CMD']), (78,[],['FAULT','RUN_EN']), (88,['IDLE','RUN_EN'],['FAULT'])])
scenario('T4 Closing timeout reopening and recovery',162,doorbase|{
 146:{'DOOR_OPEN':1},150:{'RESET':1},151:{'RESET':0},154:{'START':1},155:{'START':0},156:{'DOOR_OPEN':0},158:{'DOOR_CLOSED':1}},[
 (145,['JAM_FLT','REOPEN','DOOR_OP_CMD','BUZZER'],['MOTOR_UP','MOTOR_DOWN','DOOR_CL_CMD']), (148,['FAULT'],['REOPEN']), (152,[],['FAULT','RUN_EN']), (160,['IDLE','RUN_EN'],['FAULT'])])
scenario('T5 Emergency stop between floors and reset',28,base|{
 5:{'CAB3':1},6:{'CAB3':0,'FLOOR1':0},10:{'ESTOP_OK':0},14:{'ESTOP_OK':1,'RESET':1},17:{'RESET':0},18:{'FLOOR1':1},20:{'RESET':1},21:{'RESET':0},24:{'START':1},25:{'START':0}},[
 (12,['FAULT','ESTOP_FLT'],['MOTOR_UP','MOTOR_DOWN','RUN_EN']), (16,['FAULT'],[]),(26,['RUN_EN'],['FAULT'])])
scenario('T6 Conflicting floor sensors',10,base|{5:{'FLOOR2':1}},[(7,['SENSOR_FLT','FAULT'],['MOTOR_UP','MOTOR_DOWN','DOOR_OP_CMD','DOOR_CL_CMD'])])
scenario('T7 Door confirmation lost during travel',15,base|{5:{'CAB3':1},6:{'CAB3':0,'FLOOR1':0},10:{'DOOR_CLOSED':0}},[(12,['DOOR_FLT','FAULT'],['MOTOR_UP','MOTOR_DOWN','DOOR_OP_CMD'])])
scenario('T8 Travel timeout',164,base|{5:{'CAB3':1},6:{'CAB3':0,'FLOOR1':0}},[(160,['TRAVEL_FLT','FAULT','BUZZER'],['MOTOR_UP','MOTOR_DOWN','RUN_EN'])])
scenario('T9 Recovery opening timeout',155,doorbase|{66:{'OBSTRUCT':1}},[(68,['REOPEN','DOOR_OP_CMD'],[]),(151,['DOOR_FLT','HARD_FAULT','JAM_FLT'],['REOPEN','DOOR_OP_CMD','DOOR_CL_CMD','MOTOR_UP','MOTOR_DOWN'])])

def verify_schedules():
    for case in SCENARIOS:
        m=Model(MAIN)
        for tick in range(case['end']+1):
            if tick<2:
                m=Model(MAIN).scan(FLOOR1=1,DOOR_CLOSED=1,ESTOP_OK=1)
            else:m.scan(**case['events'].get(tick,{}))
            for at,on,off in case['checks']:
                if at==tick:m.has(*on).off(*off)
        print(case['name'],'schedule PASS')

def body():
    core=MAIN['relays']+INS
    init='C=1\nT=0\nQ=0\nDM[90]=0\nDM[91]=0\nDM[92]=0\n'
    for tag in ['WAITING','FAILED','ALL_PASS']+[f'T{i}_PASS' for i in range(1,10)]:init+=f'CLRIO {tag}\n'
    tick='IF TESTIO(WAITING)=0 AND TESTIO(FAILED)=0\nT=T+1\nENDIF\n'
    drive=['IF TESTIO(NEXT_TEST) AND Q=0 AND TESTIO(WAITING) AND C<9 AND TESTIO(FAILED)=0','C=C+1','T=0','CLRIO WAITING','ENDIF','Q=TESTIO(NEXT_TEST)','DM[92]=C','IF T<2']
    drive += [f'CLRIO {tag}' for tag in core]
    drive += ['SETIO FLOOR1','SETIO DOOR_CLOSED','SETIO ESTOP_OK','ENDIF']
    for i,case in enumerate(SCENARIOS,1):
        drive += [f'IF C={i} AND TESTIO(WAITING)=0']
        for at,changes in sorted(case['events'].items()):
            drive += [f'IF T={at}']+[f'{"SETIO" if val else "CLRIO"} {tag}' for tag,val in changes.items()]+['ENDIF']
        drive += ['ENDIF']
    check=[]
    for i,case in enumerate(SCENARIOS,1):
        check += [f'IF C={i} AND TESTIO(WAITING)=0']
        for at,on,off in case['checks']:
            # Record the first failed check; checks are evaluated after the ladder.
            bad=' OR '.join([f'TESTIO({tag})=0' for tag in on]+[f'TESTIO({tag})' for tag in off])
            check += [f'IF T={at}',f'IF {bad}','SETIO FAILED',f'DM[90]={i}',f'DM[91]={at}','SETIO WAITING','ENDIF','ENDIF']
        check += [f'IF T>={case["end"]} AND TESTIO(FAILED)=0',f'SETIO T{i}_PASS','SETIO WAITING']
        if i==9:check+=['SETIO ALL_PASS']
        check+=['ENDIF','ENDIF']
    # Always-on safety checks, independent of case-specific assertions.
    check += ['IF TESTIO(MOTOR_UP) AND TESTIO(MOTOR_DOWN)','SETIO FAILED','DM[90]=99','DM[91]=T','SETIO WAITING','ENDIF',
              'IF TESTIO(DOOR_OP_CMD) AND TESTIO(DOOR_CL_CMD)','SETIO FAILED','DM[90]=98','DM[91]=T','SETIO WAITING','ENDIF']
    return [('Initialize',init),('Tick100ms',tick),('TestStimulus','\n'.join(drive)+'\n'),('Assertions','\n'.join(check)+'\n')]

def build():
    funcs=body();rungs=['%LFn_#1=1st.Scan','%LFn_#2=Clk:0.1s','%KFn_#3=Norm.ON']+MAIN['rungs']+['%KFn_#4=Norm.ON']
    outputs=[f'T{i}_PASS' for i in range(1,10)]+['ALL_PASS','FAILED']+OUTS
    relays=['WAITING']+INS+MAIN['relays']
    s='\u00f8\u00f5TRiLOGI Ver 5.0\n'
    for group in (['NEXT_TEST'],outputs,relays,MAIN['timers'],[]):s+=''.join(f'{i},{v}\n' for i,v in enumerate(group))+'~\n'
    s+='\n'.join(rungs)+'\n\n~END_CIRCUIT~\n'
    for i,(label,code) in enumerate(funcs):s+=f'\u00c8\nFn#{i},{len(code)}\n'+code+'\n'
    s+='~END_CUSTFN~\n'+''.join(f'{i},{label}\n' for i,(label,_) in enumerate(funcs))
    s+='~END_CUSTFNLABEL~\n0,0,\n1,0,\n2,0,\n3,0,\n4,0,\n~END_QUICKTAGS~\n'
    (PROJ/'04_Native_Verification_Suite.PC7').write_text(s,encoding='utf-16')
    (PROJ/'04_Test_Harness_TBASIC.txt').write_text('\n\n'.join(label+'\n'+code for label,code in funcs),encoding='utf-8')
    (OUT/'native_test_scenarios.json').write_text(json.dumps(SCENARIOS,indent=2),encoding='utf-8')
    print('Created native suite:',len(rungs),'rungs;',len(s),'characters')

if __name__=='__main__':verify_schedules();build()
