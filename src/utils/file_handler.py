import ctypes
import logging
import os
from ctypes import wintypes
import win32security
import ntsecuritycon as con

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def save_config_to_file(file_path: str, content: str, append: bool = True) -> bool:
    try:
        if not is_admin():
            logging.warning("Application needs to be run as administrator!")
            return False

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Set proper file permissions
        if not os.path.exists(file_path):
            # Create file with admin permissions
            with open(file_path, 'w') as f:
                f.write(content)
        else:
            mode = 'a' if append else 'w'
            with open(file_path, mode) as f:
                if append:
                    # Add two newlines to ensure one empty line between configs
                    f.write(f"\n\n{content}")
                else:
                    f.write(content)

        return True
    except Exception as e:
        logging.error(f"Failed to save configuration: {e}")
        return False
