"""FBD second representation: explicit gate networks, vector PDF, and equivalence checks."""
from pathlib import Path
import json, re, random
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape,A4
from reportlab.graphics.shapes import Drawing,Rect,Line,String
from build_package import ROOT,OUT,MAIN,Model
from build_native_tests import SCENARIOS

DESIGN=OUT/'Design';DESIGN.mkdir(exist_ok=True)

def parse(src):
    ts=re.findall(r'1st\.Scan|Norm\.ON|[A-Za-z_][A-Za-z_0-9]*|[+*/()]',src);i=0
    def atom():
        nonlocal i
        t=ts[i];i+=1
        if t=='/':return dict(type='NOT',inputs=[atom()])
        if t=='(':
            n=orr();assert ts[i]==')';i+=1;return n
        return dict(type='WIRE',name=t)
    def andd():
        nonlocal i
        a=[atom()]
        while i<len(ts) and ts[i]=='*':i+=1;a.append(atom())
        return a[0] if len(a)==1 else dict(type='AND',inputs=a)
    def orr():
        nonlocal i
        a=[andd()]
        while i<len(ts) and ts[i]=='+':i+=1;a.append(andd())
        return a[0] if len(a)==1 else dict(type='OR',inputs=a)
    n=orr();assert i==len(ts);return n

networks=[dict(order=i+1,output=r.split('=')[0],expression=r.split('=')[1],network=parse(r.split('=')[1])) for i,r in enumerate(MAIN['rungs'])]
timers={s.split()[0]:int(s.split()[1]) for s in MAIN['timers']}
for net in networks:
    if net['output'] in timers:net['timer']=dict(type='TON',preset_seconds=timers[net['output']]/10)
(DESIGN/'FBD_networks.json').write_text(json.dumps(networks,indent=2),encoding='utf-8')

class FBD:
    def __init__(self):
        self.v=dict.fromkeys(MAIN['inputs']+MAIN['outputs']+MAIN['relays']+list(timers),False);self.time=dict.fromkeys(timers,0);self.first=True
    def evaluate(self,n):
        if n['type']=='WIRE':return self.first if n['name']=='1st.Scan' else True if n['name']=='Norm.ON' else self.v[n['name']]
        if n['type']=='NOT':return not self.evaluate(n['inputs'][0])
        values=[self.evaluate(c) for c in n['inputs']]
        return all(values) if n['type']=='AND' else any(values)
    def scan(self,**changes):
        self.v.update({k:bool(v) for k,v in changes.items()})
        for n in networks:
            on=self.evaluate(n['network']);key=n['output']
            if 'timer'in n:
                self.time[key]=self.time[key]+1 if on else 0
                self.v[key]=self.time[key]>=timers[key]
            else:self.v[key]=on
        self.first=False

def check():
    count=0
    for case in SCENARIOS:
        a=Model(MAIN);b=FBD()
        for tick in range(case['end']+1):
            if tick<2:a=Model(MAIN);b=FBD();changes={'FLOOR1':1,'DOOR_CLOSED':1,'ESTOP_OK':1}
            else:changes=case['events'].get(tick,{})
            a.scan(**changes);b.scan(**changes)
            for k in b.v:assert a.v[k]==b.v[k],(case['name'],tick,k)
            count+=1
    rng=random.Random(2401);a=Model(MAIN);b=FBD()
    for _ in range(5000):
        changes={rng.choice(MAIN['inputs']):rng.choice([0,1])};a.scan(**changes);b.scan(**changes)
        assert all(a.v[k]==b.v[k] for k in b.v);count+=1
    result={'comparison':'LD Boolean scan evaluator vs independently evaluated FBD gate graph','networks':len(networks),'compared_scans':count,'signals_per_scan':len(b.v),'result':'PASS','native_FBD_execution':False}
    (OUT/'Evidence').mkdir(exist_ok=True);(OUT/'Evidence/FBD_equivalence.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)

def layout(node,cols,edges,row):
    if node['type']=='WIRE':
        y=row[0]*39+22;row[0]+=1;cols.append((0,y,node['name'],False));return 0,y
    children=[layout(c,cols,edges,row) for c in node['inputs']]
    x=max(p[0] for p in children)+220;y=sum(p[1] for p in children)/len(children)
    cols.append((x,y,node['type'],len(children)))
    edges.extend((a,b,x,y,j,len(children)) for j,(a,b) in enumerate(children));return x,y

def generate():
    styles=getSampleStyleSheet();story=[Paragraph('Three Floor Elevator FBD Program',styles['Title']),Paragraph('EE-2401 | Izbassar Yesbol and Kuanysh Kali | 12 November 2026',styles['Normal']),Spacer(1,10),Paragraph('Second PLC representation. Evaluate networks in numbered order. Each named wire reads the value available at its point of evaluation; feedback stores the previous result. TON blocks are non-retentive. First scan and normally on flags are system signals. These design networks match the LD program; they are not a native TriLOGI FBD executable.',styles['Normal']),Spacer(1,15)]
    htmlnets=[]
    for net in networks:
        nodes=[];edges=[];row=[0];x,y=layout(net['network'],nodes,edges,row)
        h=max(65,row[0]*39+20);width=x+405
        label=net['output']+(f'  TON {net["timer"]["preset_seconds"]:g}s' if 'timer'in net else '')
        svg=[f'<svg viewBox="-5 -5 {width+10} {h+10}" xmlns="http://www.w3.org/2000/svg">']
        drawing=Drawing(width,h)
        from reportlab.lib.colors import HexColor
        for ax,ay,bx,by,j,total in edges:
            mid=bx-12-j*5;port=by+(j-(total-1)/2)*12
            for a,b,c,d in [(ax+140,ay,mid,ay),(mid,ay,mid,port),(mid,port,bx,port)]:
                drawing.add(Line(a,h-b,c,h-d,strokeColor=HexColor('#6d8192'),strokeWidth=1))
            svg.append(f'<path d="M{ax+140} {ay} H{mid} V{port} H{bx}" fill="none" stroke="#6d8192"/>')
        for nx,ny,text,ports in nodes:
            fill='#ddeaf1' if ports else '#f4f6f8';bh=max(28,(int(ports)-1)*12+20)
            drawing.add(Rect(nx,h-ny-bh/2,140,bh,fillColor=HexColor(fill),strokeColor=HexColor('#38546a')));drawing.add(String(nx+6,h-ny-4,text,fontName='Courier',fontSize=11))
            svg.append(f'<rect x="{nx}" y="{ny-bh/2}" width="140" height="{bh}" fill="{fill}" stroke="#38546a"/><text x="{nx+6}" y="{ny+4}" font-family="monospace" font-size="12">{text}</text>')
        drawing.add(Line(x+140,h-y,x+165,h-y));drawing.add(String(x+175,h-y-4,label,fontName='Courier-Bold',fontSize=12))
        svg.append(f'<path d="M{x+140} {y} H{x+165}" stroke="#38546a"/><text x="{x+175}" y="{y+4}" font-family="monospace" font-size="12">{label}</text></svg>')
        factor=min(1,740/width);drawing.scale(factor,factor);drawing.width=width*factor;drawing.height=h*factor
        story.append(KeepTogether([Paragraph(f'Network {net["order"]} {net["output"]}',styles['Heading2']),drawing,Spacer(1,12)]))
        htmlnets.append(f'<section><h2>Network {net["order"]} {net["output"]}</h2><code>{net["output"]} = {net["expression"]}</code>'+''.join(svg)+'</section>')
    def footer(c,d):c.setFont('Helvetica',8);c.drawString(35,20,'EE-2401 | FBD design representation | '+str(d.page))
    SimpleDocTemplate(str(DESIGN/'Elevator_FBD_Program.pdf'),pagesize=landscape(A4),leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=35).build(story,onFirstPage=footer,onLaterPages=footer)
    (DESIGN/'FBD_networks.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Elevator FBD program</title><style>body{font:16px Arial;margin:35px;color:#183247}section{border-top:1px solid #ccc;padding:15px 0}svg{display:block;width:min(100%,1500px);margin-top:12px}code{overflow-wrap:anywhere}@media print{section{break-inside:avoid}}</style><h1>Three floor elevator FBD program</h1><p>EE-2401 · Izbassar Yesbol · Kuanysh Kali. Ordered AND OR NOT and TON networks. FBD design representation verified against LD; not a native TriLOGI executable.</p>'+''.join(htmlnets)+'</html>',encoding='utf-8')
    print('Generated complete FBD diagrams and vector PDF')

if __name__=='__main__':check();generate()
