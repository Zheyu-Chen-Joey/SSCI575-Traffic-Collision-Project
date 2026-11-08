$ErrorActionPreference='Stop'
$src=Join-Path (Get-Location) '06_reports\presentations\SSCI575_Presentation2_Downloads_Minimal_Final.pptx'
$dest=Join-Path (Get-Location) '06_reports\_qa\ppt_downloads_minimal'
New-Item -ItemType Directory -Force $dest | Out-Null
$app=New-Object -ComObject PowerPoint.Application
try { $deck=$app.Presentations.Open($src,$true,$false,$false); $deck.Export($dest,'PNG',1200,900); $deck.Close() } finally { $app.Quit() }

