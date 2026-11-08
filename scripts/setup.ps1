$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 environment creation failed.' }
}
& .venv/Scripts/python.exe -m pip install -r backend/requirements-workspace.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Backend installation failed.' }
Push-Location web
try {
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed.' }
} finally { Pop-Location }
Write-Output 'Run .venv/Scripts/python.exe scripts/dev.py to start Kerquant.'
