param([string]$OutputFolder = 'dist/VirtualLibrary-Final')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m PyInstaller --noconfirm --windowed --onefile --collect-data pymupdf --add-data "web;web" --distpath build/single --name VirtualLibrary main.py
if ($LASTEXITCODE -ne 0) { throw '打包失败' }
& ./publish.ps1 -OutputFolder $OutputFolder
