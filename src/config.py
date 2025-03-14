import configparser
import os

class Config:
    def __init__(self, config_file="config/config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section, key, fallback=0):
        return self.config.getint(section, key, fallback=fallback)

    def get_app_settings(self):
        return {
            "title": self.get("app", "title", "Dashboard"),
            "spots": self.get_int("app", "spots", 6),
            "columns": self.get_int("app", "columns", 2),
            "rows": self.get_int("app", "rows", 3),
            "stations_count": self.get_int("app", "stations_count", 2),
        }

    def get_directories(self):
        return {
            "views": self.get("directories", "views"),
            "controllers": self.get("directories", "controllers"),
            "models": self.get("directories", "models"),
            "source_dir": self.get("directories", "source_dir"),
            "dt_base_dir": self.get("directories", "dt_base_dir"),

        }