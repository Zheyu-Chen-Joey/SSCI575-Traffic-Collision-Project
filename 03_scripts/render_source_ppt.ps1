$ErrorActionPreference='Stop'
$src='C:\Users\czy08\Desktop\SSCI575_Presentation2_Traffic_Project_USC_Template.pptx'
$dest=Join-Path (Get-Location) '06_reports\_qa\ppt_source'
$app=New-Object -ComObject PowerPoint.Application
try { $deck=$app.Presentations.Open($src,$true,$false,$false); $deck.Export($dest,'PNG',1200,900); $deck.Close() } finally { $app.Quit() }
