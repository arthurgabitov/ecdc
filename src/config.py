import json
import os
import flet as ft
import copy
import sys

def get_app_data_path():
    """
    Get the correct path to the application data directory.
    Works both in development mode and in a packaged application.
    Uses user's AppData directory to avoid admin privileges.
    """
    # Determine if the application is running as frozen (packaged with PyInstaller)
    if getattr(sys, 'frozen', False):
        # If the application is packaged, use user's AppData directory
        app_name = "ECDC_StationApp"
        if os.name == 'nt':  # Windows
            data_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), app_name)
        else:  # Linux/Mac
            data_dir = os.path.join(os.path.expanduser('~'), f'.{app_name.lower()}')
        
        # Create the data directory if it doesn't exist
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except Exception:
                # Fallback to user's home directory
                data_dir = os.path.expanduser('~')
    else:
        # In development mode, use the current script directory
        data_dir = os.path.dirname(os.path.abspath(__file__))
    
    return data_dir

class Config:
    def __init__(self):
        # First try to load from user's data directory
        data_dir = get_app_data_path()
        config_path = os.path.join(data_dir, 'config.json')
        
        # If config doesn't exist in data directory, try to load from packaged/development location
        if not os.path.exists(config_path):
            source_config = None
            
            if getattr(sys, 'frozen', False):
                # In packaged mode, look for config.json next to executable
                packaged_config = os.path.join(os.path.dirname(sys.executable), 'config.json')
                if os.path.exists(packaged_config):
                    source_config = packaged_config
            else:
                # In development mode, look in src directory
                dev_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
                if os.path.exists(dev_config):
                    source_config = dev_config
            
            # Copy config from source location to user data directory
            if source_config:
                try:
                    import shutil
                    os.makedirs(data_dir, exist_ok=True)
                    shutil.copy2(source_config, config_path)
                except Exception:
                    # If copy fails, use source config directly
                    config_path = source_config
        
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
                    {"name": "Unblocked", "color": "GREY"},
                    {"name": "Delievery request", "color": "YELLOW_500"},
                    {"name": "In Progress", "color": "GREEN_500"},
                    {"name": "Packing", "color": "RED_500"},
                    {"name": "Pickup request", "color": "RED"}
                ],
                "customization_settings": {
                    "search_directory": "\\\\LUECHFS101\\Shared\\European_Customisation\\ECDC-Customised Robot SW Order File"
                },
                "station_dashboard_grid": {
                    "columns": 2 
                }
            }
            # Save the default configuration to user data directory
            try:
                # Ensure the data directory exists
                os.makedirs(data_dir, exist_ok=True)
                # Save to user's data directory
                user_config_path = os.path.join(data_dir, 'config.json')
                with open(user_config_path, 'w') as config_file:
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
                    {"name": "Unblocked", "color": "GREY"},
                    {"name": "Delievery request", "color": "YELLOW_500"},
                    {"name": "In Progress", "color": "GREEN_500"},
                    {"name": "Packing", "color": "RED_500"},
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