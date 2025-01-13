@echo off
echo Uninstalling RDP Monitor Service...

REM Stop the service if it's running
sc stop RDPMonitorService
timeout /t 2 /nobreak > nul

REM Delete the service
sc delete RDPMonitorService

REM Uninstall package
python -m pip uninstall rdp_monitor_service -y

echo Service uninstallation completed.
pause
