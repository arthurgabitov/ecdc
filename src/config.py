import json
import os
import flet as ft
import copy
import sys

def get_app_data_path():
    """
    Get the correct path to the application data directory.
    Works both in development mode and in a packaged application.
    """
    # Determine if the application is running as frozen (packaged with PyInstaller)
    if getattr(sys, 'frozen', False):
        # If the application is packaged, use the directory where the executable is located
        app_dir = os.path.dirname(sys.executable)
        # Create a data directory next to the executable if it does not exist
        data_dir = os.path.join(app_dir, 'data')
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except Exception:
                # If unable to create the directory, use the executable directory
                data_dir = app_dir
    else:
        # In development mode, use the current script directory
        data_dir = os.path.dirname(os.path.abspath(__file__))
    
    return data_dir

class Config:
    def __init__(self):
        config_path = os.path.join(get_app_data_path(), 'config.json')
        
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
                    "stations": 1
                },
                "spot_statuses": [
                    {"name": "Unblocked", "color": "WHITE60"},
                    {"name": "Delievery request", "color": "YELLOW_300"},
                    {"name": "In Progress", "color": "GREEN_100"},
                    {"name": "Packing", "color": "RED_200"},
                    {"name": "Pickup request", "color": "RED"}
                ],
                "customization_settings": {
                    "search_directory": "\\\\LUECHFS101\\Shared\\European_Customisation\\ECDC-Customised Robot SW Order File"
                },
                "station_dashboard_grid": {
                    "columns": 2 
                }
            }
            # Save the default configuration if the file is not found
            try:
                with open(config_path, 'w') as config_file:
                    json.dump(self.config_data, config_file, indent=4)
            except Exception:
                # If unable to save, just continue
                pass
                
        self.controller = None
        self._cached_statuses = None
        self._dashboard_test_mode = False

    def set_controller(self, controller):
        self.controller = controller

    def get_app_settings(self):
        return self.config_data.get("app_settings", {
            "title": "ECDC Station Dashboard",
            "spots": 6,
            "columns": 2,
            "stations": 1
        })

    def get_spot_statuses(self):
        if self._cached_statuses is None:
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
                    status["color"] = getattr(ft.Colors, status["color"], ft.Colors.WHITE60)
            self._cached_statuses = statuses
        return self._cached_statuses

    def get_status_names(self):
        return [status["name"] for status in self.get_spot_statuses()]

    def set_dashboard_test_mode(self, enabled: bool):
        self._dashboard_test_mode = enabled

    def is_dashboard_test_mode_enabled(self):
        return self._dashboard_test_mode

    def get_customization_settings(self):
        return self.config_data.get("customization_settings", {
            "search_directory": "\\\\LUECHFS101\\Shared\\European_Customisation\\ECDC-Customised Robot SW Order File"
        })

    def get_station_dashboard_grid(self):
        return self.config_data.get("station_dashboard_grid", {
            "columns": 2  
        })