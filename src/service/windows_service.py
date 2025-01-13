import logging
import os
import sys
from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil

from ..monitor.rdp_monitor import RDPMonitor
from ..utils.config import Config
from ..utils.file_handler import save_config_to_file
from ..utils.github_client import GitHubClient


class RDPMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "RDPMonitorService"
    _svc_display_name_ = "RDP Monitor Service"
    _svc_description_ = "Monitors RDP version changes and updates configuration"
    _svc_deps_ = ["TermService"]  # Zależność od usługi Remote Desktop

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

        # Ustaw ścieżkę logów w katalogu ProgramData
        log_dir = Path(os.environ.get('PROGRAMDATA', '')) / \
            "RDP Monitor Service"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "rdp_monitor_service.log"
            if not log_file.exists():
                log_file.touch(mode=0o644)
        except PermissionError:
            # Fallback to temp directory if ProgramData is not accessible
            log_dir = Path(os.environ.get('TEMP', '')) / "RDP Monitor Service"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "rdp_monitor_service.log"

        # Konfiguracja logowania
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        try:
            self.config = Config()
            self.rdp_monitor = RDPMonitor(self.config)
            self.github_client = GitHubClient(self.config)
            logging.info("Service initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize service: {e}")
            raise

    def SvcStop(self):
        """
        Called when the service is stopping.
        """
        logging.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.rdp_monitor.stop_monitoring()

    def SvcDoRun(self):
        """
        Called when the service is starting.
        """
        try:
            logging.info("Service is starting")
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.main()
        except Exception as e:
            logging.error(f"Service failed: {e}")
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            raise

    def main(self):
        def on_rdp_version_change(new_version: str):
            try:
                logging.info(f"RDP version change detected: {new_version}")
                config_content = self.github_client.find_rdp_config(
                    new_version)
                if config_content:
                    if save_config_to_file(self.config.rdp_ini_path, config_content, append=True):
                        logging.info(
                            f"Updated RDP configuration for version {new_version}")
                    else:
                        logging.error(
                            "Failed to save configuration due to permission issues")
            except Exception as e:
                logging.error(f"Failed to update configuration: {e}")

        self.rdp_monitor.start_monitoring(on_rdp_version_change)


# Kod do instalacji/usuwania usługi
if __name__ == '__main__':
    if len(sys.argv) == 1:
        try:
            logging.info("Starting service control dispatcher")
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(RDPMonitorService)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception as e:
            logging.error(f"Service control dispatcher failed: {e}")
            raise
    else:
        win32serviceutil.HandleCommandLine(RDPMonitorService)
