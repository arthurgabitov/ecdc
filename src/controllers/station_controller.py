import time
import json
import os
import shutil
from config import Config

class StationController:
    def __init__(self, config: Config):
        self.config = config
        self.config.set_controller(self)
        self.stations = self.load_stations()
        self.state_file = os.path.join(os.path.dirname(__file__), '..', 'timers_state.json')
        self.timers = self.load_timers_state()
        self.initialize_spots()
        self._last_save_time = 0
        self._save_interval = 1.0  
        self._pending_coordinates = {}  

    def load_stations(self):
        settings = self.config.get_app_settings()
        num_stations = settings["stations"]
        return list(range(1, num_stations + 1))

    def get_stations(self):
        return self.stations

    def get_station_by_id(self, station_id):
        return {"id": station_id, "name": f"Station {station_id}"}

    def initialize_spots(self):
        settings = self.config.get_app_settings()
        spots_per_station = settings["spots"]
        for station_id in self.stations:
            for spot_idx in range(1, spots_per_station + 1):
                spot_id = f"{station_id}_{spot_idx}"
                self.get_spot_data(station_id, spot_id)

    def load_timers_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_timers_state_immediate(self):
        
        backup_file = self.state_file + '.bak'
        if os.path.exists(self.state_file):
            try:
                shutil.copy(self.state_file, backup_file)
            except (OSError, IOError) as e:
                print(f"Warning: Failed to create backup {backup_file}: {e}")
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.timers, f, indent=4)
        except (OSError, IOError) as e:
            print(f"Error: Failed to save timers state to {self.state_file}: {e}")

    def save_timers_state(self):
        
        current_time = time.time()
        if current_time - self._last_save_time >= self._save_interval:
            
            for spot_id, (x, y) in self._pending_coordinates.items():
                spot = self.get_spot_data(0, spot_id)
                spot["place"] = {"x": x, "y": y}
            self._pending_coordinates.clear()
            self._save_timers_state_immediate()
            self._last_save_time = current_time

    def get_spot_data(self, station_id: int, spot_id: str):
        if spot_id not in self.timers:
            self.timers[spot_id] = {
                "status": self.config.get_spot_statuses()[0]["name"],
                "start_time": 0.0,
                "elapsed_time": 0.0,
                "running": False,
                "wo_number": "",
                "place": {"x": 0, "y": 0}
            }
        spot = self.timers[spot_id]
        if spot["running"] and not spot_id.startswith("station_"):
            current_time = time.time()
            spot["elapsed_time"] += current_time - spot["start_time"]
            spot["start_time"] = current_time
        return spot

    def get_timer_value(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        return spot["elapsed_time"]

    def start_timer(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        if not spot["running"]:
            spot["start_time"] = time.time()
            spot["running"] = True
            self.save_timers_state()

    def pause_timer(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        if spot["running"]:
            spot["elapsed_time"] += time.time() - spot["start_time"]
            spot["running"] = False
            self.save_timers_state()

    def stop_timer(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        if spot["running"]:
            spot["elapsed_time"] += time.time() - spot["start_time"]
        spot["running"] = False
        self.save_timers_state()

    def set_spot_status(self, station_id: int, spot_id: str, status: str):
        spot = self.get_spot_data(station_id, spot_id)
        if status in self.config.get_status_names():
            spot["status"] = status
            self.save_timers_state()

    def set_spot_coordinates(self, spot_id: str, x: float, y: float):
        
        self._pending_coordinates[spot_id] = (x, y)
        self.save_timers_state() 