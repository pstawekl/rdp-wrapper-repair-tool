@echo off
echo Installing RDP Monitor Service...

REM Install package in development mode
python -m pip install -e ..

REM Install and start the service
sc create RDPMonitorService binPath= "%~dp0..\venv\Scripts\python.exe -m src.service.windows_service"
sc description RDPMonitorService "Monitors RDP version changes and updates configuration"
sc config RDPMonitorService start= auto
sc start RDPMonitorService

echo Service installation completed.
pause
