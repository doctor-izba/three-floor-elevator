from pathlib import Path
import json
from build_package import MAIN,OUT,ROOT

HMI=OUT/'HMI_Node_RED';HMI.mkdir(exist_ok=True)
source=(ROOT/'engine.js').read_text(encoding='utf-8')
source=source[:source.index("if(typeof module")]
code=source+'\nconst SPEC='+json.dumps(MAIN)+';\n'+'''
let s=flow.get('elevatorState')||create(SPEC);
if(msg.topic==='command')s=command(s,SPEC,msg.payload);
if(msg.topic==='tick')step(s,SPEC,0.1);
flow.set('elevatorState',s);
const payload=snapshot(s);node.status({fill:s.v.FAULT?'red':s.v.RUN_EN?'green':'grey',shape:'dot',text:payload.state});
const update={payload};const response=msg.req?{...msg,payload,statusCode:200,headers:{'Content-Type':'application/json'}}:null;
return [update,response];
'''
flows=[
 dict(id='elevator-tab',type='tab',label='Three Floor Elevator EE-2401',disabled=False,info='Local educational HMI. Simulated signals; controller equations mirror the TriLOGI LD project.'),
 dict(id='elevator-ui',type='ui-base',name='EE-2401 Elevator',path='/dashboard',includeClientData=True,acceptsClientConfig=[],showPathInSidebar=False,headerContent='none',navigationStyle='none',titleBarStyle='hidden',showReconnectNotification=True,showDisconnectNotification=True,allowInstall=False),
 dict(id='elevator-theme',type='ui-theme',name='Elevator dark',colors={'surface':'#101a29','primary':'#63ddb0','bgPage':'#0b1422','groupBg':'#101a29','groupOutline':'#2b3c54'},sizes={'density':'default','pagePadding':'12px','groupGap':'12px','groupBorderRadius':'8px','widgetGap':'12px'}),
 dict(id='elevator-page',type='ui-page',name='Elevator Control',ui='elevator-ui',path='/elevator',icon='elevator',layout='grid',theme='elevator-theme',order=1,className='',visible=True,disabled=False,breakpoints=[{'name':'Default','px':0,'cols':12},{'name':'Desktop','px':1000,'cols':12}]),
 dict(id='elevator-group',type='ui-group',name='Elevator console',page='elevator-page',width=12,height=1,order=1,showTitle=False,className='',visible=True,disabled=False,groupType='default'),
 dict(id='tick',type='inject',z='elevator-tab',name='100 ms plant and control tick',props=[{'p':'topic','vt':'str'}],topic='tick',repeat='0.1',crontab='',once=True,onceDelay=0.3,x=190,y=100,wires=[['engine']]),
 dict(id='engine',type='function',z='elevator-tab',name='Plant plus ordered PLC equations',func=code,outputs=2,timeout=0,noerr=0,initialize='',finalize='',libs=[],x=530,y=170,wires=[['console'],['http-response']]),
 dict(id='console',type='ui-template',z='elevator-tab',group='elevator-group',page='',ui='',name='Elevator animated HMI',order=1,width=12,height=0,format=(ROOT/'hmi-template.vue').read_text(encoding='utf-8'),storeOutMessages=True,passthru=False,resendOnRefresh=True,templateScope='local',className='',x=850,y=100,wires=[['engine']]),
 dict(id='api-post',type='http in',z='elevator-tab',name='Local demonstration commands',url='/elevator/api/command',method='post',upload=False,swaggerDoc='',x=190,y=220,wires=[['command-topic']]),
 dict(id='command-topic',type='change',z='elevator-tab',name='Command',rules=[{'t':'set','p':'topic','pt':'msg','to':'command','tot':'str'}],x=365,y=220,wires=[['engine']]),
 dict(id='api-get',type='http in',z='elevator-tab',name='Read local model',url='/elevator/api/state',method='get',upload=False,swaggerDoc='',x=190,y=300,wires=[['state-topic']]),
 dict(id='state-topic',type='change',z='elevator-tab',name='Snapshot',rules=[{'t':'set','p':'topic','pt':'msg','to':'snapshot','tot':'str'}],x=365,y=300,wires=[['engine']]),
 dict(id='http-response',type='http response',z='elevator-tab',name='JSON response',statusCode='',headers={},x=850,y=240,wires=[]),
]
(HMI/'flows.json').write_text(json.dumps(flows,indent=2),encoding='utf-8')
(HMI/'settings.js').write_text("module.exports = {uiPort:1888,uiHost:'127.0.0.1',flowFile:'flows.json',editorTheme:{projects:{enabled:false}},logging:{console:{level:'info',metrics:false,audit:false}}};\n",encoding='utf-8')
versions=json.loads((ROOT/'hmi_runtime/package-lock.json').read_text())['packages']
deps={k:versions['node_modules/'+k]['version'] for k in ['node-red','@flowfuse/node-red-dashboard']}
(HMI/'package.json').write_text(json.dumps({'name':'ee2401-elevator-hmi','version':'1.0.0','private':True,'scripts':{'start':'node-red --userDir . --settings settings.js'},'dependencies':deps},indent=2),encoding='utf-8')
(HMI/'START_HMI.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\nnode -e "fetch(\'http://127.0.0.1:1888/elevator/api/state\',{signal:AbortSignal.timeout(1500)}).then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))" >nul 2>&1\r\nif not errorlevel 1 goto running\r\nif not exist node_modules\\node-red\\red.js call npm.cmd ci --no-audit --no-fund\r\nif errorlevel 1 goto failed\r\necho Open http://127.0.0.1:1888/dashboard/elevator\r\ncall npm.cmd start\r\ngoto end\r\n:running\r\necho The elevator HMI is already running.\r\necho Open http://127.0.0.1:1888/dashboard/elevator\r\ngoto end\r\n:failed\r\necho Installation failed. Check Node.js 22 or newer and internet access.\r\n:end\r\npause\r\n',encoding='utf-8')
(HMI/'README.md').write_text('''# Elevator HMI — EE-2401
Authors: Izbassar Yesbol and Kuanysh Kali.

Requires Node.js 22 or newer and npm. Run START_HMI.cmd. The first run installs the exact package versions listed in package.json; internet is needed for installation. Later runs use local packages.

Dashboard: http://127.0.0.1:1888/dashboard/elevator
Flow editor: http://127.0.0.1:1888/

Press Start, choose floors, and watch the cabin and doors. Open Simulation and fault controls to inject obstruction, a closing jam, a drive stop or conflicting floor sensors. For the mandatory door-jam scenario, enable Door closing jam before a door cycle closes; after eight seconds the alarm sounds logically (BUZZER output) and the door reopens. Disable the injected condition, press Reset alarm, then Start separately. Start closes an already open door before travel. New demonstration restores the model at Floor 1.

This HMI uses simulated field signals and the same ordered controller equations as the main ladder project. It is not connected to the TriLOGI application. The animation's continuous position is a plant model value; PLC floor confirmation remains discrete. The Node-RED flow and JavaScript are supporting software, not the second PLC language. The two PLC representations are LD and FBD in Design/.
''',encoding='utf-8')
print('Created Node-RED HMI flows; versions',deps)
