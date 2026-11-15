$ErrorActionPreference='Stop'
$reportPath=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'deliverables/Final_Project_Report_EE2401_Yesbol_Kali.docx'))
$pdfPath=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'deliverables/Final_Project_Report_EE2401_Yesbol_Kali.pdf'))
$wordApp=New-Object -ComObject Word.Application
$wordApp.Visible=$false
$wordApp.DisplayAlerts=0
try {
  $reportDoc=$wordApp.Documents.Open($reportPath,$false,$true)
  try {
    $reportDoc.ExportAsFixedFormat($pdfPath,17)
    Write-Output "Exported $pdfPath"
    Write-Output "Pages: $($reportDoc.ComputeStatistics(2))"
  } finally {
    $reportDoc.Close(0)
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($reportDoc)
  }
} finally {
  $wordApp.Quit()
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp)
}
