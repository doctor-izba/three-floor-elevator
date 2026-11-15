param([switch]$CheckOnly)
$ErrorActionPreference='Stop'
$demoRoot=$PSScriptRoot
$hmiDir=Join-Path $demoRoot 'HMI_Node_RED'
$projectPath=Join-Path $demoRoot 'TriLOGI_Projects/05_Connected_Elevator_MQTT.PC7'
if (!(Test-Path -LiteralPath $projectPath)) { throw 'Extract the complete project ZIP before launching START_DEMO.bat.' }
$nodeExe=(Get-Command node -ErrorAction Stop).Source
if ([int]((& $nodeExe --version).TrimStart('v').Split('.')[0]) -lt 22) { throw 'Install Node.js 22 or newer first.' }
$triDir=@('C:\TRiLOGI\TL75Edu','C:\TRiLOGI\TL75','C:\TRiLOGI\TL7x') | Where-Object { (Test-Path (Join-Path $_ 'TL75Edu.jar')) -or (Test-Path (Join-Path $_ 'TL75.jar')) -or (Test-Path (Join-Path $_ 'TL7x.jar')) } | Select-Object -First 1
if (!$triDir) { throw 'i-TRiLOGI 7.5+ was not found in C:\TRiLOGI. Install it before starting this demonstration.' }
$triJar=Get-ChildItem -LiteralPath $triDir -Filter '*.jar' | Where-Object Name -in 'TL75Edu.jar','TL75.jar','TL7x.jar' | Select-Object -First 1 -ExpandProperty FullName
$javaExe=Join-Path (Split-Path $triDir -Parent) 'jre8/bin/javaw.exe'
if (!(Test-Path -LiteralPath $javaExe)) { $javaExe=(Get-Command javaw -ErrorAction Stop).Source }
if ($CheckOnly) {
    Write-Host "Node: $nodeExe"
    Write-Host "TriLOGI: $triJar"
    Write-Host "Project: $projectPath"
    Write-Host 'Launch prerequisites verified.'
    exit 0
}
if (!(Test-Path (Join-Path $hmiDir 'node_modules/aedes')) -or !(Test-Path (Join-Path $hmiDir 'node_modules/node-red/red.js'))) {
    Push-Location $hmiDir
    try { & npm.cmd ci --no-audit --no-fund; if ($LASTEXITCODE -ne 0) { throw 'npm installation failed.' } } finally { Pop-Location }
}
$running=$false
try { $running=(Invoke-RestMethod 'http://127.0.0.1:1888/elevator/api/state' -TimeoutSec 2).connection.source -like '*TriLOGI*' } catch {}
if (!$running) {
    Start-Process -FilePath $nodeExe -ArgumentList ('"'+(Join-Path $hmiDir 'start-connected.cjs')+'"') -WorkingDirectory $hmiDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $hmiDir 'demo.log') -RedirectStandardError (Join-Path $hmiDir 'demo-error.log') | Out-Null
    for ($demoAttempt=0;$demoAttempt -lt 30;$demoAttempt++) {
        Start-Sleep -Milliseconds 500
        try { $state=Invoke-RestMethod 'http://127.0.0.1:1888/elevator/api/state' -TimeoutSec 1; if ($state.connection) { $running=$true; break } } catch {}
    }
}
if (!$running) { throw 'HMI did not start. See HMI_Node_RED/demo-error.log. Close any older HMI using port 1888.' }
$nativeAlreadyOpen=Get-CimInstance Win32_Process -Filter "Name='java.exe' OR Name='javaw.exe' OR Name='TL75Edu.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*05_Connected_Elevator_MQTT.PC7*' } | Select-Object -First 1
if (!$nativeAlreadyOpen) {
    $nativeAlreadyOpen=Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in 'java','javaw','TL75Edu','TL75','TL7x' -and $_.MainWindowTitle -like '*05_Connected_Elevator_MQTT*' } | Select-Object -First 1
}
if (!$nativeAlreadyOpen) {
    Start-Process -FilePath $javaExe -ArgumentList ('-jar "'+$triJar+'" "'+$projectPath+'"') -WorkingDirectory $triDir
}
Start-Process 'http://127.0.0.1:1888/dashboard/elevator'
Write-Host 'HMI, local broker and TriLOGI are open.'
Write-Host 'If TriLOGI asks "Run this program now?", click Yes.'
Write-Host 'Choose Simulate > Run (All I/O Reset), or press Ctrl+F9.'
Write-Host 'Wait for TRILOGI CONNECTED, then press Reset alarm and Start on the HMI.'
Write-Host 'Use only one instance of the connected PLC project.'
