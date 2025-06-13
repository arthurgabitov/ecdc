import time
import json
import os
from config import Config, get_app_data_path

class StationController:
    def __init__(self, config: Config):
        self.config = config
        self.config.set_controller(self)
        self.stations = self.load_stations()
        
        # Use get_app_data_path to determine the correct data directory
        data_dir = get_app_data_path()
        self.state_file = os.path.join(data_dir, 'spots_state.json')
        
        self.spots = {}  # Теперь всегда dict[station_id][spot_id]
        self._dirty_spots = set()  # Track modified spots
        self.initialize_spots()    # Сначала инициализация структуры
        self.load_spots_state()    # Затем загрузка состояния

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
            if station_id not in self.spots:
                self.spots[station_id] = {}
            for spot_idx in range(1, spots_per_station + 1):
                spot_id = f"{station_id}_{spot_idx}"
                if spot_id not in self.spots[station_id]:
                    self.spots[station_id][spot_id] = {
                        "status": self.config.get_spot_statuses()[0]["name"],
                        "start_time": 0.0,
                        "elapsed_time": 0.0,
                        "running": False,
                        "wo_number": "",
                    }

    def load_spots_state(self):
        """Load all spots' WO numbers, timer states, and status from a JSON file"""
        path = "src/spots_state.json"
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        for station_id, spots in state.items():
            # Support both int and string keys (e.g., '1' or 'station_1')
            try:
                sid = int(station_id)
            except ValueError:
                # Try to extract number from string like 'station_1'
                if station_id.startswith("station_"):
                    sid = int(station_id.split("station_")[-1])
                else:
                    continue
            if sid in self.spots:
                for spot_id, spot_state in spots.items():
                    if spot_id in self.spots[sid]:
                        self.spots[sid][spot_id]["wo_number"] = spot_state.get("wo_number", "")
                        self.spots[sid][spot_id]["elapsed_time"] = spot_state.get("elapsed_time", 0)
                        self.spots[sid][spot_id]["running"] = spot_state.get("running", False)
                        self.spots[sid][spot_id]["status"] = spot_state.get("status", self.config.get_spot_statuses()[0]["name"])
                        self.spots[sid][spot_id]["start_time"] = spot_state.get("start_time", 0.0)
                        # Корректно восстанавливать elapsed_time, если таймер был запущен
                        if self.spots[sid][spot_id]["running"] and self.spots[sid][spot_id]["start_time"]:
                            now = time.time()
                            self.spots[sid][spot_id]["elapsed_time"] += now - self.spots[sid][spot_id]["start_time"]
                            self.spots[sid][spot_id]["start_time"] = now

    def save_spots_state(self):
        """Save all spots' WO numbers, timer states, and status to a JSON file"""
        state = {}
        # self.spots: {station_id: {spot_id: spot_dict}} или {spot_id: spot_dict}
        # Авто-определение структуры
        if all(isinstance(v, dict) and all(isinstance(sv, dict) for sv in v.values()) for v in self.spots.values()):
            # Структура: {station_id: {spot_id: spot_dict}}
            for station_id, spots in self.spots.items():
                state[str(station_id)] = {}
                for spot_id, spot in spots.items():
                    state[str(station_id)][spot_id] = {
                        "wo_number": spot.get("wo_number", ""),
                        "elapsed_time": spot.get("elapsed_time", 0),
                        "running": spot.get("running", False),
                        "status": spot.get("status", self.config.get_spot_statuses()[0]["name"]),
                        "start_time": spot.get("start_time", 0.0)
                    }
        else:
            # Структура: {spot_id: spot_dict}
            for spot_id, spot in self.spots.items():
                state[spot_id] = {
                    "wo_number": spot.get("wo_number", ""),
                    "elapsed_time": spot.get("elapsed_time", 0),
                    "running": spot.get("running", False),
                    "status": spot.get("status", self.config.get_spot_statuses()[0]["name"])
                }
        with open("src/spots_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f)

    def get_spot_data(self, station_id: int, spot_id: str):
        if station_id not in self.spots:
            self.spots[station_id] = {}
        if spot_id not in self.spots[station_id]:
            self.spots[station_id][spot_id] = {
                "status": self.config.get_spot_statuses()[0]["name"],
                "start_time": 0.0,
                "elapsed_time": 0.0,
                "running": False,
                "wo_number": "",
            }
            self._dirty_spots.add(spot_id)  # Mark new spot as modified
        spot = self.spots[station_id][spot_id]
        if spot["running"] and not spot_id.startswith("station_"):
            current_time = time.time()
            spot["elapsed_time"] += current_time - spot["start_time"]
            spot["start_time"] = current_time
            self._dirty_spots.add(spot_id)  # Mark as modified
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

    def set_spot_coordinates(self, station_id: int, spot_id: str, x: float, y: float):
        spot = self.get_spot_data(station_id, spot_id)
        if "place" not in spot:
            spot["place"] = {"x": 0, "y": 0}
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
