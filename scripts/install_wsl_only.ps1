$ErrorActionPreference = 'Continue'
wsl.exe --install --no-distribution
Write-Output "WSL_INSTALL_EXIT=$LASTEXITCODE"
wsl.exe --status
