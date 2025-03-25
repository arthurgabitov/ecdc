import time
import json
import os
from config import Config

class StationController:
    def __init__(self, config: Config):
        self.config = config
        self.config.set_controller(self)
        self.stations = self.load_stations()
        self.state_file = os.path.join(os.path.dirname(__file__), '..', 'spots_state.json')
        self.spots = self.load_spots_state()
        self._dirty_spots = set()  
        self.initialize_spots()

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

    def load_spots_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_spots_state(self):
        if not self._dirty_spots: 
            
            return

        
        current_data = self.load_spots_state()

       
        for spot_id in self._dirty_spots:
            current_data[spot_id] = self.spots[spot_id]

       
        try:
            with open(self.state_file, 'w') as f:
                json.dump(current_data, f, indent=4)
            
        except Exception as e:
            
            raise

        
        self._dirty_spots.clear()

    def get_spot_data(self, station_id: int, spot_id: str):
        if spot_id not in self.spots:
            self.spots[spot_id] = {
                "status": self.config.get_spot_statuses()[0]["name"],
                "start_time": 0.0,
                "elapsed_time": 0.0,
                "running": False,
                "wo_number": "",
                
            }
            self._dirty_spots.add(spot_id)  # Новый спот считается изменённым
        spot = self.spots[spot_id]
        if spot["running"] and not spot_id.startswith("station_"):
            current_time = time.time()
            spot["elapsed_time"] += current_time - spot["start_time"]
            spot["start_time"] = current_time
            self._dirty_spots.add(spot_id)  # Помечаем как изменённый
        return spot

    def get_timer_value(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        return spot["elapsed_time"]

    def start_timer(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        if not spot["running"]:
            spot["start_time"] = time.time()
            spot["running"] = True
            self._dirty_spots.add(spot_id)
            self.save_spots_state()

    def pause_timer(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        if spot["running"]:
            spot["elapsed_time"] += time.time() - spot["start_time"]
            spot["running"] = False
            self._dirty_spots.add(spot_id)
            self.save_spots_state()

    def stop_timer(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        if spot["running"]:
            spot["elapsed_time"] += time.time() - spot["start_time"]
        spot["running"] = False
        spot["start_time"] = 0.0
        self._dirty_spots.add(spot_id)
        self.save_spots_state()

    def set_spot_status(self, station_id: int, spot_id: str, status: str):
        spot = self.get_spot_data(station_id, spot_id)
        if status in self.config.get_status_names():
            spot["status"] = status
            self._dirty_spots.add(spot_id)
            self.save_spots_state()

    def set_spot_coordinates(self, spot_id: str, x: float, y: float):
        spot = self.get_spot_data(0, spot_id)
        spot["place"]["x"] = x
        spot["place"]["y"] = y
        self._dirty_spots.add(spot_id)
        

    def reset_spot(self, station_id: int, spot_id: str):
        spot = self.get_spot_data(station_id, spot_id)
        spot["running"] = False
        spot["start_time"] = 0.0
        spot["elapsed_time"] = 0.0
        spot["status"] = self.config.get_status_names()[0]
        spot["wo_number"] = ""
        self._dirty_spots.add(spot_id)
        self.save_spots_state()
        