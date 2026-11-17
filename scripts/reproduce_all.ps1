$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$python = Join-Path $root '.venv-platform\Scripts\python.exe'
$script = Join-Path $root 'scripts\reproduce_baseline.py'

$profiles = @{
  'A' = Join-Path $root 'platform\packages\A'
  'B' = Join-Path $root 'platform\packages\B'
  'C' = Join-Path $root 'platform\packages\C'
}

foreach ($profile in $profiles.Keys) {
  Write-Output "===== PROFILE $profile ====="
  & $python $script --package $profiles[$profile] --output (Join-Path $root "platform\reproduction\$profile")
  if ($LASTEXITCODE -ne 0) {
    Write-Output "PROFILE $profile FAILED"
    exit $LASTEXITCODE
  }
}
