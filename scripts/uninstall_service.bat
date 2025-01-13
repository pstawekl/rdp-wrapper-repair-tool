REM filepath: /c:/Users/admin/Documents/vsc_projects/rdp-wrapper-repair-tool/scripts/uninstall_service.bat
@echo off
setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrative privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo Uninstalling RDP Monitor Service...

REM Force kill any running service processes
for /f "tokens=1" %%p in ('tasklist ^| findstr "RDPMonitorService"') do (
    taskkill /F /IM "%%p" /T >nul 2>&1
)

REM Stop and remove service with force
sc stop RDPMonitorService >nul 2>&1
timeout /t 2 /nobreak >nul
sc delete RDPMonitorService >nul 2>&1

REM Additional cleanup - remove service from registry
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\RDPMonitorService" /f >nul 2>&1

REM Clean up any remaining service files
if exist "%ProgramFiles%\RDPMonitorService" rd /s /q "%ProgramFiles%\RDPMonitorService" >nul 2>&1
if exist "%ProgramFiles(x86)%\RDPMonitorService" rd /s /q "%ProgramFiles(x86)%\RDPMonitorService" >nul 2>&1

echo Uninstalling Python package...
python -m pip uninstall rdp_monitor_service -y >nul 2>&1

REM Final verification
sc query RDPMonitorService >nul 2>&1
if !errorLevel! equ 0 (
    echo ERROR: Service could not be completely removed.
    echo Please restart your computer and try again.
) else (
    echo Service successfully removed from system.
)

echo Service uninstallation completed.
pause
