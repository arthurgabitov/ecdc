import json
import os
import flet as ft
import copy

class Config:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        self.config_data = {}
        try:
            with open(config_path, 'r') as config_file:
                self.config_data = json.load(config_file)
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            
            self.config_data = {
                "app_settings": {
                    "title": "ECDC Station Dashboard",
                    "spots": 6,
                    "columns": 2,
                    "stations": 10
                },
                "spot_statuses": [
                    {"name": "Idle", "color": "WHITE60"},
                    {"name": "In Progress", "color": "GREEN_100"},
                    {"name": "Maintenance", "color": "ORANGE_100"},
                    {"name": "Completed", "color": "BLUE_100"}
                ]
            }
        self.controller = None

    def set_controller(self, controller):
        self.controller = controller

    def get_app_settings(self):
        return self.config_data.get("app_settings", {
            "title": "ECDC Station Dashboard",
            "spots": 6,
            "columns": 2,
            "stations": 10
        })

    def get_spot_statuses(self):
        default_statuses = [
            {"name": "Unblocked", "color": "WHITE60"},
            {"name": "Delievery request", "color": "YELLOW_300"},
            {"name": "In Progress", "color": "GREEN_100"},
            {"name": "Packing", "color": "RED_200"},
            {"name": "Pickup request", "color": "RED"}
        ]
        
        statuses = copy.deepcopy(self.config_data.get("spot_statuses", default_statuses))
        
        for status in statuses:
            
            if isinstance(status["color"], str):
                status["color"] = getattr(ft.colors, status["color"], ft.colors.WHITE60)
        
        return statuses

    def get_status_names(self):
        return [status["name"] for status in self.get_spot_statuses()]