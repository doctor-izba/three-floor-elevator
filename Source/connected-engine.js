// The connected mode contains no PLC expression evaluator. Outputs and states
// arrive only from the actual TriLOGI simulator over MQTT.
function createConnected(spec){return {v:Object.fromEntries([...spec.inputs,...spec.outputs,...spec.relays].map(k=>[k,false])),position:1,door:0,time:0,log:[],previousState:'',lastRx:0,tx:0,rx:0,session:null,obstruction:false,estop:false,jam:false,driveFault:false,conflict:false,lostDoor:false,enabledClock:true,pulses:{},linkLost:false};}
function live(s){return Date.now()-s.lastRx<1200&&s.lastRx>0;}
function receiveState(s,tags,frame){const parts=frame.split('|');if(parts.length!==3||parts[0].length!==tags.length||!/^[01]+$/.test(parts[0]))return;const tx=Number(parts[1]),rx=Number(parts[2]);if(!Number.isFinite(tx)||!Number.isFinite(rx))return;
 if(tx===s.tx&&rx===s.rx&&s.lastRx)return;
 tags.forEach((k,i)=>s.v[k]=parts[0][i]==='1');s.tx=tx;s.rx=rx;s.lastRx=Date.now();s.linkLost=false;
 const state=connectedState(s);if(state!==s.previousState){s.log.unshift({time:s.time.toFixed(1),event:state});s.log=s.log.slice(0,20);s.previousState=state;}
}
function plantTick(s,spec,dt){
 if(!live(s)){if(s.lastRx&&!s.linkLost){s.pulses={};s.log.unshift({time:s.time.toFixed(1),event:'PLC LINK LOST — FIELD MODEL HELD'});s.linkLost=true;}return;}
 if(!s.enabledClock)return;
 const v=s.v;
 if(!s.driveFault){if(v.MOTOR_UP&&!v.MOTOR_DOWN)s.position=Math.min(3,s.position+dt*.5);if(v.MOTOR_DOWN&&!v.MOTOR_UP)s.position=Math.max(1,s.position-dt*.5);}
 if(v.DOOR_OP_CMD&&!v.DOOR_CL_CMD)s.door=Math.min(1,s.door+dt);
 if(v.DOOR_CL_CMD&&!v.DOOR_OP_CMD)s.door=Math.max(s.jam?.45:0,s.door-dt);
 s.time+=dt;
}
function fieldFrame(s,spec){const fields={};for(let n=1;n<=3;n++)fields['FLOOR'+n]=Math.abs(s.position-n)<.024;
 if(s.conflict){fields.FLOOR1=true;fields.FLOOR2=true;}
 fields.DOOR_OPEN=s.door>.999;fields.DOOR_CLOSED=s.door<.001&&!s.lostDoor;fields.OBSTRUCT=s.obstruction;fields.ESTOP_OK=!s.estop;
 for(const key of spec.inputs.filter(k=>/^CALL|^CAB|^START$|^RESET$/.test(k)))fields[key]=live(s)&&Date.now()<(s.pulses[key]||0);
 return spec.inputs.map(k=>fields[k]?'1':'0').join('');
}
function connectedCommand(s,spec,p){const a=p?.action;
 if(a==='new-demo'){const fresh=createConnected(spec);fresh.lastRx=s.lastRx;fresh.v=s.v;fresh.tx=s.tx;fresh.rx=s.rx;fresh.log=[{time:'0.0',event:'FIELD MODEL RESTORED TO FLOOR 1; RESET THEN START'}];return fresh;}
 if(['start','reset','call'].includes(a)&&!live(s))return s;
 if(a==='start')s.pulses.START=Date.now()+400;
 if(a==='reset')s.pulses.RESET=Date.now()+400;
 if(a==='call'&&[1,2,3].includes(Number(p.floor)))s.pulses['CAB'+Number(p.floor)]=Date.now()+400;
 const flags={obstruction:'obstruction',estop:'estop',jam:'jam',driveFault:'driveFault',conflict:'conflict',lostDoor:'lostDoor',pause:'enabledClock'};
 if(flags[a])s[flags[a]]=typeof p.value==='boolean'?p.value:!s[flags[a]];
 return s;
}
function connectedState(s){const v=s.v;if(!live(s))return 'PLC DISCONNECTED';if(v.REOPEN)return 'FAULT — REOPENING';if(v.FAULT)return 'FAULT — RESET REQUIRED';if(!v.RUN_EN)return 'DISABLED';return ['UP_RUN','DOWN_RUN','OPENING','DWELL','CLOSING','IDLE'].find(k=>v[k])||'INITIALIZING';}
function connectedSnapshot(s){const v=s.v,online=live(s);return {state:connectedState(s),time:s.time.toFixed(1),position:s.position,door:s.door,currentFloor:[1,2,3].find(n=>v['FLOOR'+n])||null,lastFloor:[1,2,3].find(n=>v['POS'+n])||null,requests:[1,2,3].filter(n=>v['REQ'+n]),alarms:['ESTOP_FLT','SENSOR_FLT','DOOR_FLT','TRAVEL_FLT','JAM_FLT'].filter(k=>v[k]),inputs:Object.fromEntries(Object.keys(v).filter(k=>/^FLOOR|^DOOR_OPEN$|^DOOR_CLOSED$|^ESTOP_OK$|^OBSTRUCT$/.test(k)).map(k=>[k,v[k]])),outputs:Object.fromEntries(['MOTOR_UP','MOTOR_DOWN','DOOR_OP_CMD','DOOR_CL_CMD','ALARM','BUZZER'].map(k=>[k,online&&v[k]])),run:online&&!!v.RUN_EN,flags:{obstruction:s.obstruction,estop:s.estop,jam:s.jam,driveFault:s.driveFault,conflict:s.conflict,lostDoor:s.lostDoor,paused:!s.enabledClock},log:s.log,connection:{live:online,source:'Native TriLOGI ladder over local MQTT',tx:s.tx,rx:s.rx,ageMs:s.lastRx?Date.now()-s.lastRx:null,field:'Simulated cabin and doors',watchdogSeconds:2}};}
if(typeof module!=='undefined')module.exports={createConnected,receiveState,plantTick,fieldFrame,connectedCommand,connectedSnapshot};
