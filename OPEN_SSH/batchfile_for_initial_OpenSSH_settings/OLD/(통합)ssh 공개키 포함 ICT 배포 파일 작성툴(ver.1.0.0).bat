:: Tool name : (통합)ssh 공개키 포함 ICT 배포 파일 작성툴(ver.1.0.0)
:: Written by : 윤대영
:: Contact : Dreamer.Dy.Yun@gmail.com
:: Created at : 2025.06.26
:: Updated at : 2025.06.26
:: Supported by : ChatGPT-4o, ChatGPT-o3


@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: [1] SSH 키 경로 설정
set "SSH_KEY_DIR=%USERPROFILE%\.ssh"
set "SSH_PRIVATE_KEY_PATH=%SSH_KEY_DIR%\id_rsa"
set "SSH_PUBLIC_KEY_PATH=%SSH_PRIVATE_KEY_PATH%.pub"
set "SSH_DEPLOY_SCRIPT_PATH=%USERPROFILE%\Desktop\setup_ssh_accept_from_server.bat"

echo [🔧] SSH 키 디렉토리: %SSH_KEY_DIR%
echo [🔧] 개인키 경로: %SSH_PRIVATE_KEY_PATH%
echo [🔧] 공개키 경로: %SSH_PUBLIC_KEY_PATH%
echo.

:: [2] 공개키 없으면 키 생성
if not exist "%SSH_PUBLIC_KEY_PATH%" (
    echo [!] 공개키가 존재하지 않습니다. 새로 생성합니다.
    powershell -Command "Start-Process -NoNewWindow -Wait -FilePath 'ssh-keygen.exe' -ArgumentList '-t rsa -b 4096 -C pulling-server -f \"%SSH_PRIVATE_KEY_PATH%\" -N \"\"'"
)
echo [🔍] 공개키 생성 여부 확인 중...

:: [3] 키 생성 실패 시 종료
if not exist "%SSH_PUBLIC_KEY_PATH%" (
    echo [❌] 공개키 생성 실패. 관리자 권한 또는 ssh-keygen 설치 확인 필요.
    pause
    exit /b
)

echo [✅] SSH 키 쌍 생성 완료!
echo.

:: [4] 공개키 내용 로딩
set "SSH_PUBLIC_KEY_CONTENT="
for /f "usebackq delims=" %%A in ("%SSH_PUBLIC_KEY_PATH%") do (
    set "SSH_PUBLIC_KEY_CONTENT=%%A"
)

echo [📄] 공개키 내용:
echo !SSH_PUBLIC_KEY_CONTENT!
echo.

:: [5] 배포용 설치 스크립트 생성
echo [📦] 배포용 설치 스크립트 생성 중...


::=========================================================
:: 1. 최초 줄은 덮어쓰기
echo @echo off > "%SSH_DEPLOY_SCRIPT_PATH%"
echo chcp 65001 ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo setlocal enabledelayedexpansion >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo echo [🚀] OpenSSH 서버 상태 확인 및 구성 시작... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "$cap = Get-WindowsCapability -Online | Where-Object { $_.Name -like 'OpenSSH.Server*' }; if ($cap.State -ne 'Installed') { Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' }" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Start-Service sshd" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Set-Service sshd -StartupType Automatic" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "if (-not (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -EA 0)) { New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (TCP-In)' -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 }" >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo echo [🔁] 부팅시 ssh 서버 자동 시작 설정... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Set-Service -Name sshd -StartupType Automatic" >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo echo [🔐] 공개키 등록 중... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo set "sshdir=%%USERPROFILE%%\.ssh" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo mkdir "%%sshdir%%" ^>nul 2^>^&1 >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo if not exist "%%sshdir%%\authorized_keys" type nul ^> "%%sshdir%%\authorized_keys" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "$key='%SSH_PUBLIC_KEY_CONTENT%'; $f = Join-Path $env:USERPROFILE '.ssh\authorized_keys'; if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force | Out-Null }; if (-not ((Get-Content -Raw $f) -match [regex]::Escape($key))) { Add-Content -Path $f -Value $key }" >> "%SSH_DEPLOY_SCRIPT_PATH%"


:: 권한 설정 및 접속 정보 안내
echo icacls "%%sshdir%%" /inheritance:r ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo icacls "%%sshdir%%" /grant "%%USERNAME%%:R" ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo icacls "%%sshdir%%\authorized_keys" /grant "%%USERNAME%%:R" ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"


echo echo [✅] SSH 서버 구성 및 키 등록 완료. >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo echo [🔗] 접속 정보 복사... >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo for /f "tokens=2 delims=:" %%%%i in ('ipconfig ^^^^^| findstr /i "IPv4"') do (set "IP=%%%%i" ^& set "IP=^!IP: =^!") >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo set connect=ssh %%USERNAME%%@%%IP%% >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo echo 아래 내용을 운영자에게 전달해 주세요.(클립보드에 자동 복사됨) >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo echo %%connect%% >> "%SSH_DEPLOY_SCRIPT_PATH%"
:: 클립보드 복사
echo powershell -NoProfile -Command "Set-Clipboard -Value '%%connect%%'" >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo pause >> "%SSH_DEPLOY_SCRIPT_PATH%"
::=========================================================

:: [6] 완료 안내
echo.
echo [✅] 배포용 설치 스크립트가 바탕화면에 생성되었습니다:
echo     %SSH_DEPLOY_SCRIPT_PATH%
explorer "%USERPROFILE%\Desktop"
pause
