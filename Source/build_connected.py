"""Native MQTT adapter around the unchanged 68-rung controller."""
import json, shutil
from build_package import ROOT,OUT,PROJ,QA,MAIN,INS,OUTS

TAGS=INS+OUTS+[f'REQ{i}' for i in (1,2,3)]+[f'POS{i}' for i in (1,2,3)]+['RUN_EN','FAULT','REOPEN','UP_RUN','DOWN_RUN','OPENING','DWELL','CLOSING','IDLE','ESTOP_FLT','SENSOR_FLT','DOOR_FLT','TRAVEL_FLT','JAM_FLT']
init='''DM[200]=99
DM[201]=0
DM[202]=0
DM[203]=0
DM[204]=0
CLRIO MQTT_UP
CLRIO MQTT_SUB
MQTT_DISCONNECT
MQTT_CONFIG 1,"0"
MQTT_CONFIG 7,"ee2401-native-ladder"
MQTT_CONFIG 8,"1"
MQTT_CONFIG 9,""
'''
callback='''IF MQTT_STATUS(1)=10
IF STRCMP(MQTT_TOPIC$(1),"ee2401/elevator/field")=0
B$=MQTT_DATA$(1)
IF LEN(B$)=15
DM[200]=0
DM[202]=(DM[202]+1) MOD 30000
'''
for i,tag in enumerate(INS):callback+=f'DM[{210+i}]=VAL(MID$(B$,{i+1},1))\n'
callback+='''ENDIF
ENDIF
ELSE
IF MQTT_STATUS(2)=1 OR MQTT_STATUS(2)=2
SETIO MQTT_UP
SETIO MQTT_SUB
ELSE
CLRIO MQTT_UP
DM[203]=0
ENDIF
ENDIF
'''
subscribe='MQTT_SUBSCRIBE "ee2401/elevator/field",0\nCLRIO MQTT_SUB\n'
apply=''
for i,tag in enumerate(INS):apply+=f'IF DM[{210+i}]=1 AND DM[200]<20\nSETIO {tag}\nELSE\nCLRIO {tag}\nENDIF\n'
publish='''IF DM[200]<99
DM[200]=DM[200]+1
ENDIF
IF MQTT_STATUS(2)<>1 AND MQTT_STATUS(2)<>2
CLRIO MQTT_UP
ENDIF
IF TESTIO(MQTT_UP)=0
DM[203]=DM[203]+1
IF DM[203]=5
CLRIO MQTT_SUB
MQTT_DISCONNECT
MQTT_CONNECT "127.0.0.1:1889",MQTTCallback
ENDIF
IF DM[203]>=50
DM[203]=0
ENDIF
ELSE
DM[203]=0
ENDIF
IF TESTIO(MQTT_UP)
DM[204]=DM[204]+1
IF DM[204]>=10
SETIO MQTT_SUB
DM[204]=0
ENDIF
DM[201]=(DM[201]+1) MOD 30000
C$=""
'''
for tag in TAGS:publish+=f'C$=C$+MID$("01",TESTIO({tag})+1,1)\n'
publish+='''MQTT_PUBLISH "ee2401/elevator/state",C$+"|"+STR$(DM[201])+"|"+STR$(DM[202]),0
IF MQTT_STATUS(1)<0
CLRIO MQTT_UP
DM[203]=0
ENDIF
ENDIF
'''
functions=[('LinkInit',init),('MQTTCallback',callback),('Subscribe',subscribe),('FieldInputs',apply),('PublishState',publish)]
rungs=['%LFn_#1=1st.Scan','%LFn_#3=MQTT_SUB','%KFn_#4=Norm.ON']+MAIN['rungs']+['%LFn_#5=Clk:0.1s']
s='øõTRiLOGI Ver 5.0\n'
for group in ([],OUTS,INS+MAIN['relays']+['MQTT_UP','MQTT_SUB'],MAIN['timers'],[]):
    s+=''.join(f'{i},{v}\n' for i,v in enumerate(group))+'~\n'
s+='\n'.join(rungs)+'\n\n~END_CIRCUIT~\n'
for i,(name,body) in enumerate(functions):s+=f'È\nFn#{i},{len(body)}\n{body}\n'
s+='~END_CUSTFN~\n'+''.join(f'{i},{name}\n' for i,(name,_) in enumerate(functions))+'~END_CUSTFNLABEL~\n'
s+=''.join(f'{i},0,\n' for i in range(5))+'~END_QUICKTAGS~\n'
(PROJ/'05_Connected_Elevator_MQTT.PC7').write_text(s,encoding='utf-16')
(PROJ/'05_Connected_Adapter_TBASIC.txt').write_text('\n\n'.join(n+'\n'+b for n,b in functions),encoding='utf-8')
(OUT/'Design/MQTT_signal_map.json').write_text(json.dumps({'field_topic':'ee2401/elevator/field','field_bit_order':INS,'state_topic':'ee2401/elevator/state','state_format':'bitstring|tx_counter|rx_counter','state_bit_order':TAGS,'native_core_rungs':MAIN['rungs'],'input_watchdog':'20 native clock edges, approximately 2 seconds; forces ESTOP_OK false'},indent=2),encoding='utf-8')

hmi=OUT/'HMI_Node_RED'
flows=json.loads((hmi/'flows.json').read_text(encoding='utf-8'))
flows=[n for n in flows if n['id'] not in ['mqtt-local','mqtt-state','mqtt-field']]
code=(ROOT/'connected-engine.js').read_text(encoding='utf-8')
code=code[:code.index("if(typeof module")]
code+='\nconst SPEC='+json.dumps(MAIN)+';\nconst TAGS='+json.dumps(TAGS)+';\n'
code+='''
let s=flow.get('connectedElevator')||createConnected(SPEC);
if(msg.topic==='command')s=connectedCommand(s,SPEC,msg.payload);
if(msg.topic==='ee2401/elevator/state')receiveState(s,TAGS,String(msg.payload));
if(msg.topic==='tick')plantTick(s,SPEC,0.1);
flow.set('connectedElevator',s);
const payload=connectedSnapshot(s);
node.status({fill:payload.connection.live?'green':'red',shape:'dot',text:payload.state});
return [{payload},msg.req?{...msg,payload,statusCode:200,headers:{'Content-Type':'application/json'}}:null,msg.topic==='tick'?{topic:'ee2401/elevator/field',payload:fieldFrame(s,SPEC),qos:'0',retain:false}:null];
'''
for n in flows:
    if n['id']=='elevator-tab':n['info']='Live native TriLOGI LD via localhost MQTT. Node-RED simulates field mechanics only.'
    if n['id']=='engine':n.update(name='Plant physics + native PLC telemetry',func=code,outputs=3,wires=[['console'],['http-response'],['mqtt-field']])
    if n['id']=='console':n['format']=(ROOT/'hmi-template.vue').read_text(encoding='utf-8')
    if n['id']=='tick':n['name']='100 ms field model and heartbeat'
    if n['id']=='api-get':n['name']='Read native PLC telemetry and plant'
flows += [dict(id='mqtt-local',type='mqtt-broker',name='Local demo broker',broker='127.0.0.1',port='1889',clientid='ee2401-node-red',autoConnect=True,usetls=False,protocolVersion='4',keepalive='10',cleansession=True,autoUnsubscribe=True),
dict(id='mqtt-state',type='mqtt in',z='elevator-tab',name='Native TriLOGI states',topic='ee2401/elevator/state',qos='0',datatype='utf8',broker='mqtt-local',nl=False,rap=False,rh=0,inputs=0,x=200,y=380,wires=[['engine']]),
dict(id='mqtt-field',type='mqtt out',z='elevator-tab',name='Field inputs to native ladder',topic='ee2401/elevator/field',qos='0',retain='false',respTopic='',contentType='',userProps='',correl='',expiry='',broker='mqtt-local',x=850,y=380,wires=[])]
(hmi/'flows.json').write_text(json.dumps(flows,indent=2),encoding='utf-8')
package=json.loads((hmi/'package.json').read_text());package['version']='2.0.0';package['dependencies']['aedes']='0.51.3'
package['scripts']['start']='node start-connected.cjs'
(hmi/'package.json').write_text(json.dumps(package,indent=2),encoding='utf-8')
for name in ['broker.cjs','start-connected.cjs']:shutil.copy2(ROOT/name,hmi/name)
print('Created connected native project:',len(rungs),'rungs; telemetry',len(TAGS),'bits; unchanged controller',len(MAIN['rungs']),'rungs')
