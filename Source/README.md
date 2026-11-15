# Source and verification
The delivered HMI runs connected-engine.js inside its Node-RED function. It simulates cabin and door mechanics and displays native TriLOGI outputs. It does not evaluate PLC ladder equations.
engine.js is a separate reference model used in development, not the live controller.
After Word PDF export, embed_full_resolution_images.py restores the original DOCX image pixels in PDF image streams and verifies the decoded pixels. This prevents Word export downsampling; it does not synthesize or sharpen screenshot details.
The generators assume the original development workspace layout. Starting the portable demonstration with START_DEMO.bat does not require Python or these generators.
Browser QA requires Playwright. ELEVATOR_PLAYWRIGHT_MODULE may point to its installed module. qa_connected.cjs changes simulated operating conditions; qa_capture_trace.cjs records native telemetry. qa_link.cjs temporarily interrupts field heartbeat and restores the saved flow in a finally block. Its paused and resumed modes require an actual simulator pause and resume.
