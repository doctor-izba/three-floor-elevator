"""Vector engineering diagrams and recorded native telemetry plots."""
from pathlib import Path
import json,csv,math
from reportlab.graphics.shapes import Drawing,Rect,Line,String,Polygon,PolyLine,Circle
from reportlab.graphics import renderPDF,renderSVG
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parent;DESIGN=ROOT/'deliverables/Design';QA=ROOT/'qa'
DEST=DESIGN/'Engineering_Figures';DEST.mkdir(parents=True,exist_ok=True)
INK='#172b43';BLUE='#25628c';GREEN='#24745c';RED='#a33f43';GRAY='#657489'
figures=[];S=60
def col(c):return HexColor(c)
def text(d,x,y,value,size=14,c=INK,anchor='start',bold=False):
 for i,t in enumerate(value.split('\n')):d.add(String(x*S,y*S-i*size*1.35,t,fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,fillColor=col(c),textAnchor=anchor))
def box(d,x,y,w,h,title,body='',c=BLUE):
 d.add(Rect(x*S,y*S,w*S,h*S,rx=4,ry=4,fillColor=col('#ffffff'),strokeColor=col(c),strokeWidth=1.6))
 text(d,x+w/2,y+h-.3,title,14,c,'middle',True)
 if body:text(d,x+w/2,y+h/2-.1,body,13,INK,'middle')
def arrow(d,start,end,label='',rad=0,c=GRAY):
 x1,y1=start;x2,y2=end;dx,dy=x2-x1,y2-y1;cx=(x1+x2)/2-rad*dy;cy=(y1+y2)/2+rad*dx;p=[]
 for i in range(21):
  t=i/20;p += [S*((1-t)**2*x1+2*(1-t)*t*cx+t*t*x2),S*((1-t)**2*y1+2*(1-t)*t*cy+t*t*y2)]
 d.add(PolyLine(p,strokeColor=col(c),strokeWidth=1.5));theta=math.atan2(p[-1]-p[-3],p[-2]-p[-4]);x,y=x2*S,y2*S
 d.add(Polygon([x,y,x-10*math.cos(theta-.38),y-10*math.sin(theta-.38),x-10*math.cos(theta+.38),y-10*math.sin(theta+.38)],fillColor=col(c),strokeColor=col(c)))
 if label:text(d,cx,cy+.13,label,11,INK,'middle')
def save(d,name):
 renderPDF.drawToFile(d,str(DEST/(name+'.pdf')));renderSVG.drawToFile(d,str(DEST/(name+'.svg')))
 pdf=pdfium.PdfDocument(str(DEST/(name+'.pdf')));pdf[0].render(scale=4).to_pil().save(DEST/(name+'.png'));pdf.close();figures.append(d)
def canvas(title,height=7):
 d=Drawing(720,height*S);text(d,.1,height-.35,title,20,bold=True);return d

d=canvas('Three floor process and signal boundaries')
d.add(Rect(3.9*S,.8*S,3*S,5.2*S,fillColor=None,strokeColor=col(GRAY),strokeWidth=2))
for n,y in [(1,1.3),(2,3.2),(3,5.1)]:
 d.add(Line(3.9*S,y*S,6.9*S,y*S,strokeColor=col(GRAY)))
 d.add(Circle(6.9*S,(y+.25)*S,5,fillColor=col(BLUE),strokeColor=None));text(d,7.2,y+.2,f'FLOOR{n}  /  DI {n+6}',13)
 box(d,.15,y-.05,2.7,.85,f'Floor {n}',f'CALL{n}   /   DI {n}');arrow(d,(2.9,y+.4),(3.85,y+.4))
d.add(Rect(4.25*S,1.4*S,2.3*S,1.3*S,fillColor=col('#eef3f7'),strokeColor=col(BLUE),strokeWidth=1.8))
for x in [4.5,5.4]:d.add(Rect(x*S,1.52*S,.9*S,.85*S,fillColor=col('#c9d7e2'),strokeColor=col(BLUE)))
text(d,5.4,2.48,'CAB1 / CAB2 / CAB3',11,anchor='middle');text(d,5.4,1.02,'Door actuator',12,anchor='middle')
arrow(d,(5.4,3.65),(5.4,4.75),c=GREEN);text(d,5.7,4.1,'UP / DOWN',12,c=GREEN)
box(d,7.3,3.6,4.3,1.05,'Door feedback','OPEN DI10 / CLOSED DI11')
box(d,7.3,2.1,4.3,1.05,'Door path protection','OBSTRUCT DI12 / ESTOP_OK DI13',RED)
box(d,.15,0,11.45,.65,'PLC output commands');text(d,5.9,.08,'DO1/2 hoist   DO3/4 door   DO5/6 alarm and buzzer',12,anchor='middle')
text(d,.15,6.1,'One call per landing; three cabin destinations; discrete floor confirmation.',13,c=GRAY)
save(d,'A_Process_Schematic')

d=canvas('Field to control to supervision')
box(d,.5,.3,6.9,1.3,'FIELD','6 request buttons + 9 feedback/operator signals\nHoist and door interfaces + lamp and buzzer')
box(d,.5,2.65,6.9,1.3,'CONTROL','Native TriLOGI: 68 control networks\nRequest memory, dispatcher, five timers, interlocks')
box(d,.5,5,6.9,1.3,'SUPERVISORY','Node-RED HMI: commands, status, requests, alarms\nBrowser dashboard and event history')
for start,end,label,x,y in [((1.7,1.65),(1.7,2.6),'15 DI',1.9,2.1),((6.1,2.6),(6.1,1.65),'6 DO',6.3,2.1),((1.7,4),(1.7,4.95),'Native tags',1.9,4.4),((6.1,4.95),(6.1,4),'Commands',4.9,4.4)]:arrow(d,start,end);text(d,x,y,label,12)
box(d,8,2.35,3.6,2.1,'Virtual implementation','Local MQTT broker\n127.0.0.1:1889\n100 ms field frames\n41 native status bits')
text(d,8,1.8,'Node-RED: field mechanics.\nTriLOGI: controller execution.\nMQTT: virtual field/HMI data.',13)
text(d,.55,.12,'Physical design: 24 V circuits; an FMD HMI driver requires an appropriate gateway or protocol.',11,c=GRAY)
save(d,'B_Three_Level_Architecture')

d=canvas('Sequence and fault priority')
for x,y,w,title in [(4.4,5.35,3.2,'IDLE'),(.4,3.95,3,'UP_RUN'),(8.6,3.95,3,'DOWN_RUN'),(4.4,2.8,3.2,'OPENING'),(4.4,1.5,3.2,'DWELL'),(4.4,.2,3.2,'CLOSING')]:box(d,x,y,w,.8,title)
for start,end,label in [((4.4,5.55),(2.1,4.8),'Request above'),((7.6,5.55),(9.9,4.8),'Request below'),((3.4,4.15),(4.4,3.3),'Arrival'),((8.6,4.15),(7.6,3.3),'Arrival')]:arrow(d,start,end,label)
arrow(d,(6,5.3),(6,3.65));text(d,6.15,4.3,'Current-floor\nrequest',11)
arrow(d,(6,2.75),(6,2.35));text(d,6.2,2.51,'Open feedback',11)
arrow(d,(6,1.45),(6,1.05));text(d,6.2,1.21,'5 s + clear path',11)
arrow(d,(7.65,.55),(7.65,5.7),rad=-.25);text(d,8,5.8,'Closed feedback',11)
box(d,.4,.3,3.15,2.6,'JAM recovery','Closing obstruction\nor 8 s timeout\nREOPEN + buzzer\nOpen feedback stops output',RED);arrow(d,(4.35,.65),(3.6,.65),c=RED)
box(d,8.65,.3,3,2.6,'Hard fault priority','E-stop / bad sensors\nLost door / travel timeout\nRecovery timeout\nMotion commands OFF',RED)
text(d,.4,3.55,'DISABLED is an overlay.\nReset clears corrected faults;\nStart separately enables.',12)
text(d,8.65,3.45,'Reopening needs a valid\nfloor and no hard fault.',12)
save(d,'C_State_Sequence')

d=canvas('Electrical interface concept',5)
box(d,.3,2.6,4.6,1.3,'NPN compatible input','NPN sensor or dry contact to 0 V\nLow terminal voltage = logical TRUE')
box(d,7,2.6,4.6,1.3,'NPN sinking output','24 V low current interposing interface\nOutput sinks interface current to 0 V')
arrow(d,(4.95,3.25),(6.95,3.25),'PLC scan')
text(d,.35,2.2,'FMD1616-10 input logic:\nON: 0 to 2.5 V; OFF: open or 10 to 24 V.\nCommon 0 V for non-isolated signals.',13)
text(d,7,2.2,'Design target: interface input <= 20 mA.\nSuppress DC coil transients.\nMotor power bypasses PLC outputs.',13)
text(d,.35,.45,'E-stop status is diagnostic feedback from an independent protection circuit.',12,c=RED)
text(d,.35,.12,'This conceptual diagram is not a construction or safety circuit drawing.',12,c=RED)
save(d,'D_Electrical_Interface')

def trace_plot(name,tags,title,filename):
 data=json.loads((QA/(name+'_trace.json')).read_text());rows=data['rows'];duration=rows[-1]['elapsed_ms']/1000
 d=Drawing(780,360);text(d,.1,5.65,title,19,bold=True);left=155;right=760;bottom=43;top=302;spacing=(top-bottom)/len(tags)
 for second in range(0,math.ceil(duration)+1,2):
  x=left+(right-left)*second/duration
  if x>right:continue
  d.add(Line(x,bottom,x,top,strokeColor=col('#d9e0e6'),strokeWidth=.6));d.add(String(x,bottom-18,str(second),textAnchor='middle',fontSize=12))
 colors=[BLUE,GREEN,RED,'#965e29']
 for j,(label,group,key) in enumerate(tags):
  baseline=top-(j+1)*spacing+5;d.add(String(left-12,baseline+9,label,textAnchor='end',fontSize=12,fillColor=col(INK)));points=[];previous=None
  for r in rows:
   x=left+(right-left)*(r['elapsed_ms']/1000)/duration;on=key in r['alarms'] if group=='alarms' else bool(r[group][key]);y=baseline+int(on)*spacing*.6
   if previous is not None:points.extend([x,previous])
   points.extend([x,y]);previous=y
  d.add(PolyLine(points,strokeColor=col(colors[j%len(colors)]),strokeWidth=1.8))
 d.add(String((left+right)/2,8,'Elapsed capture wall time / s',textAnchor='middle',fontSize=13));save(d,filename)
 flat=[{'elapsed_ms':r['elapsed_ms'],'native_tx':r['connection']['tx'],'native_rx':r['connection']['rx'],'state':r['state'],**{k:int(v) for k,v in r['inputs'].items()},**{k:int(v) for k,v in r['outputs'].items()},'JAM_FLT':int('JAM_FLT' in r['alarms'])} for r in rows]
 with (DESIGN/(name+'_native_trace.csv')).open('w',newline='',encoding='utf-8') as file:
  w=csv.DictWriter(file,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
if (QA/'normal_trace.json').exists():
 trace_plot('normal',[('MOTOR_UP','outputs','MOTOR_UP'),('FLOOR3','inputs','FLOOR3'),('OPEN command','outputs','DOOR_OP_CMD'),('OPEN feedback','inputs','DOOR_OPEN'),('CLOSE command','outputs','DOOR_CL_CMD'),('CLOSED feedback','inputs','DOOR_CLOSED')],'Normal trip from floor 1 to floor 3','E_Normal_Recorded_Timing')
 trace_plot('door_jam',[('CLOSE command','outputs','DOOR_CL_CMD'),('CLOSED feedback','inputs','DOOR_CLOSED'),('JAM_FLT','alarms','JAM_FLT'),('OPEN command','outputs','DOOR_OP_CMD'),('OPEN feedback','inputs','DOOR_OPEN'),('BUZZER','outputs','BUZZER')],'Door closing timeout and deliberate recovery','F_Jam_Recorded_Timing')
c=Canvas(str(DESIGN/'Engineering_Diagrams_and_Timing.pdf'))
for d in figures:c.setPageSize((d.width,d.height));renderPDF.draw(d,c,0,0);c.showPage()
c.save();print('Created',len(figures),'engineering figures and vector PDF')
