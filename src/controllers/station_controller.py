import time
from config import Config

class StationController:
    def __init__(self, config: Config):
        self.config = config
        self.config.set_controller(self)
        self.stations = self.load_stations()
        self.timers = {}

    def load_stations(self):
        return [1, 2, 3]

    def get_stations(self):
        return self.stations

    def get_station_by_id(self, station_id):
        return {"id": station_id, "name": f"Station {station_id}"}

    def get_spot_data(self, station_id: int, spot_id: int):
        if spot_id not in self.timers:
            self.timers[spot_id] = {
                "start_time": 0.0,
                "elapsed_time": 0.0,
                "running": False
            }
        spot = self.timers[spot_id]
        if spot["running"]:
            current_time = time.time()
            spot["elapsed_time"] += current_time - spot["start_time"]
            spot["start_time"] = current_time
        return spot

    def get_timer_value(self, station_id: int, spot_id: int):
        spot = self.get_spot_data(station_id, spot_id)
        return spot["elapsed_time"]

    def start_timer(self, station_id: int, spot_id: int):
        spot = self.get_spot_data(station_id, spot_id)
        if not spot["running"]:
            spot["start_time"] = time.time()
            spot["running"] = True

    def pause_timer(self, station_id: int, spot_id: int):
        spot = self.get_spot_data(station_id, spot_id)
        if spot["running"]:
            spot["elapsed_time"] += time.time() - spot["start_time"]
            spot["running"] = False

    def stop_timer(self, station_id: int, spot_id: int):
        spot = self.get_spot_data(station_id, spot_id)
        if spot["running"]:
            spot["elapsed_time"] += time.time() - spot["start_time"]
        spot["running"] = False