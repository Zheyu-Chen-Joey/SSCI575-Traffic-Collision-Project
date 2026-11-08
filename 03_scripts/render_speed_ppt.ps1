$ErrorActionPreference='Stop'
$src=Join-Path (Get-Location) '06_reports\presentations\SSCI575_Presentation2_1km_SpeedAudit_Final.pptx'
$dest=Join-Path (Get-Location) '06_reports\_qa\ppt_speed_audit'
New-Item -ItemType Directory -Force $dest | Out-Null
$app=New-Object -ComObject PowerPoint.Application
try { $deck=$app.Presentations.Open($src,$true,$false,$false); $deck.Export($dest,'PNG',1200,900); $deck.Close() } finally { $app.Quit() }

