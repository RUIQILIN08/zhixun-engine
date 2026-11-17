$ErrorActionPreference = 'Continue'
Write-Output '== enable Microsoft-Hyper-V-All =='
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
Write-Output "HYPERV_DISM_EXIT=$LASTEXITCODE"
