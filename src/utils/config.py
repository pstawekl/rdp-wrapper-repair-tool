import json
import os


class Config:
    def __init__(self):
        self.config_path = "app_settings.json"
        self.settings = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file {self.config_path} not found")

        with open(self.config_path, 'r') as f:
            return json.load(f)

    @property
    def is_development(self):
        return self.settings["app_mode"] == "development"

    @property
    def rdp_ini_path(self):
        return self.settings["path_to_ini"]

    @property
    def github_settings(self):
        return self.settings["github"]

    @property
    def monitoring_settings(self):
        return self.settings["monitoring"]

    @property
    def github_token(self):
        return self.settings["github"].get("token")
