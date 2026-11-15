"""Build the final course report from verified native and HMI evidence."""
from pathlib import Path
import csv,json,shutil,hashlib,re
from docx import Document
from docx.shared import Cm,Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from build_package import ROOT,OUT,QA,MAIN,INS,OUTS
from build_native_tests import SCENARIOS

for n in range(1,10):assert (QA/f'native_T{n}.png').exists(),f'Native T{n} evidence missing'
assert json.loads((QA/'hmi_browser_results.json').read_text())['result']=='PASS'
assert json.loads((OUT/'Evidence/FBD_equivalence.json').read_text())['result']=='PASS'
EVID=OUT/'Evidence';EVID.mkdir(exist_ok=True)
for pattern in ['native_*.png','hmi_*.png','connected_*.png','connected_results.json','connected_link_results.json','normal_trace.json','door_jam_trace.json','trace_results.json','hmi_browser_results.json','reference_model_results.csv']:
    for f in QA.glob(pattern):shutil.copy2(f,EVID/f.name)

doc=Document()
# Preserve original PNG pixels in Word and PDF; no automatic picture downsampling.
no_compress=OxmlElement('w:doNotAutoCompressPictures');doc.settings.element.append(no_compress)
default_dpi=OxmlElement('w14:defaultImageDpi');default_dpi.set(qn('w14:val'),'600');doc.settings.element.append(default_dpi)
sec=doc.sections[0];sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.7);sec.left_margin=Cm(2);sec.right_margin=Cm(2)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
    sty=doc.styles[name];sty.font.name='Arial';sty.font.color.rgb=RGBColor(0,0,0)
    for b in list(sty._element.iter(qn('w:pBdr'))):b.getparent().remove(b)
doc.styles['Normal'].font.size=Pt(11);doc.styles['Normal'].paragraph_format.line_spacing=1.08;doc.styles['Normal'].paragraph_format.space_after=Pt(7);doc.styles['Normal'].paragraph_format.keep_with_next=False
doc.styles['Title'].font.size=Pt(27);doc.styles['Heading 1'].font.size=Pt(17);doc.styles['Heading 2'].font.size=Pt(12)
doc.styles['Caption'].font.size=Pt(9);doc.styles['Caption'].font.italic=True
footer=sec.footer.paragraphs[0];footer.alignment=2;footer.add_run('EE-2401 | Industrial Automation | ')
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)

def p(text,style=None):return doc.add_paragraph(text,style)
NEED_PAGE=False
def h(text):
    global NEED_PAGE
    par=doc.add_heading(text,1)
    if NEED_PAGE:par.paragraph_format.page_break_before=True;NEED_PAGE=False
    return par
def h2(text):return doc.add_heading(text,2)
def page():
    global NEED_PAGE
    NEED_PAGE=True
FIGURE=0
def caption(text):
    global FIGURE
    FIGURE+=1
    p(f'Figure {FIGURE}. '+re.sub(r'^Figure \d+\.\s*','',text),'Caption')
FIGS=OUT/'Design/Engineering_Figures'
def image(file,width=6.35):
    par=doc.add_paragraph();par.alignment=1;par.add_run().add_picture(str(file),width=Inches(width))
def table(headers,rows,widths=None,size=9.5):
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for i,text in enumerate(headers):t.rows[0].cells[i].text=text
    for values in rows:
        for cell,text in zip(t.add_row().cells,values):cell.text=str(text)
    for ri,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        for ci,c in enumerate(row.cells):
            if widths:c.width=Cm(widths[ci])
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tc=c._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E6EDF3' if ri==0 else 'FFFFFF');tc.append(shade)
            borders=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
            tc.append(borders)
            margins=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                m=OxmlElement('w:'+side);m.set(qn('w:w'),'70');m.set(qn('w:type'),'dxa');margins.append(m)
            tc.append(margins)
            for par in c.paragraphs:
                par.paragraph_format.space_before=Pt(1);par.paragraph_format.space_after=Pt(2);par.paragraph_format.line_spacing=1.02
                if ci==0 and len(headers)>2:par.alignment=1
                for r in par.runs:r.font.size=Pt(size);r.bold=ri==0
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    p('')
    return t
def link(label,target):
    par=doc.add_paragraph();rel=par.part.relate_to(target,RT.HYPERLINK,is_external=True);hy=OxmlElement('w:hyperlink');hy.set(qn('r:id'),rel);run=OxmlElement('w:r');props=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'185980');props.append(color);run.append(props);text=OxmlElement('w:t');text.text=label;run.append(text);hy.append(run);par._p.append(hy)

p('ASTANA IT UNIVERSITY','Subtitle');p('School of Intelligent Systems','Subtitle');p('Industrial Automation','Subtitle')
p('Three Floor Elevator Control System','Title')
p('Final Course Project Report','Subtitle');p('PLC programming and simulation with an operator interface')
p('Group EE-2401\nIzbassar Yesbol\nKuanysh Kali\n\nCourse instructor\nGulnara Abitova PhD\n\n12 November 2026')
h2('Project deliverables')
p('The accompanying package contains the native TriLOGI ladder controller, a repeatable native verification suite, the complete FBD diagrams, a Node-RED HMI project, input and output schedules, test evidence, and operating instructions.')
link('Open the working ladder program','TriLOGI_Projects/01_Three_Floor_Elevator_LD.PC7')
link('Open the connected live HMI ladder program','TriLOGI_Projects/05_Connected_Elevator_MQTT.PC7')
link('Open the complete FBD program diagrams','Design/Elevator_FBD_Program.pdf')

page();h('Abstract')
p('This project develops a three-level automation design for an elevator serving three floors. The process receives hall and cabin requests, stores pending destinations, selects a travel direction, stops at requested floors, and controls opening, dwell and closing of the door. Field devices are represented by digital floor switches, door endpoint switches, a light curtain, pushbuttons, and actuator commands. A Triangle Research FMD1616-10 family PLC is selected as a physical design candidate on the basis of 15 digital inputs and six digital outputs.')
p('The controller is implemented as 68 Ladder Diagram networks in i-TRiLOGI. A second representation uses Function Block Diagram networks with AND, OR, NOT and non-retentive timer blocks. Their signal values agree over 5,931 comparison scans. Nine scenarios execute in the native TriLOGI simulator using the unchanged ladder equations and timers, with scripted virtual field signals. The scenarios cover a normal trip, queued stops, direction reversal, obstruction, door closing timeout, emergency stop, conflicting sensors, loss of door confirmation, travel timeout and recovery opening timeout. All nine native scenario assertions pass.')
p('A local Node-RED application with FlowFuse Dashboard provides an animated operator interface and fault controls. MQTT links it directly to the running TriLOGI simulator. The native ladder executes all control decisions; Node-RED simulates cabin and door mechanics, sends field feedback and displays native telemetry. Connection monitoring blocks stale commands. Mechanical dynamics, passenger lift certification and real equipment safety verification remain outside the scope.')
p('Keywords: industrial automation, PLC, elevator, Ladder Diagram, Function Block Diagram, Node-RED, HMI, interlocks.')
h2('Report organisation')
p('The report first defines the process, requirements, architecture and I/O. It then explains the LD and FBD control strategy, presents native simulation results, documents the HMI, and evaluates reliability, limitations and improvements. The final sections contain conclusions, references, team responsibility allocation and the AI-use disclosure.')

page();h('1 Introduction and project objectives')
p('A small elevator is a useful example of discrete industrial automation because motion depends on both stored operator requests and current feedback. A controller must maintain destinations after buttons are released, prevent opposite movement commands, sequence the doors, and respond to failures without an unintended restart. These decisions can be demonstrated through a bounded three-floor simulation.')
p('The objective is to design, program and verify a three-floor elevator control model that combines field signals, PLC logic and an operator interface. This follows Topic 7 and the final project requirements supplied for the Industrial Automation course [1, 2].')
h2('Engineering tasks')
p('The design defines ten verifiable requirements, selects instrumentation and a PLC family, allocates every digital signal, implements the control strategy in LD, represents the same logic in FBD, verifies normal and abnormal behaviour, and provides an HMI screen with its tag mapping. The simulation results are recorded as expected and observed outcomes with native screenshots.')
h2('Process boundary and assumptions')
p('One cabin serves Floors 1, 2 and 3. Each landing has a single call button; the cabin has three destination buttons. There are no separate upward and downward hall buttons. Both button sets feed the same three request memories. The initial cabin location is Floor 1 and the initial door condition is closed.')
p('Exactly one floor sensor is true when the cabin is at a landing. All three may be false between floors. The last confirmed floor is retained separately. Door-open and door-closed feedback may both be false while the door moves, but may never both be true. All memory is treated as non-retentive on a fresh simulator run. Requests entered while disabled, or pending when a fault occurs, are discarded.')
p('The PLC model has no measured continuous cabin position, acceleration, brake, speed control or levelling algorithm. The HMI plant model uses a continuous position only to create animation and discrete field events. A physical lift would need independently engineered drive, brake, door-lock and safety circuits.')

page();h('1 1 Process schematic and signal boundary')
image(FIGS/'A_Process_Schematic.png');caption('Conceptual three-floor process. DI and DO numbers refer to the standalone controller allocation; the connected simulator represents the same channels as field relays.')
p('A landing is confirmed by its own floor switch. Between landings, all floor switches are inactive and the last confirmed floor remains in POS1 to POS3. Hall and cabin buttons set the same destination memories. Motor commands act through separate upward and downward interfaces; door movement has separate open and close commands and independent endpoint feedback.')
p('The schematic identifies the process signals, not a construction-ready installation. Start and Reset occupy DI14 and DI15; the three cabin buttons occupy DI4 to DI6. No measured continuous position, physical brake or passenger rescue mechanism is represented. This boundary keeps the control problem small enough for complete signal allocation and repeatable fault tests.')

requirements=[
('R1','Latch hall and cabin requests on rising edges.','A released button leaves REQn pending until the door is confirmed open at that floor.','T1 T2'),
('R2','Serve pending requests in the preferred direction.','Stop at Floor 2 before Floor 3; reverse for a later Floor 1 request.','T2'),
('R3','Prevent simultaneous UP and DOWN commands.','The two outputs are mutually exclusive throughout execution.','T1 to T9'),
('R4','Require a confirmed closed door for travel.','Loss of closed feedback or obstruction during travel stops motion and latches a fault.','T7'),
('R5','Stop at a requested landing.','The arrival sensor removes the travel command and starts opening.','T1 T2'),
('R6','Sequence opening, dwell and closing.','Confirmed open starts a 5 s dwell; endpoint feedback completes closing.','T1'),
('R7','Reopen and alarm on closing obstruction or jam.','Obstruction or an 8 s closing timeout blocks travel, sounds the buzzer logically and commands reopening.','T3 T4'),
('R8','Detect sensor and actuator failures.','Contradictory sensors, missing travel arrival in 15 s, or missing recovery-open feedback in 8 s produce a latched fault.','T6 T8 T9'),
('R9','Require deliberate recovery.','Reset is refused with unresolved conditions or unknown floor; a separate Start is required after a valid reset.','T3 T4 T5'),
('R10','Show the required operator information.','HMI shows floor confirmation, direction, requests, door feedback, commands and fault categories.','HMI review')]
page();h('2 Functional requirements and design parameters')
table(['ID','Requirement','Acceptance criterion','Verification'],requirements,[.9,5,8.1,3],9)
table(['Parameter','Design setting','Reason'],[
('Floors','3','Small, bounded discrete process.'),('Door dwell','5 s','Provides an observable boarding interval.'),('Open and close timeout','8 s each','Detects missing endpoint feedback.'),('Recovery opening timeout','8 s','Prevents indefinite reopening command after a second failure.'),('Travel timeout','15 s per travel state','Detects failure to reach an arrival sensor.'),('Request policy','Direction preference with intermediate stops','Avoids losing calls while keeping the dispatcher simple.')],[4,4,9],9.5)
p('Timer values are educational design settings, not certified lift timing values. TriLOGI normal timers use 0.1 s units: 50 represents 5 s, 80 represents 8 s and 150 represents 15 s [3].')

page();h('3 Three level automation architecture')
table(['Level','Elements','Connection to the next level'],[
('Field','Call buttons, floor switches, door switches, obstruction detector, E-stop status, motor and door command interfaces.','Digital field states feed Input 1 to Input 15. Output 1 to Output 6 represent actuator and alarm commands.'),
('Control','PLC inputs, request memory, state machine, timers, fault latches and output permissives.','PLC states and commands have named HMI tags. Commands enter through defined request or operator inputs.'),
('Supervisory','Node-RED and FlowFuse Dashboard with the operator screen, indicators, commands and event history.','Local MQTT exchanges field inputs and native control states with the running TriLOGI ladder. Node-RED simulates field mechanics only.')],[2.7,7.2,7.1])
h2('Instrumentation and actuators')
table(['Element','Qty','Design characteristics','Selection justification'],[
('Floor detectors','3','24 V DC discrete proximity or position switches; one active landing at a time.','Floor confirmation is sufficient for the bounded process; no analog encoder is required.'),
('Door endpoint switches','2','Discrete fully-open and fully-closed signals; separate channels.','Enable endpoint validation, travel interlocking and timeout detection.'),
('Obstruction detector','1','Photoelectric light curtain represented by a blocked/not-blocked input.','Provides the required reopen interlock during closing.'),
('Request buttons','6','Momentary normally-open contacts, three hall and three cabin.','Edge detection captures a call without requiring a held button.'),
('Start and Reset','2','Separate momentary controls.','Reset acknowledgement cannot substitute for a new Start.'),
('E-stop status','1','ESTOP_OK = 1 represents a healthy circuit.','Loss of the status blocks motion; hardware safety functionality is outside this model.'),
('Motor and door interfaces','4','Two direction commands for each drive, with suitable interposing interfaces.','Separates low-power PLC commands from actuator power switching.'),
('Lamp and buzzer','2','Discrete alarm indication commands.','Makes a latched failure visible and provides the required buzzer signal.')],[3.2,.8,6.6,6.4],9)
p('These are design specifications. NPN-compatible signal interfaces and normal states are specified in Section 4 1. The submitted simulation has no connected physical actuators.')

page();h('3 1 Architecture diagram and implementation')
image(FIGS/'B_Three_Level_Architecture.png');caption('Mandatory three-level architecture and the local virtual implementation. Field feedback, output commands and HMI states have distinct responsibilities.')
p('In a physical installation the field signals would be electrical I/O. In the demonstration, Node-RED simulates the field mechanics and carries operator commands, while the actual TriLOGI process executes the control program. Local MQTT transports virtual field inputs and native control telemetry. The browser does not decide which motor or door command should turn on.')
p('The connected file replaces physical input terminals with internal field relays, but preserves the same 68 controller equations and their order. Its communication adapter applies received input values before the ladder core and publishes native states after the core. The field model moves only from received native output commands and holds when telemetry becomes stale.')

page();h('4 PLC selection and I O allocation')
p('The proposed controller family is Triangle Research FMD1616-10. Manufacturer documentation states that the unit has 16 digital inputs and 16 digital outputs and supports i-TRiLOGI programming [4, 5]. The process requires 15 DI and 6 DO, leaving one DI and ten DO unused. The small input reserve is a limitation: additional independent door-lock or drive feedback would require expansion.')
p('An indoor control cabinet and a regulated 24 V DC supply are assumed. Field interfaces must be selected for the actual controller input polarity and output ratings. PLC outputs represent commands; they do not prove motor or door movement. TriLOGI simulator numbering starts at Input 1 and Output 1; it is not a Siemens I/Q address map.')
descs=['Hall call Floor 1','Hall call Floor 2','Hall call Floor 3','Cabin request Floor 1','Cabin request Floor 2','Cabin request Floor 3','Cabin at Floor 1','Cabin at Floor 2','Cabin at Floor 3','Door fully open','Door fully closed','Door path obstructed','E-stop circuit healthy','Enable operation on a rising edge','Reset corrected fault on a rising edge']
table(['Address','Tag','Signal meaning when true'],[(str(i+1),tag,descs[i]) for i,tag in enumerate(INS)],[1.8,4.8,10.4],9)
table(['Output','Tag','Command'],[(str(i+1),tag,text) for i,(tag,text) in enumerate(zip(OUTS,['Travel upward','Travel downward','Open door','Close door','Alarm lamp','Alarm buzzer']))],[1.8,4.8,10.4],9)

page();h('4 1 PLC alternatives and electrical interfaces')
table(['PLC option','Built in DI DO','Assessment for 15 DI and 6 DO'],[
('FMD88-10','8 DI / 8 DO','Insufficient built-in inputs; would need expansion [10].'),
('FMD1616-10','16 DI / 16 DO','Selected for the bounded standalone LD design: one spare DI, ten spare DO [4, 5].'),
('Fx2424','24 DI / 24 DO','More expansion reserve: nine spare DI, eighteen spare DO. Preferable if extra feedback is added [11].')],[3.4,3.1,10.5],9.5)
p('The selection minimizes unused built-in input capacity for this educational scope; it is not a certified passenger-lift controller selection. All analog channels remain unused. An indoor cabinet at nominal 20 to 30 C with a regulated 24 V DC supply is a design assumption. Additional door-lock or contactor feedback would consume the last input or require expansion.')
table(['Signal group','Specified interface and normal state'],[
('Floor and door limits','24 V powered NPN sensors or dry contacts to 0 V. Logical TRUE means the corresponding endpoint is reached.'),
('Call Start Reset','Momentary NO dry contacts to 0 V; released = FALSE. Logical rising edges capture button commands.'),
('OBSTRUCT','An isolated interface asserts TRUE when the simulated path is blocked. A physical light curtain requires a suitable independent safety interface.'),
('ESTOP_OK','Healthy diagnostic contact closed to 0 V = TRUE; opening or a broken diagnostic wire = FALSE.'),
('Six output interfaces','NPN sinking outputs drive 24 V interposing relay or driver inputs, design target at most 20 mA per interface. Motor power uses separate contactors/drives.')],[4.1,12.9],9)
image(FIGS/'D_Electrical_Interface.png',6.15);caption('Conceptual NPN-compatible signal interface. Input thresholds follow the FMD manual; the 20 mA interface target is a conservative design choice, not the PLC maximum rating [5].')
p('The manual defines logical ON at 0 to 2.5 V and OFF for an open input or 10 to 24 V. Use external suppression on inductive DC coils and match the actual board revision before construction [5].')

page();h('5 Control sequence and interlocks')
table(['State','Action','Transition'],[
('IDLE','Wait at a known floor.','A current-floor request starts opening; another request dispatches travel only with the door closed. Start with an open door first initiates closing.'),
('UP_RUN','Command upward travel.','A requested floor or the top-floor sensor starts opening.'),
('DOWN_RUN','Command downward travel.','A requested floor or the bottom-floor sensor starts opening.'),
('OPENING','Command the door open.','Open feedback starts DWELL; an 8 s timeout produces a hard door fault.'),
('DWELL','Hold the door open.','After 5 s and a clear path, begin CLOSING.'),
('CLOSING','Command the door closed.','Closed feedback returns to IDLE; obstruction or timeout initiates alarmed recovery opening.'),
('REOPEN overlay','Open after a closing obstruction or timeout.','Open feedback removes the opening command; the jam alarm remains latched. A second opening timeout stops the command.')],[2.8,4.4,9.8],9.5)
h2('Requests and dispatcher')
p('Independent rising-edge detectors capture the six request buttons. REQ1 to REQ3 retain the destinations until OPENING or DWELL confirms an open door at the corresponding floor. A held button does not continuously requeue a served request. POS1 to POS3 retain the last confirmed floor. ABOVE and BELOW indicate remaining requests relative to that position. The dispatcher prefers the previous direction when both sides have pending requests; startup preference is upward.')
h2('Fault priority and recovery')
p('A closing obstruction or timeout latches JAM_FLT, removes RUN_EN, blocks both travel commands, activates ALARM and BUZZER, and attempts recovery opening at a valid floor. Recovery opening is permitted only with a healthy E-stop status, no hard fault and no travel state. The open endpoint stops the recovery command. If it is not reached within 8 s, DOOR_FLT becomes a hard fault and opening stops.')
p('E-stop loss, contradictory sensors, door confirmation loss during travel and travel timeout have higher priority. Reset requires a known floor, a valid door endpoint, a clear path, no active fault cause, no active recovery opening, and Start released. Reset leaves the system disabled. A separate Start enables it; if the door is open, closing completes before travel can begin.')

page();h('5 1 Sequence diagram and abnormal operation')
image(FIGS/'C_State_Sequence.png');caption('Main operating path with jam recovery and hard-fault priority. The accompanying state table defines the additional startup and recovery conditions.')
p('The diagram summarizes the normal path. At a requested landing, travel stops before the opening command is issued. Confirmed open starts the dwell interval; a clear path and the completed dwell allow closing. Confirmed closed returns the process to dispatch. A Start with an already-open door first enters closing, so no travel command is issued with an open door.')
p('JAM_FLT is distinct from a hard fault. A closing obstruction or timeout requests recovery opening only at a valid floor with healthy E-stop status and no hard fault. If recovery opening also times out, all door commands stop. Reset removes a corrected fault, but the run-enable latch stays off until a new Start. These conditions are checked in native tests T3 to T9.')

page();h('6 PLC program in LD and FBD')
p('The working program is 01_Three_Floor_Elevator_LD.PC7. It contains 68 ladder networks. Timers and faults are evaluated before request handling and dispatch. All next-state bits are calculated before current states are assigned, preventing several sequence transitions from cascading through a single scan. Output permissives are evaluated last. Numbered complete listings accompany the native file.')
table(['Network group','Implementation purpose'],[
('Edges','Start, Reset, hall request and cabin request edge detection.'),('Timers and faults','Five non-retentive timers, sensor validation, fault categories and recovery opening.'),('Position and requests','Last confirmed floor, served flags and latched request memory.'),('Dispatch and states','Direction preference, arrival conditions and next-state calculation.'),('Outputs','Mutually exclusive travel and door commands; latched alarm indication.')],[4,13])
h2('Equivalent Function Block Diagram representation')
p('The second representation is FBD. Each ladder expression is represented with explicit AND, OR and NOT blocks and named feedback wires. The five timer networks use non-retentive TON blocks with the same settings. Networks execute in numbered order, with named wires reading the value available at that point. This preserves the stored-memory and scan-order behaviour of the ladder program.')
p('Design/Elevator_FBD_Program.pdf and Design/FBD_networks.html contain the complete graphical representation. The machine-readable gate graph is in FBD_networks.json. An independently evaluated graph matches all controller signals over 5,931 scans, including the nine scheduled scenarios and randomized inputs. The executed native project is LD; FBD is supplied as the second diagram type permitted by the course requirements [1]. The test harness TBASIC and HMI JavaScript are supporting tools and are not counted as the second PLC language.')
link('Complete LD source listing','TriLOGI_Projects/01_Three_Floor_Elevator_LD_listing.txt')
link('Complete FBD network diagrams','Design/Elevator_FBD_Program.pdf')

page();h('6 1 Graphical program evidence')
image(QA/'native_main_compile.png',3.5)
caption('Successful native compilation of the final 68-network controller. The program uses no TBASIC custom functions; the separate test fixture supplies the scripted stimulus.')
image(QA/'fbd_excerpt.png',6.35)
caption('Excerpt from the complete FBD diagram set: a served-floor condition and its request memory. The full set preserves the ordered logic and timer settings of the LD controller.')

page();h('7 Simulation and verification method')
p('Verification uses three distinct forms of evidence. Native tests execute in i-TRiLOGI 7.52 Build 07 Educational. FBD equivalence tests compare a gate-graph evaluator with the ordered ladder equations. HMI tests run the Node-RED dashboard in an isolated browser context and exercise actual operator controls. These evidence types are identified separately throughout the report.')
h2('Repeatable native test fixture')
p('04_Native_Verification_Suite.PC7 contains the unchanged 68 controller rung equations and the same five native timers. Its virtual field signals are internal relays instead of manually operated physical input channels. TBASIC test functions set those field relays according to a published event schedule and check controller states and outputs after the ladder executes. This removes human timing variability from the normal and fault sequences.')
p('At the end of each successful scenario, its Tn_PASS output latches and the fixture waits. NEXT_TEST starts the next case. FAILED stops progress and records the case and tick in DM[90] and DM[91]. A separate invariant check rejects simultaneous UP/DOWN commands and simultaneous door OPEN/CLOSE commands. ALL_PASS is set only after all nine scenarios complete. The detailed stimulus, checkpoints and expected signal values are included in native_test_scenarios.json and the harness listing.')
p('The screenshot for each test shows the native simulator at the held end condition, with its pass output active and FAILED inactive. The pass bit records all scheduled assertions for that scenario, including intermediate states that are no longer displayed at the final hold point. The suite tests the controller logic under virtual field assumptions; it does not validate real mechanical dynamics or a physical safety function.')
table(['Verification','Result','Evidence'],[
('Native TriLOGI scenarios','9 of 9 passed','Screenshots T1 to T9 and the native verification suite.'),('Reference checks','12 checks passed','Controller, request memory and randomized invariants in reference_model_results.csv.'),('LD to FBD comparison','5,931 matching scans','FBD_equivalence.json; all Boolean and timer signals compared.'),('Connected HMI checks','See section 12','connected_results.json and connected_link_results.json; actual native MQTT exchange.')],[4.2,4.4,8.4])

testdetails=[
('Startup at Floor 1, door closed and E-stop healthy.','Enable; request Floor 3; simulate departure, Floor 2 passage and Floor 3 arrival, then door endpoints.','UP starts and stops at Floor 3. The door opens, dwells for 5 s and closes. REQ3 clears.','Native checkpoints confirmed MOTOR_UP and REQ3, OPENING at Floor 3, DWELL with REQ3 cleared, CLOSING and final IDLE with RUN_EN. T1_PASS is active.'),
('Enabled at Floor 1 with closed door.','Request Floors 2 and 3. Serve both door cycles; then request Floor 1.','Serve Floor 2 before Floor 3, preserve REQ3 through the first stop, and travel downward for the later Floor 1 request.','Native checkpoints confirmed the intermediate stop, retained REQ3, upward continuation, downward command and completion at Floor 1. T2_PASS is active.'),
('Cabin stationary at Floor 1; door cycle reaches closing.','Activate obstruction during closing; confirm open; try Reset while obstructed; clear obstruction, Reset and Start.','Closing stops, alarm and buzzer latch, reopening is commanded and travel remains disabled. Reset while blocked is refused; valid Reset still requires Start.','Native checkpoints confirmed JAM_FLT, REOPEN, DOOR_OP_CMD and BUZZER with motor and close commands off. Blocked reset was refused; corrected reset and separate Start restored the closed-door idle state. T3_PASS is active.'),
('Cabin at Floor 1; closing begins with endpoint feedback inactive.','Withhold DOOR_CLOSED beyond 8 s. Confirm recovery-open feedback, Reset and Start.','Closing timeout blocks motion, latches a jam alarm and buzzer, and commands reopening. Recovery requires valid Reset and separate Start.','Native checkpoints confirmed JAM_FLT, REOPEN and opening command after the timeout. Open feedback ended recovery opening; Reset did not enable operation; separate Start closed the door. T4_PASS is active.'),
('Cabin travelling upward between floors.','Remove ESTOP_OK, restore it, attempt Reset between floors, then restore a known floor and perform Reset and Start.','Movement stops immediately. Release alone and an unknown-position reset cannot restart the cabin.','Native checkpoints confirmed ESTOP_FLT and FAULT with travel off, rejected reset between floors, and deliberate recovery at a known floor. T5_PASS is active.'),
('Enabled cabin at Floor 1 with closed door.','Activate FLOOR2 while FLOOR1 remains true.','Contradictory floor feedback latches SENSOR_FLT and blocks all actuator commands.','Native checkpoints confirmed SENSOR_FLT and FAULT; both travel commands and both door commands were off. T6_PASS is active.'),
('Cabin travelling upward with closed-door feedback.','Remove DOOR_CLOSED.','Travel stops and a hard door fault latches; no recovery movement is attempted between floors.','Native checkpoints confirmed DOOR_FLT and FAULT with both motor directions and opening command off. T7_PASS is active.'),
('Cabin travelling after a Floor 3 request.','Withhold arrival feedback for more than 15 s.','TRAVEL_FLT, FAULT and buzzer latch; RUN_EN and travel outputs switch off.','Native checkpoints confirmed TRAVEL_FLT, FAULT and BUZZER with both motor directions and RUN_EN off. T8_PASS is active.'),
('Cabin at a floor; obstruction has initiated recovery opening.','Withhold DOOR_OPEN for more than 8 s during recovery.','A hard door fault stops the recovery command; the jam remains latched and travel stays disabled.','Native checkpoints first confirmed recovery opening, then DOOR_FLT, HARD_FAULT and JAM_FLT with all motor and door commands off. T9_PASS and ALL_PASS are active.')]

results=[]
for i,(case,detail) in enumerate(zip(SCENARIOS,testdetails),1):
    page();h(f'7 {i} '+case['name'])
    initial,event,expected,observed=detail
    rows=[('Initial condition',initial),('Input',event),('Expected result',expected),('Observed result',observed),('Conclusion','PASS. The scheduled native assertions satisfy the expected logical behaviour.')]
    table(['Test record','Description'],rows,[3,14],9.5)
    image(QA/f'native_T{i}.png',6.35)
    caption(f'Figure {i}. Actual i-TRiLOGI verification screenshot for T{i}. Red output T{i}_PASS records success; FAILED remains inactive. Outputs from earlier passed cases remain latched.')
    results.append(dict(test=case['name'],initial_condition=initial,input=event,expected_result=expected,observed_result=observed,conclusion='PASS',screenshot=f'Evidence/native_T{i}.png',method='Native TriLOGI fixture with unchanged controller equations and timers'))
(OUT/'Evidence/native_test_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
with (OUT/'Test_Results.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)

page();h('7 10 Recorded native timing evidence')
trace=json.loads((QA/'trace_results.json').read_text())
assert trace['result']=='PASS'
image(FIGS/'E_Normal_Recorded_Timing.png',6.4);caption('Normal connected trip recorded from actual native TriLOGI telemetry. The door cycle follows arrival at Floor 3; zero and one are shown as low and high levels.')
image(FIGS/'F_Jam_Recorded_Timing.png',6.4);caption('Recorded closing jam, alarm, recovery opening and deliberate reset. Both charts use elapsed capture wall time; they are not idealized timing sketches.')
p(f"The jam timeout spans {trace['closing_timeout_native_ticks']} native 100 ms clock events, matching the nominal 8 s preset. The recorded wall interval was {trace['closing_timeout_wall_s']:.3f} s. Simulator scheduling and blocking MQTT work can stretch wall time; this is not a hard real-time controller measurement. CSV traces and original JSON samples are supplied for inspection.")

page();h('8 HMI application and operator screen')
p('The selected HMI environment is Node-RED 5.0.9 with FlowFuse Dashboard 1.36.1, also called Node-RED Dashboard 2.0 [6, 7]. It runs locally and provides a browser operator screen. The complete flow is delivered as HMI_Node_RED/flows.json with settings, pinned package versions and a Windows launch script. An initial npm installation needs internet access; subsequent operation uses the installed local packages.')
image(QA/'connected_travelling.png',6.4);caption('Figure 10. Running HMI during native ladder controlled travel. The connection indicator identifies TriLOGI and MQTT; the field mechanics are simulated.')
p('The cabin animation, floor call buttons, cabin destinations, direction, request indicators, door position, output lamps and event history support a visually clear demonstration. Between floors, confirmed floor is shown as a dash and last confirmed floor is displayed separately. Continuous animation position belongs to the plant model, not a PLC position measurement.')

page();h('8 1 HMI signals commands and alarms')
table(['Screen element','Controller or model tags','Operator use'],[
('Confirmed and last floor','FLOOR1 to FLOOR3; POS1 to POS3','Distinguish a confirmed landing from travel between floors.'),('Direction and pending calls','MOTOR_UP, MOTOR_DOWN; REQ1 to REQ3','See current travel and stored destinations.'),('Door state','DOOR_OPEN, DOOR_CLOSED, OPENING, DWELL, CLOSING, REOPEN','Observe commands separately from endpoint feedback.'),('Alarm banner','FAULT, ESTOP_FLT, SENSOR_FLT, DOOR_FLT, TRAVEL_FLT, JAM_FLT','Identify why operation is blocked.'),('Start Reset destinations','START, RESET, CAB1 to CAB3; hall calls mapped to the same destination memories','Issue pulses into controller inputs instead of writing output coils.'),('Fault controls','OBSTRUCT, ESTOP_OK and simulated actuator or sensor failures','Create repeatable demonstrations of abnormal conditions.'),('History and clock','Simulated state transitions and elapsed model time','Follow the sequence and discuss fault timing.')],[3.6,6.6,6.8],9)
image(QA/'connected_jam_reopening.png',5.3);caption('Figure 11. Connected HMI after the native closing timeout. TriLOGI commands recovery opening and latches the alarm until a valid Reset.')
p('The interface exchanges live data with TriLOGI over localhost MQTT. The connected PC7 wraps the unchanged 68 controller networks with communication functions. Commands and simulated sensors become field relays; motor, door and alarm outputs and all displayed control states are read from native telemetry. See section 12 for protocol, watchdogs and connected verification.')

page();h('9 System evaluation and improvements')
h2('Integration and reliability')
p('The I/O table traces every field signal to the controller, and the HMI tag map traces every displayed state and command. Request memory separates momentary inputs from service decisions. Next-state calculations make the sequence explicit. Door feedback gates travel, conflicting sensors cause a fault, and actuator timeouts detect missing feedback. The mandatory closing fault is handled as alarmed recovery opening, with a separate limit for recovery failure.')
h2('Safety and practical limits')
p('The simulation demonstrates logical interlocks under stated assumptions. It does not prove physical equipment safety. The model omits independent door-lock confirmation, drive and contactor feedback, mechanical braking, overspeed protection, final limits, overload protection and rescue control. ESTOP_OK is only a simulated status; a real E-stop function would require an independent engineered safety circuit. A command or screen animation is not proof of physical actuator movement.')
p('The simplified direction policy has one hall call per landing and does not distinguish passenger travel direction. Position is confirmed only by discrete sensors. Reset is deliberately refused at an unknown position; the native fixture restores a known landing for recovery, while the HMI New demonstration command restores initial simulated conditions. Neither action is a real passenger rescue procedure.')
h2('Recommended improvements')
p('A physical extension should add independent door-lock proof, travel limits, motor and brake feedback, stuck-sensor diagnostics and a documented recovery procedure. The connected HMI already monitors native telemetry and communication loss; a real PLC driver would require hardware commissioning and command acknowledgement beyond simulated relay feedback. More floors would require an expanded dispatcher and I/O design.')
h2('Requirement coverage')
p('R1, R2 and R5 are covered by normal and queued service tests. R3 is checked by the native output invariant and all scenarios. R4 and R8 are exercised by explicit fault tests. R6 and R7 are covered by timed door cycles and recovery opening. R9 is checked through invalid and valid reset sequences. R10 is covered by the running HMI review and browser control tests. The delivered FBD graph separately confirms equivalent representation of the controller logic.')

page();h('10 Conclusion')
p('The project achieves the bounded design objective: a three-floor elevator control model with stored requests, direction selection, door sequencing, interlocks and fault handling. Nine native scenarios pass. The FBD representation matches LD over 5,931 scans. The Node-RED HMI exchanges live MQTT data with the running native ladder, with connected normal, queued, fault, recovery and communication-loss tests recorded separately.')
p('The package documents the technical deliverables for process requirements, three-level architecture, instrumentation and PLC selection, I/O allocation, two PLC diagram types, simulation evidence, HMI design and evaluation. Submission also requires a truthful account of individual contribution and compliance with the instructor\'s AI-use rules. The result remains a virtual educational design with the physical limitations stated in the report.')
h('References')
references=[
 '[1] Abitova G. Final Course Project Requirements and Assessment. Supplied course PDF. English pages 2 to 5. Requirements, diagram types, verification, HMI and assessment rubric.',
 '[2] Abitova G. Final Project Topics List EN RU. Supplied course PDF. Topic 7 Elevator Lift Control System, English page 6.',
 '[3] Triangle Research International. i-TRiLOGI Editor Compiler Simulator and reference manual. https://docs.triplc.com/i-trilogi/ Accessed 12 November 2026.',
 '[4] Triangle Research International. FMD1616-10 PLC product information. https://triplc.com/~triplc/fmd161610.htm Accessed 12 November 2026.',
 '[5] Triangle Research International. FMD1616-10 User Manual, Chapter 1 Installation Guide. https://triplc.com/documents/FMD1616-10-UserManual.pdf Accessed 12 November 2026.',
 '[6] OpenJS Foundation. About Node-RED. https://nodered.org/about/ Accessed 12 November 2026.',
 '[7] FlowFuse. Dashboard getting started and ui-template documentation. https://dashboard.flowfuse.com/getting-started.html and https://dashboard.flowfuse.com/nodes/widgets/ui-template.html Accessed 12 November 2026.',
 '[8] Abitova G. Final Project Ready Example Water Tank EN RU. Supplied course worked example. Used for report and test-record structure; the water-tank controller was not reused.',
 '[9] Triangle Research International. MQTT Quickstart 1 Connect Wx100 to HiveMQ. https://triplc.com/documents/MQTT_Quickstart1-Connect_Wx100_to_HiveMQ.pdf Accessed 12 November 2026.',
 '[10] Triangle Research International. FMD88-10 Product Information Sheet Rev 3. https://triplc.com/documents/FMD88-10_Product_Info_Sheet.pdf Accessed 12 November 2026.',
 '[11] Triangle Research International. Fx2424 PLC product specifications. https://triplc.com/fx2424.htm Accessed 12 November 2026.'
]
for ref in references:p(ref)

page();h('11 Team responsibility and AI use disclosure')
p('Authors: Izbassar Yesbol and Kuanysh Kali. Group: EE-2401. The table below allocates responsibility for reviewing, explaining and demonstrating the delivered material. It is a proposed defence allocation, not a fabricated log of individual work already performed. No personal hours, percentages or unobserved student activities are claimed.')
table(['Team member','Review and demonstration responsibility','Evidence to explain'],[
('Izbassar Yesbol','Process requirements, I/O, PLC selection, LD and FBD logic, normal operation and request scheduling.','Controller project, diagrams, native tests T1 and T2, and the signal allocation.'),
('Kuanysh Kali','HMI operation, door interlocks, alarm recovery, fault verification and system limitations.','Node-RED flow, HMI screenshots, native tests T3 to T9 and recovery rules.'),
('Both authors','Check the final submission, understand the full sequence and answer individual technical questions.','Complete report, program files and test evidence.')],[3.2,7.3,6.5],10)
h2('AI use disclosure')
p('OpenAI Codex assisted with design exploration, generation and revision of the report, ladder project files, FBD networks, HMI source, test stimulus and automated checks. The package records which tests were executed natively and which were model or browser checks. The materials are AI-assisted; no claim is made that either student independently authored every generated artifact or has already completed a personal review.')
p('The course policy requires instructor authorization for permitted AI uses, disclosure of actual use and substantial student understanding and contribution [1]. The authors must ensure the submitted disclosure and any individual contribution statement accurately reflect their own work and the authorization applicable to their course. This report does not assert that such authorization has been granted.')
h2('Defence preparation')
p('The accompanying Russian defence guide gives a concise demonstration sequence and technical questions to practise. Each author should be able to trace a request through its memory, selected state and output permissives; explain why Reset does not restart the lift; distinguish a jam recovery from a hard fault; and identify the limits of the HMI simulation and the FBD representation.')

page();h('12 Live HMI connection and demonstration')
p('The connected demonstration runs 05_Connected_Elevator_MQTT.PC7 in i-TRiLOGI 7.52 Educational. Its 68 control networks are identical to the main LD controller. Four adapter networks initialize MQTT, subscribe to field input frames, apply received field values before the controller scan, and publish telemetry after the controller scan. Five TBASIC functions implement this adapter. The connected mode does not evaluate PLC equations in JavaScript.')
table(['Direction','Endpoint and message','Purpose'],[
('HMI to PLC','127.0.0.1:1889; ee2401/elevator/field; 15 binary characters in I/O list order.','100 ms field feedback frames include 400 ms operator button pulses.'),
('PLC to HMI','ee2401/elevator/state; 41 binary state values followed by transmit and receive counters.','Native outputs, request memories, floor memories, states and alarms. Design/MQTT_signal_map.json defines every bit.'),
('Connection health','HMI freshness limit 1.2 s; PLC field age limit 20 native 100 ms clock ticks.','Stale HMI data blocks commands and holds the field model. Missing field frames force ESTOP_OK false and latch the native alarm.')],[3.0,7.2,6.8],9.5)
p('A local Aedes broker binds only to 127.0.0.1. Both clients use MQTT 3.1.1 without retained command frames. No internet connection is needed after package installation. The adapter retries lost connections and periodically renews its field subscription; this also restores input exchange after a full Node-RED flow redeploy. Counter rollover is bounded and field age saturates. After a communication fault, corrected conditions, Reset and a separate Start are required.')
p('The selected FMD1616-10 remains the base I/O design candidate for the standalone ladder. This MQTT adapter targets the simulator and the Wx100 MQTT command set [9]; it is not a claim that FMD hardware implements those MQTT instructions. A physical FMD installation would require a suitable gateway or driver. The connected simulator uses internal field relays in place of physical input terminals.')
h2('Demonstration sequence')
p('Run START_DEMO.bat. It opens the connected PC7 and HMI. If TriLOGI asks whether to run the program, click Yes; otherwise press Ctrl+F9. Wait for TRILOGI CONNECTED, then Reset alarm and Start. Show a 1 to 3 trip, queue floors 2 and 3, then inject Door closing jam at a landing. Explain the native timeout, alarm and reopening; remove the jam, Reset and Start. Finally pause TriLOGI to show PLC DISCONNECTED and blocked commands. Keep the native simulator beside the HMI to compare output bits. Reconnection can take up to 15 s.')
p('Evidence/connected_results.json and connected_link_results.json record live snapshots and counters. T1 to T9 remain the separate native regression fixture.')

page();h('12 1 Connected verification evidence')
connected=json.loads((QA/'connected_results.json').read_text())
links=json.loads((QA/'connected_link_results.json').read_text())
assert connected['result']=='PASS' and links['result']=='PASS'
table(['Connected check','Observed result'],[(x['test'],x['result']) for x in connected['checks']+links['checks']],[13.8,3.2],9)
image(QA/'connected_disconnected.png',4.0);caption('Figure 12. HMI after pausing the actual TriLOGI simulator. Stale telemetry blocks movement controls.')

path=OUT/'Final_Project_Report_EE2401_Yesbol_Kali.docx';doc.core_properties.author='Izbassar Yesbol; Kuanysh Kali';doc.core_properties.title='Three Floor Elevator Control System';doc.core_properties.subject='Industrial Automation final course project EE-2401';doc.save(path)
print('Created',path,'with native and HMI evidence')

with (OUT/'I_O_List.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Address','Tag','Type','Meaning']);w.writerows([(f'Input {i+1}',tag,'DI',descs[i]) for i,tag in enumerate(INS)]);w.writerows([(f'Output {i+1}',tag,'DO',tag) for i,tag in enumerate(OUTS)])
