const aedes=require('aedes')(),net=require('net');
const server=net.createServer(aedes.handle);
server.on('error',e=>{console.error('Local MQTT:',e.message);process.exit(1)});
server.listen(1889,'127.0.0.1',()=>console.log('Elevator MQTT broker on 127.0.0.1:1889'));
function stop(){aedes.close(()=>server.close(()=>process.exit(0)));}process.on('SIGINT',stop);process.on('SIGTERM',stop);
