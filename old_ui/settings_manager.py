import json
import os

class SettingsManager:
    SETTINGS_FILE = "settings.json"

    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, 'r') as f:
                return json.load(f)
        return {"theme": "light"}  # default

    def save_settings(self):
        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

settings_manager = SettingsManager()