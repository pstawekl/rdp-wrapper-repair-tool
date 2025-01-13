@echo off
setlocal enabledelayedexpansion

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrative privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo Installing RDP Monitor Service...

REM Kill any running processes first
taskkill /F /FI "SERVICES eq RDPMonitorService" /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM Force stop and remove existing service
sc stop RDPMonitorService >nul 2>&1
timeout /t 2 /nobreak >nul
sc delete RDPMonitorService >nul 2>&1
timeout /t 2 /nobreak >nul

REM Clean registry
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\RDPMonitorService" /f >nul 2>&1
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\Eventlog\Application\RDPMonitorService" /f >nul 2>&1

REM Wait until service is completely removed with timeout
set "retries=0"
:wait_loop
sc query RDPMonitorService >nul 2>&1
if !errorLevel! neq 1060 (
    set /a "retries+=1"
    if !retries! gtr 10 (
        echo Service removal is stuck. Please restart your computer.
        pause
        exit /b 1
    )
    echo Waiting for service cleanup... Attempt !retries!/10
    timeout /t 3 /nobreak >nul
    goto wait_loop
)

REM Additional forced cleanup
net stop RDPMonitorService /y >nul

REM Clean existing directories
rd /s /q "%ProgramFiles%\RDPMonitorService" 2>nul
rd /s /q "%ProgramFiles(x86)%\RDPMonitorService" 2>nul
rd /s /q "..\venv" 2>nul

REM Create fresh Python environment
python -m venv ..\venv
call ..\venv\Scripts\activate.bat
python -m pip install -r ..\requirements.txt
python -m pip install -e ..

REM Install service with full path
set "PYTHON_PATH=%~dp0..\venv\Scripts\pythonw.exe"
set "SERVICE_SCRIPT=%~dp0..\src\service\windows_service.py"

echo Creating new service...
sc create RDPMonitorService binPath= "%PYTHON_PATH% %SERVICE_SCRIPT%" start= auto
if !errorLevel! neq 0 (
    echo Failed to create service. Error code: !errorLevel!
    pause
    exit /b 1
)

sc description RDPMonitorService "Monitors RDP version changes and updates configuration"
sc start RDPMonitorService

echo Verifying service installation...
sc query RDPMonitorService >nul 2>&1
if !errorLevel! equ 0 (
    echo Service successfully installed.
) else (
    echo Warning: Service installation may have failed.
)

pause
