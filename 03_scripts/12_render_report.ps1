$ErrorActionPreference='Stop'
$qa = Join-Path (Get-Location) '06_reports\_qa\final_report'
New-Item -ItemType Directory -Force -Path $qa | Out-Null
$docPath = Join-Path (Get-Location) '06_reports\SSCI575_Grid_Methods_and_Validation_Report.docx'
$word = New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
try {
 $doc=$word.Documents.Open($docPath,$false,$true)
 $doc.Repaginate()
 $count=$doc.ComputeStatistics(2)
 Write-Output ('Pages: '+$count)
 $doc.ExportAsFixedFormat((Join-Path $qa 'report.pdf'),17)
 $doc.Close(0)
} finally { $word.Quit() }
& 'C:\Users\czy08\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe' -scale-to 1400 -png (Join-Path $qa 'report.pdf') (Join-Path $qa 'page')
