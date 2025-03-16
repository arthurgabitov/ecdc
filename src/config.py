import json
import os

class Config:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config_data = {}
        try:
            with open(config_path, 'r') as config_file:
                self.config_data = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load config.json at {config_path}. Using default settings. Error: {e}")
            self.config_data = {
                "app_settings": {
                    "title": "ECDC Station Dashboard",
                    "spots": 6,
                    "columns": 2
                }
            }
        self.controller = None

    def set_controller(self, controller):
        """Устанавливаем контроллер после создания."""
        self.controller = controller

    def get_app_settings(self):
        return self.config_data.get("app_settings", {"title": "ECDC Station Dashboard", "spots": 6, "columns": 2})