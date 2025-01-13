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

echo Cleaning stuck services...

REM Kill any related processes
taskkill /F /IM RDPMonitorService.exe /T >nul 2>&1
net stop RDPMonitorService /y >nul 2>&1

REM Clean registry entries more thoroughly
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\RDPMonitorService" /f >nul 2>&1
reg delete "HKLM\SYSTEM\ControlSet001\Services\RDPMonitorService" /f >nul 2>&1
reg delete "HKLM\SYSTEM\ControlSet002\Services\RDPMonitorService" /f >nul 2>&1

REM Remove service with sc
sc delete RDPMonitorService >nul 2>&1

REM Clean pending delete flags
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager" /v PendingFileRenameOperations /f >nul 2>&1

echo Cleanup complete. A system restart is required.
echo After restart, run install_service.bat to reinstall the service.
pause