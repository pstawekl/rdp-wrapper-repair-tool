# RDP Wrapper Repair Tool by pstawekl

I have created an application that works as a system service, allowing for the automatic fixing of the RDP Wrapper error - Listener state: Not listening.

# How to install it in the system?

## The application has two modes of operation:
- DEV
- PROD

### DEV
Allows for a one-time execution of the application in PowerShell. Administrator privileges are required. The application will return the correct configuration for `rdpwrap.ini` in the PowerShell window and save it to a file.

### PROD
The application runs as a service in Windows. It automatically detects changes in the RDP version in the Windows system and adds the correct configuration to the `rdpwrap.ini` file.

# How to install the service?
Configure the `app_settings.json` file. Add your GitHub token and define the correct path to the `rdpwrap.ini` file.  
Then, open PowerShell with administrator privileges. Navigate to the application's folder /scripts and execute the following command:
`install.bat`

If you want to install the application manually, follow these steps:
`.venv\Scripts\activate
pip install -r requirements.txt
python setup.py install
python -m src install

# Start service:
net start RDPMonitorService

# Stop service:
net stop RDPMonitorService

# Remove service:
python -m src remove`

Open Services (services.msc)
Look for "RDP Monitor Service"
Check service status
Service will auto-start on system boot when installed.
