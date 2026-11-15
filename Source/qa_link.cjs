const fs=require('fs'),path=require('path'),base='http://127.0.0.1:1888';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function note(result,test,s){const entry={test,result:'PASS'};result.checks=result.checks.filter(x=>x.test!==test);result.checks.push(entry);result.observations.push({recorded_at:new Date().toISOString(),test,snapshot:s});}
async function state(){return(await fetch(base+'/elevator/api/state')).json();}
async function post(action,extra={}){return(await fetch(base+'/elevator/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...extra})})).json();}
async function deploy(flows){const r=await fetch(base+'/flows',{method:'POST',headers:{'Content-Type':'application/json','Node-RED-Deployment-Type':'nodes'},body:JSON.stringify(flows)});if(!r.ok)throw Error('Deploy '+r.status);}
async function main(){let result={checks:[],observations:[]};const file=path.join(__dirname,'qa/connected_link_results.json');if(fs.existsSync(file))result=JSON.parse(fs.readFileSync(file));
 if(process.argv[2]==='prepare-pause'){
  await post('estop',{value:true});await wait(600);let s=await state();
  if(s.run||!s.alarms.includes('ESTOP_FLT'))throw Error('Pause precondition E-stop failed');
  await post('estop',{value:false});await wait(600);await post('reset');await wait(600);s=await state();
  if(s.run||s.alarms.length||!s.inputs.FLOOR1)throw Error('Pause precondition must be disabled at floor 1');
  console.log('Verified pause initial condition: disabled, healthy and at floor 1');return;
 }else if(process.argv[2]==='paused'){
  await wait(1600);let s=await state();if(s.connection.live||s.run||Object.values(s.outputs).some(Boolean))throw Error('Stale PLC data still enabled');
  await post('start');await post('call');await wait(300);s=await state();if(s.run)throw Error('Offline start accepted');note(result,'Pausing actual TriLOGI causes PLC DISCONNECTED and blocks controls',s);
 }else if(process.argv[2]==='restart'){
  const started=Date.now();let s;
  do{await wait(300);s=await state();}while((!s.connection.live||!s.inputs.ESTOP_OK||!s.inputs.FLOOR1||s.connection.tx>200)&&Date.now()-started<30000);
  if(!s.connection.live||!s.inputs.ESTOP_OK||s.connection.tx>200)throw Error('Fresh simulator run did not reconnect with reset native counters');
  note(result,'Repeated Ctrl+F9 reconnects the native MQTT session',s);
  await post('reset');await wait(600);s=await state();if(s.run||s.alarms.length)throw Error('Restart reset did not remain disabled');
 }else if(process.argv[2]==='redeploy'){
  const saved=await(await fetch(base+'/flows')).json();
  const r=await fetch(base+'/flows',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(saved)});
  if(!r.ok)throw Error('Full redeploy failed '+r.status);
  await wait(1500);const before=await state();let s;const started=Date.now();
  do{await wait(300);s=await state();}while((!s.connection.live||s.connection.rx===before.connection.rx||!s.inputs.FLOOR1||!s.inputs.ESTOP_OK)&&Date.now()-started<30000);
  if(!s.connection.live||s.connection.rx===before.connection.rx||!s.inputs.FLOOR1||!s.inputs.ESTOP_OK)throw Error('Field subscription did not recover after full Node-RED redeploy');
  note(result,'Full Node-RED redeploy recovers native field subscription and live telemetry',s);
  await post('reset');await wait(600);s=await state();if(s.run||s.alarms.length)throw Error('Redeploy recovery reset failed');
 }else if(process.argv[2]==='resumed'){
  const started=Date.now(); let s;
  do{await wait(250);s=await state();}while((!s.connection.live||!s.inputs.ESTOP_OK||!s.inputs.FLOOR1||(!s.inputs.DOOR_CLOSED&&!s.inputs.DOOR_OPEN))&&Date.now()-started<60000);
  if(!s.connection.live||!s.inputs.ESTOP_OK||!s.inputs.FLOOR1)throw Error('Native MQTT and healthy field frames did not recover after resume');
  note(result,'Native MQTT recovers after a long simulator pause without restarting TriLOGI',s);
  await post('reset');await wait(600);s=await state();
  if(s.run||s.alarms.length)throw Error('Resume recovery did not remain disabled after reset');
  result.checks=result.checks.filter(x=>x.test!=='Resume recovery remains disabled until a separate Start');
  note(result,'A disabled PLC remains disabled after a long pause and Reset',s);
 }else{
  const saved=await(await fetch(base+'/flows')).json();const flows=Array.isArray(saved)?saved:saved.flows;const changed=structuredClone(flows);changed.find(n=>n.id==='engine').wires[2]=[];
  try{await deploy(changed);let s;const started=Date.now();do{await wait(300);s=await state();}while((!s.connection.live||s.inputs.ESTOP_OK||!s.alarms.includes('ESTOP_FLT'))&&Date.now()-started<12000);if(!s.connection.live||s.inputs.ESTOP_OK||!s.alarms.includes('ESTOP_FLT')||s.run)throw Error('Native watchdog failed '+JSON.stringify(s));note(result,'Stopping field heartbeat trips native watchdog and latches ESTOP_FLT while telemetry stays live',s);}finally{await deploy(flows);}
  await wait(800);await post('reset');await wait(600);let s=await state();if(s.alarms.length||s.run)throw Error('Recovery reset failed');note(result,'Link recovery requires deliberate Reset and separate Start',s);
 }
 result.result='PASS';fs.writeFileSync(file,JSON.stringify(result,null,2));console.log(JSON.stringify(result.checks));
}
main().catch(e=>{console.error(e);process.exit(1)});
