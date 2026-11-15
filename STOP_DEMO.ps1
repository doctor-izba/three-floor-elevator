$ErrorActionPreference='Stop'
$hmiDir=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'HMI_Node_RED'))
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -in 1888,1889 | ForEach-Object {
    $demoProcess=Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)"
    if ($demoProcess.Name -eq 'node.exe' -and $demoProcess.CommandLine.IndexOf($hmiDir,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
        Stop-Process -Id $demoProcess.ProcessId -ErrorAction SilentlyContinue
    }
}
Write-Host 'Stopped the Node-RED and broker processes belonging to this package.'
