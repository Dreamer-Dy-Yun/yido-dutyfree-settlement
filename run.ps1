# Windows 한글 경로 등에서 [Errno 42] 방지 - UTF-8 모드로 실행
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$localPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$parentPython = Join-Path (Split-Path -Parent $scriptDir) "venv\Scripts\python.exe"

if (Test-Path $localPython) {
    & $localPython main.py
} elseif (Test-Path $parentPython) {
    & $parentPython main.py
} else {
    python main.py
}

exit $LASTEXITCODE
