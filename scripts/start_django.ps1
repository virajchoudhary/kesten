$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& .venv/Scripts/python.exe scripts/dev.py --api-only
exit $LASTEXITCODE
