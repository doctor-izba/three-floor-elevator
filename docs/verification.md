# Verification record

The files below record checks performed during development. Native ladder execution, browser checks and model comparisons measure different parts of the project.

| Check | Record | Scope |
| --- | --- | --- |
| Native regression suite | [Test_Results.csv](../Test_Results.csv), [native_test_results.json](../Evidence/native_test_results.json) | Nine scenarios executed in the TriLOGI simulator; screenshots T1–T9 are in Evidence |
| Connected operator panel | [connected_results.json](../Evidence/connected_results.json) | Recorded HMI interaction with native PLC telemetry |
| Communication loss | [connected_link_results.json](../Evidence/connected_link_results.json) | Recorded heartbeat interruption and recovery checks |
| FBD equivalence | [FBD_equivalence.json](../Evidence/FBD_equivalence.json) | 68 networks, 5,931 compared scans; does not execute an FBD project in a PLC IDE |
| Controller identity | [native_fixture_identity.json](../Evidence/native_fixture_identity.json) | Identity of the controller and test fixture used for the recorded tests |

For a native rerun, open `TriLOGI_Projects/04_Native_Verification_Suite.PC7` and press Ctrl+F9. T1 starts automatically. Pulse NEXT_TEST after each pass. Check T1_PASS through T9_PASS and ALL_PASS; FAILED should remain off. This fixture is separate from the connected demonstration.

## Video scope

[Elevator_Live_Demo.webm](../Presentation/Elevator_Live_Demo.webm) is a silent 40.68-second recording at 1440×1100 and 25 fps. It shows a connected HMI: travel from floor 1 to 3, arrival and door opening, a closing jam with reopening, Reset, a separate Start, and E-stop.

An earlier recording attempt failed during a queued stop at floor 2: the field model stopped at 2.05 and subsequently raised DOOR_FLT. This load-sensitive case remains open. Previous passing records do not override that later observation. See [the video notes](../Presentation/VIDEO_NOTES_RU.md).

## Reproducibility

The runnable demonstration uses the checked-in PC7 projects and Node-RED flow. npm dependencies are pinned in the lockfile. The Python files under Source are development scripts retained for inspection; some assume the original workspace layout and are not a single-command build system for this repository.

`SHA256_manifest.json` covers the original delivered package files, which are copied without alteration. It is not a checksum list for the additional repository documentation. `PUBLIC_FILES_SHA256.json` covers the publication snapshot, excluding itself and Git metadata.
