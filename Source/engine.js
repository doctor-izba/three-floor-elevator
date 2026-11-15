/* Fixed-step educational plant and controller. Node-RED loads the same rung
 * specification used to generate the TriLOGI project. No PLC connection implied. */
function create(spec) {
  const v = Object.fromEntries([...spec.inputs,...spec.outputs,...spec.relays,...spec.timers.map(x=>x.split(' ')[0])].map(k=>[k,false]));
  return {v, elapsed:{}, position:1, door:0, first:true, enabledClock:true, obstruction:false, estop:false, jam:false, driveFault:false, conflict:false, lostDoor:false, pulses:{}, time:0, log:[], previousState:''};
}
const expressionCache = new Map();
function expression(src,v,first) {
  let tree=expressionCache.get(src);
  if(!tree){
    const ts=src.match(/1st\.Scan|Norm\.ON|[A-Za-z_][A-Za-z_0-9]*|[+*/()]/g);let i=0;
    function atom(){let t=ts[i++];if(t==='/')return ['NOT',atom()];if(t==='('){let n=or();if(ts[i++]!==')')throw Error('Parenthesis');return n;}return ['TAG',t];}
    function and(){let a=atom();while(ts[i]==='*'){i++;a=['AND',a,atom()];}return a;}
    function or(){let a=and();while(ts[i]==='+'){i++;a=['OR',a,and()];}return a;}
    tree=or();if(i!==ts.length)throw Error('Expression');expressionCache.set(src,tree);
  }
  function run(t){if(t[0]==='TAG')return t[1]==='1st.Scan'?first:t[1]==='Norm.ON'?true:!!v[t[1]];if(t[0]==='NOT')return !run(t[1]);if(t[0]==='AND')return run(t[1])&&run(t[2]);return run(t[1])||run(t[2]);}
  return run(tree);
}
function step(s,spec,dt=0.1){
  if(!s.enabledClock)return;
  const v=s.v;
  // Previous controller outputs drive the plant for the next time interval.
  if(!s.driveFault){
    if(v.MOTOR_UP)s.position=Math.min(3,s.position+dt*0.5);
    if(v.MOTOR_DOWN)s.position=Math.max(1,s.position-dt*0.5);
  }
  if(v.DOOR_OP_CMD)s.door=Math.min(1,s.door+dt);
  if(v.DOOR_CL_CMD)s.door=Math.max(s.jam?0.45:0,s.door-dt);
  for(let n=1;n<=3;n++)v['FLOOR'+n]=Math.abs(s.position-n)<0.024;
  if(s.conflict){v.FLOOR1=true;v.FLOOR2=true;}
  v.DOOR_OPEN=s.door>0.999;v.DOOR_CLOSED=s.door<0.001&&!s.lostDoor;
  v.OBSTRUCT=s.obstruction;v.ESTOP_OK=!s.estop;
  for(const k of spec.inputs.filter(x=>/^CALL|^CAB|^START$|^RESET$/.test(x)))v[k]=!!s.pulses[k];
  const timers=Object.fromEntries(spec.timers.map(x=>{let[k,n]=x.split(' ');return[k,Number(n)/10];}));
  for(const r of spec.rungs){const [out,src]=r.split('=');const on=expression(src,v,s.first);if(out in timers){s.elapsed[out]=on?(s.elapsed[out]||0)+dt:0;v[out]=s.elapsed[out]+1e-8>=timers[out];}else v[out]=on;}
  s.first=false;s.pulses={};s.time+=dt;
  if(v.MOTOR_UP&&v.MOTOR_DOWN)throw Error('Opposite motor commands');
  if(v.DOOR_OP_CMD&&v.DOOR_CL_CMD)throw Error('Opposite door commands');
  const state=stateName(s);
  if(state!==s.previousState){s.log.unshift({time:s.time.toFixed(1),event:state});s.log=s.log.slice(0,14);s.previousState=state;}
}
function stateName(s){const v=s.v;if(v.REOPEN)return 'FAULT — REOPENING';if(v.FAULT)return 'FAULT — RESET REQUIRED';if(!v.RUN_EN)return 'DISABLED';return ['UP_RUN','DOWN_RUN','OPENING','DWELL','CLOSING','IDLE'].find(k=>v[k])||'INITIALIZING';}
function command(s,spec,p){
  const a=p?.action;
  if(a==='new-demo')return create(spec);
  if(a==='start')s.pulses.START=true;
  if(a==='reset')s.pulses.RESET=true;
  if(a==='call'&&[1,2,3].includes(Number(p.floor)))s.pulses['CAB'+Number(p.floor)]=true;
  const flags={obstruction:'obstruction',estop:'estop',jam:'jam',driveFault:'driveFault',conflict:'conflict',lostDoor:'lostDoor',pause:'enabledClock'};
  if(flags[a])s[flags[a]]=typeof p.value==='boolean'?p.value:!s[flags[a]];
  return s;
}
function snapshot(s){const v=s.v;return {state:stateName(s),time:s.time.toFixed(1),position:s.position,door:s.door,currentFloor:[1,2,3].find(n=>v['FLOOR'+n])||null,lastFloor:[1,2,3].find(n=>v['POS'+n])||null,requests:[1,2,3].filter(n=>v['REQ'+n]),alarms:['ESTOP_FLT','SENSOR_FLT','DOOR_FLT','TRAVEL_FLT','JAM_FLT'].filter(k=>v[k]),inputs:Object.fromEntries(Object.keys(v).filter(k=>/^FLOOR|^DOOR_OPEN$|^DOOR_CLOSED$|^ESTOP_OK$|^OBSTRUCT$/.test(k)).map(k=>[k,v[k]])),outputs:Object.fromEntries(['MOTOR_UP','MOTOR_DOWN','DOOR_OP_CMD','DOOR_CL_CMD','ALARM','BUZZER'].map(k=>[k,v[k]])),run:!!v.RUN_EN,flags:{obstruction:s.obstruction,estop:s.estop,jam:s.jam,driveFault:s.driveFault,conflict:s.conflict,lostDoor:s.lostDoor,paused:!s.enabledClock},log:s.log};}
if(typeof module!=='undefined')module.exports={create,step,command,snapshot,expression};
