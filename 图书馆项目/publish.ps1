param([string]$OutputFolder = 'dist/VirtualLibrary-Final')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force $OutputFolder | Out-Null
Copy-Item -LiteralPath build/single/VirtualLibrary.exe -Destination (Join-Path $OutputFolder 'VirtualLibrary.exe') -Force
Copy-Item README.md,DEVELOPMENT_LOG.md -Destination $OutputFolder -Force
# No developer personal paths or book data are shipped. First launch initializes them.
