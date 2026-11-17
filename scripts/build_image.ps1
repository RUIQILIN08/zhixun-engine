$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
docker build -f harness\Dockerfile -t zhixun-engine:0.1 .
Write-Output 'build complete: zhixun-engine:0.1'

