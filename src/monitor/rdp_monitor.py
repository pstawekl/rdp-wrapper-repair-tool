import logging
import os
import time
import winreg
from typing import Callable, Optional

import win32api


class RDPMonitor:
    def __init__(self, config):
        self.config = config
        self.current_version = self._get_rdp_version()
        self.callback: Optional[Callable[[str], None]] = None
        self._running = False

    def _get_rdp_version(self) -> str:
        # Try getting version from mstsc.exe first
        try:
            rdp_path = os.path.join(
                os.getenv('SystemRoot'), 'System32', 'mstsc.exe')
            info = win32api.GetFileVersionInfo(rdp_path, "\\")
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            logging.info(f"Found RDP version {version} from mstsc.exe")
            return version
        except Exception as e:
            logging.debug(f"Failed to get version from mstsc.exe: {e}")

            # Fallback to registry method
            registry_paths = [
                r"SYSTEM\CurrentControlSet\Control\Terminal Server\Wds\rdpwd\Tds\tcp",
                r"SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp",
                self.config.monitoring_settings["rdp_registry_path"]
            ]

            for path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                        for value_name in ["CurrentVersion", "TerminalVersion", "ServerVersion"]:
                            try:
                                value, _ = winreg.QueryValueEx(key, value_name)
                                logging.info(
                                    f"Found RDP version {value} in registry at {path}")
                                return value
                            except WindowsError:
                                continue
                except WindowsError as e:
                    logging.debug(
                        f"Failed to read from registry path {path}: {e}")
                    continue

            logging.error("Could not find RDP version in any location")
            return ""

    def start_monitoring(self, callback: Callable[[str], None]):
        self.callback = callback
        self._running = True

        while self._running:
            new_version = self._get_rdp_version()
            if new_version != self.current_version:
                logging.info(
                    f"RDP version changed from {self.current_version} to {new_version}")
                self.current_version = new_version
                if self.callback:
                    self.callback(new_version)

            time.sleep(self.config.monitoring_settings["check_interval"])

    def stop_monitoring(self):
        self._running = False
