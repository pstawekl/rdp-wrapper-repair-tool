import logging
import sys
import ctypes
import win32serviceutil

from .monitor.rdp_monitor import RDPMonitor
from .service.windows_service import RDPMonitorService
from .utils.config import Config
from .utils.github_client import GitHubClient
from .utils.file_handler import save_config_to_file, is_admin


def elevate_privileges():
    if not is_admin():
        print("Requesting administrator privileges...")
        if sys.platform == 'win32':
            script = sys.argv[0]
            params = ' '.join(sys.argv[1:])
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            if ret > 32:
                return True
            else:
                print("Failed to get administrator privileges")
                return False
    return True

def run_dev_mode():
    if not is_admin():
        if elevate_privileges():
            return  # Original process exits, elevated process continues
        sys.exit(1)  # Exit if elevation failed

    config = Config()
    rdp_monitor = RDPMonitor(config)
    github_client = GitHubClient(config)

    print("Starting RDP Monitor in DEV mode (with admin privileges)...")
    current_version = rdp_monitor._get_rdp_version()
    # current_version = "10.0.22621.4249"
    print(f"Current RDP version: {current_version}")

    # Check configuration for current version immediately
    print("Searching for config for current version...")
    initial_config = github_client.find_rdp_config(current_version)
    if initial_config:
        print("\nFound configuration for current version:")
        print("-" * 50)
        print(initial_config)
        print("-" * 50)
        
        print(f"\nSaving configuration to {config.rdp_ini_path}...")
        if save_config_to_file(config.rdp_ini_path, initial_config):
            print("Configuration saved successfully!")
        else:
            print("Failed to save configuration. Make sure you run the program as administrator.")
    else:
        print("No configuration found for current version")

    def on_version_change(new_version: str):
        print(f"\nDetected RDP version change: {new_version}")
        print("Searching for config...")
        config_content = github_client.find_rdp_config(new_version)
        if config_content:
            print("\nFound configuration:")
            print("-" * 50)
            print(config_content)
            print("-" * 50)
            
            if save_config_to_file(config.rdp_ini_path, config_content):
                print("Configuration saved successfully!")
            else:
                print("Failed to save configuration. Make sure you run the program as administrator.")
        else:
            print("No configuration found for this version")

    rdp_monitor.start_monitoring(on_version_change)


def main():
    try:
        config = Config()

        if config.is_development:
            try:
                run_dev_mode()
            except KeyboardInterrupt:
                print("\nStopping DEV mode...")
            except Exception as e:
                logging.error(f"Development mode error: {e}")
                sys.exit(1)
        else:
            win32serviceutil.HandleCommandLine(RDPMonitorService)
    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
