$ErrorActionPreference = 'Continue'

Write-Output '== enable Microsoft-Windows-Subsystem-Linux =='
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
Write-Output "SUB_DISM_EXIT=$LASTEXITCODE"

Write-Output '== enable VirtualMachinePlatform =='
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
Write-Output "VMP_DISM_EXIT=$LASTEXITCODE"

Write-Output '== wsl update =='
wsl.exe --update
Write-Output "WSL_UPDATE_EXIT=$LASTEXITCODE"

Write-Output '== wsl status =='
wsl.exe --status
Write-Output "WSL_STATUS_EXIT=$LASTEXITCODE"
