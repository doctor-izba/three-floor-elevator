const {spawn}=require('child_process'),net=require('net'),path=require('path');
let broker,red;
const port=net.connect({host:'127.0.0.1',port:1889});
port.once('connect',()=>{port.destroy();startRed();});
port.once('error',()=>{broker=spawn(process.execPath,[path.join(__dirname,'broker.cjs')],{stdio:'inherit',windowsHide:true});setTimeout(startRed,600);});
function startRed(){if(red)return;red=spawn(process.execPath,[require.resolve('node-red/red.js'),'--userDir',__dirname,'--settings',path.join(__dirname,'settings.js')],{stdio:'inherit',windowsHide:true});red.on('exit',code=>{if(broker)broker.kill();process.exit(code||0)});}
function stop(){if(red)red.kill();if(broker)broker.kill();}process.on('SIGINT',stop);process.on('SIGTERM',stop);
