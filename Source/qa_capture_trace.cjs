const fs=require('fs'),path=require('path'),base='http://127.0.0.1:1888';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function command(action,extra={}){const r=await fetch(base+'/elevator/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...extra})});if(!r.ok)throw Error('Command HTTP '+r.status);return r.json();}
async function state(){return(await fetch(base+'/elevator/api/state')).json();}
async function until(fn,timeout=24000){const t=Date.now();let s;do{s=await state();if(fn(s))return s;await delay(80);}while(Date.now()-t<timeout);throw Error('Timed out '+JSON.stringify(s));}
async function restore(){await command('new-demo');await delay(650);await command('reset');await until(s=>!s.alarms.length&&s.connection.live);await delay(500);}
async function capture(name,action){const rows=[],commands=[];const began=Date.now();let lastTx=-1,stopped=false;
 const loop=(async()=>{while(!stopped){const s=await state();if(!s.connection.live)throw Error('Lost live native telemetry');if(s.connection.tx!==lastTx){rows.push({elapsed_ms:Date.now()-began,...s});lastTx=s.connection.tx;}await delay(50);}})();
 const issue=async(a,extra={})=>{commands.push({elapsed_ms:Date.now()-began,action:a,...extra});return command(a,extra);};
 try{await action(issue);await delay(300);}finally{stopped=true;await loop;}
 const result={source:'Live native TriLOGI MQTT telemetry sampled through Node-RED API; elapsed_ms is capture wall clock',recorded_at:new Date().toISOString(),name,commands,rows};
 fs.writeFileSync(path.join(__dirname,'qa',name+'_trace.json'),JSON.stringify(result,null,2));return result;
}
async function main(){await until(s=>s.connection.live);await restore();
 const normal=await capture('normal',async issue=>{await issue('start');await until(s=>s.run);await delay(500);await issue('call',{floor:3});await until(s=>s.currentFloor===3&&s.state==='DWELL');await until(s=>s.state==='IDLE'&&s.inputs.DOOR_CLOSED);});
 await restore();
 const jam=await capture('door_jam',async issue=>{await issue('start');await until(s=>s.run);await delay(500);await issue('jam',{value:true});await issue('call',{floor:1});await until(s=>s.state==='CLOSING');await until(s=>s.state==='FAULT — REOPENING');await until(s=>s.inputs.DOOR_OPEN&&s.alarms.includes('JAM_FLT'));await issue('jam',{value:false});await issue('reset');await until(s=>!s.alarms.length&&!s.run);await delay(500);await issue('start');await until(s=>s.state==='IDLE'&&s.inputs.DOOR_CLOSED);});
 const closing=jam.rows.find(s=>s.outputs.DOOR_CL_CMD),fault=jam.rows.find(s=>s.alarms.includes('JAM_FLT'));
 const measured=(fault.elapsed_ms-closing.elapsed_ms)/1000;
 const nativeTicks=(fault.connection.tx-closing.connection.tx+30000)%30000;
 if(nativeTicks<79||nativeTicks>82)throw Error('Closing timeout outside native clock tolerance '+nativeTicks);
 for(const s of [...normal.rows,...jam.rows]){if(s.outputs.MOTOR_UP&&s.outputs.MOTOR_DOWN)throw Error('Opposite motors');if(s.outputs.DOOR_OP_CMD&&s.outputs.DOOR_CL_CMD)throw Error('Opposite door commands');}
 const result={result:'PASS',normal_samples:normal.rows.length,jam_samples:jam.rows.length,closing_timeout_wall_s:measured,closing_timeout_native_ticks:nativeTicks,native_tick_nominal_s:0.1,nominal_timeout_s:8,timing_note:'Native clock ticks verify the timer preset; wall time includes simulator and MQTT scheduling overhead and is not hard real-time.',source:'Actual running native ladder; no controller equation evaluator used'};
 fs.writeFileSync(path.join(__dirname,'qa/trace_results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 await command('new-demo');await delay(600);await command('reset');
}
main().catch(e=>{console.error(e);process.exit(1)});
