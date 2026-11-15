# Three Floor Elevator Control System
EE-2401 — Izbassar Yesbol and Kuanysh Kali

The HMI is connected to the actual running i-TRiLOGI simulator over local MQTT. TriLOGI executes the control logic. Node-RED supplies simulated cabin and door mechanics and displays native PLC states.

## Start the connected demonstration

1. Extract the entire ZIP to a folder. Install Node.js 22 or newer and i-TRiLOGI 7.5 Educational if they are not already installed.
2. Run START_DEMO.bat. Its first run installs pinned npm packages and needs internet. Subsequent runs operate locally. It starts Node-RED and a broker bound to localhost, opens TriLOGI with the connected PC7, and opens the dashboard.
3. If TriLOGI asks "Run this program now using the Simulator?", click Yes. Otherwise press Ctrl+F9, or Simulate → Run (All I/O Reset). Use one instance of this connected project.
4. Open http://127.0.0.1:1888/dashboard/elevator and wait for TRILOGI CONNECTED and increasing TX/RX counters. A repeated simulator restart can take up to 15 seconds while its old MQTT session closes.
5. Press Reset alarm, wait for the alarm to clear, then Start. Initial ESTOP_FLT records the interval before the first healthy field frame arrives.
6. Choose a destination. The field model automatically generates floor and door sensors; no manual sensor clicking is required in this connected file.

The main standalone controller is 01_Three_Floor_Elevator_LD.PC7. The connected file wraps the same 68 control networks with four communication networks. Its field channels are internal relays driven by MQTT, so do not manually override these relays during the connected demonstration.

## Files

- Final_Project_Report_EE2401_Yesbol_Kali.pdf and .docx: report with Abstract, architecture, I/O, LD/FBD, native tests, live HMI integration, evaluation and disclosure.
- TriLOGI_Projects/01_Three_Floor_Elevator_LD.PC7: standalone LD controller with physical input allocation.
- TriLOGI_Projects/03_Request_Memory_Bench_LD.PC7: optional small request-memory bench.
- TriLOGI_Projects/04_Native_Verification_Suite.PC7: nine native regression scenarios. Ctrl+F9 starts T1; pulse NEXT_TEST after each pass. T1_PASS through T9_PASS and ALL_PASS must light; FAILED must remain off.
- TriLOGI_Projects/05_Connected_Elevator_MQTT.PC7: use this file for the live HMI demonstration.
- Design/: complete 68-network FBD diagrams, graph and MQTT bit mapping. FBD is a second diagram representation, not a native TriLOGI FBD executable.
- HMI_Node_RED/: flows, local broker, pinned dependencies and launch files. Node-RED editor: http://127.0.0.1:1888/ .
- Evidence/: screenshots, nine native regression results, connected browser checks, link-loss tests and FBD equivalence.
- Defence_Guide_RU.md: practical Russian demonstration script and technical questions.
- Source/: generators and supporting scripts. To regenerate the connected HMI, build_hmi.py creates the base flow and build_connected.py then installs the connected adapter.

## Connection behaviour

The localhost broker is on port 1889. The field topic is ee2401/elevator/field; native telemetry is ee2401/elevator/state. All command frames are non-retained. Field frames are sent every 100 ms. HMI freshness is limited to 1.2 seconds. Missing field frames force native ESTOP_OK false after 20 native clock ticks, nominally 2 seconds. Simulator timing can slow under load and is not a hard real-time guarantee. Recovery requires corrected conditions, Reset and a separate Start.

Keep the broker and Node-RED running while demonstrating. If disconnected, check that the connected PC7 is running and not paused. The adapter retries lost connections and periodically renews its field subscription. After resuming a long pause, allow about 15 seconds for reconnection before troubleshooting; simulator scheduling can vary. A fresh Ctrl+F9 reconnects the MQTT session. If you opened another connected instance, close it and restart the remaining simulator. Reset is refused when the cabin is between floors; Restore field to floor 1 is an explicit educational reset of the simulated mechanics, not a real lift rescue function.

After the demonstration, run STOP_DEMO.cmd to stop this package's Node-RED and local broker. The TriLOGI simulator is closed separately.

The FMD1616-10 is the base physical I/O design candidate. The MQTT adapter uses simulator/Wx100 instructions and is not an FMD hardware MQTT implementation. No real lift hardware or certified safety controller is connected.

The report contains a truthful AI-use disclosure and a proposed defence responsibility allocation. Authors must understand the material and make personal contribution statements match their actual work.
