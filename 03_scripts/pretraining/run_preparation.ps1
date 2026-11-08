$ErrorActionPreference='Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
python 03_scripts/pretraining/build_1km_features.py
if ($LASTEXITCODE -ne 0) { throw 'Feature construction failed' }
python 03_scripts/pretraining/enrich_road_features.py
if ($LASTEXITCODE -ne 0) { throw 'Road enrichment failed' }
python 03_scripts/pretraining/audit_traffic_summary.py
python 03_scripts/pretraining/finalize_inputs.py
if ($LASTEXITCODE -ne 0) { throw 'Finalization failed' }
python 03_scripts/pretraining/prepare_training.py --check-only
if ($LASTEXITCODE -ne 0) { throw 'Preparation checks failed' }
python 03_scripts/pretraining/verify_inputs.py
if ($LASTEXITCODE -ne 0) { throw 'Integrity checks failed' }
Write-Output 'Preparation finished. No model was fitted. Read04_outputs/pretraining/readiness.json for data gates.'
