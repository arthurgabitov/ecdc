import time
import json
import os
from config import Config

class StationController:
    def __init__(self, config: Config):
        self.config = config
        self.config.set_controller(self)
        self.stations = self.load_stations()
        self.state_file = os.path.join(os.path.dirname(__file__), '..', 'timers_state.json')
        self.timers = self.load_timers_state()

    def load_stations(self):
        settings = self.config.get_app_settings()
        num_stations = settings["stations"]
        return list(range(1, num_stations + 1))

    def get_stations(self):
        return self.stations

    def get_station_by_id(self, station_id):
        return {"id": station_id, "name": f"Station {station_id}"}

    def load_timers_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_timers_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.timers, f, indent=4)

    def get_spot_data(self, station_id: int, spot_id: str):
        if spot_id not in self.timers:
            self.timers[spot_id] = {
                "status": self.config.get_spot_statuses()[0]["name"],  # "Idle" по умолчанию
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
        spot = self.get_spot_data(0, spot_id)
        spot["place"] = {"x": x, "y": y}
        self.save_timers_state()