@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo # Tool name 	: (Integrated) SSH deploy-script generator (ver.1.1.1)
echo # Written by 	: Yun Dae-young
echo # Contact   	: Dreamer.Dy.Yun@gmail.com
echo # Created at 	: 2025.06.26
echo # Updated at 	: 2025.11.14
echo # Note 		: Uses both CMD and PowerShell for "Run as administrator" scenario
echo # 2025.11.14 	: Changed languge from Kor to Eng
echo ============================================================

REM ============================================================
REM [1] SSH key path settings
REM ============================================================

set "SSH_KEY_DIR=%USERPROFILE%\.ssh"
set "SSH_PRIVATE_KEY_PATH=%SSH_KEY_DIR%\id_rsa"
set "SSH_PUBLIC_KEY_PATH=%SSH_PRIVATE_KEY_PATH%.pub"
set "SSH_DEPLOY_SCRIPT_PATH=%USERPROFILE%\Desktop\setup_ssh_accept_from_server.bat"

echo [INFO] SSH key directory  : %SSH_KEY_DIR%
echo [INFO] Private key path   : %SSH_PRIVATE_KEY_PATH%
echo [INFO] Public  key path   : %SSH_PUBLIC_KEY_PATH%
echo.

REM ============================================================
REM [2] Generate public key if missing
REM ============================================================

echo [STEP] Checking SSH key pair...

REM Ensure .ssh directory exists
if not exist "%SSH_KEY_DIR%" (
    echo [INFO] .ssh directory does not exist. Creating...
    mkdir "%SSH_KEY_DIR%"
)

REM If public key does not exist, generate key pair
if not exist "%SSH_PUBLIC_KEY_PATH%" (
    echo [INFO] Public key not found. Generating new RSA key pair...
    ssh-keygen -t rsa -b 4096 -C "pulling-server" -f "%SSH_PRIVATE_KEY_PATH%" -N ""
)

echo [STEP] Verifying public key existence...

REM Abort if key generation failed
if not exist "%SSH_PUBLIC_KEY_PATH%" (
    echo [ERROR] SSH public key creation failed.
    echo         Please check permissions or ssh-keygen installation.
    pause
    exit /b
)

echo [OK] SSH key pair is ready.
echo.

REM ============================================================
REM [3] Load public key (single-line)
REM ============================================================

set "SSH_PUBLIC_KEY_CONTENT="
for /f "usebackq delims=" %%A in ("%SSH_PUBLIC_KEY_PATH%") do (
    set "SSH_PUBLIC_KEY_CONTENT=%%A"
)

echo [INFO] Loaded public key:
echo !SSH_PUBLIC_KEY_CONTENT!
echo.

REM ============================================================
REM [4] Create deploy script (to run on target host)
REM ============================================================

echo [INFO] Creating deploy script on Desktop...
echo.

REM 4-1. Create base of deploy script
echo @echo off > "%SSH_DEPLOY_SCRIPT_PATH%"
echo setlocal enabledelayedexpansion>> "%SSH_DEPLOY_SCRIPT_PATH%"

REM 4-2. OpenSSH server installation and basic service settings
echo echo [INFO] Checking and installing OpenSSH Server if needed... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "$cap = Get-WindowsCapability -Online ^| Where-Object { $_.Name -like 'OpenSSH.Server*' }; if ($cap.State -ne 'Installed') { Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' }" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Start-Service sshd" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Set-Service sshd -StartupType Automatic" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "if (-not (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -EA 0)) { New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (TCP-In)' -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 }" >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo echo [INFO] Ensuring sshd service starts automatically on boot... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Set-Service -Name sshd -StartupType Automatic" >> "%SSH_DEPLOY_SCRIPT_PATH%"

REM ============================================================
REM [5] Register public key for current user (USER scope)
REM ============================================================

echo echo [INFO] Registering public key for CURRENT USER scope... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo set "sshdir=%%USERPROFILE%%\.ssh" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo mkdir "%%sshdir%%" ^>nul 2^>^&1 >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo if not exist "%%sshdir%%\authorized_keys" type nul ^> "%%sshdir%%\authorized_keys" >> "%SSH_DEPLOY_SCRIPT_PATH%"

set "msg_succeed=    >> [OK] User authorized_keys updated."
set "msg_failed=    >> [ERROR] User authorized_keys update failed."
set "pscmd="
set "pscmd=%pscmd% $key='%SSH_PUBLIC_KEY_CONTENT%';"
set "pscmd=%pscmd% $f = Join-Path $env:USERPROFILE '.ssh\authorized_keys';"
set "pscmd=%pscmd% if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force ^| Out-Null };"
set "pscmd=%pscmd% if (-not ((Get-Content -Raw $f) -match [regex]::Escape($key))) { Add-Content -Path $f -Value $key };"
set "pscmd=%pscmd% if ((Get-Content -Raw $f) -match [regex]::Escape($key)) { Write-Host '%msg_succeed%' `n '    >> path : ' $f } else { Write-Host '%msg_failed%' }"

echo powershell -NoProfile -Command "%pscmd%" >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo icacls "%%sshdir%%" /inheritance:r ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo icacls "%%sshdir%%" /grant "%%USERNAME%%:F" ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo icacls "%%sshdir%%\authorized_keys" /grant "%%USERNAME%%:F" ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"

REM ============================================================
REM [6] Register public key for ADMIN scope
REM ============================================================

echo echo [INFO] Registering public key for ADMIN scope... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo set "sshdir=%%PROGRAMDATA%%\ssh" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo mkdir "%%sshdir%%" ^>nul 2^>^&1 >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo if not exist "%%sshdir%%\administrators_authorized_keys" type nul ^> "%%sshdir%%\administrators_authorized_keys" >> "%SSH_DEPLOY_SCRIPT_PATH%"

set "msg_succeed=    >> [OK] Admin authorized_keys updated."
set "msg_failed=    >> [ERROR] Admin authorized_keys update failed."
set "pscmd="
set "pscmd=%pscmd% $key='%SSH_PUBLIC_KEY_CONTENT%';"
set "pscmd=%pscmd% $f = Join-Path $env:ProgramData 'ssh\administrators_authorized_keys';"
set "pscmd=%pscmd% if (-not (Test-Path $f)) { New-Item -ItemType File -Path $f -Force ^| Out-Null };"
set "pscmd=%pscmd% if (-not ((Get-Content -Raw $f) -match [regex]::Escape($key))) { Add-Content -Path $f -Value $key };"
set "pscmd=%pscmd% if ((Get-Content -Raw $f) -match [regex]::Escape($key)) { Write-Host '%msg_succeed%' `n '    >> path : ' $f } else { Write-Host '%msg_failed%' }"

echo powershell -NoProfile -Command "%pscmd%" >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo icacls "%%sshdir%%" /inheritance:r ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo icacls "%%sshdir%%" /grant "Administrators:F" ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo icacls "%%sshdir%%\administrators_authorized_keys" /grant "%%USERNAME%%:F" ^>nul >> "%SSH_DEPLOY_SCRIPT_PATH%"

echo echo [INFO] SSH server configuration and key registration finished. >> "%SSH_DEPLOY_SCRIPT_PATH%"

REM ============================================================
REM [7] Firewall rule for port 22
REM ============================================================

echo echo [INFO] Adding firewall rule for port 22... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo netsh advfirewall firewall add rule name="Open Port 22 SSH" dir=in action=allow protocol=TCP localport=22 >> "%SSH_DEPLOY_SCRIPT_PATH%"

REM ============================================================
REM [8] Show SSH connection string and copy to clipboard
REM ============================================================

echo echo [INFO] Preparing SSH connection string... >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo for /f "tokens=2 delims=:" %%%%i in ('ipconfig ^^^^^| findstr /i "IPv4"') do (set "IP=%%%%i" ^& set "IP=^!IP: =^!") >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo set CONNECT=ssh %%USERNAME%%@%%IP%% >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo echo Please send the following connection string to the operator. >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo echo %%CONNECT%% >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo powershell -NoProfile -Command "Set-Clipboard -Value '%%CONNECT%%'" >> "%SSH_DEPLOY_SCRIPT_PATH%"
echo pause >> "%SSH_DEPLOY_SCRIPT_PATH%"

REM ============================================================
REM [9] Done
REM ============================================================

echo.
echo [OK] Deploy script created on Desktop:
echo      %SSH_DEPLOY_SCRIPT_PATH%
explorer "%USERPROFILE%\Desktop"
pause
